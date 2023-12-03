from collections import defaultdict, deque
import random
from typing import Generator
import itertools

import pygame
from pygame import Vector2, Color

from src.entity import Corpse, Entity, DummyEntity
from src.oil_spill import OilSpill
from src.player import Player
from src.enums import EntityType, EnemyType, ProjectileType
from src.projectile import Projectile, ProjectileType
from src.utils import Timer, Feedback
from src.energy_orb import EnergyOrb
from src.exceptions import OnCooldown, NotEnoughEnergy, ShootingDirectionUndefined
from src.enemy import ENEMY_SIZE_MAP, ENEMY_TYPE_TO_CLASS, Enemy

from config import (REMOVE_DEAD_ENTITIES_EVERY, ENERGY_ORB_DEFAULT_ENERGY, ENERGY_ORB_LIFETIME_RANGE,
    INCREASE_LEVEL_EVERY, GAME_MAX_LEVEL, ENERGY_ORB_SIZE, ENERGY_ORB_COOLDOWN_RANGE, SPAWN_ENEMY_EVERY, BM)


def get_enemy_type_prob_weights(level: int) -> dict[EnemyType, float]:
    return {
        EnemyType.BASIC: 200,
        EnemyType.FAST: (level - 1) * 10,
        EnemyType.ARTILLERY: level * 8,
        EnemyType.TANK: 10 + level * 5,
        EnemyType.BOSS: 0.,
    }


class Game:
    def __init__(self, screen_rectangle: pygame.Rect) -> None:
        self.level = 1
        self.time = 0.
        self.paused = False
        self.screen_rectangle = screen_rectangle
        
        self.feedback_buffer: deque[Feedback] = deque()
        self._last_fps: float = 0.

        # entities:
        self.player = Player(Vector2(*self.screen_rectangle.center))
        self.e_dummies: list[DummyEntity] = []
        self.e_oil_spills: list[OilSpill] = []
        self.e_corpses: list[Corpse] = []
        self.e_projectiles: list[Projectile] = []
        self.e_energy_orbs: list[EnergyOrb] = []
        self.e_enemies: list[Enemy] = []

        self.remove_dead_entities_timer = Timer(max_time=REMOVE_DEAD_ENTITIES_EVERY)
        self.one_wave_timer = Timer(max_time=INCREASE_LEVEL_EVERY)
        self.new_energy_orb_timer = Timer(max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
        self.current_spawn_enemy_cooldown = SPAWN_ENEMY_EVERY
        self.spawn_enemy_timer = Timer(max_time=self.current_spawn_enemy_cooldown)
        self.reason_of_death = ''

    def all_entities_iter(self, 
            with_player: bool = True,
            include_dead: bool = False
        ) -> Generator[Entity, None, None]:
        yield from self.oil_spills(include_dead)
        yield from self.corpses(include_dead)
        yield from self.projectiles(include_dead)
        yield from self.energy_orbs(include_dead)
        yield from self.enemies(include_dead)
        yield from self.dummies(include_dead)
        if with_player: yield self.player

    def oil_spills(self, include_dead: bool = False) -> Generator[OilSpill, None, None]:
        yield from (ent for ent in self.e_oil_spills if include_dead or ent.is_alive())
    def corpses(self, include_dead: bool = False) -> Generator[Corpse, None, None]:
        yield from (ent for ent in self.e_corpses if include_dead or ent.is_alive())
    def projectiles(self, include_dead: bool = False) -> Generator[Projectile, None, None]:
        yield from (ent for ent in self.e_projectiles if include_dead or ent.is_alive())
    def energy_orbs(self, include_dead: bool = False) -> Generator[EnergyOrb, None, None]:
        yield from (ent for ent in self.e_energy_orbs if include_dead or ent.is_alive())
    def enemies(self, include_dead: bool = False) -> Generator[Enemy, None, None]:
        yield from (ent for ent in self.e_enemies if include_dead or ent.is_alive())
    def dummies(self, include_dead: bool = False) -> Generator[DummyEntity, None, None]:
        yield from (ent for ent in self.e_dummies if include_dead or ent.is_alive())

    def is_running(self) -> bool:
        return self.player.is_alive()
    
    def toggle_pause(self) -> None: self.paused = not self.paused

    def new_level(self) -> bool:
        self.feedback_buffer.append(Feedback(f'new wave!', 3.5, color=Color('green'), at_pos='cursor'))
        if self.level >= GAME_MAX_LEVEL: return False
        print(f'new wave! new level: {self.level}')
        self.feedback_buffer.append(Feedback(f'new level: {self.level}', 3.5, color=Color('green'), at_pos='player'))
        self.level += 1
        self.player.new_level()
        self.current_spawn_enemy_cooldown *= 0.93
        return True

    def kill_projectiles(self):
        for projectile in self.projectiles():
            projectile.kill()
    
    def spawn_energy_orb(self):
        self.add_entity(
            EnergyOrb(
                pos=self.get_random_screen_position_for_entity(entity_size=ENERGY_ORB_SIZE),
                lifetime=random.uniform(*ENERGY_ORB_LIFETIME_RANGE) + 1. * (self.level - 1),
                energy=ENERGY_ORB_DEFAULT_ENERGY + 20. * (self.level - 1)
            )
        )

    def spawn_enemy(self, enemy_type: EnemyType):
        position = self.get_random_screen_position_for_entity(entity_size=ENEMY_SIZE_MAP[enemy_type])
        self.add_entity(
            ENEMY_TYPE_TO_CLASS[enemy_type](
                pos=position,
                player=self.player,
            )
        )
    
    def spawn_random_enemy(self):
        """Is called once every SPAWN_ENEMY_EVERY seconds."""
        type_weights = get_enemy_type_prob_weights(level=self.level)
        enemy_type = random.choices(
            list(type_weights.keys()), 
            list(type_weights.values()), 
        k=1)[0]
        self.spawn_enemy(enemy_type)

    def process_timers(self, time_delta: float) -> None:
        """Process events that happen periodically."""
        self.remove_dead_entities_timer.tick(time_delta)
        if not self.remove_dead_entities_timer.running():
            self.remove_dead_entities()
            self.remove_dead_entities_timer.reset()
            print('Removed dead entities')
        self.one_wave_timer.tick(time_delta)
        if not self.one_wave_timer.running():
            self.one_wave_timer.reset()
            # spawn boss at the end of the wave unless one is already alive
            if any(ent._enemy_type == EnemyType.BOSS for ent in self.enemies()):
                print('tried to spawn a new boss, but one is still alive')
                self.feedback_buffer.append(Feedback('boss is still alive!', 2., color=Color('red')))
                return
            self.spawn_enemy(EnemyType.BOSS)
            print('Increased level')
        self.new_energy_orb_timer.tick(time_delta)
        if not self.new_energy_orb_timer.running():
            self.spawn_energy_orb()
            self.new_energy_orb_timer.reset(with_max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
            print('Spawned energy orb')
        self.spawn_enemy_timer.tick(time_delta)
        if not self.spawn_enemy_timer.running():
            self.spawn_random_enemy()
            self.spawn_enemy_timer.reset(with_max_time=self.current_spawn_enemy_cooldown)
            print('Spawned enemy')

    def update(self, time_delta: float) -> None:
        if not self.is_running() or self.paused: return
        self.time += time_delta
        for entity in self.all_entities_iter():
            entity.update(time_delta)
        self.process_timers(time_delta)
        self.process_collisions()
        self.spawn_buffered_entities()
    
    def player_try_shooting(self):
        try:
            new_projectile = self.player.shoot()
        except OnCooldown as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            print(e)
        except NotEnoughEnergy as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            print(e)
        except ShootingDirectionUndefined as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            print(e)
        else:
            self.add_entity(new_projectile)

    def player_try_spawning_energy_orb(self):
        try: new_energy_orb = self.player.spawn_energy_orb()
        except NotEnoughEnergy as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            print(e)
        else:
            self.add_entity(new_energy_orb)

    def spawn_buffered_entities(self) -> None:
        """
        Spawn all entities that are in the buffer of the other entities.
        """
        new_ent = []
        # TODO: this is confusing: 
        #       the player can spawn entities, but player._can_spawn_entities is False
        for entity in self.all_entities_iter(with_player=False, include_dead=True):
            if entity.can_spawn_entities:
                new_ent.extend(entity.entities_buffer)
                entity.entities_buffer.clear()
        for ent in new_ent:
            self.add_entity(ent)

    def reflect_entities_vel(self,) -> None:
        """
        Reflect the velocity of all entities that are outside of the screen.
        Add some delta to the position to prevent the entity from getting stuck.
        """
        delta = 10.
        for entity in self.all_entities_iter(with_player=False):
            pos_ = entity.get_pos()
            if entity.is_alive() and not self.screen_rectangle.collidepoint(pos_):
                if entity.get_type() == EntityType.PROJECTILE:
                    entity._ricochet_count += 1 # type: ignore
                if pos_.x < self.screen_rectangle.left:
                    entity.vel.x *= -1.
                    entity.pos.x += delta
                if pos_.x > self.screen_rectangle.right:
                    entity.vel.x *= -1.
                    entity.pos.x -= delta
                if pos_.y < self.screen_rectangle.top:
                    entity.vel.y *= -1.
                    entity.pos.y += delta
                if pos_.y > self.screen_rectangle.bottom:
                    entity.vel.y *= -1.
                    entity.pos.y -= delta
    
    def process_collisions(self) -> None:
        # player collides with anything:
        for eo in self.energy_orbs():
            if not eo.intersects(self.player): continue
            energy_collected: float = eo.energy_left()
            self.player.energy.change(energy_collected)
            if not eo.spawned_by_player:
                # count stats only for env energy orbs
                self.player.get_stats().ENERGY_ORBS_COLLECTED += 1
                self.player.get_stats().ENERGY_COLLECTED += energy_collected
            eo.kill()
            self.feedback_buffer.append(Feedback(f'+{energy_collected:.0f}e', color=pygame.Color('magenta')))
        for projectile in self.projectiles():
            if not projectile.intersects(self.player): continue
            damage_taken_actual = -self.player.health.change(-projectile._damage)
            self.player.get_stats().BULLETS_CAUGHT += 1
            self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
            projectile.kill()
            self.feedback_buffer.append(Feedback(f'-{damage_taken_actual:.0f}hp', 2.5, color=pygame.Color('red')))
            self.reason_of_death = f'caught Bullet::{projectile._projectile_type.name.title()}'
        for enemy in self.enemies():
            if not enemy.intersects(self.player): continue
            damage_taken_actual = -self.player.health.change(-enemy._damage_on_collision)
            self.player.get_stats().ENEMIES_COLLIDED_WITH += 1
            self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
            enemy.kill()
            self.feedback_buffer.append(Feedback('collided!', 3.5, color=pygame.Color('pink')))
            self.feedback_buffer.append(Feedback(f'-{damage_taken_actual:.1f}hp', 2., color=pygame.Color('orange'), at_pos='player'))
            self.reason_of_death = f'collided with Enemy::{enemy._enemy_type.name.title()}'
        for corpse in self.corpses():
            if not corpse.intersects(self.player): continue
            damage_taken_actual = -self.player.health.change(-corpse._damage_on_collision)
            self.player.get_stats().ENEMIES_COLLIDED_WITH += 1
            self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
            corpse.kill()
            self.feedback_buffer.append(Feedback('collided!', 3.5, color=pygame.Color('pink')))
            self.feedback_buffer.append(Feedback(f'-{damage_taken_actual:.1f}hp', 2., color=pygame.Color('orange'), at_pos='player'))
            self.reason_of_death = f'collided with Corpse'
        for oil_spill in self.oil_spills():
            if not oil_spill.intersects(self.player): continue
            self.player.effect_flags.OIL_SPILL = True
            self.reason_of_death = 'slipped on oil to death'

        # player bullets collide with enemies -> enemies get damage, player gets energy:
        player_bullets = [el for el in self.projectiles() if el._projectile_type == ProjectileType.PLAYER_BULLET]
        for bullet in player_bullets:
            for enemy in self.enemies():
                if not bullet.intersects(enemy): continue
                bullet.kill()
                self.player.get_stats().ACCURATE_SHOTS += 1
                print('accurate shot')
                damage_dealt = bullet._damage
                damage_dealt_actual = -enemy.get_health().change(-damage_dealt)
                self.player.get_stats().DAMAGE_DEALT += damage_dealt_actual
                self.feedback_buffer.append(Feedback(f'-{damage_dealt_actual:.1f}hp', 2., color=pygame.Color('orange'), at_pos=enemy.get_pos()))
                enemy.update(0.)
                if enemy.is_alive(): continue
                enemy.kill()
                reward = enemy.get_reward()
                self.player.energy.change(reward)
                self.player.get_stats().ENEMIES_KILLED += 1
                self.player.get_stats().ENERGY_COLLECTED += reward
                if enemy._enemy_type == EnemyType.BOSS:
                    # killed the boss
                    self.new_level()
                    self.kill_projectiles()
                    if bullet._ricochet_count > 0 and not self.player.get_achievements().KILL_BOSS_RICOCHET:
                        print('new achievement: killed boss with ricochet')
                        self.player.get_achievements().KILL_BOSS_RICOCHET = True
                        self.feedback_buffer.append(Feedback('killed boss with ricochet!', 3., color=pygame.Color('blue')))
                print(f'enemy killed: {enemy._enemy_type.name}')
                self.feedback_buffer.append(Feedback(f'+{reward:.1f}e', 2., color=pygame.Color('magenta')))
        
        # enemy-enemy collisions
        MULT = 0.4
        for enem1, enem2 in itertools.combinations(self.enemies(), 2):
            if enem1.intersects(enem2):
                if enem1.intersects(enem2):
                    vec_between = enem2.get_pos() - enem1.get_pos() # 1 -> 2
                    enem1.pos -= vec_between * MULT; enem2.pos += vec_between * MULT

    def add_entity(self, entity: Entity) -> None:
        ent_type = entity.get_type()
        if ent_type == EntityType.ENERGY_ORB:
            self.e_energy_orbs.append(entity) # type: ignore
        elif ent_type == EntityType.ENEMY:
            self.e_enemies.append(entity) # type: ignore
        elif ent_type == EntityType.PROJECTILE:
            self.e_projectiles.append(entity) # type: ignore
        elif ent_type == EntityType.CORPSE:
            self.e_corpses.append(entity) # type: ignore
        elif ent_type == EntityType.DUMMY:
            self.e_dummies.append(entity) # type: ignore
        elif ent_type == EntityType.OIL_SPILL:
            self.e_oil_spills.append(entity) # type: ignore
        else:
            raise ValueError(f'Unknown entity type {ent_type}')

    def remove_dead_entities(self):
        """
        Remove all dead entities.
        This function is called every REMOVE_DEAD_ENTITIES_EVERY seconds.
        """
        self.e_dummies: list[DummyEntity] = list(self.dummies())
        self.e_oil_spills: list[OilSpill] = list(self.oil_spills())
        self.e_corpses: list[Corpse] = list(self.corpses())
        self.e_projectiles: list[Projectile] = list(self.projectiles())
        self.e_energy_orbs: list[EnergyOrb] = list(self.energy_orbs())
        self.e_enemies: list[Enemy] = list(self.enemies())

    def get_random_screen_position_for_entity(self, entity_size: float) -> Vector2:
        """
        Get a random position inside the screen.
        Try a position and return it if it doesn't collide with any other entity.
        """
        while True:
            pos_candidate = self.get_random_screen_position()
            dummy = DummyEntity(pos_candidate, entity_size)
            if (pos_candidate - self.player.get_pos()).magnitude_squared() > 400.**2 and\
                not any(entity.intersects(dummy) for entity in self.all_entities_iter()):
                    return pos_candidate
    

    def get_random_screen_position(self) -> Vector2:
        x = random.uniform(self.screen_rectangle.left + BM * 10, self.screen_rectangle.right - BM * 10)
        y = random.uniform(self.screen_rectangle.top + BM * 10, self.screen_rectangle.bottom - BM * 10)
        return Vector2(x, y)
    
    def set_last_fps(self, fps: float):
        self._last_fps = fps

    def get_last_fps(self) -> float:
        return self._last_fps

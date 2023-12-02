from collections import defaultdict, deque
import random
from typing import Generator

import pygame
from pygame import Vector2, Color

from config import (REMOVE_DEAD_ENTITIES_EVERY, PLAYER_STARTING_POSITION, ENERGY_ORB_DEFAULT_ENERGY, ENERGY_ORB_LIFETIME_RANGE,
    INCREASE_LEVEL_EVERY, GAME_MAX_LEVEL, ENERGY_ORB_SIZE, ENERGY_ORB_COOLDOWN_RANGE, SPAWN_ENEMY_EVERY, BM)
from src import DummyEntity, Player, Timer, Entity, EntityType, EnergyOrb, EnemyType, ProjectileType, Feedback
from src.exceptions import OnCooldown, NotEnoughEnergy, ShootingDirectionUndefined
from src.enemy import ENEMY_STATS_MAP, BasicEnemy, TankEnemy, ArtilleryEnemy, BossEnemy, FastEnemy, ENEMY_TYPE_TO_CLASS


class Game:
    def __init__(self, screen_rectangle: pygame.Rect) -> None:
        self._level = 1
        self._time = 0.
        self._paused = False
        self.screen_rectangle = screen_rectangle
        
        self.feedback_buffer: deque[Feedback] = deque()
        self._last_fps: float = 0.

        self.player = Player(Vector2(*self.screen_rectangle.center))
        self.entities: defaultdict[EntityType, list[Entity]] = defaultdict(list)
        # TODO: split entity types into different lists;
        # TODO  then split the draw methods into different methods for each entity type

        self.remove_dead_entities_timer = Timer(max_time=REMOVE_DEAD_ENTITIES_EVERY)
        self.increase_level_timer = Timer(max_time=INCREASE_LEVEL_EVERY)
        self.new_energy_orb_timer = Timer(max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
        self.current_spawn_enemy_cooldown = SPAWN_ENEMY_EVERY
        self.spawn_enemy_timer = Timer(max_time=self.current_spawn_enemy_cooldown)
        self.reason_of_death = ''
    
    def all_entities_iter(self, with_player: bool = True, include_dead: bool = False) -> Generator[Entity, None, None]:
        if with_player: yield self.player
        for _, entities in self.entities.items():
            for entity in entities:
                if include_dead or entity.is_alive():
                    yield entity

    def is_running(self) -> bool:
        return self.player.is_alive()
    
    def toggle_pause(self) -> None: self._paused = not self._paused

    def new_level(self):
        if self._level >= GAME_MAX_LEVEL: return False
        self._level += 1
        self.player.new_level()
        self.spawn_enemy(EnemyType.BOSS)
        self.current_spawn_enemy_cooldown *= 0.92
        return True
    
    def spawn_energy_orb(self):
        self.add_entity(
            EnergyOrb(
                _pos=self.get_random_screen_position_for_entity(entity_size=ENERGY_ORB_SIZE),
                _lifetime=random.uniform(*ENERGY_ORB_LIFETIME_RANGE),
                _energy=ENERGY_ORB_DEFAULT_ENERGY + 10 * (self._level - 1)
            )
        )

    def spawn_enemy(self, enemy_type: EnemyType):
        position = self.get_random_screen_position_for_entity(entity_size=ENEMY_STATS_MAP[enemy_type].size)
        self.add_entity(
            ENEMY_TYPE_TO_CLASS[enemy_type](
                _pos=position,
                _player=self.player,
            )
        )
    
    def spawn_random_enemy(self):
        """Is called once every SPAWN_ENEMY_EVERY seconds."""
        TYPE_WEIGHTS = {
            EnemyType.BASIC: 150,
            EnemyType.FAST: 20,
            EnemyType.ARTILLERY: 10,
            EnemyType.TANK: 20,
            EnemyType.BOSS: 0.,
        }
        enemy_type = random.choices(
            list(TYPE_WEIGHTS.keys()), 
            list(TYPE_WEIGHTS.values()), 
        k=1)[0]
        self.spawn_enemy(enemy_type)

    def process_timers(self, time_delta: float) -> None:
        """Process events that happen periodically."""
        self.remove_dead_entities_timer.tick(time_delta)
        if not self.remove_dead_entities_timer.running():
            self.remove_dead_entities()
            self.remove_dead_entities_timer.reset()
            print('Removed dead entities')
        self.increase_level_timer.tick(time_delta)
        if not self.increase_level_timer.running():
            self.new_level()
            self.increase_level_timer.reset()
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
        if not self.is_running() or self._paused: return
        self._time += time_delta
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

    def spawn_buffered_entities(self) -> None:
        """
        Spawn all entities that are in the buffer of the other entities.
        """
        new_ent = []
        for entity in self.all_entities_iter(with_player=False, include_dead=True):
            if entity._can_spawn_entities:
                new_ent.extend(entity._entities_buffer)
                entity._entities_buffer.clear()
        for ent in new_ent:
            self.add_entity(ent)

    def reflect_entities_vel(self,) -> None:
        """
        Reflect the velocity of all entities that are outside of the screen.
        """
        for entity in self.all_entities_iter():
            pos_ = entity.get_pos()
            if entity.is_alive() and not self.screen_rectangle.collidepoint(pos_):
                if pos_.x < self.screen_rectangle.left or pos_.x > self.screen_rectangle.right:
                    entity._vel.x *= -1.
                if pos_.y < self.screen_rectangle.top or pos_.y > self.screen_rectangle.bottom:
                    entity._vel.y *= -1.
    
    def process_collisions(self) -> None:
        # player collides with anything:
        for entity in self.all_entities_iter(with_player=False):
            if not entity.intersects(self.player):
                continue
            ent_type = entity.get_type()
            if ent_type == EntityType.ENERGY_ORB:
                energy_collected: float = entity.energy_left() # type: ignore
                self.player._energy.change(energy_collected)
                self.player.get_stats().ENERGY_ORBS_COLLECTED += 1
                self.player.get_stats().ENERGY_COLLECTED += energy_collected
                entity.kill()
                self.feedback_buffer.append(Feedback(f'+{energy_collected:.0f}e', color=pygame.Color('magenta')))
            elif ent_type == EntityType.PROJECTILE:
                damage_taken: float = entity._damage # type: ignore
                damage_taken_actual = -self.player._health.change(-damage_taken) # type: ignore
                self.player.get_stats().BULLETS_CAUGHT += 1
                self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
                entity.kill()
                self.feedback_buffer.append(Feedback(f'-{damage_taken_actual:.0f}hp', 2.5, color=pygame.Color('red')))
                self.reason_of_death = f'caught Bullet::{entity._projectile_type.name.title()}' # type: ignore
            elif ent_type in {EntityType.ENEMY, EntityType.CORPSE}:
                damage_on_collision = entity._damage_on_collision # type: ignore
                damage_taken_actual = -self.player._health.change(-damage_on_collision)
                self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
                entity.kill()
                self.feedback_buffer.append(Feedback('collided!', 3.5, color=pygame.Color('pink')))
                self.reason_of_death = f'collided with {ent_type.name.title()}'
                if ent_type == EntityType.ENEMY:
                    self.reason_of_death += f'::{entity._enemy_type.name.title()}' # type: ignore

        # player bullets collide with enemies -> enemies get damage, player gets energy:
        player_bullets = [el for el in self.entities[EntityType.PROJECTILE] if el._projectile_type == ProjectileType.PLAYER_BULLET] # type: ignore
        for bullet in player_bullets:
            for enemy in self.entities[EntityType.ENEMY]:
                if bullet.intersects(enemy):
                    bullet.kill()
                    self.player.get_stats().ACCURATE_SHOTS += 1
                    print('accurate shot')
                    damage_dealt = bullet._damage # type: ignore
                    damage_dealt_actual = -enemy.get_health().change(-damage_dealt) # type: ignore
                    self.player.get_stats().DAMAGE_DEALT += damage_dealt_actual
                    self.feedback_buffer.append(Feedback(f'-{damage_dealt_actual:.1f}hp', 2., color=pygame.Color('orange'), at_pos=enemy.get_pos()))
                    enemy.update(0.)
                    if not enemy.is_alive():
                        enemy.kill()
                        reward = enemy.get_reward() # type: ignore
                        self.player._energy.change(reward)
                        self.player.get_stats().ENEMIES_KILLED += 1
                        self.player.get_stats().ENERGY_COLLECTED += reward
                        print('enemy killed')
                        self.feedback_buffer.append(Feedback(f'+{reward:.1f}e', 2., color=pygame.Color('magenta')))

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.get_type()].append(entity)

    def remove_dead_entities(self):
        """
        Remove all dead entities.
        This function is called every REMOVE_DEAD_ENTITIES_EVERY seconds.
        """
        new_entities = defaultdict(list)
        for entity_type, entities in self.entities.items():
            for entity in entities:
                if entity.is_alive():
                    new_entities[entity_type].append(entity)
        self.entities = new_entities
        # print('Removed dead entities')

    def get_random_screen_position_for_entity(self, entity_size: float) -> Vector2:
        """
        Get a random position inside the screen.
        Try a position and return it if it doesn't collide with any other entity.
        """
        while True:
            pos_candidate = self.get_random_screen_position()
            if (pos_candidate - self.player.get_pos()).magnitude_squared() > 400.**2 and\
                not any(entity.intersects(DummyEntity(pos_candidate, entity_size)) for entity in self.all_entities_iter()):
                    return pos_candidate
    
    def get_random_screen_position(self) -> Vector2:
        x = random.uniform(self.screen_rectangle.left + BM * 10, self.screen_rectangle.right - BM * 10)
        y = random.uniform(self.screen_rectangle.top + BM * 10, self.screen_rectangle.bottom - BM * 10)
        return Vector2(x, y)
    
    def set_last_fps(self, fps: float):
        self._last_fps = fps

    def get_last_fps(self) -> float:
        return self._last_fps

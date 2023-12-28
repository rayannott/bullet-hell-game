from collections import deque
import random
from typing import Generator
import itertools

import pygame
from pygame import Vector2, Color

from config.back import ARTIFACT_CHEST_SIZE
from config.settings import Settings
from src.artifacts import Artifact
from src.entity import Entity, DummyEntity
from src.corpse import Corpse
from src.aoe_effect import AOEEffect, AOEEffectEffectType
from src.mine import Mine
from src.oil_spill import OilSpill
from src.player import Player
from src.enums import ArtifactType, EntityType, EnemyType, ProjectileType
from src.projectile import Projectile, ProjectileType
from src.utils import Timer, Feedback, random_unit_vector
from src.energy_orb import EnergyOrb
from src.exceptions import ArtifactMissing, OnCooldown, NotEnoughEnergy, ShootingDirectionUndefined, ShieldRunning, TimeStopRunning
from src.enemy import ENEMY_SIZE_MAP, ENEMY_TYPE_TO_CLASS, Enemy
from src.artifact_chest import ArtifactChest

from config import (REMOVE_DEAD_ENTITIES_EVERY, ENERGY_ORB_DEFAULT_ENERGY, ENERGY_ORB_LIFETIME_RANGE, 
    NICER_MAGENTA_HEX, NICER_BLUE_HEX, NICER_YELLOW_HEX, NICER_GREEN_HEX,
    WAVE_DURATION, GAME_MAX_LEVEL, ENERGY_ORB_SIZE, ENERGY_ORB_COOLDOWN_RANGE, SPAWN_ENEMY_EVERY, BM,
    PLAYER_SHOT_COST,
)
from front.sounds import play_sfx


NICER_YELLOW = pygame.Color(NICER_YELLOW_HEX)
NICER_GREEN = pygame.Color(NICER_GREEN_HEX)
BLUE = pygame.Color(NICER_BLUE_HEX)


def get_enemy_type_prob_weights(level: int, difficulty: int) -> dict[EnemyType, float]:
    DIFF_MULTS = {1: 0, 2: 1, 3: 2, 4: 5, 5: 8}
    # the higher the difficulty, the lower the probability of spawning a basic enemy
    return {
        EnemyType.BASIC: 230 - DIFF_MULTS[difficulty] * 10,
        EnemyType.FAST: (level - 1) * 10. * (difficulty > 2),
        EnemyType.ARTILLERY: level * 10.,
        EnemyType.TANK: 10. + level * 5.,
        EnemyType.MINER: 40. + level * 4.,
        EnemyType.BOSS: 0.,
    }


class Game:
    def __init__(self, screen_rectangle: pygame.Rect, settings: Settings) -> None:
        self.level = 1
        self.time = 0.
        self.paused = False
        self.screen_rectangle = screen_rectangle
        self.settings = settings
        
        self.feedback_buffer: deque[Feedback] = deque()
        self._last_fps: float = 0.

        # entities:
        self.player = Player(Vector2(*self.screen_rectangle.center), settings)
        self.e_dummies: list[DummyEntity] = []
        self.e_oil_spills: list[OilSpill] = []
        self.e_corpses: list[Corpse] = []
        self.e_projectiles: list[Projectile] = []
        self.e_energy_orbs: list[EnergyOrb] = []
        self.e_enemies: list[Enemy] = []
        self.e_mines: list[Mine] = []
        self.e_aoe_effects: list[AOEEffect] = []
        self.e_artifact_chests: list[ArtifactChest] = []

        self.remove_dead_entities_timer = Timer(max_time=REMOVE_DEAD_ENTITIES_EVERY)
        self.one_wave_timer = Timer(max_time=WAVE_DURATION)
        self.new_energy_orb_timer = Timer(max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
        self.current_spawn_enemy_cooldown = SPAWN_ENEMY_EVERY
        self.spawn_enemy_timer = Timer(max_time=self.current_spawn_enemy_cooldown)
        self.reason_of_death = ''
        self.collected_artifact_cache: list[Artifact] = []
        self.energy_orbs_spawned = 0
        self.time_frozen = False

    def all_entities_iter(self, 
            with_player: bool = True,
            include_dead: bool = False,
            with_enemies: bool = True,
            with_projectiles: bool = True,
        ) -> Generator[Entity, None, None]:
        yield from self.oil_spills(include_dead)
        yield from self.corpses(include_dead)
        if with_projectiles: yield from self.projectiles(include_dead)
        yield from self.energy_orbs(include_dead)
        if with_enemies: yield from self.enemies(include_dead)
        yield from self.dummies(include_dead)
        yield from self.mines(include_dead)
        yield from self.aoe_effects(include_dead)
        yield from self.artifact_chests(include_dead)
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
    def mines(self, include_dead: bool = False) -> Generator[Mine, None, None]:
        yield from (ent for ent in self.e_mines if include_dead or ent.is_alive())
    def aoe_effects(self, include_dead: bool = False) -> Generator[AOEEffect, None, None]:
        yield from (ent for ent in self.e_aoe_effects if include_dead or ent.is_alive())
    def artifact_chests(self, include_dead: bool = False) -> Generator[ArtifactChest, None, None]:
        yield from (ent for ent in self.e_artifact_chests if include_dead or ent.is_alive())

    def is_running(self) -> bool:
        return self.player.is_alive()
    
    def toggle_pause(self) -> None: self.paused = not self.paused

    def new_level(self) -> bool:
        self.feedback_buffer.append(Feedback(f'new wave!', 3.5, color=Color('green'), at_pos='cursor'))
        if self.level >= GAME_MAX_LEVEL: return False
        play_sfx('new_level')
        self.level += 1
        self.feedback_buffer.append(Feedback(f'new level: {self.level}', 3.5, color=Color('green'), at_pos='player'))
        self.player.new_level()
        # the higher the difficulty, the faster the spawn cooldown shrinks
        self.current_spawn_enemy_cooldown *= (1. - 0.02 * self.settings.difficulty)

        art_chests_to_spawn = self.player.artifacts_generator.get_artifact_chests(self.level)
        _len = len(art_chests_to_spawn)
        _positions = [
            Vector2(500 + (self.screen_rectangle.width - 500) * i / _len, self.screen_rectangle.height//2)
            for i in range(_len)]
        for _pos, ac in zip(_positions, art_chests_to_spawn):
            ac.set_pos(_pos)
            self.add_entity(ac)

        # achievements:
        if self.level == 2:
            if not self.player.get_achievements().COLLECT_ALL_ENERGY_ORBS_BY_LEVEL_2 and self.energy_orbs_spawned == self.player.get_stats().ENERGY_ORBS_COLLECTED:
                self.player.get_achievements().COLLECT_ALL_ENERGY_ORBS_BY_LEVEL_2 = True
                self.feedback_buffer.append(Feedback('[A!] collected all energy orbs by level 2', 3., color=BLUE))
        elif self.level == 5:
            simultaneous_achievements_cnt = 0
            if not self.player.get_achievements().REACH_LEVEL_5_WITH_NO_CORPSES and not self.player.get_stats().CORPSES_LET_SPAWN:
                self.player.get_achievements().REACH_LEVEL_5_WITH_NO_CORPSES = True; simultaneous_achievements_cnt += 1
                self.feedback_buffer.append(Feedback('[A] reach level 5 without corpses', 3., color=BLUE))
            if not self.player.get_achievements().REACH_LEVEL_5_WITHOUT_TAKING_DAMAGE and not self.player.get_stats().DAMAGE_TAKEN:
                self.player.get_achievements().REACH_LEVEL_5_WITHOUT_TAKING_DAMAGE = True; simultaneous_achievements_cnt += 1
                self.feedback_buffer.append(Feedback('[A] reach level 5 without taking damage', 3., color=BLUE))
            if not self.player.get_achievements().REACH_LEVEL_5_WITH_100_PERCENT_ACCURACY and self.player.get_stats().ACCURATE_SHOTS == self.player.get_stats().PROJECTILES_FIRED:
                self.player.get_achievements().REACH_LEVEL_5_WITH_100_PERCENT_ACCURACY = True; simultaneous_achievements_cnt += 1
                self.feedback_buffer.append(Feedback('[A] reach level 5 with 100% accuracy', 3., color=BLUE))
            if not self.player.get_achievements().REACH_LEVEL_5_WITHOUT_COLLECTING_ENERGY_ORBS and not self.player.get_stats().ENERGY_ORBS_COLLECTED:
                self.player.get_achievements().REACH_LEVEL_5_WITHOUT_COLLECTING_ENERGY_ORBS = True; simultaneous_achievements_cnt += 1
                self.feedback_buffer.append(Feedback('[A] reach level 5 without collecting energy orbs', 3., color=BLUE))
            
            if not self.player.get_achievements().GET_ALL_LEVEL_5_ACHIEVEMENTS_SIMULTANEOUSLY and simultaneous_achievements_cnt == 4:
                self.player.get_achievements().GET_ALL_LEVEL_5_ACHIEVEMENTS_SIMULTANEOUSLY = True
                self.feedback_buffer.append(Feedback('[A!!] get all level 5 achievements simultaneously', 3., color=BLUE))

        elif self.level == 10:
            if not self.player.get_achievements().REACH_LEVEL_10:
                self.player.get_achievements().REACH_LEVEL_10 = True
                self.feedback_buffer.append(Feedback('[A!] you\'ve reached the last level!', 3., color=BLUE))
        return True

    def kill_projectiles(self):
        for projectile in self.projectiles():
            projectile.kill()
    
    def spawn_energy_orb(self):
        difficulty_mult = 1 + 0.1 * (self.settings.difficulty - 1)
        self.add_entity(
            EnergyOrb(
                pos=self.get_random_screen_position_for_entity(entity_size=ENERGY_ORB_SIZE),
                lifetime=random.uniform(*ENERGY_ORB_LIFETIME_RANGE) + 1. * (self.level - 1),
                energy=ENERGY_ORB_DEFAULT_ENERGY * difficulty_mult + 20. * (self.level - 1),
                num_extra_bullets=int(random.random() < 0.05)
            )
        )

    def spawn_enemy(self, enemy_type: EnemyType):
        if enemy_type == EnemyType.BOSS:
            position = self.screen_rectangle.center
        else:
            position = self.get_screen_position_for_enemy(enemy_size=ENEMY_SIZE_MAP[enemy_type])
        self.add_entity(
            ENEMY_TYPE_TO_CLASS[enemy_type](
                pos=position,
                player=self.player,
            )
        )
    
    def spawn_random_enemy(self):
        """Is called once every SPAWN_ENEMY_EVERY seconds."""
        type_weights = get_enemy_type_prob_weights(level=self.level, difficulty=self.settings.difficulty)
        enemy_type = random.choices(
            list(type_weights.keys()), 
            list(type_weights.values()), 
        k=1)[0]
        if enemy_type == EnemyType.BASIC and self.level > 3:
            num = random.randint(1, self.level//3 + 1)
        else: num = 1
        for _ in range(num):
            self.spawn_enemy(enemy_type)

    def process_timers(self, time_delta: float) -> None:
        """Process events that happen periodically."""
        self.remove_dead_entities_timer.tick(time_delta)
        if not self.remove_dead_entities_timer.running():
            self.remove_dead_entities()
            self.remove_dead_entities_timer.reset()
        self.one_wave_timer.tick(time_delta)
        if not self.one_wave_timer.running():
            self.one_wave_timer.reset()
            # spawn boss at the end of the wave unless one is already alive
            if any(ent.enemy_type == EnemyType.BOSS for ent in self.enemies()):
                self.feedback_buffer.append(Feedback('boss is still alive!', 2., color=Color('red')))
                return
            self.spawn_enemy(EnemyType.BOSS)
        self.new_energy_orb_timer.tick(time_delta)
        if not self.new_energy_orb_timer.running():
            self.spawn_energy_orb()
            self.new_energy_orb_timer.reset(with_max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
        self.spawn_enemy_timer.tick(time_delta)
        if not self.spawn_enemy_timer.running():
            self.spawn_random_enemy()
            self.spawn_enemy_timer.reset(with_max_time=self.current_spawn_enemy_cooldown)

    def update(self, time_delta: float) -> None:
        if not self.is_running() or self.paused: return
        self.time += time_delta
        self.time_frozen = self.player.artifacts_handler.is_present(ArtifactType.TIME_STOP) and self.player.artifacts_handler.get_time_stop().is_on()
        for entity in self.all_entities_iter(with_enemies=not self.time_frozen, with_projectiles=not self.time_frozen):
            entity.update(time_delta)
        self.process_timers(time_delta)
        self.process_collisions()
        self.spawn_buffered_entities()
        self.process_dash()
        self.register_new_achievements()
    
    def process_dash(self):
        if not self.player.dash_needs_processing: return
        if not self.player.artifacts_handler.is_present(ArtifactType.DASH): return
        dash = self.player.artifacts_handler.get_dash()
        for enemy in self.enemies():
            if not dash.dash_path_intersects_enemy(enemy): continue
            self.deal_damage_to_enemy(enemy, self.player.get_damage() * 1.5)
            self.player.get_stats().DASHED_THROUGH_ENEMIES += 1
            self.feedback_buffer.append(Feedback('x', 3.5, color=NICER_GREEN, at_pos=enemy.get_pos()))
        self.player.dash_needs_processing = False
    
    def register_new_achievements(self):
        ach = self.player.get_achievements()
        st = self.player.get_stats()
        
        if not ach.RECEIVE_1000_DAMAGE and st.DAMAGE_TAKEN >= 1000:
            ach.RECEIVE_1000_DAMAGE = True
            self.feedback_buffer.append(Feedback('[A] receive 1000 damage', color=BLUE))
            play_sfx('new_achievement')
        if not ach.KILL_100_ENEMIES and st.ENEMIES_KILLED >= 100:
            ach.KILL_100_ENEMIES = True
            self.feedback_buffer.append(Feedback('[A] killed 100 enemies', color=BLUE))
            play_sfx('new_achievement')
        if not ach.FIRE_200_PROJECTILES and st.PROJECTILES_FIRED >= 200:
            ach.FIRE_200_PROJECTILES = True
            self.feedback_buffer.append(Feedback('[A] fired 200 projectiles', color=BLUE))
            play_sfx('new_achievement')
        if not ach.BLOCK_100_BULLETS and st.BULLET_SHIELD_BULLETS_BLOCKED >= 100:
            ach.BLOCK_100_BULLETS = True
            self.feedback_buffer.append(Feedback('[A] blocked 100 bullets', color=BLUE))
            play_sfx('new_achievement')
        if not ach.COLLECT_200_ENERGY_ORBS and st.ENERGY_ORBS_COLLECTED >= 200:
            ach.COLLECT_200_ENERGY_ORBS = True
            self.feedback_buffer.append(Feedback('[A] collected 200 energy orbs', color=BLUE))
            play_sfx('new_achievement')
        if not ach.COLLIDE_WITH_15_ENEMIES and st.ENEMIES_COLLIDED_WITH >= 15:
            ach.COLLIDE_WITH_15_ENEMIES = True
            self.feedback_buffer.append(Feedback('[A] collided with 15 enemies', color=BLUE))
            play_sfx('new_achievement')
        if not ach.DASH_THROUGH_10_ENEMIES and st.DASHED_THROUGH_ENEMIES >= 10:
            ach.DASH_THROUGH_10_ENEMIES = True
            self.feedback_buffer.append(Feedback('[A] dashed through 10 enemies', color=BLUE))
            play_sfx('new_achievement')
        if not ach.LIFT_20_BLOCKS and st.BLOCKS_LIFTED >= 20:
            ach.LIFT_20_BLOCKS = True
            self.feedback_buffer.append(Feedback('[A] lifted 20 blocks', color=BLUE))
            play_sfx('new_achievement')

    def player_try_shooting(self):
        try:
            new_projectile = self.player.shoot()
        except OnCooldown as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            play_sfx('warning')
        except NotEnoughEnergy as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            play_sfx('warning')
        except ShootingDirectionUndefined as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            play_sfx('warning')
        else:
            self.add_entity(new_projectile)
            play_sfx('player_shot')

    def player_try_ultimate(self, artifact_type: ArtifactType):
        try: self.player.ultimate_ability(artifact_type)
        except (ArtifactMissing, OnCooldown, NotEnoughEnergy, ShieldRunning, TimeStopRunning) as e:
            self.feedback_buffer.append(Feedback(str(e), 2., color=Color('red')))
            play_sfx('warning')

    def spawn_buffered_entities(self) -> None:
        """
        Spawn all entities that are in the buffer of the other entities.
        """
        new_ent = []
        for entity in self.all_entities_iter(with_player=True, include_dead=True):
            if entity.can_spawn_entities:
                new_ent.extend(entity.entities_buffer)
                entity.entities_buffer.clear()
        for ent in new_ent:
            self.add_entity(ent)

    def reflect_projectiles_vel(self) -> None:
        """
        Reflect the velocity of all projectiles that are outside of the screen.
        Add some delta to the position to prevent the projectile from getting stuck.
        """
        delta = 10.
        for projectile in self.projectiles():
            pos_ = projectile.get_pos()
            if (not projectile.is_alive() or self.screen_rectangle.collidepoint(pos_) or 
                projectile.projectile_type == ProjectileType.DEF_TRAJECTORY):
                continue
            projectile.ricochet_count += 1
            if pos_.x < self.screen_rectangle.left:
                projectile.vel.x *= -1.
                projectile.pos.x += delta
            if pos_.x > self.screen_rectangle.right:
                projectile.vel.x *= -1.
                projectile.pos.x -= delta
            if pos_.y < self.screen_rectangle.top:
                projectile.vel.y *= -1.
                projectile.pos.y += delta
            if pos_.y > self.screen_rectangle.bottom:
                projectile.vel.y *= -1.
                projectile.pos.y -= delta
    
    def process_collisions(self) -> None:
        self.process_collisions_player()
        if not self.time_frozen:
            self.process_collisions_enemies()

    def process_collisions_player(self) -> None:
        # player collides with anything:
        for eo in self.energy_orbs():
            if not eo.intersects(self.player): continue
            energy_collected: float = eo.energy_left()
            energy_collected_actually = self.player.energy.change(energy_collected)
            self.player.get_stats().ENERGY_ORBS_COLLECTED += 1
            self.player.get_stats().ENERGY_COLLECTED += energy_collected_actually
            if eo.num_extra_bullets:
                actually_added = self.player.add_extra_bullets(eo.num_extra_bullets)
                self.feedback_buffer.append(Feedback(f'+{actually_added}eb', color=Color('white')))
            self.player.get_stats().BONUS_ORBS_COLLECTED += int(eo.is_enemy_bonus_orb())
            play_sfx('energy_collected')
            eo.kill()
            self.feedback_buffer.append(Feedback(f'+{energy_collected_actually:.0f}e', color=pygame.Color(NICER_MAGENTA_HEX)))
        for oil_spill in self.oil_spills():
            if not oil_spill.intersects(self.player): continue
            if not oil_spill.is_activated(): continue
            self.player.effect_flags.OIL_SPILL = True
            self.reason_of_death = 'slipped on oil to death'
            play_sfx('in_oil_spill')
        for projectile in self.projectiles():
            if (projectile.projectile_type != ProjectileType.PLAYER_BULLET and 
                self.player.artifacts_handler.is_present(ArtifactType.BULLET_SHIELD) and
                self.player.artifacts_handler.get_bullet_shield().point_inside_shield(projectile.get_pos())
            ):
                projectile.kill()
                self.feedback_buffer.append(Feedback(f'blocked', 1., color=pygame.Color('yellow')))
                self.player.get_stats().BULLET_SHIELD_BULLETS_BLOCKED += 1
                play_sfx('shield_blocked')
                continue
            if not projectile.intersects(self.player): continue
            if self.time_frozen: continue
            self.player_get_damage(projectile.damage)
            self.player.get_stats().BULLETS_CAUGHT += 1
            projectile.kill()
            self.reason_of_death = f'caught Bullet::{projectile.projectile_type.name.title()}'
        for enemy in self.enemies():
            if not enemy.intersects(self.player): continue
            if self.time_frozen: continue
            self.player_get_damage(enemy.damage_on_collision, ignore_invul_timer=enemy.enemy_type == EnemyType.BOSS)
            self.player.get_stats().ENEMIES_COLLIDED_WITH += 1
            enemy.kill()
            self.feedback_buffer.append(Feedback('collided!', 3.5, color=pygame.Color('pink')))
            self.reason_of_death = f'collided with Enemy::{enemy.enemy_type.name.title()}'
        for corpse in self.corpses():
            if not corpse.intersects(self.player): continue
            self.player_get_damage(corpse.damage_on_collision, ignore_invul_timer=True)
            self.player.get_stats().ENEMIES_COLLIDED_WITH += 1
            corpse.kill()
            self.feedback_buffer.append(Feedback('collided!', 3.5, color=pygame.Color('pink')))
            self.reason_of_death = f'collided with Corpse'
            # play_sfx('fart')
        for mine in self.mines():
            if not mine.intersects(self.player): continue
            if not mine.is_activated(): continue
            self.player_get_damage(mine.damage, ignore_invul_timer=True)
            self.player.get_stats().MINES_STEPPED_ON += 1
            mine.kill()
            self.feedback_buffer.append(Feedback('mine!', 3.5, color=pygame.Color('pink')))
            self.reason_of_death = f'stepped on a mine'
            play_sfx('explosion')
        for aoe_effect in self.aoe_effects():
            if not aoe_effect.intersects(self.player): continue
            if aoe_effect.applied_effect_player: continue
            if aoe_effect.effect_type == AOEEffectEffectType.DAMAGE:
                self.player_get_damage(aoe_effect.damage)
                self.reason_of_death = f'impact AOE damage'
            aoe_effect.applied_effect_player = True
        for artifact_chest in self.artifact_chests():
            if not artifact_chest.intersects(self.player): continue
            if not artifact_chest.can_be_picked_up(): continue
            artifact = artifact_chest.get_artifact()
            self.player.add_artifact(artifact)
            self.collected_artifact_cache.append(artifact)
            self.feedback_buffer.append(Feedback(f'+{artifact}', 3., color=NICER_YELLOW))
            play_sfx('artifact_collected')
            # remove all artifacts:
            for ac in self.artifact_chests(): ac.kill()

    def process_collisions_enemies(self) -> None:
        # TODO: move the for enemy in enemies outside of individual collision checks
        # player bullets collide with enemies
        player_bullets = [el for el in self.projectiles() if el.projectile_type == ProjectileType.PLAYER_BULLET]
        for bullet in player_bullets:
            for enemy in self.enemies():
                if not bullet.intersects(enemy): continue
                bullet.kill()
                is_ricochet = bullet.ricochet_count > 0
                self.player.get_stats().ACCURATE_SHOTS += 1
                if is_ricochet:
                    self.player.get_stats().ACCURATE_SHOTS_RICOCHET += 1
                    self.feedback_buffer.append(Feedback('ricochet!', 2., color=pygame.Color('pink'), at_pos=enemy.get_pos()))
                self.deal_damage_to_enemy(enemy, bullet.damage)
                enemy.caught_bullet()
                play_sfx('accurate_shot')
                if (not self.player.get_achievements().KILL_BOSS_WITH_RICOCHET and
                    is_ricochet and 
                    not enemy.is_alive() and
                    enemy.enemy_type == EnemyType.BOSS
                ):
                    self.player.get_achievements().KILL_BOSS_WITH_RICOCHET = True
                    self.feedback_buffer.append(Feedback('[A] killed the boss with ricochet!', 3., color=BLUE))
                    play_sfx('new_achievement')
        # enemy-enemy collisions
        MULT = 0.3
        for enem1, enem2 in itertools.combinations(self.enemies(), 2):
            if enem1.intersects(enem2):
                if enem1.intersects(enem2):
                    vec_between = enem2.get_pos() - enem1.get_pos()
                    enem1.pos -= vec_between * MULT; enem2.pos += vec_between * MULT
        # enemy-mine collisions
        for mine in self.mines():
            if not mine.is_activated(): continue
            for enemy in self.enemies():
                if not mine.intersects(enemy): continue
                self.deal_damage_to_enemy(enemy, mine.damage)
                play_sfx('explosion')
                mine.kill()
        # enemy-aoe_effect collisions
        for aoe_effect in self.aoe_effects():
            if aoe_effect.applied_effect_enemies: continue
            for enemy in self.enemies():
                if not aoe_effect.intersects(enemy): continue
                if aoe_effect.effect_type == AOEEffectEffectType.DAMAGE:
                    self.deal_damage_to_enemy(enemy, aoe_effect.damage)
                elif aoe_effect.effect_type == AOEEffectEffectType.ENEMY_BLOCK_ON:
                    enemy.has_block = True
            aoe_effect.applied_effect_enemies = True

        # check if the Boss just died
        for enemy in self.enemies(include_dead=True):
            if enemy.enemy_type != EnemyType.BOSS: continue
            if enemy.is_alive(): continue
            if not self.player.get_achievements().KILL_BOSS_WITHOUT_BULLETS and enemy.get_num_bullets_caught() == 0:
                self.player.get_achievements().KILL_BOSS_WITHOUT_BULLETS = True
                self.feedback_buffer.append(Feedback('[A] killed the boss without bullets', 3., color=BLUE))
                play_sfx('new_achievement')
            if not self.player.get_achievements().KILL_BOSS_USING_EXACTLY_7_BULLETS and enemy.get_num_bullets_caught() == 7:
                self.player.get_achievements().KILL_BOSS_USING_EXACTLY_7_BULLETS = True
                self.feedback_buffer.append(Feedback('[A] killed the boss using exactly 7 bullets', 3., color=BLUE))
                play_sfx('new_achievement')
            if not self.player.get_achievements().KILL_BOSS_WITHIN_ONE_SECOND and enemy.lifetime_cooldown.current_time < 1.:
                self.player.get_achievements().KILL_BOSS_WITHIN_ONE_SECOND = True
                self.feedback_buffer.append(Feedback('[A] killed the boss within one second', 3., color=BLUE))
                play_sfx('new_achievement')

    def deal_damage_to_enemy(self, enemy: Enemy, damage: float, get_damage_feedback: bool = True) -> None:
        if enemy.has_block:
            # checks if that enemy has the block on
            enemy.has_block = False
            self.player.get_stats().BLOCKS_LIFTED += 1
            # lift the block and either give energy or extra bullets
            energy_collected = self.player.energy.change(PLAYER_SHOT_COST * 1.35)
            self.player.get_stats().ENERGY_COLLECTED += energy_collected
            self.feedback_buffer.append(Feedback(f'+{energy_collected:.0f}e', 2., color=pygame.Color(NICER_MAGENTA_HEX)))

            self.feedback_buffer.append(Feedback('block lifted', 2., color=pygame.Color('yellow')))
            return
        damage_dealt_actual = -enemy.get_health().change(-damage)
        enemy.get_health().current_value = round(enemy.get_health().current_value)
        self.player.get_stats().DAMAGE_DEALT += damage_dealt_actual
        if get_damage_feedback:
            self.feedback_buffer.append(Feedback(f'-{damage_dealt_actual:.0f}hp', 2., color=pygame.Color('orange'), at_pos=enemy.get_pos()))
        enemy.update(0.)
        if enemy.is_alive(): return
        enemy.kill()
        enemy.on_killed_by_player()
        reward = enemy.get_reward()
        reward_actually_collected = self.player.energy.change(reward)
        self.player.get_stats().ENEMIES_KILLED += 1
        self.player.get_stats().ENERGY_COLLECTED += reward_actually_collected
        if enemy.enemy_type == EnemyType.BOSS:
            # killed the boss
            self.new_level()
            self.kill_projectiles()
        self.feedback_buffer.append(Feedback(f'+{reward_actually_collected:.0f}e', 2., color=pygame.Color(NICER_MAGENTA_HEX)))
        play_sfx('enemy_killed')
    
    def player_get_damage(self, damage: float, ignore_invul_timer: bool = False) -> float:
        if not ignore_invul_timer and self.player.invulnerability_timer.running(): 
            self.player.invulnerability_timer.turn_off()
            return 0.
        self.player.invulnerability_timer.reset()
        damage_taken_actual = -self.player.health.change(-damage)
        self.player.get_stats().DAMAGE_TAKEN += damage_taken_actual
        self.feedback_buffer.append(Feedback(f'-{damage_taken_actual:.0f}hp', 2., color=pygame.Color('red'), at_pos='player'))
        play_sfx('damage_taken')
        return damage_taken_actual

    def add_entity(self, entity: Entity) -> None:
        ent_type = entity.get_type()
        if ent_type == EntityType.ENERGY_ORB:
            self.energy_orbs_spawned += 1
            self.e_energy_orbs.append(entity) # type: ignore
        elif ent_type == EntityType.ENEMY:
            self.e_enemies.append(entity) # type: ignore
        elif ent_type == EntityType.PROJECTILE:
            self.e_projectiles.append(entity) # type: ignore
        elif ent_type == EntityType.CORPSE:
            self.e_corpses.append(entity) # type: ignore
            self.player.get_stats().CORPSES_LET_SPAWN += 1
        elif ent_type == EntityType.DUMMY:
            self.e_dummies.append(entity) # type: ignore
        elif ent_type == EntityType.OIL_SPILL:
            self.e_oil_spills.append(entity) # type: ignore
        elif ent_type == EntityType.MINE:
            self.e_mines.append(entity) # type: ignore
        elif ent_type == EntityType.CRATER:
            self.e_aoe_effects.append(entity) # type: ignore
        elif ent_type == EntityType.ARTIFACT_CHEST:
            self.e_artifact_chests.append(entity) # type: ignore
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
            if ((pos_candidate - self.player.get_pos()).magnitude_squared() > 400.**2 and
                not any(entity.intersects(dummy) for entity in self.all_entities_iter())):
                    return pos_candidate
    
    def get_screen_position_for_enemy(self, enemy_size: float) -> Vector2:
        """Give a position behind the player.
        If it is outside of the screen, return a random position inside the screen."""
        player_vel = self.player.get_vel() + random_unit_vector()
        pos = self.player.get_pos() - player_vel.normalize() * 300.
        if self.screen_rectangle.collidepoint(pos): return pos
        return self.get_random_screen_position_for_entity(enemy_size)

    def get_random_screen_position(self, margin=BM*15) -> Vector2:
        x = random.uniform(self.screen_rectangle.left + margin, self.screen_rectangle.right - margin)
        y = random.uniform(self.screen_rectangle.top + margin, self.screen_rectangle.bottom - margin)
        return Vector2(x, y)
    
    def set_last_fps(self, fps: float):
        self._last_fps = fps

    def get_last_fps(self) -> float:
        return self._last_fps

    def get_info(self) -> dict:
        score = (
            self.time +
            self.player.get_stats().ENEMIES_KILLED * 1.3 +
            self.player.get_stats().ACCURATE_SHOTS * 2. +
            self.player.get_stats().BONUS_ORBS_COLLECTED * 1.2 +
            len(self.player.get_achievements().achievements_pretty()) * 20. +
            len(list(self.player.artifacts_handler.iterate_active())) * 15. +
            len(self.player.artifacts_handler.inactive_artifacts) * 8.
        ) * (1. + 0.1 * (self.settings.difficulty - 3))

        return {
            'level': self.level,
            'difficulty': self.settings.difficulty,
            'time': self.time,
            'stats': self.player.get_stats(),
            'achievements': self.player.get_achievements(),
            'artifacts': self.player.artifacts_handler, 
            'reason_of_death': self.reason_of_death,
            'score': int(score),
        }

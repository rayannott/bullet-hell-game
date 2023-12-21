from dataclasses import dataclass
import math
import random

from pygame import Vector2, Color

from front.sounds import play_sfx
from src.aoe_effect import AOEEffect
from src.energy_orb import EnergyOrb
from src.entity import Entity
from src.corpse import Corpse
from src.enums import EntityType, EnemyType, ProjectileType
from src.mine import Mine
from src.player import Player
from src.utils import Slider, Timer, random_unit_vector
from src.projectile import Projectile, HomingProjectile, ExplosiveProjectile, DefinedTrajectoryProjectile
from src.oil_spill import OilSpill
from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, BOSS_DEFAULT_REGEN_RATE,
    PROJECTILE_DEFAULT_SPEED, ENEMY_DEFAULT_SHOOTING_SPREAD, BOSS_DEFAULT_OIL_SPILL_SPAWN_COOLDOWN,
    ENEMY_DEFAULT_LIFETIME, OIL_SPILL_SIZE, ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN,
    ENEMY_DEFAULT_REWARD, ENEMY_DEFAULT_DAMAGE, ENEMY_DEFAULT_DAMAGE_SPREAD, ENEMY_DEFAULT_COLLISION_DAMAGE,
    BOSS_ENEMY_COLOR_HEX, PROBABILITY_SPAWN_EXTRA_BULLET_ORB, MINE_DEFAULT_DAMAGE
)


@dataclass
class EnemyStats:
    size: float
    color: Color
    speed: float
    health: float
    shoot_cooldown: float
    reward: float
    lifetime: float
    damage_on_collision: float


ENEMY_SIZE_MAP = {
    EnemyType.BASIC: ENEMY_DEFAULT_SIZE,
    EnemyType.FAST: ENEMY_DEFAULT_SIZE * 0.87,
    EnemyType.TANK: ENEMY_DEFAULT_SIZE * 1.8,
    EnemyType.ARTILLERY: ENEMY_DEFAULT_SIZE * 2,
    EnemyType.MINER: ENEMY_DEFAULT_SIZE * 0.92,
    EnemyType.BOSS: ENEMY_DEFAULT_SIZE * 2.6,
}


class Enemy(Entity):
    def __init__(self, 
            pos: Vector2,
            enemy_type: EnemyType,
            color: Color,
            speed: float,
            health: float,
            shoot_cooldown: float,
            reward: float,
            lifetime: float,
            player: Player,     
            damage_on_collision: float = ENEMY_DEFAULT_COLLISION_DAMAGE,
            damage: float = ENEMY_DEFAULT_DAMAGE,
            damage_spread: float = ENEMY_DEFAULT_DAMAGE_SPREAD,
            spread: float = ENEMY_DEFAULT_SHOOTING_SPREAD,
            turn_coefficient: float = 1.,
        ):
        super().__init__(
            pos=pos,
            type=EntityType.ENEMY,
            size=ENEMY_SIZE_MAP[enemy_type],
            speed=speed, 
            color=color,
            can_spawn_entities=True,
            homing_target=player,
            turn_coefficient=turn_coefficient,
        )
        self.homing_target: Player # to avoid typing errors (this is always a player)
        self.health = Slider(health)
        self.cooldown = Timer(max_time=shoot_cooldown)
        self.cooldown.set_percent_full(random.random())
        self.lifetime_cooldown = Timer(max_time=lifetime)
        self.reward = reward
        self.enemy_type = enemy_type
        self.spread = spread # in radians
        self.damage = damage
        self.damage_spread = damage_spread
        self.num_bullets_caught = 0

        self.damage_on_collision = damage_on_collision
        self.shoots_player = True
        self.post_init()

    def post_init(self):
        """Called after the constructor.
        This is used to adjust values according to the difficulty."""
        difficulty = self.homing_target.settings.difficulty
        difficulty_mult = 1. + 0.1 * (difficulty - 3) # from 0.8 to 1.2
        self.speed *= difficulty_mult
        self.damage *= difficulty_mult
        self.cooldown = Timer(max_time=self.cooldown.max_time / difficulty_mult)
        self.health = Slider(self.health.max_value + [-10., 0., 5., 15., 30][difficulty - 1])
        self.reward *= difficulty_mult
        self.damage_on_collision *= difficulty_mult
    
    def get_shoot_direction(self) -> Vector2:
        rot_angle = random.uniform(-self.spread, self.spread) * 180./math.pi if self.spread else 0.
        return self.vel.rotate(rot_angle).normalize()

    def shoot(self):
        self.shoot_normal()
    
    def update(self, time_delta: float):
        if not self.is_alive(): return
        if not self.health.is_alive(): self.kill()
        super().update(time_delta)
        self.cooldown.tick(time_delta)
        self.lifetime_cooldown.tick(time_delta)
        if not self.lifetime_cooldown.running():
            self.kill()
            self.on_natural_death()
        if not self.shoots_player: return
        if not self.cooldown.running():
            self.shoot()
            self.cooldown.reset()

    def shoot_normal(self, **kwargs):
        speed_mult = kwargs.get('speed_mult', 1.)
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            Projectile(
                pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                vel=direction,
                damage=self.damage + random.uniform(-self.damage_spread, self.damage_spread),
                projectile_type=ProjectileType.NORMAL,
                speed=self.speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.4) * speed_mult,
            )
        )
    
    def shoot_homing(self, **kwargs):
        speed_mult = kwargs.get('speed_mult', 1.)
        player_level = self.homing_target.get_level()
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            HomingProjectile(
                pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                vel=direction,
                damage=self.damage + random.uniform(-self.damage_spread, self.damage_spread),
                speed=(self.speed + PROJECTILE_DEFAULT_SPEED * 0.8) * speed_mult,
                homing_target=self.homing_target,
                turn_coefficient=0.2 + 0.02 * player_level,
            )
        )

    def shoot_explosive(self, num_of_subprojectiles: int = 6):
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            ExplosiveProjectile(
                pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                vel=direction,
                damage=self.damage + random.uniform(-self.damage_spread, self.damage_spread),
                speed=self.speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.2),
                num_subprojectiles=num_of_subprojectiles,
            )
        )
    
    def shoot_def_trajectory_one(self):
        points_around_player = [ # TODO: fix this
            self.homing_target.get_pos() + Vector2(0., 1.).rotate(i * 360. / 5) * random.uniform(200, 700) 
            for i in range(5)
        ]
        random.shuffle(points_around_player)
        self.entities_buffer.append(
            DefinedTrajectoryProjectile(
                points=[self.pos.copy(), *points_around_player, self.homing_target.get_pos()],
                damage=self.damage,
            )
        )
    
    def shoot_def_trajectory(self, num_of_projectiles=2):
        for _ in range(num_of_projectiles):
            self.shoot_def_trajectory_one()

    def on_natural_death(self):
        self.entities_buffer.append(Corpse(self))
    
    def on_killed_by_player(self):
        reward, bullets = (self.reward * 0.5, int(self.reward / 100)) if random.random() < PROBABILITY_SPAWN_EXTRA_BULLET_ORB else (self.reward, 0)
        self.entities_buffer.append(
            EnergyOrb(self.pos, reward, 0.25, num_extra_bullets=bullets, is_enemy_bonus_orb=True)
        )
    
    def caught_bullet(self):
        self.num_bullets_caught += 1
    
    def get_num_bullets_caught(self) -> int:
        return self.num_bullets_caught
    
    def get_health(self) -> Slider: return self.health

    def get_reward(self) -> float: return self.reward


class BasicEnemy(Enemy):
    """Just a normal enemy."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self.difficulty = player.settings.difficulty
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.BASIC,
            player=player,
            color=Color('#e82337'),
            speed=ENEMY_DEFAULT_SPEED,
            health=ENEMY_DEFAULT_MAX_HEALTH // 2,
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            reward=ENEMY_DEFAULT_REWARD,
            lifetime=ENEMY_DEFAULT_LIFETIME,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE,
            damage=ENEMY_DEFAULT_DAMAGE + 12. * (player.get_level() - 1),
            damage_spread=ENEMY_DEFAULT_DAMAGE_SPREAD,
        )

    def shoot(self):
        if self.difficulty == 5:
            self.shoot_explosive()
        if self.difficulty >= 4:
            self.shoot_def_trajectory()
        else:
            self.shoot_normal()


class FastEnemy(Enemy):
    """Moves fast, has low health, small size and does not shoot."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        _player_level = player.get_level()
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.FAST,
            player=player,
            color=Color('#ad2f52'),
            speed=ENEMY_DEFAULT_SPEED * 1.3 + 30. * _player_level,
            health=ENEMY_DEFAULT_MAX_HEALTH * 3.,
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            reward=ENEMY_DEFAULT_REWARD * (1.4 + 0.1 * _player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 6. * (_player_level - 1),
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.15,
            turn_coefficient=0.35,
        )
        self.shoots_player = False


class TankEnemy(Enemy):
    """Moves slowly, has high health and big size. Shoots in bursts.
    Spawns some basic enemies on natural death."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self._player_level = player.get_level()
        self._difficulty = player.settings.difficulty
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.TANK,
            player=player,
            color=Color('#9e401e'),
            speed=ENEMY_DEFAULT_SPEED * 0.7,
            health=ENEMY_DEFAULT_MAX_HEALTH * 3. + 80. * (self._player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.0,
            reward=ENEMY_DEFAULT_REWARD * (2.3 + 0.1 * self._player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 3. * self._player_level,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.4,
            damage=ENEMY_DEFAULT_DAMAGE * (1. + 0.1 * self._player_level),
        )
        self._spread = 1. + 0.03 * (self._player_level + player.settings.difficulty)
        self.cooldown.set_percent_full(0.8)
    
    def shoot(self):
        """Shoots in bursts with probability 0.5 and explosive projectiles with probability 0.5."""
        delta_num_proj = [-2, -2, -1, 1, 2][self._difficulty - 1]
        if random.random() < 0.5:
            num_subproj = 3 + self._player_level + delta_num_proj
            self.shoot_explosive(num_of_subprojectiles=num_subproj)
            return
        num_shots = random.randint(2, 2 + int(self._player_level) + delta_num_proj)
        for _ in range(num_shots):
            self.shoot_normal(speed_mult=1.2 + 0.05 * self._player_level)
    
    def on_natural_death(self):
        super().on_natural_death()
        for _ in range(random.randint(3, 7)):
            self.entities_buffer.append(
                BasicEnemy(
                    pos=self.pos + random_unit_vector() * 150,
                    player=self.homing_target, # type: ignore
                )
            )


class ArtilleryEnemy(Enemy):
    """Does not move, shoots homing projectiles."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self._player_level = player.get_level()
        self._difficulty = player.settings.difficulty
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.ARTILLERY,
            player=player,
            color=Color('#005c22'),
            speed=10.,
            health=ENEMY_DEFAULT_MAX_HEALTH * 2. + 40. * (self._player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 1.3,
            reward=ENEMY_DEFAULT_REWARD * (1.9 + 0.1 * self._player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 3. * self._player_level,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.3,
            damage=ENEMY_DEFAULT_DAMAGE * 1.35,
        )
        self.cooldown.set_percent_full(0.2)
    
    def shoot(self):
        delta_num_proj = [-1, -1, 0, 1, 1][self._difficulty - 1]
        if random.random() < 0.5:
            self.shoot_def_trajectory(num_of_projectiles=1 + random.randint(1, 3) + delta_num_proj)
            return
        self.shoot_homing(speed_mult=1.2 + 0.05 * self._player_level)
    
    def on_natural_death(self):
        super().on_natural_death()
        self.spread = math.pi / 2.
        for _ in range(random.randint(1, 5)):
            self.shoot_homing(speed_mult=1.4)
        self.entities_buffer.append(
            FastEnemy(
                pos=self.pos + random_unit_vector() * 150,
                player=self.homing_target, # type: ignore
            )
        )


class MinerEnemy(Enemy):
    """Does not shoot. Dashes towards the player,
    explodes and spawns a bunch of mines when getting close."""
    def __init__(self,
            pos: Vector2,
            player: Player,
        ):         
        self._player_level = player.get_level()
        self._difficulty = player.settings.difficulty
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.MINER,
            player=player,
            color=Color('#103d9e'),
            speed=ENEMY_DEFAULT_SPEED * 1.2,
            health=ENEMY_DEFAULT_MAX_HEALTH + 20. * (self._player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 1.3,
            reward=ENEMY_DEFAULT_REWARD * (2. + 0.1 * self._player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 3. * self._player_level,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE,
            turn_coefficient=0.4,
        )
        self.shoots_player = False
        self.render_trail = True
        self.dash_cooldown_timer = Timer(max_time=6.)
        self.dash_active_timer = Timer(max_time=0.5 + 0.04 * self._player_level)
        self.dash_active_timer.turn_off()
        self.COLOR_IN_DASH = Color('#d3e8e3')
        self.NORMAL_COLOR = self.color
    
    def is_in_dash(self) -> bool:
        return self.dash_active_timer.running()
    
    def update(self, time_delta: float):
        self.dash_cooldown_timer.tick(time_delta)
        if not self.dash_cooldown_timer.running():
            self.dash_active_timer.reset()
            play_sfx('miner_dash')
            self.dash_cooldown_timer.reset()
        if self.is_in_dash():
            self.dash_active_timer.tick(time_delta)
            self.speed = ENEMY_DEFAULT_SPEED * 4 + self._player_level // 2.
            self.color = self.COLOR_IN_DASH
        else:
            self.speed = ENEMY_DEFAULT_SPEED * 1.2
            self.color = self.NORMAL_COLOR
        if (self.homing_target.get_pos() - self.pos).magnitude_squared() < 65.**2:
            self.kill()
            for _ in range(random.randint(0, 3) + self._player_level // 4):
                self.entities_buffer.append(
                    Mine(
                        self.homing_target.pos + random_unit_vector() * random.uniform(50., 200. + 30 * self._player_level),
                        damage=MINE_DEFAULT_DAMAGE + 8. * self._player_level,
                    )
                )
            self.entities_buffer.append(
                AOEEffect(
                    pos=self.pos,
                    size=80.,
                    damage=self.damage_on_collision * 0.7,
                    color=self.color,
                    animation_lingering_time=0.8
                )
            )
        super().update(time_delta)


class BossEnemy(Enemy):
    """Moves fast, has high health, big size, low cooldown. 
    Shoots normal and homing projectiles."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self._player_level = player.get_level()
        self.difficulty = player.settings.difficulty
        self.difficulty_mult = 1. + 0.1 * (self.difficulty - 3) # from 0.8 to 1.2
        self._player_pos = player.get_pos()
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.BOSS,
            player=player,
            color=Color(BOSS_ENEMY_COLOR_HEX),
            speed=ENEMY_DEFAULT_SPEED + self.difficulty_mult * 20 * (self._player_level - 1),
            health=ENEMY_DEFAULT_MAX_HEALTH * 5. + 70. * (self._player_level - 1) * self.difficulty_mult**2,
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.6,
            reward=ENEMY_DEFAULT_REWARD * (3. + 0.2 * self._player_level),
            damage=ENEMY_DEFAULT_DAMAGE + 5 * self._player_level * self.difficulty_mult**2,
            lifetime=math.inf,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE * 10.,
            turn_coefficient=0.65,
        )
        self._spawn_oil_spills_cooldown = max(BOSS_DEFAULT_OIL_SPILL_SPAWN_COOLDOWN / self.difficulty_mult - 2. * self._player_level, 5.)
        self._spawn_oil_spills_timer = Timer(max_time=self._spawn_oil_spills_cooldown)
        DIFF_MULT = {1: 0, 2: 0.8, 3: 1, 4: 3, 5: 8}
        self._regen_rate = (BOSS_DEFAULT_REGEN_RATE * DIFF_MULT[self.difficulty] +
            5. * (self._player_level - 1))
        self.PROJECTILE_TYPES_TO_WEIGHTS = {
            ProjectileType.NORMAL: 200,
            ProjectileType.HOMING: 30 + 20 * DIFF_MULT[self.difficulty] + 20 * (self._player_level - 1),
            ProjectileType.EXPLOSIVE: 20 + 30 * DIFF_MULT[self.difficulty] + 30 * (self._player_level - 1),
            ProjectileType.DEF_TRAJECTORY: 10 + 20 * DIFF_MULT[self.difficulty] + 20 * (self._player_level - 1),
        }

    def update(self, time_delta: float):
        super().update(time_delta)
        self._spawn_oil_spills_timer.tick(time_delta)
        self.health.change(self._regen_rate * time_delta)
        if not self._spawn_oil_spills_timer.running():
            self.spawn_oil_spills()
            self._spawn_oil_spills_cooldown *= 0.9 # with every spawn the cooldown decreases
            self._spawn_oil_spills_timer.reset(with_max_time=self._spawn_oil_spills_cooldown)

    def shoot(self):
        projectile_type_to_shoot = random.choices(
            list(self.PROJECTILE_TYPES_TO_WEIGHTS.keys()),
            weights=list(self.PROJECTILE_TYPES_TO_WEIGHTS.values()),
            k=1
        )[0]
        if projectile_type_to_shoot == ProjectileType.NORMAL:
            self.shoot_normal()
        elif projectile_type_to_shoot == ProjectileType.HOMING:
            self.shoot_homing(speed_mult=0.7)
        elif projectile_type_to_shoot == ProjectileType.EXPLOSIVE:
            self.shoot_explosive(num_of_subprojectiles=4)
        elif projectile_type_to_shoot == ProjectileType.DEF_TRAJECTORY:
            self.shoot_def_trajectory(num_of_projectiles=1 + self._player_level // 3)
    
    def on_natural_death(self):
        raise ValueError('Bosses should not die naturally.')

    def spawn_oil_spills(self):
        towards_player = self._player_pos - self.pos
        # precision of spawning oil spills increases with level and difficulty
        inprecision = 0.5 - 0.03 * (self._player_level + self.difficulty - 3)
        self.entities_buffer.append(
            OilSpill(pos=self.pos + towards_player * random.uniform(1. - inprecision, 1. + inprecision), 
                size=OIL_SPILL_SIZE * random.uniform(0.5, 1.5))
        )


ENEMY_TYPE_TO_CLASS = {
    EnemyType.BASIC: BasicEnemy,
    EnemyType.FAST: FastEnemy,
    EnemyType.ARTILLERY: ArtilleryEnemy,
    EnemyType.TANK: TankEnemy,
    EnemyType.MINER: MinerEnemy,
    EnemyType.BOSS: BossEnemy,
}

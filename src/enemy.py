from dataclasses import dataclass
import math
import random
from pygame import Vector2, Color

from src.entity import Entity, Corpse
from src.enums import EntityType, EnemyType, ProjectileType
from src.player import Player
from src.utils import Slider, Timer
from src.projectile import Projectile, HomingProjectile, ExplosiveProjectile
from src.oil_spill import OilSpill
from front.utils import random_unit_vector

from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, ENEMY_DEFAULT_SHOOTING_SPREAD,
    ENEMY_DEFAULT_LIFETIME, OIL_SPILL_SIZE, ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN,
    ENEMY_DEFAULT_REWARD, ENEMY_DEFAULT_DAMAGE, ENEMY_DEFAULT_DAMAGE_SPREAD, ENEMY_DEFAULT_COLLISION_DAMAGE)


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
    EnemyType.FAST: ENEMY_DEFAULT_SIZE * 0.85,
    EnemyType.TANK: ENEMY_DEFAULT_SIZE * 1.8,
    EnemyType.ARTILLERY: ENEMY_DEFAULT_SIZE * 2,
    EnemyType.BOSS: ENEMY_DEFAULT_SIZE * 2.7,
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
        ):
        super().__init__(
            pos=pos,
            type=EntityType.ENEMY,
            size=ENEMY_SIZE_MAP[enemy_type],
            speed=speed, 
            color=color,
            can_spawn_entities=True,
            homing_target=player,
        )
        self._health = Slider(health)
        self._cooldown = Timer(max_time=shoot_cooldown)
        self._cooldown.set_percent_full(0.5) # enemies start with half of the cooldown
        self._lifetime_cooldown = Timer(max_time=lifetime)
        self._reward = reward
        self._enemy_type = enemy_type
        self._spread = spread # in radians
        self._damage = damage
        self._damage_spread = damage_spread

        self._damage_on_collision = damage_on_collision
        self._shoots_player = True
        
    
    def get_shoot_direction(self) -> Vector2:
        rot_angle = random.uniform(-self._spread, self._spread) if self._spread else 0.
        return self.vel.rotate(rot_angle).normalize()

    def shoot(self):
        self.shoot_normal()
    
    def update(self, time_delta: float):
        if not self.is_alive(): return
        if not self._health.is_alive(): self.kill()
        super().update(time_delta)
        self._cooldown.tick(time_delta)
        self._lifetime_cooldown.tick(time_delta)
        if not self._lifetime_cooldown.running():
            self.kill()
            self.on_natural_death()
        if not self._shoots_player: return
        if not self._cooldown.running():
            self.shoot()
            self._cooldown.reset()

    def shoot_normal(self, **kwargs):
        speed_mult = kwargs.get('speed_mult', 1.)
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            Projectile(
                pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                vel=direction,
                damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                projectile_type=ProjectileType.NORMAL,
                speed=self.speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.4) * speed_mult,
            )
        )
    
    def shoot_homing(self, **kwargs):
        speed_mult = kwargs.get('speed_mult', 1.)
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            HomingProjectile(
                _pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                _vel=direction,
                _damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                _speed=(self.speed + PROJECTILE_DEFAULT_SPEED * 0.8) * speed_mult,
                _homing_target=self.homing_target,
            )
        )

    def shoot_explosive(self, num_of_subprojectiles: int = 6):
        direction = self.get_shoot_direction()
        self.entities_buffer.append(
            ExplosiveProjectile(
                _pos=self.pos.copy() + direction * (self.size * random.uniform(1.5, 2.5)),
                _vel=direction,
                _damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                _speed=self.speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.2),
                _num_subprojectiles=num_of_subprojectiles,
            )
        )
    
    def on_natural_death(self):
        self.entities_buffer.append(Corpse(self))

    def get_health(self) -> Slider: return self._health

    def get_reward(self) -> float: return self._reward


class BasicEnemy(Enemy):
    """Just a normal enemy."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.BASIC,
            player=player,
            color=Color('red'),
            speed=ENEMY_DEFAULT_SPEED,
            health=ENEMY_DEFAULT_MAX_HEALTH,
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            reward=ENEMY_DEFAULT_REWARD,
            lifetime=ENEMY_DEFAULT_LIFETIME,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE,
            damage=ENEMY_DEFAULT_DAMAGE,
            damage_spread=ENEMY_DEFAULT_DAMAGE_SPREAD,
        )


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
            speed=ENEMY_DEFAULT_SPEED * (1.6 + 0.05 * _player_level),
            health=ENEMY_DEFAULT_MAX_HEALTH * 0.8 + 20. * (_player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            reward=ENEMY_DEFAULT_REWARD * (1.4 + 0.1 * _player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 6. * (_player_level - 1),
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.15,
        )
        self._shoots_player = False


class TankEnemy(Enemy):
    """Moves slowly, has high health and big size. Shoots in bursts.
    Spawns some basic enemies on natural death."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self._player_level = player.get_level()
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.TANK,
            player=player,
            color=Color('#9e401e'),
            speed=ENEMY_DEFAULT_SPEED * 0.6,
            health=ENEMY_DEFAULT_MAX_HEALTH * 3.5 + 35. * (self._player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.0,
            reward=ENEMY_DEFAULT_REWARD * (2.3 + 0.1 * self._player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 3. * self._player_level,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.4,
            damage=ENEMY_DEFAULT_DAMAGE * (1. + 0.1 * self._player_level),
        )
        self._spread = 1.3 + 0.03 * self._player_level
    
    def shoot(self):
        """Shoots in bursts with probability 0.5 and explosive projectiles with probability 0.5."""
        if random.random() < 0.5:
            num_shots = 3 + self._player_level
            self.shoot_explosive(num_of_subprojectiles=num_shots)
            return
        num_shots = random.randint(2, 3 + int(self._player_level // 2))
        for _ in range(num_shots):
            self.shoot_normal(speed_mult=1.4)
    
    def on_natural_death(self):
        super().on_natural_death()
        for _ in range(random.randint(1, 3)):
            self.entities_buffer.append(
                BasicEnemy(
                    pos=self.pos + random_unit_vector() * self.size * 1.5,
                    player=self.homing_target, # type: ignore
                )
            )


class ArtilleryEnemy(Enemy):
    """Does not move, shoots homing projectiles."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        _player_level = player.get_level()
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.ARTILLERY,
            player=player,
            color=Color('#005c22'),
            speed=10.,
            health=ENEMY_DEFAULT_MAX_HEALTH * 2.5 + 35. * (_player_level - 1),
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 1.4,
            reward=ENEMY_DEFAULT_REWARD * (2. + 0.1 * _player_level),
            lifetime=ENEMY_DEFAULT_LIFETIME + 3. * _player_level,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.3,
            damage=ENEMY_DEFAULT_DAMAGE * 1.35,
        )
    
    def shoot(self):
        self.shoot_homing(speed_mult=1.2)
    
    def on_natural_death(self):
        super().on_natural_death()
        # spawn some homing projectiles
        for _ in range(random.randint(1, 3)):
            self.shoot_homing(speed_mult=1.4)


class BossEnemy(Enemy):
    """Moves fast, has high health, big size, low cooldown. 
    Shoots normal and homing projectiles."""
    def __init__(self, 
            pos: Vector2,
            player: Player,
        ):
        self._player_level = player.get_level()
        self._player_pos = player.get_pos()
        super().__init__(
            pos=pos,
            enemy_type=EnemyType.BOSS,
            player=player,
            color=Color('#510e78'),
            speed=ENEMY_DEFAULT_SPEED + 40 * (self._player_level - 1),
            health=(ENEMY_DEFAULT_MAX_HEALTH) * 3.5 + 35. * self._player_level,
            shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.5,
            reward=ENEMY_DEFAULT_REWARD * (3. + 0.12 * self._player_level),
            lifetime=math.inf,
            damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE * 10.,
        )
        self._spawn_oil_spills_cooldown = 18. - 1.3 * self._player_level
        self._spawn_oil_spills_timer = Timer(max_time=self._spawn_oil_spills_cooldown)
        self._regen_rate = 0.6 + 0.15 * (self._player_level - 1)

    def update(self, time_delta: float):
        super().update(time_delta)
        self._spawn_oil_spills_timer.tick(time_delta)
        self._health.change(self._regen_rate * time_delta)
        if not self._spawn_oil_spills_timer.running():
            self.spawn_oil_spills()
            self._spawn_oil_spills_cooldown *= 0.9 # with every spawn the cooldown decreases
            self._spawn_oil_spills_timer.reset(with_max_time=self._spawn_oil_spills_cooldown)

    def shoot(self):
        if random.random() < 0.3:
            self.shoot_homing(speed_mult=0.65)
        else:
            self.shoot_normal()
    
    def on_natural_death(self):
        raise ValueError('Bosses should not die naturally.')

    def spawn_oil_spills(self):
        towards_player = self._player_pos - self.pos
        # precision of spawning oil spills increases with level
        inprecision = 0.5 - 0.028 * self._player_level 
        self.entities_buffer.append(
            OilSpill(_pos=self.pos + towards_player * random.uniform(1. - inprecision, 1. + inprecision), 
                     _size=OIL_SPILL_SIZE * random.uniform(0.5, 1.5))
        )


ENEMY_TYPE_TO_CLASS = {
    EnemyType.BASIC: BasicEnemy,
    EnemyType.FAST: FastEnemy,
    EnemyType.ARTILLERY: ArtilleryEnemy,
    EnemyType.TANK: TankEnemy,
    EnemyType.BOSS: BossEnemy,
}

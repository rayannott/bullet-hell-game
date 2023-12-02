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

from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, ENEMY_DEFAULT_LIFETIME, OIL_SPILL_SIZE,
    ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN, ENEMY_DEFAULT_REWARD, ENEMY_DEFAULT_DAMAGE, ENEMY_DEFAULT_DAMAGE_SPREAD)


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


ENEMY_STATS_MAP = {
    # size, color, speed, health, shoot_cooldown, reward
    EnemyType.BASIC: EnemyStats(
        size=ENEMY_DEFAULT_SIZE, color=Color('red'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH, 
        shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
        reward=ENEMY_DEFAULT_REWARD, lifetime=ENEMY_DEFAULT_LIFETIME, damage_on_collision=60.),
    EnemyType.FAST: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 0.85, color=Color('#ad2f52'), speed=ENEMY_DEFAULT_SPEED * 1.7, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 0.8, 
        shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
        reward=ENEMY_DEFAULT_REWARD * 1.2, lifetime=ENEMY_DEFAULT_LIFETIME, damage_on_collision=70),
    EnemyType.TANK: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 1.8, color=Color('#9e401e'), speed=ENEMY_DEFAULT_SPEED * 0.7, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 4., 
        shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.0,
        reward=ENEMY_DEFAULT_REWARD * 1.8, lifetime=ENEMY_DEFAULT_LIFETIME, damage_on_collision=80),
    EnemyType.ARTILLERY: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2, color=Color('#005c22'), speed=0., 
        health=ENEMY_DEFAULT_MAX_HEALTH * 2.5, 
        shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 1.4,
        reward=ENEMY_DEFAULT_REWARD * 2.5, lifetime=ENEMY_DEFAULT_LIFETIME, damage_on_collision=80.),
    EnemyType.BOSS: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2.7, color=Color('#510e78'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 5., 
        shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.5,
        reward=ENEMY_DEFAULT_REWARD * 5., lifetime=math.inf, damage_on_collision=math.inf),
}


class Enemy(Entity):
    def __init__(self, 
            _pos: Vector2,
            _enemy_type: EnemyType,
            _player: Player,
        ):
        stats = ENEMY_STATS_MAP[_enemy_type]
        super().__init__(
            _pos=_pos,
            _type=EntityType.ENEMY,
            _size=stats.size,
            _speed=stats.speed, 
            _color=stats.color,
            _can_spawn_entities=True,
            _homing_target=_player,
        )
        # TODO move stats to classes below
        self._health = Slider(stats.health)
        self._cooldown = Timer(max_time=stats.shoot_cooldown)
        self._lifetime_cooldown = Timer(max_time=stats.lifetime)
        self._reward = stats.reward
        self._enemy_type = _enemy_type
        self._spread = 0.5 # in radians
        self._damage = ENEMY_DEFAULT_DAMAGE
        self._damage_spread = ENEMY_DEFAULT_DAMAGE_SPREAD

        self._damage_on_collision = stats.damage_on_collision
        self._shoots_player = True
        
    
    def get_shoot_direction(self) -> Vector2:
        rot_angle = random.uniform(-self._spread, self._spread) if self._spread else 0.
        return self._vel.rotate(rot_angle).normalize()

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

    def shoot_normal(self):
        direction = self.get_shoot_direction()
        self._entities_buffer.append(
            Projectile(
                _pos=self._pos.copy() + direction * (self._size * random.uniform(1.5, 2.5)),
                _vel=direction,
                _damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                _projectile_type=ProjectileType.NORMAL,
                _speed=self._speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.2),
            )
        )
    
    def shoot_homing(self):
        direction = self.get_shoot_direction()
        self._entities_buffer.append(
            HomingProjectile(
                _pos=self._pos.copy() + direction * (self._size * random.uniform(1.5, 2.5)),
                _vel=direction,
                _damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                _speed=self._speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.2),
                _homing_target=self._homing_target,
            )
        )

    def shoot_explosive(self, num_of_subprojectiles: int = 6):
        direction = self.get_shoot_direction()
        self._entities_buffer.append(
            ExplosiveProjectile(
                _pos=self._pos.copy() + direction * (self._size * random.uniform(1.5, 2.5)),
                _vel=direction,
                _damage=self._damage + random.uniform(-self._damage_spread, self._damage_spread),
                _speed=self._speed + PROJECTILE_DEFAULT_SPEED * random.uniform(0.8, 1.2),
                _num_subprojectiles=num_of_subprojectiles,
                # _homing_target=self._homing_target,
            )
        )
    
    def on_natural_death(self):
        self._entities_buffer.append(Corpse(self))

    def get_health(self): return self._health

    def get_reward(self): return self._reward


class BasicEnemy(Enemy):
    """Just a normal enemy."""
    def __init__(self, 
            _pos: Vector2,
            _player: Player,
        ):
        super().__init__(
            _pos=_pos,
            _enemy_type=EnemyType.BASIC,
            _player=_player,
        )


class FastEnemy(Enemy):
    """Moves fast, has low health, small size and does not shoot."""
    def __init__(self, 
            _pos: Vector2,
            _player: Player,
        ):
        super().__init__(
            _pos=_pos,
            _enemy_type=EnemyType.FAST,
            _player=_player,
        )
        self._shoots_player = False


class TankEnemy(Enemy):
    """Moves slowly, has high health and big size. Shoots in bursts."""
    def __init__(self, 
            _pos: Vector2,
            _player: Player,
        ):
        super().__init__(
            _pos=_pos,
            _enemy_type=EnemyType.TANK,
            _player=_player,
        )
        self._player_level = _player.get_level()
        self._spread = 1.4
    
    def shoot(self):
        """Shoots in bursts with probability 0.5 and explosive projectiles with probability 0.5."""
        if random.random() < 0.5:
            num_shots = 3 + self._player_level
            self.shoot_explosive(num_of_subprojectiles=num_shots)
            return
        num_shots = random.randint(2, 5)
        for _ in range(num_shots):
            self.shoot_normal()
    
    def on_natural_death(self):
        super().on_natural_death()
        for _ in range(random.randint(1, 3)):
            self._entities_buffer.append(
                BasicEnemy(
                    _pos=self._pos + random_unit_vector() * self._size * 1.5,
                    _player=self._homing_target, # type: ignore
                )
            )


class ArtilleryEnemy(Enemy):
    """Does not move, shoots homing projectiles."""
    def __init__(self, 
            _pos: Vector2,
            _player: Player,
        ):
        super().__init__(
            _pos=_pos,
            _enemy_type=EnemyType.ARTILLERY,
            _player=_player,
        )
    
    def shoot(self):
        self.shoot_homing()
    
    def on_natural_death(self):
        super().on_natural_death()
        # spawn some homing projectiles
        for _ in range(random.randint(1, 3)):
            self.shoot_homing()


class BossEnemy(Enemy):
    """Moves fast, has high health, big size, low cooldown. 
    Shoots normal and homing projectiles."""
    def __init__(self, 
            _pos: Vector2,
            _player: Player,
        ):
        super().__init__(
            _pos=_pos,
            _enemy_type=EnemyType.BOSS,
            _player=_player,
        )
        self._player_level = _player.get_level()
        self._player_pos = _player.get_pos()
        spawn_oil_spills_cooldown = 18. - 1.3 * self._player_level
        self._spawn_oil_spills_cooldown = Timer(max_time=spawn_oil_spills_cooldown)

    def update(self, time_delta: float):
        super().update(time_delta)
        self._spawn_oil_spills_cooldown.tick(time_delta)
        if not self._spawn_oil_spills_cooldown.running():
            self.spawn_oil_spills()
            self._spawn_oil_spills_cooldown.reset()

    def shoot(self):
        if random.random() < 0.3:
            self.shoot_homing()
        else:
            self.shoot_normal()
    
    def on_natural_death(self):
        raise ValueError('Bosses should not die naturally.')

    def spawn_oil_spills(self):
        towards_player = self._player_pos - self._pos
        self._entities_buffer.append(
            OilSpill(_pos=self._pos + towards_player * random.uniform(0.5, 1.5), 
                     _size=OIL_SPILL_SIZE * random.uniform(0.5, 1.7))
        )


ENEMY_TYPE_TO_CLASS = {
    EnemyType.BASIC: BasicEnemy,
    EnemyType.FAST: FastEnemy,
    EnemyType.ARTILLERY: ArtilleryEnemy,
    EnemyType.TANK: TankEnemy,
    EnemyType.BOSS: BossEnemy,
}

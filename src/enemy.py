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

from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, 
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
            _pos: Vector2,
            _enemy_type: EnemyType,
            _color: Color,
            _speed: float,
            _health: float,
            _shoot_cooldown: float,
            _reward: float,
            _lifetime: float,
            _damage_on_collision: float,
            _player: Player,     
        ):
        super().__init__(
            _pos=_pos,
            _type=EntityType.ENEMY,
            _size=ENEMY_SIZE_MAP[_enemy_type],
            _speed=_speed, 
            _color=_color,
            _can_spawn_entities=True,
            _homing_target=_player,
        )
        # TODO move _to classes below
        self._health = Slider(_health)
        self._cooldown = Timer(max_time=_shoot_cooldown)
        self._lifetime_cooldown = Timer(max_time=_lifetime)
        self._reward = _reward
        self._enemy_type = _enemy_type
        self._spread = 0.5 # in radians
        self._damage = ENEMY_DEFAULT_DAMAGE
        self._damage_spread = ENEMY_DEFAULT_DAMAGE_SPREAD

        self._damage_on_collision = _damage_on_collision
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
            _color=Color('red'),
            _speed=ENEMY_DEFAULT_SPEED,
            _health=ENEMY_DEFAULT_MAX_HEALTH,
            _shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            _reward=ENEMY_DEFAULT_REWARD,
            _lifetime=ENEMY_DEFAULT_LIFETIME,
            _damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE,
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
            _color=Color('#ad2f52'),
            _speed=ENEMY_DEFAULT_SPEED * 1.7,
            _health=ENEMY_DEFAULT_MAX_HEALTH * 0.8,
            _shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN,
            _reward=ENEMY_DEFAULT_REWARD * 1.2,
            _lifetime=ENEMY_DEFAULT_LIFETIME,
            _damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.15,
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
            _color=Color('#9e401e'),
            _speed=ENEMY_DEFAULT_SPEED * 0.6,
            _health=ENEMY_DEFAULT_MAX_HEALTH * 3.5,
            _shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.0,
            _reward=ENEMY_DEFAULT_REWARD * 1.8,
            _lifetime=ENEMY_DEFAULT_LIFETIME,
            _damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.4,
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
            _color=Color('#005c22'),
            _speed=0.,
            _health=ENEMY_DEFAULT_MAX_HEALTH * 2.5,
            _shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 1.4,
            _reward=ENEMY_DEFAULT_REWARD * 2.5,
            _lifetime=ENEMY_DEFAULT_LIFETIME,
            _damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE*1.3,
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
            _color=Color('#510e78'),
            _speed=ENEMY_DEFAULT_SPEED,
            _health=ENEMY_DEFAULT_MAX_HEALTH * 5.,
            _shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.5,
            _reward=ENEMY_DEFAULT_REWARD * 5.,
            _lifetime=math.inf,
            _damage_on_collision=ENEMY_DEFAULT_COLLISION_DAMAGE * 10.,
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

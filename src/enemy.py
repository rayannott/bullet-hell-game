from dataclasses import dataclass
import random
from pygame import Vector2, Color

from src import Entity, Corpse, EntityType, EnemyType, Slider, Player, Timer, Projectile, HomingProjectile, ProjectileType
from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, ENEMY_DEFAULT_LIFETIME,
    ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN, ENEMY_DEFAULT_REWARD)


@dataclass
class EnemyStats:
    size: float
    color: Color
    speed: float
    health: float
    shoot_cooldown: float
    reward: float


ENEMY_STATS_MAP = {
    # size, color, speed, health, shoot_cooldown, reward
    EnemyType.BASIC: EnemyStats(
        size=ENEMY_DEFAULT_SIZE, color=Color('red'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN, reward=ENEMY_DEFAULT_REWARD),
    EnemyType.FAST: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 0.8, color=Color('#912644'), speed=ENEMY_DEFAULT_SPEED * 1.8, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 0.8, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN, reward=ENEMY_DEFAULT_REWARD * 1.2),
    EnemyType.TANK: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 1.8, color=Color('#9e401e'), speed=ENEMY_DEFAULT_SPEED * 0.7, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 4., shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.0, reward=ENEMY_DEFAULT_REWARD * 1.8),
    EnemyType.ARTILLERY: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2, color=Color('#005c22'), speed=0., 
        health=ENEMY_DEFAULT_MAX_HEALTH * 2.5, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.3, reward=ENEMY_DEFAULT_REWARD * 2.5),
    EnemyType.BOSS: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2.7, color=Color('#510e78'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 5., shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.5, reward=ENEMY_DEFAULT_REWARD * 5.),
}
# TODO: split these types into different classes 
# TODO  (make them have different behaviors like dogging bullets, dashes, etc.)


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
        self._health = Slider(stats.health)
        self._cooldown = Timer(max_time=stats.shoot_cooldown)
        self._lifetime_cooldown = Timer(max_time=ENEMY_DEFAULT_LIFETIME)
        self._reward = stats.reward
        self._enemy_type = _enemy_type
        self._spread = 0.5 # in radians
        self._shoots_player = True
    
    def get_shoot_direction(self) -> Vector2:
        rot_angle = random.uniform(-self._spread, self._spread) if self._spread else 0.
        return self._vel.rotate(rot_angle).normalize()

    def shoot(self):
        self.shoot_normal()
    
    def update(self, time_delta: float):
        if not self._health.is_alive(): self.kill()
        if not self.is_alive(): return
        super().update(time_delta)
        self._cooldown.tick(time_delta)
        self._lifetime_cooldown.tick(time_delta)
        if not self._lifetime_cooldown.running():
            self.on_natural_death()
        if not self._shoots_player: return
        if not self._cooldown.running():
            self.shoot()
            self._cooldown.reset()

    def shoot_normal(self):
        direction = self.get_shoot_direction()
        self._entities_buffer.append(
            Projectile(
                _pos=self._pos.copy() + direction * self._size * 1.5,
                _vel=direction,
                _projectile_type=ProjectileType.NORMAL,
                _speed=self._speed + PROJECTILE_DEFAULT_SPEED,
            )
        )
    
    def shoot_homing(self):
        direction = self.get_shoot_direction()
        self._entities_buffer.append(
            HomingProjectile(
                _pos=self._pos.copy() + direction * self._size * 1.5,
                _vel=direction,
                _speed=self._speed + PROJECTILE_DEFAULT_SPEED,
                _homing_target=self._homing_target,
            )
        )
    
    def on_natural_death(self):
        # default: die and spawn corpse
        self.kill()
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
        self._spread = 1.4
    
    def shoot(self):
        num_shots = random.randint(2, 5)
        for _ in range(num_shots):
            self.shoot_normal()


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
    
    def shoot(self):
        if random.random() < 0.3:
            self.shoot_homing()
        else:
            self.shoot_normal()

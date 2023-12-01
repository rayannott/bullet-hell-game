from pygame import Vector2, Color

from src import HomingEntity, EntityType, EnemyType, Slider, Player, Timer, Projectile, ProjectileType
from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, 
    ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN)


ENEMY_STATS_MAP = {
    # size, color, speed, health
    EnemyType.BASIC: (ENEMY_DEFAULT_SIZE, Color('red'), ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_MAX_HEALTH),
    EnemyType.FAST: (ENEMY_DEFAULT_SIZE * 0.9, Color('#912644'), ENEMY_DEFAULT_SPEED * 2.2, ENEMY_DEFAULT_MAX_HEALTH * 0.8),
    EnemyType.TANK: (ENEMY_DEFAULT_SIZE * 1.8, Color('#9e401e'), ENEMY_DEFAULT_SPEED * 0.8, ENEMY_DEFAULT_MAX_HEALTH * 2.5),
    EnemyType.ARTILLERY: (ENEMY_DEFAULT_SIZE * 2, Color('#005c22'), 0., ENEMY_DEFAULT_MAX_HEALTH),
    EnemyType.BOSS: (ENEMY_DEFAULT_SIZE * 2.7, Color('#510e78'), ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_MAX_HEALTH * 5.),
}


class Enemy(HomingEntity):
    def __init__(self, 
            _pos: Vector2,
            _enemy_type: EnemyType,
            _player: Player,
        ):
        _size, _color, _speed, _health = ENEMY_STATS_MAP[_enemy_type]
        super().__init__(
            _pos=_pos,
            _type=EntityType.ENEMY,
            _size=_size,
            _speed=_speed, 
            _color=_color,
            _target=_player
        )
        self._health = Slider(_health)
        self._cooldown = Timer(max_time=ENEMY_DEFAULT_SHOOT_COOLDOWN)
    
    def shoot(self):
        # TODO: how to send this info to the game?
        direction = self._vel.normalize()
        return Projectile(
            _pos=self._pos.copy() + direction * self._size * 1.5,
            _vel=direction,
            _projectile_type=ProjectileType.NORMAL,
            _speed=self._speed + PROJECTILE_DEFAULT_SPEED,
        )
    
    def update(self, time_delta: float):
        if not self._health.is_alive(): self.kill()
        if not self._is_alive: return
        super().update(time_delta)
        self._cooldown.tick(time_delta)
        if not self._cooldown.running():
            self.shoot()
            self._cooldown.reset()

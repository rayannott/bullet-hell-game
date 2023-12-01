from pygame import Vector2, Color

from src import Entity, EntityType, ProjectileType, Timer
from config import (PROJECTILE_DEFAULT_SIZE, 
                        PROJECTILE_DEFAULT_SPEED, PROJECTILE_DEFAULT_LIFETIME)


class Projectile(Entity): # TODO: change this to EntityLifetime
    def __init__(self, 
            _pos: Vector2, 
            _vel: Vector2,
            _projectile_type: ProjectileType,
            _level: int,
            _speed: float = PROJECTILE_DEFAULT_SPEED,
            _lifetime: float = PROJECTILE_DEFAULT_LIFETIME
        ):
        super().__init__(
            _pos=_pos,
            _type=EntityType.PROJECTILE,
            _size=PROJECTILE_DEFAULT_SIZE,
            _speed=_speed,
            _vel=_vel,
        )
        self._projectile_type = _projectile_type
        self._level = _level
        self._lifetime = _lifetime
        self._color = Color('yellow')
        self._life_timer = Timer(max_time=self._lifetime)

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()

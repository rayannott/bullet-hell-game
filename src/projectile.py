from pygame import Vector2

from src import Entity, EntityType, ProjectileType, Timer
from src import EntityType, ProjectileType
from config.back import (PROJECTILE_DEFAULT_SIZE, 
                        PROJECTILE_DEFAULT_SPEED, PROJECTILE_DEFAULT_LIFETIME)


class Projectile(Entity):
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
        self.life_timer = Timer(max_time=self._lifetime)

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self.life_timer.tick(time_delta)
        if not self.life_timer.running():
            self.kill()

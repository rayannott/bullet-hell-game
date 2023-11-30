from base import Entity
from enums import EntityType, ProjectileType
from config.back import PROJECTILE_DEFAULT_SIZE

from pygame import Vector2


class Projectile(Entity):
    def __init__(self, 
            _pos: Vector2, 
            _vel: Vector2,
            _projectile_type: ProjectileType,
            _level: int
        ):
        super().__init__(
            _pos=_pos,
            _vel=_vel,
            _type=EntityType.PROJECTILE,
            _size=PROJECTILE_DEFAULT_SIZE,
        )
        self._projectile_type = _projectile_type
        self._level = _level
        # self._max_lifetime = 100
        # self._lifetime = 0

    def update(self):
        super().update()
        # self._lifetime += 1

    def is_alive(self) -> bool:
        # return super().is_alive() and self._lifetime < self._max_lifetime
        return True

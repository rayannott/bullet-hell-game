from base import Entity, EntityType

from pygame import Vector2


class Player(Entity):
    def __init__(self, _pos: Vector2):
        super().__init__(
            _pos=_pos,
            _vel=Vector2(0., 0.),
            _type=EntityType.PLAYER,
            _size=30.
        )
        self._vel_decay = 0.99
        self._gravity_point: Vector2 = self._pos
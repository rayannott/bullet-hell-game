from base import Entity
from enums import EntityType
from utils import Slider, Stats
from config.back import (PLAYER_SIZE, PLAYER_MAX_HEALTH, PLAYER_SPEED_RANGE,
                        PLAYER_MAX_ENERGY, PLAYER_STARTING_ENERGY)

from pygame import Vector2


class Player(Entity):
    def __init__(self, _pos: Vector2):
        super().__init__(
            _pos=_pos,
            _type=EntityType.PLAYER,
            _size=PLAYER_SIZE,
            _speed=PLAYER_SPEED_RANGE[0],
            _render_trail=True
        )
        self._vel_decay = 0.99 # ? do I need this at all?
        self._gravity_point: Vector2 = self._pos
        self._health = Slider(PLAYER_MAX_HEALTH)
        self._energy = Slider(PLAYER_MAX_ENERGY, PLAYER_STARTING_ENERGY)
        self._stats = Stats()

    def update(self, time_delta: float):
        super().update(time_delta)
        # TODO: velocity decay(?) and change according to gravity point
        # TODO: decrease energy, regenerate health

    def set_gravity_point(self, gravity_point: Vector2):
        self._gravity_point = gravity_point
    
from pygame import Color, Vector2

from config import ENERGY_ORB_SIZE, ENERGY_ORB_DEFAULT_LIFETIME
from src import Entity, EntityType, Timer


class EnergyOrb(Entity): # TODO: change this to EntityLifetime
    """
    An energy orb that the player can collect to increase their energy.
    """
    def __init__(self,
            _pos: Vector2,
            _energy: float,
            _lifetime: float = ENERGY_ORB_DEFAULT_LIFETIME
        ) -> None:
        super().__init__(
            _pos=_pos,
            _type=EntityType.ENERGY_ORB,
            _size=ENERGY_ORB_SIZE,
            _color=Color('magenta'),
            _render_trail=False
        )
        self._energy = _energy
        self._lifetime = _lifetime
        self._life_timer = Timer(max_time=self._lifetime)

    def energy_left(self) -> float:
        return self._energy * (1. - self._life_timer.progress())

    def update(self, time_delta: float) -> None:
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()
    
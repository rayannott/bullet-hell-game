from pygame import Color, Vector2

from src.entity import Entity, EntityType
from src.utils import Timer
from config import ENERGY_ORB_SIZE


class EnergyOrb(Entity): # TODO: change this to EntityLifetime
    """
    An energy orb that the player can collect to increase their energy.
    """
    def __init__(self,
            pos: Vector2,
            energy: float,
            lifetime: float
        ) -> None:
        super().__init__(
            pos=pos,
            type=EntityType.ENERGY_ORB,
            size=ENERGY_ORB_SIZE,
            color=Color('#f014a0'),
            render_trail=False
        )
        self._energy = energy
        self._lifetime = lifetime
        self._life_timer = Timer(max_time=self._lifetime)

    def energy_left(self) -> float:
        return self._energy * (1. - self._life_timer.get_percent_full())

    def update(self, time_delta: float) -> None:
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()
    
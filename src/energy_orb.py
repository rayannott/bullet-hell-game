from pygame import Color, Vector2

from src.entity import Entity, EntityType
from src.utils import Timer
from config import ENERGY_ORB_SIZE, NICER_MAGENTA_HEX, LIGHT_MAGENTA_HEX


class EnergyOrb(Entity): # TODO: change this to EntityLifetime
    """
    An energy orb that the player can collect to increase their energy.
    """
    def __init__(self,
            pos: Vector2,
            energy: float,
            lifetime: float,
            num_extra_bullets: int = False,
            is_enemy_bonus_orb: bool = False
        ) -> None:
        size = ENERGY_ORB_SIZE
        self.num_extra_bullets = num_extra_bullets
        color = Color(LIGHT_MAGENTA_HEX if self.num_extra_bullets else NICER_MAGENTA_HEX)
        super().__init__(
            pos=pos,
            type=EntityType.ENERGY_ORB,
            size=size,
            color=color,
            render_trail=False
        )
        self._energy = energy
        self._is_enemy_bonus_orb = is_enemy_bonus_orb
        self._lifetime = lifetime
        self._life_timer = Timer(max_time=self._lifetime)

    def energy_left(self) -> float:
        return self._energy * (1. - self._life_timer.get_percent_full())

    def is_enemy_bonus_orb(self) -> bool:
        return self._is_enemy_bonus_orb

    def update(self, time_delta: float) -> None:
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()
    
from pygame import Color, Vector2

from src.entities.entity import Entity, EntityType
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
            render_trail=False,
            lifetime=lifetime,
        )
        self._energy = energy
        self._is_enemy_bonus_orb = is_enemy_bonus_orb

    def energy_left(self) -> float:
        return self._energy * (1. - self.i_has_lifetime.timer.get_percent_full())

    def is_enemy_bonus_orb(self) -> bool:
        return self._is_enemy_bonus_orb

    def update(self, time_delta: float) -> None:
        return super().update(time_delta)
    
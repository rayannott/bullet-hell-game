from pygame import Color

from src.entity import Entity
from src.enums import EntityType


class Corpse(Entity):
    def __init__(self,
        of_entity: Entity,
    ):
        super().__init__(
            pos=of_entity.get_pos(),
            type=EntityType.CORPSE,
            size=of_entity.get_size() * 1.5, # make the corpse a bit bigger than the entity
            color=Color('gray'),
        )
        self._damage_on_collision = 70.

    def update(self, time_delta: float): return super().update(time_delta)

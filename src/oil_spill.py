from pygame import Vector2, Color

from src.entity import Entity
from src.enums import EntityType
from src.utils import Timer
from config import OIL_SPILL_SIZE, OIL_SPILL_LIFETIME, OIL_SPILL_SIZE_GROWTH_RATE


class OilSpill(Entity):
    def __init__(self, pos: Vector2, size: float = OIL_SPILL_SIZE):
        super().__init__(
            pos=pos,
            size=size,
            type=EntityType.OIL_SPILL,
            speed=0.,
            render_trail=False,
            can_spawn_entities=False,
            color=Color('#a37d37'),
            lifetime=OIL_SPILL_LIFETIME,
        )
        self.ACTIVATED_COLOR = self.color
        self.INACTIVE_COLOR = Color('#453820')
        self._activation_timer = Timer(max_time=1.5)
    
    def is_activated(self) -> bool:
        return not self._activation_timer.running()

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self.is_alive(): return
        self._activation_timer.tick(time_delta)
        if self.is_activated():
            self.color = self.ACTIVATED_COLOR
            self.size += OIL_SPILL_SIZE_GROWTH_RATE * time_delta
        else:
            self.color = self.INACTIVE_COLOR

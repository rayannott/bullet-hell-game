from src.base import Entity
from src.enums import EntityType
from src.utils import Timer
from config import OIL_SPILL_SIZE, OIL_SPILL_LIFETIME, OIL_SPILL_SIZE_GROWTH_RATE

from pygame import Vector2, Color

class OilSpill(Entity):
    def __init__(self, _pos: Vector2, _size: float = OIL_SPILL_SIZE):
        super().__init__(
            _pos=_pos,
            _size=_size,
            _type=EntityType.OIL_SPILL,
            _speed=0.,
            _render_trail=False,
            _can_spawn_entities=False,
            _color=Color('#453820'),
        )
        self._lifetime_timer = Timer(max_time=OIL_SPILL_LIFETIME)

    def update(self, time_delta: float):
        if not self.is_alive(): return
        self._lifetime_timer.tick(time_delta)
        if not self._lifetime_timer.running(): self.kill()
        self._size += OIL_SPILL_SIZE_GROWTH_RATE * time_delta

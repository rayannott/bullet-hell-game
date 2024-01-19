from __future__ import annotations
from collections import deque
from pygame import Vector2

from src.utils.utils import Timer
import src.entities.entity
from config import TRAIL_MAX_LENGTH, TRAIL_POINTS_PER_SECOND


class HasLifetimeInterface:
    def __init__(self, lifetime: float) -> None:
        self.timer = Timer(max_time=lifetime)
    
    def tick_is_alive(self, time_delta: float) -> bool:
        """Returns True if the object is still alive."""
        self.timer.tick(time_delta)
        return self.timer.running()


class CanSpawnEntitiesInterface:
    def __init__(self) -> None:
        self.entities_buffer: list[src.entities.entity.Entity] = []
    
    def add(self, entity: src.entities.entity.Entity) -> None:
        self.entities_buffer.append(entity)
    
    def get_entities_buffer(self) -> list[src.entities.entity.Entity]:
        return self.entities_buffer
    
    def clear(self) -> None:
        self.entities_buffer.clear()


class RendersTrailInterface:
    def __init__(self):
        self.render_trail_pseudo_timer = 1.
        self.trail: deque[Vector2] = deque(maxlen=TRAIL_MAX_LENGTH)
    
    def tick_check_should_add(self, time_delta: float) -> bool:
        """Increases timer var. Returns True if the new point should be added."""
        self.render_trail_pseudo_timer += time_delta
        return self.render_trail_pseudo_timer >= 1. / TRAIL_POINTS_PER_SECOND
    
    def add(self, pos: Vector2):
        self.trail.append(pos)
        self.render_trail_pseudo_timer = 0.

    def get_trail(self) -> deque[Vector2]:
        return self.trail

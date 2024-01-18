from pygame import Vector2

from src.utils import Timer
from src.entity import Entity


class CanDieInterface:
    def __init__(self, lifetime: float) -> None:
        self.timer = Timer(max_time=lifetime)
    
    def tick_is_alive(self, time_delta: float) -> bool:
        """Returns True if the object is still alive."""
        ...


class CanSpawnEntitiesInterface:
    def __init__(self) -> None:
        self.entities_buffer: list[Entity] = []
    
    def add(self, entity: Entity) -> None:
        self.entities_buffer.append(entity)
    
    


class FollowsEntityInterface:
    def __init__(self, entity: Entity) -> None:
        self.entity = entity
    
    ...


class RendersTrailInterface:
    def __init__(self):
        self.trail: list[Vector2] = []
    
    ...

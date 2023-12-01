"""
Abstract classes and enumerators for the game.
"""
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

from pygame.math import Vector2

from config import TRAIL_MAX_LENGTH
from src.enums import EntityType


def deque_factory() -> deque[Vector2]: return deque(maxlen=TRAIL_MAX_LENGTH)


@dataclass
class Entity(ABC):
    """
    Abstract class for all entities in the game.
    """
    _pos: Vector2
    _type: EntityType
    _size: float # model's circle's radius

    _speed: float = 0. # velocity magnitude
    _vel: Vector2 = field(default_factory=Vector2) # velocity vector
    _is_alive: bool = True
    _render_trail: bool = False
    # add the max_length parameter to the deque constructor:
    _trail: deque[Vector2] = field(default_factory=deque_factory)

    @abstractmethod
    def update(self, time_delta: float):
        """
        Update the entity. This is called every game tick.
        """
        if not self._is_alive: return
        if self._speed > 0. and self._vel.magnitude_squared() > 0.:
            self._vel.scale_to_length(self._speed) # TODO: scale speed using time_delta
            self._pos += self._vel
        if self._render_trail: self._trail.append(self._pos)

    def intersects(self, other: 'Entity') -> bool:
        """
        Check if this entity intersects with another entity.
        """
        return (self._pos - other._pos).magnitude_squared() < (self._size + other._size) ** 2
    
    def get_pos(self) -> Vector2: return self._pos
    
    def get_vel(self) -> Vector2: return self._vel
    
    def get_type(self) -> EntityType: return self._type

    def is_alive(self) -> bool: return self._is_alive

    def kill(self): self._is_alive = False

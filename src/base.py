"""
Abstract classes and enumerators for the game.
"""
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from pygame.math import Vector2

from config.back import TRAIL_MAX_LENGTH
from enums import EntityType


@dataclass
class Entity(ABC):
    """
    Abstract class for all entities in the game.
    """
    _pos: Vector2
    _vel: Vector2
    _type: EntityType
    _size: float # model's circle's radius

    _is_alive: bool = True
    _render_trail: bool = False
    _trail: deque[Vector2] = deque(maxlen=TRAIL_MAX_LENGTH)

    @abstractmethod
    def update(self):
        """
        Update the entity. This is called every game tick.
        """
        self._pos += self._vel
        if self._render_trail:
            self._trail.append(self._pos)

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

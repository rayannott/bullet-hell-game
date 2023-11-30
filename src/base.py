"""
Abstract classes and enumerators for the game.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from pygame.math import Vector2


class EntityType(Enum):
    """
    Enumeration of all entity types.
    """
    PLAYER = auto()
    PROJECTILE = auto()
    ENERGY_ORB = auto()
    ENEMY = auto()
    SPAWNER = auto()


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

    @abstractmethod
    def update(self):
        """
        Update the entity. This is called every game tick.
        """
        self._pos += self._vel

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

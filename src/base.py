"""
Abstract classes and enumerators for the game.
"""
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from pygame.math import Vector2

from config.back import TRAIL_MAX_LENGTH


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    # TODO: add more stats

    def get_as_dict(self) -> dict:
        return self.__dict__


class Slider[T: int | float]:
    def __init__(self, _max_value: T, _current_value: T | None = None):
        self.max_value = _max_value
        self.current_value = _current_value if _current_value is not None else _max_value
    
    def is_alive(self) -> bool:
        return self.current_value > 0
    
    def get_current(self) -> T:
        return self.current_value
    
    def __str__(self) -> str:
        return f'Slider({self.current_value:.1f}/{self.max_value:.1f})'


class ProjectileType(Enum):
    """
    Enumeration of all projectile types.
    """
    NORMAL = auto()
    HOMING = auto()
    EXPLOSIVE = auto()


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

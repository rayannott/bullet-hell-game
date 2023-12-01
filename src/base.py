"""
Abstract classes and enumerators for the game.
"""
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import field
from enum import Enum, auto
import logging
from typing import Optional
import pygame

from pygame import Vector2, Color

from config import TRAIL_MAX_LENGTH, setup_logging
from src import EntityType, Timer

setup_logging('DEBUG')


class Entity(ABC):
    """
    Abstract class for all entities in the game.
    """
    def __init__(self,
        _pos: Vector2,
        _type: EntityType,
        _size: float, # model's circle's radius
        _speed: float = 0., # velocity magnitude
        _vel: Vector2 | None = None, # velocity vector
        _is_alive: bool = True,
        _render_trail: bool = False,
        _can_spawn_entities: bool = False,
        _color: pygame.Color | None = None,
        _homing_target: Optional['Entity'] = None,
    ):
        self._pos = _pos
        self._type = _type
        self._size = _size
        self._speed = _speed
        self._vel = _vel if _vel is not None else Vector2(0., 0.)
        self._is_alive = _is_alive
        self._render_trail = _render_trail
        self._can_spawn_entities = _can_spawn_entities
        self._trail = deque(maxlen=TRAIL_MAX_LENGTH)
        self._entities_buffer: list[Entity] = []
        self._color = _color if _color is not None else Color('white')
        self._homing_target = _homing_target
    
    @abstractmethod
    def update(self, time_delta: float):
        """
        Update the entity. This is called every game tick.
        """
        if not self.is_alive(): return
        if self._homing_target is not None:
            self._vel = (self._homing_target.get_pos() - self._pos)
        if self._speed > 0. and self._vel.magnitude_squared() > 0.:
            self._vel.scale_to_length(self._speed * time_delta)
            self._pos += self._vel
        if self._render_trail: self._trail.append(self._pos.copy())

    def intersects(self, other: 'Entity') -> bool:
        """
        Check if this entity intersects with another entity.
        """
        return self.is_alive() and other.is_alive() and (self._pos - other._pos).magnitude_squared() < (self._size + other._size) ** 2
    
    def get_pos(self) -> Vector2: return self._pos
    
    def get_vel(self) -> Vector2: return self._vel
    
    def get_type(self) -> EntityType: return self._type

    def get_size(self) -> float: return self._size

    def get_color(self) -> pygame.Color: return self._color

    def is_alive(self) -> bool: return self._is_alive

    def kill(self):
        self._is_alive = False
        logging.debug(f'Killed {self}')
        print(f'Killed {self}')

    def __str__(self) -> str:
        return f'{self._type.name}(pos={self._pos})'


class DummyEntity(Entity):
    def __init__(self, _pos: Vector2, _size: float = 0.):
        super().__init__(
            _pos=_pos,
            _type=EntityType.DUMMY,
            _size=_size
        )

    def update(self, time_delta: float): return super().update(time_delta)

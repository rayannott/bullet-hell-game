from abc import ABC, abstractmethod
from collections import deque
from typing import Optional
import pygame

from pygame import Vector2, Color

from src.enums import EntityType
from src.utils import random_unit_vector
from config import TRAIL_MAX_LENGTH


class Entity(ABC):
    """
    Abstract class for all entities in the game.
    """
    def __init__(self,
        pos: Vector2,
        type: EntityType,
        size: float, # model's circle's radius
        speed: float = 0., # velocity magnitude
        vel: Vector2 | None = None, # velocity vector
        is_alive: bool = True,
        render_trail: bool = False,
        can_spawn_entities: bool = False,
        color: pygame.Color | None = None,
        homing_target: Optional['Entity'] = None,
        turn_coefficient: float = 1.,
    ):
        self.pos = pos
        self.type = type
        self.size = size
        self.speed = speed
        self.vel = vel if vel is not None else random_unit_vector()
        self._is_alive = is_alive
        self.render_trail = render_trail
        self.can_spawn_entities = can_spawn_entities
        self.turn_coefficient = turn_coefficient
        self.trail = deque(maxlen=TRAIL_MAX_LENGTH)
        self.entities_buffer: list[Entity] = []
        self.color = color if color is not None else Color('white')
        self.homing_target = homing_target
    
    @abstractmethod
    def update(self, time_delta: float):
        """
        Update the entity. This is called every game tick.
        """
        if not self.is_alive(): return
        if self.homing_target is not None:
            self.vel = ((self.homing_target.get_pos() - self.pos).normalize() * self.turn_coefficient + 
                        self.vel * (1 - self.turn_coefficient))
        if self.speed > 0. and self.vel.magnitude_squared() > 0.:
            self.vel.scale_to_length(self.speed * time_delta)
            self.pos += self.vel
        if self.render_trail: self.trail.append(self.pos.copy())

    def intersects(self, other: 'Entity') -> bool:
        """
        Check if this entity intersects with another entity.
        """
        return self.is_alive() and other.is_alive() and (self.pos - other.pos).magnitude_squared() < (self.get_size() + other.get_size()) ** 2
    
    def get_pos(self) -> Vector2: return self.pos
    
    def get_vel(self) -> Vector2: return self.vel
    
    def get_type(self) -> EntityType: return self.type

    def get_size(self) -> float: return self.size

    def get_color(self) -> pygame.Color: return self.color

    def set_color(self, color: pygame.Color): self.color = color

    def is_alive(self) -> bool: return self._is_alive

    def kill(self):
        self._is_alive = False

    def __str__(self) -> str:
        return f'{self.type.name.title()}(pos={self.pos})'


class DummyEntity(Entity):
    def __init__(self, _pos: Vector2, _size: float = 0.):
        super().__init__(
            pos=_pos,
            type=EntityType.DUMMY,
            size=_size
        )

    def update(self, time_delta: float): return super().update(time_delta)

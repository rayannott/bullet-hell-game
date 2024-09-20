from abc import ABC, abstractmethod
from typing import Optional
import random
import math

import pygame
from pygame import Vector2, Color

from src.utils.enums import EntityType
from src.utils.utils import random_unit_vector
from src.misc.interfaces import (
    RendersTrailInterface,
    CanSpawnEntitiesInterface,
    HasLifetimeInterface,
)


class Entity(ABC):
    """
    Abstract class for all entities in the game.
    """

    def __init__(
        self,
        pos: Vector2,
        type: EntityType,
        size: float,  # model's circle's radius
        speed: float = 0.0,  # velocity magnitude
        vel: Vector2 | None = None,  # velocity vector
        is_alive: bool = True,
        render_trail: bool = False,
        can_spawn_entities: bool = False,
        color: pygame.Color | None = None,
        homing_target: Optional["Entity"] = None,
        turn_coefficient: float = 1.0,
        lifetime: float = math.inf,
    ):
        self.pos = pos
        self.type = type
        self.size = size
        self.speed = speed
        self.vel = vel if vel is not None else random_unit_vector()
        self._is_alive = is_alive
        self.turn_coefficient = turn_coefficient
        self.lifetime = lifetime
        self.color = color if color is not None else Color("white")
        self.homing_target = homing_target
        self._id = random.randrange(2**32)

        # interfaces:
        self.i_render_trail = RendersTrailInterface() if render_trail else None
        self.i_can_spawn_entities = (
            CanSpawnEntitiesInterface() if can_spawn_entities else None
        )
        self.i_has_lifetime = HasLifetimeInterface(lifetime)

    @abstractmethod
    def update(self, time_delta: float):
        """
        Update the entity. This is called every game tick.
        """
        if not self.is_alive():
            return
        if self.i_has_lifetime:
            if not self.i_has_lifetime.tick_is_alive(time_delta):
                self.kill()
                self.on_natural_death()
                return
        if self.homing_target is not None:
            self.vel = (
                self.homing_target.get_pos() - self.pos
            ).normalize() * self.turn_coefficient + self.vel * (
                1 - self.turn_coefficient
            )
        if self.speed > 0.0 and self.vel.magnitude_squared() > 0.0:
            self.vel.scale_to_length(self.speed * time_delta)
            self.pos += self.vel
        if self.i_render_trail:
            if self.i_render_trail.tick_check_should_add(time_delta):
                self.i_render_trail.add(self.pos.copy())

    def on_natural_death(self):
        """
        Called when the entity dies naturally (e.g. lifetime ends).
        """
        pass

    def intersects(self, other: "Entity") -> bool:
        """
        Check if this entity intersects with another entity.
        """
        return (
            self.is_alive()
            and other.is_alive()
            and (self.pos - other.pos).magnitude_squared()
            < (self.get_size() + other.get_size()) ** 2
        )

    def get_pos(self) -> Vector2:
        return self.pos

    def get_vel(self) -> Vector2:
        return self.vel

    def get_type(self) -> EntityType:
        return self.type

    def get_size(self) -> float:
        return self.size

    def get_color(self) -> pygame.Color:
        return self.color

    def set_color(self, color: pygame.Color):
        self.color = color

    def get_id(self) -> int:
        return self._id

    def is_alive(self) -> bool:
        return self._is_alive

    def kill(self):
        self._is_alive = False

    def __str__(self) -> str:
        return f"{self.type.name.title()}(pos={self.pos})"


class DummyEntity(Entity):
    def __init__(self, _pos: Vector2, _size: float = 0.0):
        super().__init__(pos=_pos, type=EntityType.DUMMY, size=_size)

    def update(self, time_delta: float):
        return super().update(time_delta)

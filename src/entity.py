from abc import ABC, abstractmethod
from collections import deque
from typing import Optional
import pygame

from pygame import Vector2, Color
from front.utils import ColorGradient

from src.enums import EntityType
from src.utils import Timer, random_unit_vector
from config import (TRAIL_MAX_LENGTH, MINE_SIZE, MINE_ACTIVATION_TIME,
    MINE_LIFETIME, MINE_DEFAULT_DAMAGE, BACKGROUND_COLOR_HEX, MINE_AOE_EFFECT_SIZE)


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


class Corpse(Entity):
    def __init__(self,
        of_entity: Entity,
    ):
        super().__init__(
            pos=of_entity.get_pos(),
            type=EntityType.CORPSE,
            size=of_entity.get_size() * 1.5, # make the corpse a bit bigger than the entity
            color=Color('gray'),
        )
        self._damage_on_collision = 70.

    def update(self, time_delta: float): return super().update(time_delta)


class Mine(Entity):
    def __init__(self,
        pos: Vector2,
        damage: float = MINE_DEFAULT_DAMAGE,
        aoe_damage: float = MINE_DEFAULT_DAMAGE // 2,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.MINE,
            size=MINE_SIZE,
            color=Color('#851828'),
            can_spawn_entities=True
        )
        self.damage = damage
        self.activation_timer = Timer(max_time=MINE_ACTIVATION_TIME)
        self.aoe_damage = aoe_damage
        self.lifetime_timer = Timer(max_time=MINE_LIFETIME)

    def is_activated(self) -> bool:
        return not self.activation_timer.running()

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.activation_timer.tick(time_delta)
        if not self.lifetime_timer.running(): self.kill()
        return super().update(time_delta)
    
    def kill(self):
        self.entities_buffer.append(
            AOEEffect(
                pos=self.pos,
                size=MINE_AOE_EFFECT_SIZE,
                damage=self.aoe_damage,
                color=self.color,
                animation_lingering_time=0.8
            )
        )
        return super().kill()


class AOEEffect(Entity):
    def __init__(self,
        pos: Vector2,
        size: float,
        damage: float,
        color: Color = Color('black'),
        animation_lingering_time: float = 0.5,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.CRATER,
            size=size,
            color=color,
        )
        self.color_gradient = ColorGradient(color, Color(BACKGROUND_COLOR_HEX))
        self.damage = damage
        self.lifetime_timer = Timer(max_time=animation_lingering_time)

        self.applied_effect_player = False
        self.applied_effect_enemies = False

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.set_color(self.color_gradient(self.lifetime_timer.get_percent_full()))
        if not self.lifetime_timer.running(): self.kill()
        return super().update(time_delta)

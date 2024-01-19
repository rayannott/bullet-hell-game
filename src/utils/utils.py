from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import random, math

from pygame import Color, Vector2
from scipy.interpolate import make_interp_spline, BSpline
import numpy as np

from src.utils.enums import EntityType


def random_unit_vector() -> Vector2:
    alpha = random.random() * 2 * math.pi
    return Vector2(math.cos(alpha), math.sin(alpha))

# import src.entity

class Slider:
    def __init__(self, max_value: float, current_value: float | None = None):
        self.max_value = max_value
        self.current_value = current_value if current_value is not None else max_value
    
    def is_alive(self) -> bool:
        return self.current_value > 0
    
    def get_value(self) -> float:
        return self.current_value
    
    def get_percent_full(self) -> float:
        return self.current_value / self.max_value

    def set_percent_full(self, percent: float) -> None:
        self.current_value = self.max_value * percent
    
    def change(self, delta: float) -> float:
        """Change the current value by delta. Return by how much it actually changed."""
        cache_current_value = self.current_value
        self.current_value += delta
        self.current_value = min(self.current_value, self.max_value)
        self.current_value = max(self.current_value, 0.)
        return self.current_value - cache_current_value
    
    def __repr__(self) -> str:
        return f'Slider({self})'
    
    def __str__(self) -> str:
        return f'{self.current_value:.0f}/{self.max_value:.0f}'


class Timer:
    """
    Counts time in seconds.
    """
    def __init__(self, max_time: float):
        self.max_time = max_time
        self.current_time = 0.
    
    def tick(self, time_delta: float) -> None:
        self.current_time += time_delta

    def turn_off(self) -> None:
        self.current_time = self.max_time + 0.01
    
    def get_time_left(self) -> float:
        return self.max_time - self.current_time

    def running(self) -> bool:
        return self.current_time < self.max_time
    
    def get_value(self) -> float:
        return self.current_time
    
    def reset(self, with_max_time: float | None = None) -> None:
        if with_max_time is not None:
            self.max_time = with_max_time
        self.current_time = 0.

    def get_percent_full(self) -> float:
        return self.current_time / self.max_time

    def set_percent_full(self, percent: float) -> None:
        self.current_time = self.max_time * percent
    
    def get_slider(self, reverse=False) -> Slider:
        if reverse:
            return Slider(self.max_time, self.max_time - self.current_time)
        return Slider(self.max_time, self.current_time)

    def __repr__(self) -> str:
        return f'Timer({self.current_time:.1f}/{self.max_time:.1f})'


def default_color() -> Color:
    return Color('white')


@dataclass
class Feedback:
    text: str
    duration: float = 1.5
    at_pos: Literal['player', 'cursor', 'center'] | Vector2 = 'player'
    color: Color = field(default_factory=default_color)


class AppliedToEntityManager:
    """Interface class for effects that can be applied to some entities."""
    def __init__(self, affects_player: bool, affects_enemies: bool):
        self.applied_to = set()
        self.affects_player = affects_player
        self.affects_enemies = affects_enemies
    
    def should_apply(self, entity) -> bool:
        id_in_applied_to = entity.get_id() in self.applied_to
        if entity.get_type() == EntityType.PLAYER:
            return self.affects_player and not id_in_applied_to
        elif entity.get_type() == EntityType.ENEMY:
            return self.affects_enemies and not id_in_applied_to
        else:
            raise NotImplementedError(f'Unknown entity type {entity.get_type()}')            
    
    def check_applied(self, entity) -> None:
        self.applied_to.add(entity.get_id())
        # TODO from __future__ import annotations add hints


class Interpolate2D:
    """
    A cubic interpolator for a sequence of 2D points.

    Usage:
    >>> path = Interpolate2D(points)
    >>> path(0.5) # get the point in the middle of the path
    """

    def __init__(self, points: list[Vector2]):
        self.ts = np.linspace(0, 1, len(points))
        self.spline = make_interp_spline(self.ts, points, bc_type='natural')
        self.d = BSpline.derivative(self.spline)

    def derivative(self, t: float) -> Vector2:
        """Get the derivative at point t."""
        assert 0 <= t <= 1
        return Vector2(*self.d(t))

    def __call__(self, t: float) -> Vector2:
        assert 0 <= t <= 1
        return Vector2(*self.spline(t))

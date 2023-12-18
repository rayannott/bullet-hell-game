from dataclasses import dataclass, field
from typing import Literal
import random, math

from pygame import Color, Vector2
from scipy.interpolate import make_interp_spline, BSpline
import numpy as np

def random_unit_vector() -> Vector2:
    alpha = random.random() * 2 * math.pi
    return Vector2(math.cos(alpha), math.sin(alpha))


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    ACCURATE_SHOTS_RICOCHET: int = 0
    BULLETS_CAUGHT: int = 0
    ACCURATE_SHOTS: int = 0
    ENEMIES_COLLIDED_WITH: int = 0
    ENERGY_ORBS_SPAWNED: int = 0
    CORPSES_LET_SPAWN: int = 0
    BULLET_SHIELDS_ACTIVATED: int = 0
    BULLET_SHIELD_BULLETS_BLOCKED: int = 0
    MINES_STEPPED_ON: int = 0
    MINES_PLANTED: int = 0
    DASHES_ACTIVATED: int = 0

    DAMAGE_TAKEN: float = 0.
    DAMAGE_DEALT: float = 0.
    ENERGY_COLLECTED: float = 0.
    OIL_SPILL_TIME_SPENT: float = 0.

    def get_accuracy(self) -> float:
        return self.ACCURATE_SHOTS / self.PROJECTILES_FIRED if self.PROJECTILES_FIRED > 0 else 0.

    def get_as_dict(self) -> dict:
        return self.__dict__


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

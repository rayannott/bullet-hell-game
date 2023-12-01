from dataclasses import dataclass, field
import math
import random
from typing import Literal

from pygame import Color, Vector2


def paint(text: str, color: Color, size: int = 4) -> str:
    hex_color = "#{:02x}{:02x}{:02x}".format(color.r, color.g, color.b)
    return f'<font color={hex_color} size={size}>{text}</font>'


class ColorGradient:
    def __init__(self, start_color: Color, end_color: Color):
        self.start_color = start_color
        self.end_color = end_color

    def __call__(self, percent: float) -> Color:
        return Color(
        int(self.start_color.r + (self.end_color.r - self.start_color.r) * percent),
        int(self.start_color.g + (self.end_color.g - self.start_color.g) * percent),
        int(self.start_color.b + (self.end_color.b - self.start_color.b) * percent),
        int(self.start_color.a + (self.end_color.a - self.start_color.a) * percent)
    )


def random_unit_vector() -> Vector2:
    alpha = random.uniform(0, 2 * math.pi)
    return Vector2(math.cos(alpha), math.sin(alpha))


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    BULLETS_CAUGHT: int = 0
    ACCURATE_SHOTS: int = 0
    DAMAGE_TAKEN: float = 0.
    DAMAGE_DEALT: float = 0.
    ENERGY_COLLECTED: float = 0.
    # TODO: add more stats

    def get_accuracy(self) -> float:
        return self.ACCURATE_SHOTS / self.PROJECTILES_FIRED if self.PROJECTILES_FIRED > 0 else 0.

    def get_as_dict(self) -> dict:
        return self.__dict__


class Slider:
    def __init__(self, _max_value: float, _current_value: float | None = None):
        self.max_value = _max_value
        self.current_value = _current_value if _current_value is not None else _max_value
    
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
        return f'{self.current_value:.1f}/{self.max_value:.1f}'


class Timer:
    """
    Counts time in seconds.
    """
    def __init__(self, max_time: float):
        self.max_time = max_time
        self.current_time = 0.
    
    def tick(self, time_delta: float) -> None:
        self.current_time += time_delta 

    def running(self) -> bool:
        return self.current_time < self.max_time
    
    def get_current(self) -> float:
        return self.current_time
    
    def reset(self, with_max_time: float | None = None) -> None:
        if with_max_time is not None:
            self.max_time = with_max_time
        self.current_time = 0.

    def progress(self) -> float:
        return self.current_time / self.max_time
    
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
    at_pos: Literal['player', 'cursor'] | Vector2 = 'player'
    color: Color = field(default_factory=default_color)

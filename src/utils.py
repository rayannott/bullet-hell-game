from dataclasses import dataclass, field
from typing import Literal

from pygame import Color, Vector2


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    BULLETS_CAUGHT: int = 0
    ACCURATE_SHOTS: int = 0
    ENEMIES_COLLIDED_WITH: int = 0
    DAMAGE_TAKEN: float = 0.
    DAMAGE_DEALT: float = 0.
    ENERGY_COLLECTED: float = 0.
    OIL_SPILL_TIME_SPENT: float = 0.

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
    at_pos: Literal['player', 'cursor'] | Vector2 = 'player'
    color: Color = field(default_factory=default_color)

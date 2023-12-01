from dataclasses import dataclass

import pygame


def color_gradient(start_color: pygame.Color, end_color: pygame.Color, percent: float) -> pygame.Color:
    return pygame.Color(
        int(start_color.r + (end_color.r - start_color.r) * percent),
        int(start_color.g + (end_color.g - start_color.g) * percent),
        int(start_color.b + (end_color.b - start_color.b) * percent),
        int(start_color.a + (end_color.a - start_color.a) * percent)
    )


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    # TODO: add more stats

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
    
    def change(self, delta: float) -> None:
        self.current_value += delta
        self.current_value = min(self.current_value, self.max_value)
        self.current_value = max(self.current_value, 0.)
    
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

    # def __bool__(self) -> bool:
    #     return self.running()
    
    def __repr__(self) -> str:
        return f'Timer({self.current_time:.1f}/{self.max_time:.1f})'

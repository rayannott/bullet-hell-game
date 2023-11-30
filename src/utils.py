from dataclasses import dataclass


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
    
    def reset(self) -> None:
        self.current_time = 0.
    
    def __str__(self) -> str:
        return f'Timer({self.current_time:.1f}/{self.max_time:.1f})'

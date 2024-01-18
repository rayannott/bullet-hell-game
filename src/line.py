from typing import TypedDict, NotRequired, Unpack
from enum import Enum, auto

from pygame import Vector2, Color

from src.entity import Entity
from src.utils import Timer, AppliedToEntityManager


class LineType(Enum):
    """Enumeration of all line types."""
    DASH = auto() #TODO: move dash effect to this
    EFFECTS = auto()
    DAMAGE = auto()


class LineKwargs(TypedDict):
    """Dictionary of line effects types."""
    damage: NotRequired[float]
    slow: NotRequired[float]


class Line:
    def __init__(self, 
        p1: Vector2,
        p2: Vector2,
        line_type: LineType,
        affects_player: bool = True,
        affects_enemies: bool = True,
        **kwargs: Unpack[LineKwargs]
    ):
        self.p1 = p1
        self.p2 = p2
        self.line_type = line_type
        self.affects_player = affects_player
        self.affects_enemies = affects_enemies
        self.life_timer = Timer(max_time=5.)
        self._is_alive = True
        self.color = Color('white')
        self.can_spawn_entities = False
        self.kwargs = kwargs
        self.applied_manager = AppliedToEntityManager(affects_player, affects_enemies)

    def intersects(self, ent: Entity) -> bool:
        """Checks if the enemy is affected by the dash.
        Should be called only after self.dash is called."""
        # check if the line segment a->b intersects the circle c_r
        c = ent.get_pos(); r = ent.get_size()
        # this is a check to see if the circle is in the line segment's bounding box
        if not ((min(self.p1.x, self.p2.x) - r <= c.x <= max(self.p1.x, self.p2.x) + r) 
            and (min(self.p1.y, self.p2.y) - r <= c.y <= max(self.p1.y, self.p2.y) + r)): 
            return False
        d = self.p2 - self.p1
        f = self.p1 - c
        # quadratic equation coefficients
        a_ = d.dot(d)
        b_ = 2 * f.dot(d)
        c_ = f.dot(f) - r ** 2
        discriminant = b_ ** 2 - 4 * a_ * c_
        return discriminant >= 0
    
    def __call__(self, p: float) -> Vector2:
        """Returns the point on the line at the given parameter value."""
        return self.p1 + (self.p2 - self.p1) * p

    def is_alive(self) -> bool:
        return self._is_alive

    def kill(self):
        self._is_alive = False

    def update(self, time_delta: float):
        if not self._is_alive: return
        # TODO: use interface for CanDie instead of checking for life_timer
        self.life_timer.tick(time_delta)
        if not self.life_timer.running():
            self.kill()
        
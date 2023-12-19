from pygame import Vector2, Color

from front.utils import ColorGradient
from src.entity import Entity
from src.enums import EntityType
from src.utils import Timer

from config import BACKGROUND_COLOR_HEX


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

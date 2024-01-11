from enum import Enum, auto

from pygame import Vector2, Color

from front.utils import ColorGradient
from src.entity import Entity
from src.enums import EntityType, AOEEffectEffectType
from src.utils import AppliedToEntityManager, Timer

from config import BACKGROUND_COLOR_HEX


class AOEEffect(Entity):
    def __init__(self,
        pos: Vector2,
        size: float,
        effect_type: AOEEffectEffectType = AOEEffectEffectType.DAMAGE,
        affects_enemies: bool = True,
        affects_player: bool = True,
        color: Color = Color('black'),
        animation_lingering_time: float = 0.5,
        damage: float = 0.,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.CRATER,
            size=size,
            color=color,
        )
        self.application_manager = AppliedToEntityManager(affects_player, affects_enemies)

        self.effect_type = effect_type
        self.color_gradient = ColorGradient(color, Color(BACKGROUND_COLOR_HEX))
        self.damage = damage
        self.lifetime_timer = Timer(max_time=animation_lingering_time)

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.set_color(self.color_gradient(self.lifetime_timer.get_percent_full()))
        if not self.lifetime_timer.running(): self.kill()
        return super().update(time_delta)
    
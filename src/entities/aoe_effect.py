from pygame import Vector2, Color

from front.utils import ColorGradient
from src.entities.entity import Entity
from src.utils.enums import EntityType, AOEEffectEffectType
from src.utils.utils import AppliedToEntityManager

from config import BACKGROUND_COLOR_HEX


class AOEEffect(Entity):
    def __init__(
        self,
        pos: Vector2,
        size: float,
        effect_type: AOEEffectEffectType = AOEEffectEffectType.DAMAGE,
        affects_enemies: bool = True,
        affects_player: bool = True,
        color: Color = Color("black"),
        animation_lingering_time: float = 0.5,
        damage: float = 0.0,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.CRATER,
            size=size,
            color=color,
            lifetime=animation_lingering_time,
        )
        self.application_manager = AppliedToEntityManager(
            affects_player, affects_enemies
        )

        self.effect_type = effect_type
        self.color_gradient = ColorGradient(color, Color(BACKGROUND_COLOR_HEX))
        self.damage = damage

    def update(self, time_delta: float):
        return super().update(time_delta)

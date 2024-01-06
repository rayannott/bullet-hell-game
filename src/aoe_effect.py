from enum import Enum, auto

from pygame import Vector2, Color

from front.utils import ColorGradient
from src.entity import Entity
from src.enums import EntityType
from src.utils import Timer

from config import BACKGROUND_COLOR_HEX


class AOEEffectEffectType(Enum):
    DAMAGE = auto()
    ENEMY_BLOCK_ON = auto()


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
        self.affects_enemies = affects_enemies
        self.affects_player = affects_player
        self.applied_effect_to = set()
        if not affects_player: self.applied_effect_to.add(0)

        self.effect_type = effect_type
        self.color_gradient = ColorGradient(color, Color(BACKGROUND_COLOR_HEX))
        self.damage = damage
        self.lifetime_timer = Timer(max_time=animation_lingering_time)

        self.applied_effect_enemies = not affects_enemies
        if self.effect_type == AOEEffectEffectType.ENEMY_BLOCK_ON:
            self.applied_effect_player = True # this does not apply to players

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.set_color(self.color_gradient(self.lifetime_timer.get_percent_full()))
        if not self.lifetime_timer.running(): self.kill()
        return super().update(time_delta)

    def should_apply_to_entity(self, ent: Entity) -> bool:
        return not ent.get_id() in self.applied_effect_to

    def check_entity_applied_effect(self, ent: Entity) -> None:
        self.applied_effect_to.add(ent.get_id())
    
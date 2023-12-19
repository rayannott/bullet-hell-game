from pygame import Vector2, Color

from src.entity import Entity
from src.enums import EntityType
from src.utils import Timer
from src.aoe_effect import AOEEffect
from config import (MINE_SIZE, MINE_ACTIVATION_TIME, MINE_LIFETIME, MINE_DEFAULT_DAMAGE, MINE_AOE_EFFECT_SIZE)


class Mine(Entity):
    def __init__(self,
        pos: Vector2,
        damage: float = MINE_DEFAULT_DAMAGE,
        aoe_damage: float = MINE_DEFAULT_DAMAGE // 2,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.MINE,
            size=MINE_SIZE,
            color=Color('#851828'),
            can_spawn_entities=True
        )
        self.damage = damage
        self.activation_timer = Timer(max_time=MINE_ACTIVATION_TIME)
        self.aoe_damage = aoe_damage
        self.lifetime_timer = Timer(max_time=MINE_LIFETIME)

    def is_activated(self) -> bool:
        return not self.activation_timer.running()

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.activation_timer.tick(time_delta)
        if not self.lifetime_timer.running(): self.kill()
        return super().update(time_delta)
    
    def kill(self):
        self.entities_buffer.append(
            AOEEffect(
                pos=self.pos,
                size=MINE_AOE_EFFECT_SIZE,
                damage=self.aoe_damage,
                color=self.color,
                animation_lingering_time=0.8
            )
        )
        return super().kill()

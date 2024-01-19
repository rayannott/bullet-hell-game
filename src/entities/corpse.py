from pygame import Color
from src.entities.aoe_effect import AOEEffect, AOEEffectEffectType

from src.entities.entity import Entity
from src.utils.enums import EntityType
from src.utils.utils import Timer
from config import LIGHT_ORANGE_HEX, BLOCKS_FOR_ENEMIES_EFFECT_SIZE, CORPSE_GIVE_BLOCKS_COOLDOWN

LIGHT_ORANGE = Color(LIGHT_ORANGE_HEX)


class Corpse(Entity):
    def __init__(self,
        of_entity: Entity,
    ):
        super().__init__(
            pos=of_entity.get_pos(),
            type=EntityType.CORPSE,
            size=of_entity.get_size() * 1.5, # make the corpse a bit bigger than the entity
            color=Color('gray'),
            can_spawn_entities=True,
        )
        self.damage_on_collision = 70.
        self.give_blocks_timer = Timer(CORPSE_GIVE_BLOCKS_COOLDOWN)
        self.give_blocks_timer.set_percent_full(0.5)

    def update(self, time_delta: float): 
        super().update(time_delta)
        self.give_blocks_timer.tick(time_delta)
        if not self.give_blocks_timer.running():
            self.give_blocks()
            self.give_blocks_timer.reset()

    def give_blocks(self):
        assert self.i_can_spawn_entities
        self.i_can_spawn_entities.add(
            AOEEffect(
                self.get_pos(),
                BLOCKS_FOR_ENEMIES_EFFECT_SIZE,
                effect_type=AOEEffectEffectType.ENEMY_BLOCK_ON,
                affects_enemies=True, affects_player=False,
                color=LIGHT_ORANGE,
                animation_lingering_time=0.8,
            )
        )

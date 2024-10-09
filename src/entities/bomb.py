import random

from src.entities.entity import Entity
from src.entities.aoe_effect import AOEEffect, AOEEffectEffectType
from src.entities.projectile import ExplosiveProjectile
from src.entities.mine import Mine
from src.utils.enums import EntityType
from src.utils.utils import Timer, random_unit_vector
from config import BOMB_DEFAULT_SIZE, BOMB_DEFAULT_LIFETIME, MINE_LIFETIME

from pygame import Vector2, Color


class Bomb(Entity):
    def __init__(
        self,
        pos: Vector2,
        player,
        size: float = BOMB_DEFAULT_SIZE,
        lifetime: float = BOMB_DEFAULT_LIFETIME,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.BOMB,
            size=size,
            color=Color("#FF00FF"),
            can_spawn_entities=True,
            lifetime=lifetime,
        )
        self.defuse_timer = Timer(max_time=1.0 / 3 * lifetime)
        self.defusing_last_frame = False
        self.player = player

    def update(self, time_delta: float):
        if self.defusing_last_frame:
            self.defuse_timer.tick(time_delta)
        else:
            self.defuse_timer.reset()
        return super().update(time_delta)

    def kill(self):
        return super().kill()

    def on_natural_death(self):
        assert self.i_can_spawn_entities
        self.i_can_spawn_entities.add(
            AOEEffect(
                pos=self.pos,
                size=400.0,
                effect_type=AOEEffectEffectType.DAMAGE,
                color=Color("black"),
                animation_lingering_time=1.2,
                damage=100.0,
            )
        )
        for _ in range(4):
            self.i_can_spawn_entities.add(
                ExplosiveProjectile(
                    pos=self.pos.copy(),
                    vel=random_unit_vector(),
                    speed=400.0,
                    damage=50.0,
                )
            )
        for _ in range(16):
            pos = self.player.get_pos() + random_unit_vector() * random.uniform(
                0.0, 800.0
            )
            self.i_can_spawn_entities.add(
                Mine(
                    pos=pos,
                    lifetime=MINE_LIFETIME + random.uniform(-2.0, 2.0),
                )
            )

    def is_defused(self) -> bool:
        return not self.defuse_timer.running()

from typing import TypedDict, Unpack, NotRequired

import pygame
from pygame import Vector2, Color

from src.utils.utils import Timer
from src.utils.enums import AnimationType
from front.utils import ColorGradient
from config import BACKGROUND_COLOR_HEX, BOSS_ENEMY_COLOR_HEX, NICER_MAGENTA_HEX


WHITE = Color("white")
YELLOW = Color("yellow")
NICER_MAGENTA = Color(NICER_MAGENTA_HEX)
BG_COLOR = Color(BACKGROUND_COLOR_HEX)
BOSS_COLOR = Color(BOSS_ENEMY_COLOR_HEX)

yellow_to_bg_gradient = ColorGradient(YELLOW, BG_COLOR)
boss_to_bg_gradient = ColorGradient(BOSS_COLOR, BG_COLOR)
white_to_bg_gradient = ColorGradient(WHITE, BG_COLOR)
magenta_to_bg_gradient = ColorGradient(NICER_MAGENTA, BG_COLOR)


def draw_accurate_shot(animation: "Animation"):
    bullet_vel, enemy_size = (
        animation.kwargs["bullet_vel"],  # type: ignore
        animation.kwargs["enemy_size"],  # type: ignore
    )
    bullet_vel = bullet_vel.normalize()
    p = animation.life_timer.get_percent_full()
    for i in [1.0, 1.5, 2.0]:
        line_seed = (
            animation.pos
            + bullet_vel * (1 - p + (10 * i) * p)
            + enemy_size * bullet_vel
        )
        line_width = (enemy_size * 5 * (1 - p)) / i
        line_wing = bullet_vel.rotate(90) * line_width * 0.5
        pygame.draw.line(
            animation.surface,
            yellow_to_bg_gradient(p),
            line_seed - line_wing,
            line_seed + line_wing,
            3,
        )


def draw_enemy_spawned(animation: "Animation"):
    enemy_size = animation.kwargs["enemy_size"]  # type: ignore
    p = animation.life_timer.get_percent_full()
    pygame.draw.circle(
        animation.surface,
        white_to_bg_gradient(p),
        animation.pos,
        enemy_size * (1.0 + 2.0 * p),
        width=3,
    )


def draw_boss_died(animation: "Animation"):
    boss_size = animation.kwargs["enemy_size"]  # type: ignore
    p = animation.life_timer.get_percent_full()
    for i in [2, 3, 4]:
        pygame.draw.circle(
            animation.surface,
            boss_to_bg_gradient(p),
            animation.pos,
            boss_size * (1.0 + i * p),
            width=i,
        )


def draw_energy_orb_collected(animation: "Animation"):
    p = animation.life_timer.get_percent_full()
    pygame.draw.circle(
        animation.surface, magenta_to_bg_gradient(p), animation.pos, 10, width=3
    )


ANIM_TYPE_TO_FUNC_DUR = {
    AnimationType.ACCURATE_SHOT: (draw_accurate_shot, 0.5),
    AnimationType.ENEMY_SPAWNED: (draw_enemy_spawned, 0.45),
    AnimationType.BOSS_DIED: (draw_boss_died, 1.5),
    AnimationType.ENERGY_ORB_COLLECTED: (draw_energy_orb_collected, 0.4),
}


class AnimKwargs(TypedDict):
    bullet_vel: NotRequired[Vector2]
    enemy_size: NotRequired[float]


class Animation:
    def __init__(
        self,
        pos: Vector2,
        surface: pygame.Surface,
        animation_type: AnimationType,
        **kwargs: Unpack[AnimKwargs],
    ):
        self.is_alive = True
        self.pos = pos
        self.surface = surface
        self.animation_type = animation_type
        self.kwargs = kwargs
        # choose duration and draw function based on animation type:
        self._draw, duration = ANIM_TYPE_TO_FUNC_DUR[animation_type]
        self.life_timer = Timer(max_time=duration)
        # TODO: maybe replace with the interface?

    def draw(self):
        self._draw(self)

    def kill(self):
        self.is_alive = False

    def update(self, time_delta: float):
        if not self.life_timer.running():
            self.kill()
            return
        self.life_timer.tick(time_delta)
        self.draw()


class AnimationHandler:
    def __init__(self):
        self.surface: pygame.Surface
        self.animations: list[Animation] = []
        self.clean_up_timer = Timer(max_time=2.0)

    def set_surface(self, surface: pygame.Surface):
        self.surface = surface

    def add_animation(
        self, pos: Vector2, animation_type: AnimationType, **kwargs: Unpack[AnimKwargs]
    ):
        self.animations.append(Animation(pos, self.surface, animation_type, **kwargs))

    def update(self, time_delta: float):
        self.clean_up_timer.tick(time_delta)
        for animation in self.animations:
            animation.update(time_delta)
        if not self.clean_up_timer.running():
            self.clean_up()
            self.clean_up_timer.reset()

    def clean_up(self) -> int:
        old_len = len(self.animations)
        self.animations = [
            animation for animation in self.animations if animation.is_alive
        ]
        return old_len - len(self.animations)

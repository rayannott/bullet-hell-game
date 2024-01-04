from typing import TypedDict, Unpack, NotRequired

import pygame
from pygame import Vector2, Color

from src.utils import Timer
from src.enums import AnimationType
from front.utils import ColorGradient
from config import BACKGROUND_COLOR_HEX


WHITE = Color('white')
YELLOW = Color('yellow')
BG_COLOR = Color(BACKGROUND_COLOR_HEX)

yellow_to_bg_gradient = ColorGradient(YELLOW, BG_COLOR)



def draw_accurate_shot(animation: 'Animation'):
    bullet_vel = animation.kwargs['bullet_vel'] # type: ignore
    p = animation.life_timer.get_percent_full()
    for i in [1., 1.2, 1.4]:
        line_seed = animation.pos + bullet_vel * (1 * (1-p) + (10 * i) * p)
        line_width = (10. - 8. * p) / i
        line_wing = bullet_vel.rotate(90) * line_width * 0.5
        pygame.draw.line(animation.surface, yellow_to_bg_gradient(p), line_seed - line_wing, line_seed + line_wing, 3)


def draw_enemy_spawned(animation: 'Animation'):
    enemy_size = animation.kwargs['enemy_size'] # type: ignore
    print('enemy spawned', animation.life_timer.get_percent_full())


def draw_enemy_died(animation: 'Animation'):
    #? do I need this?
    print('enemy died', animation.life_timer.get_percent_full())


ANIM_TYPE_TO_FUNC_DUR = {
    AnimationType.ACCURATE_SHOT: (draw_accurate_shot, 0.45),
    AnimationType.ENEMY_SPAWNED: (draw_enemy_spawned, 0.85),
    AnimationType.ENEMY_DIED: (draw_enemy_died, 0.85),
}


class AnimKwargs(TypedDict):
    bullet_vel: NotRequired[Vector2]
    enemy_size: NotRequired[float]


class Animation:
    def __init__(self,
        pos: Vector2,
        surface: pygame.Surface,
        animation_type: AnimationType,
        **kwargs: Unpack[AnimKwargs]
    ):
        self.is_alive = True
        self.pos = pos
        self.surface = surface
        self.animation_type = animation_type
        self.kwargs = kwargs
        # choose duration and draw function based on animation type:
        self._draw, duration = ANIM_TYPE_TO_FUNC_DUR[animation_type]
        self.life_timer = Timer(max_time=duration)
    
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
        self.clean_up_timer = Timer(max_time=2.)
    
    def set_surface(self, surface: pygame.Surface):
        self.surface = surface

    def add_animation(self, pos: Vector2, animation_type: AnimationType, **kwargs: Unpack[AnimKwargs]):
        self.animations.append(Animation(pos, self.surface, animation_type, **kwargs))
    
    def update(self, time_delta: float):
        self.clean_up_timer.tick(time_delta)
        for animation in self.animations:
            animation.update(time_delta)
        if not self.clean_up_timer.running():
            self.clean_up()
            self.clean_up_timer.reset()
    
    def clean_up(self):
        self.animations = [animation for animation in self.animations if animation.is_alive]

import math
import random

import pygame, pygame_gui
from pygame import Color, Vector2

from src import Slider, Timer


def paint(text: str, color: Color, size: int = 4) -> str:
    hex_color = "#{:02x}{:02x}{:02x}".format(color.r, color.g, color.b)
    return f'<font color={hex_color} size={size}>{text}</font>'


class ColorGradient:
    def __init__(self, start_color: Color, end_color: Color):
        self.start_color = start_color
        self.end_color = end_color

    def __call__(self, percent: float) -> Color:
        return Color(
        int(self.start_color.r + (self.end_color.r - self.start_color.r) * percent),
        int(self.start_color.g + (self.end_color.g - self.start_color.g) * percent),
        int(self.start_color.b + (self.end_color.b - self.start_color.b) * percent),
        int(self.start_color.a + (self.end_color.a - self.start_color.a) * percent)
    )


def random_unit_vector() -> Vector2:
    alpha = random.uniform(0, 2 * math.pi)
    return Vector2(math.cos(alpha), math.sin(alpha))



class ProgressBar(pygame_gui.elements.UIStatusBar):
    def __init__(self, color_gradient_pair: tuple[Color, Color], **kwargs):
        self.text_to_render = ''
        super().__init__(**kwargs)
        self.percent_full = 0
        self.color_gradient = ColorGradient(*color_gradient_pair)
    
    def status_text(self):
        return self.text_to_render
    
    def update_color(self):
        self.bar_filled_colour = self.color_gradient(self.percent_full)
    
    def set_slider(self, slider: Slider):
        self.text_to_render = str(slider)
        self.percent_full = slider.get_percent_full()
        self.update_color()


class Notification(pygame_gui.elements.UITextBox):
    def __init__(self,
            text: str,
            position: Vector2,
            manager: pygame_gui.UIManager,
            duration: float = 3.,
            color: Color = Color('white'),
            **kwargs):
        rect = pygame.Rect(0., 0., len(text) * 12, 40)
        rect.center = position
        super().__init__(
            html_text=paint(text, color, 8),
            relative_rect=rect,
            manager=manager,
            object_id='#notification', #! this doesn't work
            **kwargs)
        self.lifetime_timer = Timer(max_time=duration)
        self._is_alive = True
    
    def update(self, time_delta: float):
        if not self._is_alive: return
        self.lifetime_timer.tick(time_delta)
        self.rect.y -= 3. * time_delta # type: ignore
        if not self.lifetime_timer.running():
            self._is_alive = False
            self.kill()
        super().update(time_delta)
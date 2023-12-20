from typing import Literal

import pygame, pygame_gui
from pygame import Color, Vector2, freetype

from src.utils import Slider, Timer
from config import FONT_FILE

freetype.init()
FONT = freetype.Font(FONT_FILE, 20)
HUGE_FONT = freetype.Font(FONT_FILE, 150)


def paint(text: str, color: Color) -> str:
    hex_color = "#{:02x}{:02x}{:02x}".format(color.r, color.g, color.b)
    return f'<font color={hex_color}>{text}</font>'


def bold(text: str) -> str:
    return f'<b>{text}</b>'


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


class Label:
    def __init__(self,
            text: str,
            surface: pygame.Surface,
            rect: pygame.Rect | None = None,
            position: Vector2 | None = None,
            color: Color = Color('white'),
            anker: Literal['center', 'topleft', 'topright', 'bottomleft', 'bottomright'] = 'center',
            font: freetype.Font = FONT
        ):
        self.font = font
        self.position = position
        self.rect = rect
        if self.rect is None and self.position is None:
            raise ValueError('either rect or position must be given')
        
        self.text = text
        self.surface = surface
        self.color = color
        if self.rect is None and self.position is not None:
            self.rect = pygame.Rect(0, 0, 100, 40)
            if anker == 'center':
                self.rect.center = self.position
            elif anker == 'topleft':
                self.rect.topleft = self.position
            elif anker == 'topright':
                self.rect.topright = self.position
            elif anker == 'bottomleft':
                self.rect.bottomleft = self.position
        
    def draw(self):
        self.font.render_to(self.surface, self.rect, self.text, self.color) # type: ignore
    
    def update(self):
        self.draw()
    
    def set_text(self, text: str):
        self.text = text
    
    def set_color(self, color: Color):
        self.color = color


class TextBox:
    def __init__(self, 
            text_lines: list[str],
            position: Vector2,
            surface: pygame.Surface,
        ):
        self.labels: list[Label]
        self.text_lines = text_lines
        self.position = position
        self.surface = surface
        self.rebuild(self.position)

    def rebuild(self, top_left: Vector2):
        r = pygame.Rect(0, 0, 200, 25)
        r.topleft = top_left
        self.rects = [r]
        for _ in range(len(self.text_lines) - 1):
            r = self.rects[-1].copy()
            r.topleft = r.bottomleft; r.y += 2.
            self.rects.append(r)
        assert len(self.rects) == len(self.text_lines)
        self.labels = [Label(text, self.surface, rect) for text, rect in zip(self.text_lines, self.rects)]
        for i, r in enumerate(self.rects):
            self.labels[i].rect = r

    def total_size(self) -> Vector2:
        return Vector2(self.rects[-1].bottomright) - Vector2(self.rects[0].topleft)
    
    def set_bottom_right(self, bottom_right: Vector2):
        position = bottom_right - self.total_size()
        self.rebuild(position)
    
    def set_top_right(self, top_right: Vector2):
        position = top_right - Vector2(self.total_size().x, 0)
        self.rebuild(position)
    
    def set_bottom_left(self, bottom_left: Vector2):
        position = bottom_left - Vector2(0, self.total_size().y)
        self.rebuild(position)

    def update(self):
        for label in self.labels:
            label.update()

    def set_lines(self, text_lines: list[str]):
        assert len(text_lines) == len(self.labels), f'{len(text_lines)=} != {len(self.labels)=}'
        self.text_lines = text_lines
        for label, text in zip(self.labels, self.text_lines):
            label.set_text(text)


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


class Notification(Label):
    def __init__(self, 
        text: str, 
        position: Vector2, 
        surface: pygame.Surface,
        duration: float = 3.,
        color: Color = Color('white')
    ):
        super().__init__(text=text, surface=surface, position=position, color=color, anker='center')
        self.lifetime_timer = Timer(max_time=duration)
        self._is_alive = True

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.rect.y -= 3. * time_delta # type: ignore
        if not self.lifetime_timer.running():
            self._is_alive = False
        if self._is_alive:
            super().update()

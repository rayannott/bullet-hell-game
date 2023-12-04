from pygame import Color, Surface, Rect
import pygame_gui

from front.utils import paint

GREEN, RED, BLUE, YELLOW, ORANGE = map(Color, ('green', 'red', 'blue', 'yellow', 'orange'))

TEXT = f'''Some <b>rules</b> {paint(("here"), GREEN)}.
'''


class RulesWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 600, 800)
        super().__init__(
            rect=rect,
            manager=manager,
            window_title='Rules',
            html_message=TEXT
        )

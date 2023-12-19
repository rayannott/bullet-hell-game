from pygame import Color, Surface, Rect
import pygame_gui

from front.utils import paint
from config import (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX)

LIGHT_MAGENTA, NICER_GREEN, LIGHT_ORANGE = map(Color, (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX))

# TODO !!!
TEXT = f'''Some <b>rules</b> {paint(("here"), NICER_GREEN)}.
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

import shelve

from pygame import Color, Surface, Rect
import pygame_gui

from front.utils import paint
from config import (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX, SAVES_FILE)


LIGHT_MAGENTA, NICER_GREEN, LIGHT_ORANGE = map(Color, (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX))


class StatsWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 1000, 800)
        rect.center = surface.get_rect().center
        with shelve.open(str(SAVES_FILE)) as saves:
            print(saves, *saves.items())
            text = self.construct_html(saves)

        super().__init__(
            rect=rect,
            manager=manager,
            window_title='Stats',
            html_message=text
        )
    
    def construct_one_save_html(self, datetime_str: str, info: dict) -> str:
        # TODO
        text = f'{datetime_str}:<br> {info}<br><br>'
        return text
    
    def construct_html(self, saves: shelve.Shelf) -> str:
        if len(saves) == 0:
            return 'No saves yet'
        text = ''
        for datetime_str, info in saves.items():
            text += self.construct_one_save_html(datetime_str, info)
        return text

import pygame
import pygame_gui

from front import Screen
from front.game_screen import GameScreen
from config import MENU_BUTTONS_SIZE


class MenuScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        start_game_btn_rect = pygame.Rect(0, 0, 0, 0)
        start_game_btn_rect.size = MENU_BUTTONS_SIZE
        start_game_btn_rect.center = self.surface.get_rect().center
        self.start_game_btn = pygame_gui.elements.UIButton(start_game_btn_rect, 'PLAY', self.manager)

        stats_btn_rect = pygame.Rect(0, 0, 0, 0)
        stats_btn_rect.size = MENU_BUTTONS_SIZE
        stats_btn_rect.topleft = start_game_btn_rect.bottomleft
        self.stats_btn = pygame_gui.elements.UIButton(stats_btn_rect, 'STATS', self.manager)

        settings_btn_rect = pygame.Rect(0, 0, 0, 0)
        settings_btn_rect.size = MENU_BUTTONS_SIZE
        settings_btn_rect.topleft = stats_btn_rect.bottomleft
        self.settings_btn = pygame_gui.elements.UIButton(settings_btn_rect, 'SETTINGS', self.manager)

    def process_ui_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.start_game_btn:
                print('Game started')
                self.game_screen = GameScreen(self.surface)
                self.game_screen.run()
            elif event.ui_element == self.stats_btn:
                print('Stats opened')
            elif event.ui_element == self.settings_btn:
                print('Settings opened')
        super().process_ui_event(event)

    def process_event(self, event: pygame.event.Event):
        ...

    def update(self, time_delta: float):
        ...

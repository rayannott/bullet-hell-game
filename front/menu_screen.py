import pygame
import pygame_gui

from front.screen import Screen
from front.game_screen import GameScreen
from front.console_window import ConsoleWindow
from front.settings_window import SettingsWindow
from front.rules_window import RulesWindow
from front.sounds import set_sfx_volume, set_bg_music_vol, play_bg_music
from config import MENU_BUTTONS_SIZE
from config.settings import Settings
from front.stats_window import StatsWindow
from src.player_utils import Achievements


class MenuScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)

        self.reload_settings()

        start_game_btn_rect = pygame.Rect(0, 0, 0, 0)
        start_game_btn_rect.size = MENU_BUTTONS_SIZE
        start_game_btn_rect.center = self.surface.get_rect().center
        start_game_btn_rect.y -= MENU_BUTTONS_SIZE[1]
        self.start_game_btn = pygame_gui.elements.UIButton(start_game_btn_rect, 'PLAY', self.manager)

        stats_btn_rect = pygame.Rect(0, 0, 0, 0)
        stats_btn_rect.size = MENU_BUTTONS_SIZE
        stats_btn_rect.topleft = start_game_btn_rect.bottomleft
        self.stats_btn = pygame_gui.elements.UIButton(stats_btn_rect, 'STATS', self.manager)

        settings_btn_rect = pygame.Rect(0, 0, 0, 0)
        settings_btn_rect.size = MENU_BUTTONS_SIZE
        settings_btn_rect.topleft = stats_btn_rect.bottomleft
        self.settings_btn = pygame_gui.elements.UIButton(settings_btn_rect, 
            'SETTINGS', self.manager, allow_double_clicks=True, tool_tip_text='Double click to open console')

        rules_btn_rect = pygame.Rect(0, 0, 0, 0)
        rules_btn_rect.size = MENU_BUTTONS_SIZE
        rules_btn_rect.topleft = settings_btn_rect.bottomleft
        self.rules_btn = pygame_gui.elements.UIButton(rules_btn_rect, 'RULES', self.manager)


        self.console_window = None
        self.stats_window = None
        self.rules_window = None
        self.settings_window = None
        self.achievements_window = None

        self.game_screen = None

    def reload_settings(self):
        self.settings = Settings.load()
        set_sfx_volume(self.settings.sfx_volume)
        set_bg_music_vol(self.settings.music_volume)
        if self.settings.music_volume > 0:
            play_bg_music()

    def process_ui_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_DOUBLE_CLICKED:
            if event.ui_element == self.settings_btn:
                if self.console_window is not None:
                    self.console_window.kill()
                self.console_window = ConsoleWindow(self.manager, self)
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.start_game_btn:
                self.game_screen = GameScreen(self.surface, self.settings)
                self.game_screen.run()
            elif event.ui_element == self.stats_btn:
                if self.stats_window is not None:
                    self.stats_window.kill()
                self.stats_window = StatsWindow(self.manager, self.surface)
            elif event.ui_element == self.settings_btn:
                if self.settings_window is not None:
                    self.settings_window.kill()
                self.settings_window = SettingsWindow(self.manager, self)
            elif event.ui_element == self.rules_btn:
                if self.rules_window is not None:
                    self.rules_window.kill()
                self.rules_window = RulesWindow(self.manager, self.surface)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                if self.achievements_window is not None:
                    self.achievements_window.kill()
                # confirmation dialog
                self.achievements_window = pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect(30, 30, 400, 500),
                    action_long_desc='\n'.join(Achievements().all_achievements_pretty()),
                    manager=self.manager,
                    window_title='All possible achievements',
                    action_short_name='Ok',
                    blocking=False,
                )
        super().process_ui_event(event)

    def process_event(self, event: pygame.event.Event):
        ...

    def update(self, time_delta: float):
        ...

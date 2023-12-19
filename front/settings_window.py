import pygame
import pygame_gui

from config.settings import Settings


SETTINGS_WINDOW_SIZE = (500, 400)
SLIDERS_SIZE = (400, 50)
LABEL_SIZE = SETTINGS_WINDOW_SIZE[0]-SLIDERS_SIZE[0], 50


class SettingsWindow(pygame_gui.elements.UIWindow):
    def __init__(self, manager: pygame_gui.UIManager, menu_screen):
        rect = pygame.Rect(0, 0, *SETTINGS_WINDOW_SIZE)
        top_right = menu_screen.surface.get_rect().topright
        rect.topright = (top_right[0] - 50, top_right[1] + 50)
        super().__init__(
            rect=rect,
            manager=manager,
            window_display_title='Settings',
        )
        self.menu_screen = menu_screen
        self.settings: Settings = self.menu_screen.settings

        self.sfx_volume_slider = pygame_gui.elements.UIHorizontalSlider(
            pygame.Rect(0, 0, *SLIDERS_SIZE),
            min(200 * self.settings.sfx_volume, 100),
            (0, 100),
            manager=manager,
            container=self,
        )
        # this is scaled to 200, because otherwise the values are too low
        self.sfx_volume_slider.set_tooltip('SFX volume')
        rect_label_sfx = pygame.Rect(0, 0, *LABEL_SIZE)
        rect_label_sfx.topleft = self.sfx_volume_slider.relative_rect.topright
        self.sfx_volume_label = pygame_gui.elements.UILabel(
            rect_label_sfx,
            f'{self.settings.sfx_volume:.0%}',
            manager=manager,
            container=self,
        )

        rect1 = pygame.Rect(0, 0, *SLIDERS_SIZE)
        rect1.topleft = self.sfx_volume_slider.relative_rect.bottomleft
        self.music_volume_slider = pygame_gui.elements.UIHorizontalSlider(
            rect1,
            min(200 * self.settings.music_volume, 100),
            (0, 100),
            manager=manager,
            container=self,
        )
        self.music_volume_slider.set_tooltip('Music volume')

        rect_label_music = pygame.Rect(0, 0, *LABEL_SIZE)
        rect_label_music.topleft = rect1.topright
        self.music_volume_label = pygame_gui.elements.UILabel(
            rect_label_music,
            f'{self.settings.music_volume:.0%}',
            manager=manager,
            container=self,
        )

        rect2 = pygame.Rect(0, 0, *SLIDERS_SIZE)
        rect2.topleft = rect1.bottomleft
        self.difficulty_slider = pygame_gui.elements.UIHorizontalSlider(
            rect2,
            self.settings.difficulty,
            (1, 5),
            manager=manager,
            container=self,
        )
        self.music_volume_slider.set_tooltip('Difficulty')

        rect_label_difficulty = pygame.Rect(0, 0, *LABEL_SIZE)
        rect_label_difficulty.topleft = rect2.topright
        self.difficulty_label = pygame_gui.elements.UILabel(
            rect_label_difficulty,
            f'{self.settings.difficulty}',
            manager=manager,
            container=self,
        )

        rect_save_btn = pygame.Rect(0, 0, *LABEL_SIZE)
        rect_save_btn.topleft = rect2.bottomleft
        self.save_btn = pygame_gui.elements.UIButton(
            rect_save_btn,
            'Save',
            manager=manager,
            container=self,
        )
        rect_default_btn = pygame.Rect(0, 0, *LABEL_SIZE)
        rect_default_btn.topleft = rect_save_btn.topright
        self.default_btn = pygame_gui.elements.UIButton(
            rect_default_btn,
            'Reset',
            manager=manager,
            container=self,
            tool_tip_text='Reset to default settings',
        )
    
    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.sfx_volume_slider:
                self.settings.sfx_volume = self.sfx_volume_slider.get_current_value() / 200
                self.sfx_volume_label.set_text(f'{self.settings.sfx_volume:.0%}')
            elif event.ui_element == self.music_volume_slider:
                self.settings.music_volume = self.music_volume_slider.get_current_value() / 200
                self.music_volume_label.set_text(f'{self.settings.music_volume:.0%}')
            elif event.ui_element == self.difficulty_slider:
                self.settings.difficulty = int(self.difficulty_slider.get_current_value())
                self.difficulty_label.set_text(f'{self.settings.difficulty}')
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.save_btn:
                self.settings.dump()
                self.menu_screen.reload_settings()
            elif event.ui_element == self.default_btn:
                self.settings = Settings.create_default()
                self.menu_screen.reload_settings()
                self.sfx_volume_slider.set_current_value(min(200 * self.settings.sfx_volume, 100))
                self.music_volume_slider.set_current_value(min(200 * self.settings.music_volume, 100))
                self.difficulty_slider.set_current_value(self.settings.difficulty)
                self.sfx_volume_label.set_text(f'{self.settings.sfx_volume:.0%}')
                self.music_volume_label.set_text(f'{self.settings.music_volume:.0%}')
                self.difficulty_label.set_text(f'{self.settings.difficulty}')

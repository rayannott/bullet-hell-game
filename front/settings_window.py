import pygame
import pygame_gui


class SettingsWindow(pygame_gui.elements.UIWindow):
    def __init__(self, manager: pygame_gui.UIManager, menu_screen):
        rect = pygame.Rect(0, 0, 400, 400)
        top_right = menu_screen.surface.get_rect().topright
        rect.topright = (top_right[0] - 50, top_right[1] + 50)
        super().__init__(
            rect=rect,
            manager=manager,
            window_display_title='Settings',
        )
        self.menu_screen = menu_screen

from abc import ABC, abstractmethod
import logging

import pygame
import pygame_gui

from config import QUIT_BUTTON_SIZE, FRAMERATE
from config import setup_logging
setup_logging('DEBUG')


class Screen(ABC):
    """Abstract class for all screens in the game."""
    def __init__(self,
            surface: pygame.Surface,
            bg_color: str = '#101010'
        ):
        self.surface = surface
        self.window_size = self.surface.get_rect().size
        self.background = pygame.Surface(self.window_size)
        self.background.fill(pygame.Color(bg_color))
        self.manager = pygame_gui.UIManager(self.window_size)
        self.is_running = True

        # adding the quit button
        quit_button_rect = pygame.Rect(0, 0, 0, 0)
        quit_button_rect.size = QUIT_BUTTON_SIZE
        quit_button_rect.topright = self.surface.get_rect().topright
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=quit_button_rect,
            text='x',
            manager=self.manager
        )

    @abstractmethod
    def process_event(self, event: pygame.event.Event):
        ...
    
    @abstractmethod
    def update(self, time_delta: float):
        ...

    def run(self):
        clock = pygame.time.Clock()
        while self.is_running:
            time_delta = clock.tick(FRAMERATE)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_running = False
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.quit_button:
                        self.is_running = False
                        logging.debug('Quit button pressed')
                self.manager.process_events(event)
                self.process_event(event)
            self.surface.blit(self.background, (0, 0))
            self.manager.update(time_delta)
            self.update(time_delta)
            self.manager.draw_ui(self.surface)
            pygame.display.update()

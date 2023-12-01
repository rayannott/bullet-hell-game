from typing import override
import logging

import pygame
import pygame_gui

from screens import Screen
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)
from src import Game, Slider
setup_logging('DEBUG')


def color_gradient(start_color: pygame.Color, end_color: pygame.Color, percent: float) -> pygame.Color:
    return pygame.Color(
        int(start_color.r + (end_color.r - start_color.r) * percent),
        int(start_color.g + (end_color.g - start_color.g) * percent),
        int(start_color.b + (end_color.b - start_color.b) * percent),
        int(start_color.a + (end_color.a - start_color.a) * percent)
    )


class HealthBar(pygame_gui.elements.UIStatusBar):
    def __init__(self, **kwargs):
        self.text_to_render = ''
        super().__init__(**kwargs)
        self.percent_full = 0
        self.bar_filled_colour = pygame.Color('green')
    
    def status_text(self):
        return self.text_to_render
    
    def update_color(self):
        self.bar_filled_colour = color_gradient(
            pygame.Color('red'),
            pygame.Color('green'),
            self.percent_full
        )
    
    def set_health(self, health: Slider):
        self.text_to_render = str(health)
        self.percent_full = health.get_percent_full()
        self.update_color()


class StatsPanel:
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager):
        self.surface = surface
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, *GAME_STATS_PANEL_SIZE),
            manager=manager
        )
        self.health_bar = HealthBar(
            relative_rect=pygame.Rect(SM, SM, *GAME_HEALTH_BAR_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.stats_textbox = pygame_gui.elements.UITextBox(
            html_text='some text',
            relative_rect=pygame.Rect(SM, SM + GAME_HEALTH_BAR_SIZE[1], *GAME_STATS_TEXTBOX_SIZE),
            manager=manager,
            parent_element=self.panel
        )

    def update(self, player_health: Slider):
        self.health_bar.set_health(player_health)

class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.game = Game()
        self.stats_panel = StatsPanel(surface, self.manager)

    @override
    def process_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.game.player.get_health().change_by(-1.)

    @override
    def update(self, time_delta: float):
        self.game.update(time_delta)
        self.stats_panel.update(
            player_health=self.game.player.get_health()
        )

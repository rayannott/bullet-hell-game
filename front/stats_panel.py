import pygame, pygame_gui
from pygame import Color, Vector2, freetype

from src.game import Game
from front.utils import ProgressBar, Label, TextBox
from config import (SM, BM, GAME_STATS_PANEL_SIZE, FONT_FILE,
    GAME_HEALTH_BAR_SIZE, GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)

freetype.init()
font = freetype.Font(FONT_FILE, 20)


class StatsPanel:
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, game: Game):
        self.surface = surface
        self.game = game
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, *GAME_STATS_PANEL_SIZE),
            manager=manager
        )
        self.health_bar = ProgressBar(
            color_gradient_pair=(Color('red'), Color('green')),
            relative_rect=pygame.Rect(SM, SM, *GAME_HEALTH_BAR_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.energy_bar = ProgressBar(
            color_gradient_pair=(Color('blue'), Color('yellow')),
            relative_rect=pygame.Rect(SM, SM + GAME_HEALTH_BAR_SIZE[1], *GAME_ENERGY_BAR_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.stats_textbox = TextBox(
            text_lines=[''] * 3,
            position=Vector2(BM, SM + self.energy_bar.relative_rect.bottomleft[1] + 2 * BM),
            surface=surface
        )

    def update(self, time_delta: float):
        player = self.game.player
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        self.stats_textbox.set_lines([
                f'{"difficulty":<16} {self.game.settings.difficulty}',
                f'{"level":<16} {self.game.level}',
                f'{"time":<16} {self.game.time:.2f}',
            ])
        self.stats_textbox.update()

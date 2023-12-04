import pygame, pygame_gui
from pygame import Color, freetype

from src.game import Game
from front.utils import ProgressBar
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
        r = pygame.Rect(0, 0, *GAME_ENERGY_BAR_SIZE)
        r.topleft = self.energy_bar.relative_rect.bottomleft; r.y += 2 * BM; r.x += BM
        self.stats_rects = [r]
        for _ in range(3):
            r = self.stats_rects[-1].copy()
            r.topleft = r.bottomleft; r.y += SM
            self.stats_rects.append(r)

    def update(self, time_delta: float):
        player = self.game.player
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        for rect, text in zip(self.stats_rects, [
            f'difficulty: {self.game.settings.difficulty}',
            f'level: {self.game.level}',
            f'time: {self.game.time:.2f}',
        ]): font.render_to(self.surface, rect, text, Color('white'))

import pygame, pygame_gui
from pygame import Color, Vector2, freetype

from src.game import Game
from front.utils import ProgressBar, TextBox
from config import (SM, BM, GAME_STATS_PANEL_SIZE, FONT_FILE,
    GAME_HEALTH_BAR_SIZE, GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)

freetype.init()
font = freetype.Font(FONT_FILE, 20)


class StatsPanel:
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, game: Game):
        self.surface = surface
        self.game = game
        self.show_stats_panel = True
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, *GAME_STATS_PANEL_SIZE),
            manager=manager
        )
        self.health_bar = ProgressBar(
            color_gradient_pair=(Color('#751729'), Color('#58ed71')),
            relative_rect=pygame.Rect(SM, SM, *GAME_HEALTH_BAR_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.energy_bar = ProgressBar(
            color_gradient_pair=(Color('#0d182b'), Color('#3f7ae8')),
            relative_rect=pygame.Rect(SM, SM + GAME_HEALTH_BAR_SIZE[1], *GAME_ENERGY_BAR_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.stats_textbox = TextBox(
            text_lines=[''] * 8,
            position=Vector2(BM, SM + self.energy_bar.relative_rect.bottomleft[1] + 2 * BM),
            surface=surface
        )

    def update(self, time_delta: float):
        if not self.show_stats_panel: return
        player = self.game.player
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        self.stats_textbox.set_lines([
                f'{"difficulty":<16} {self.game.settings.difficulty}',
                f'{"level":<16} {self.game.level}',
                f'{"time":<16} {self.game.time:.2f}',
                f'{"extra bullets":<16} {player.extra_bullets}/{player.max_extra_bullets}',
                f'{"damage":<16} {player.get_damage():.0f}',
                f'{"speed":<16} {player.get_max_speed():.1f}',
                f'{"regen":<16} {player.get_regen():.1f}',
                f'{"cooldown":<16} {player.get_shoot_coolodown():.2f}',

            ])
        self.stats_textbox.update()

    def toggle_visibility(self):
        self.show_stats_panel = not self.show_stats_panel
        self.panel.visible = self.show_stats_panel
        self.health_bar.visible = self.show_stats_panel
        self.energy_bar.visible = self.show_stats_panel

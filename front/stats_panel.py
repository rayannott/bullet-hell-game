import pygame, pygame_gui
from pygame import Color

from src.game import Game
from src.utils import Timer
from front.utils import ProgressBar
from config import SM, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE


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
        # TODO: replace this with just text like in drawing debug
        # TODO  or make it transparent
        self.stats_textbox = pygame_gui.elements.UITextBox(
            html_text='',
            relative_rect=pygame.Rect(SM, 2*SM + GAME_HEALTH_BAR_SIZE[1] + GAME_ENERGY_BAR_SIZE[1], *GAME_STATS_TEXTBOX_SIZE),
            manager=manager,
            parent_element=self.panel
        )
        self.rewrite_stats_timer = Timer(0.5)

    def update(self, time_delta: float):
        player = self.game.player
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        # TODO: choose more interesting stats
        self.rewrite_stats_timer.tick(time_delta)
        if not self.rewrite_stats_timer.running():
            STATS_LABELS = ['time', 'level', 'enemies killed', 'accuracy', 'avg damage']
            STATS_VALUES = [self.game.time, self.game.level, player.stats.ENEMIES_KILLED, player.stats.get_accuracy(), player.damage]
            FORMATS = ['.1f', 'd', 'd', '.1%', '.0f']
            self.stats_textbox.set_text(
                '<br>'.join((f'{label:<15} {value:{format_}}' for label, value, format_ in zip(STATS_LABELS, STATS_VALUES, FORMATS)))
            )
            self.rewrite_stats_timer.reset()

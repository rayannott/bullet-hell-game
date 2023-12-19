import pygame
from pygame import Vector2

from front.utils import TextBox
from src.player import Player
from config.front import LIGHT_ORANGE_HEX


ORANGE = pygame.Color(LIGHT_ORANGE_HEX)


class InventoryInfo:
    def __init__(self, surface: pygame.Surface, player: Player):
        self.player = player
        self.surface = surface; self.surf_rect = surface.get_rect()
        self.N_old = 0
        self.rebuild_textbox_if()
    
    def rebuild_textbox_if(self):
        actives_list = list(self.player.artifacts_handler.iterate_active())
        N = len(actives_list) + 2
        if N == self.N_old:
            # rebuild only if number of actives changed
            return
        self.textbox = TextBox(['']*N, Vector2(), self.surface)
        self.textbox.set_bottom_right(Vector2(self.surf_rect.bottomright) - Vector2(50, 10))
        for i, active in enumerate(actives_list):
            self.textbox.labels[i].set_text(f'{active}')
            self.textbox.labels[i].set_color(ORANGE)
        self.N_old = N
    
    def update(self, time_delta: float):
        self.rebuild_textbox_if()
        self.textbox.labels[-1].set_text(f'{self.player.boosts}')
        self.textbox.update()
    
import pygame
from pygame import Vector2

from front.utils import TextBox
from src.entities.player import Player
from config.front import LIGHT_ORANGE_HEX, NICER_RED_HEX


ORANGE = pygame.Color(LIGHT_ORANGE_HEX)
NICER_RED = pygame.Color(NICER_RED_HEX)


class InventoryInfo:
    def __init__(self, surface: pygame.Surface, player: Player):
        self.player = player
        self.surface = surface
        self.surf_rect = surface.get_rect()
        self.N_old = 0
        self.rebuild_textbox_if()

    def rebuild_textbox_if(self):
        actives_list = list(self.player.artifacts_handler.iterate_active())
        N = len(actives_list) + 2
        if N != self.N_old:
            self.textbox = TextBox([""] * N, Vector2(), self.surface)
            self.textbox.set_bottom_left(
                Vector2(self.surf_rect.bottomleft) + Vector2(10, -10)
            )
            self.N_old = N
        for i, active in enumerate(actives_list):
            self.textbox.labels[i].set_text(f"{active.get_verbose_string()}")
            color = (
                NICER_RED
                if active.cooldown_timer.running()
                or active.cost > self.player.energy.get_value()
                else ORANGE
            )
            self.textbox.labels[i].set_color(color)

    def update(self, time_delta: float):
        self.rebuild_textbox_if()
        self.textbox.labels[-1].set_text(f"{self.player.boosts}")
        self.textbox.update()

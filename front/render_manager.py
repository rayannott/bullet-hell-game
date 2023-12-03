import math

import pygame, pygame_gui
from pygame import Color, Vector2, freetype
from src.enemy import Enemy

from src.game import Game
from src.entity import Entity
from src.utils import Slider
from src.enums import EntityType
from front.utils import ColorGradient
from config import PLAYER_SHOT_COST

freetype.init()
font = freetype.SysFont('Arial', 20)


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        self.rel_rect = pygame.Rect(0, 0, 220, 80)
        self.rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
    
    def render(self):
        for oil_spill in self.game.oil_spills():
            self.draw_entity_basics(oil_spill)
        for projectile in self.game.projectiles():
            self.draw_entity_basics(projectile)
        for enemy in self.game.enemies():
            self.draw_entity_basics(enemy)
            self.draw_entity_circular_status_bar(enemy, enemy.get_health(),
                enemy.get_size() * 1.5, color=Color('green'), draw_full=True, width=2)
            if self.debug: self.draw_enemy_health_debug(enemy)
        for energy_orb in self.game.energy_orbs():
            self.draw_entity_basics(energy_orb)
            self.draw_entity_circular_status_bar(energy_orb, energy_orb._life_timer.get_slider(reverse=True),
                energy_orb.get_size() * 2., color=Color('magenta'), draw_full=True, width=1)
        for corpse in self.game.corpses():
            self.draw_entity_basics(corpse)
        self.draw_player()
        if self.debug:
            font.render_to(self.surface, self.rel_rect, 
                f'[fps {self.game.get_last_fps():.1f}] [entd {self.entities_drawn}]',
                Color('white')
            )
        self.reset()

    def draw_entity_debug(self, entity: Entity):
        if entity._speed and entity._vel.magnitude_squared():
            pygame.draw.line(
                self.surface,
                Color('white'),
                entity.get_pos(),
                entity.get_pos() + entity._vel.normalize() * entity._speed * 0.1,
                width=2
            )

    def draw_enemy_health_debug(self, enemy: Enemy):
        health_text = f'{enemy.get_health()}'
        rect = pygame.Rect(0, 0, 85, 40)
        rect.center = enemy.get_pos() + Vector2(0, -enemy.get_size() * 1.5)
        font.render_to(self.surface, rect, health_text, Color('white'))

    def draw_entity_circular_status_bar(self, entity: Entity, slider: Slider, 
                                        radius: float, color: Color = Color('white'),
                                        draw_full: bool = False, width: int = 3):
        arc_percent = slider.get_percent_full()
        if draw_full or arc_percent < 1.:
            angle = math.pi * (2 * arc_percent + 0.5)
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = entity.get_pos()
            pygame.draw.arc(
                self.surface,
                color,
                rect,
                math.pi / 2,
                angle,
                width=width
            )

    def draw_player(self):
        player = self.game.player
        self.draw_entity_basics(player)
        self.draw_entity_circular_status_bar(player, player._shoot_cooldown_timer.get_slider(), player.get_size()*2)
        if player.get_energy().get_value() > PLAYER_SHOT_COST:
            pygame.draw.circle(
                self.surface,
                Color('yellow'),
                player.get_pos(),
                player.get_size() + 4,
                width=2
            )

    def draw_entity_trail(self, entity: Entity):
        _trail_len = len(entity._trail)
        color_gradient = ColorGradient(Color('black'), entity.get_color())
        for i, pos in enumerate(entity._trail):
            pygame.draw.circle(
                self.surface,
                color_gradient(i / _trail_len),
                pos,
                2.,
                width=1
            )

    def draw_entity_basics(self, entity: Entity):
        _current_color = entity.get_color()
        pygame.draw.circle(self.surface, _current_color, entity.get_pos(), entity.get_size())
        self.entities_drawn += 1
        if entity._render_trail:
            self.draw_entity_trail(entity)
        if self.debug: self.draw_entity_debug(entity)

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0

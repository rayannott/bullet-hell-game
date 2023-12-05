import math

import pygame
from pygame import Color, Vector2, freetype
from src.enemy import Enemy

from src.game import Game
from src.entity import Entity
from src.utils import Slider, Timer
from front.utils import ColorGradient, Label, TextBox
from config import PLAYER_SHOT_COST, GAME_DEBUG_RECT_SIZE, WAVE_DURATION, BM

freetype.init()
font = freetype.SysFont('Arial', 20)


NICER_GREEN = Color('#3ce870')
MAGENTA = Color('magenta')
LIGHTER_MAGENTA = Color('#a22ac9')


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        debug_rel_rect = pygame.Rect(0, 0, *GAME_DEBUG_RECT_SIZE)
        debug_rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
        self.five_sec_timer = Timer(5.)
        self.boss_soon_slider = Slider(1., 0.)
        top_right = Vector2(*self.surface.get_rect().topright)
        self.debug_textbox = TextBox(['']*6, top_right - Vector2(310., -BM), self.surface)
    
    def render(self):
        for oil_spill in self.game.oil_spills():
            self.draw_entity_basics(oil_spill)
        for projectile in self.game.projectiles():
            self.draw_entity_basics(projectile)
        for enemy in self.game.enemies():
            self.draw_entity_basics(enemy)
            self.draw_circular_status_bar(enemy.get_pos(), enemy.get_health(),
                enemy.get_size() * 1.5, color=NICER_GREEN, draw_full=True, width=2)
            if self.debug: self.draw_enemy_health_debug(enemy)
        for energy_orb in self.game.energy_orbs():
            self.draw_entity_basics(energy_orb)
            self.draw_circular_status_bar(energy_orb.get_pos(), energy_orb._life_timer.get_slider(reverse=True),
                energy_orb.get_size() * 2., color=MAGENTA, draw_full=True, width=1)
        for corpse in self.game.corpses():
            self.draw_entity_basics(corpse)
        self.draw_player()

        # "boss spawns in 5 seconds" indicator
        if self.game.one_wave_timer.get_value() > WAVE_DURATION - 5.:
            self.boss_soon_slider.set_percent_full(1. - (self.game.one_wave_timer.get_value() - (WAVE_DURATION - 5.)) / 5.)
            self.draw_circular_status_bar(self.game.player.get_gravity_point(), self.boss_soon_slider,
                self.game.player.get_size() * 4., color=LIGHTER_MAGENTA, draw_full=True, width=6)
            
        if self.debug:
            ROWS = ['fps', 'entities drawn', 'speed', 'avg damage', 'accuracy', 'orbs collected']
            VALUES = [f'{self.game.get_last_fps():.1f}', f'{self.entities_drawn}',
                f'{self.game.player.speed:.1f}', f'{self.game.player.damage:.0f}',
                f'{self.game.player.stats.get_accuracy():.0%}', f'{self.game.player.stats.ENERGY_ORBS_COLLECTED}']
            self.debug_textbox.set_lines(
                [f'[{row:<16} {value:>5}]' for row, value in zip(ROWS, VALUES)]
            )
            self.debug_textbox.update()
        self.reset()

    def draw_entity_debug(self, entity: Entity):
        if entity.speed and entity.vel.magnitude_squared():
            pygame.draw.line(
                self.surface,
                Color('white'),
                entity.get_pos(),
                entity.get_pos() + entity.vel.normalize() * entity.speed * 0.1,
                width=2
            )

    def draw_enemy_health_debug(self, enemy: Enemy):
        health_text = f'{enemy.get_health()}'
        label = Label(health_text, self.surface, 
            position=enemy.get_pos() + Vector2(enemy.get_size(), -enemy.get_size() * 1.5))
        label.update()
        # TODO: check if this is expensive; if so, cache it

    def draw_circular_status_bar(self, pos: Vector2, slider: Slider, 
                                        radius: float, color: Color = Color('white'),
                                        draw_full: bool = False, width: int = 3):
        arc_percent = slider.get_percent_full()
        if draw_full or arc_percent < 1.:
            angle = math.pi * (2 * arc_percent + 0.5)
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = pos
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
        self.draw_circular_status_bar(player.get_pos(), player.shoot_cooldown_timer.get_slider(), player.get_size()*2)
        if player.get_energy().get_value() > PLAYER_SHOT_COST:
            pygame.draw.circle(
                self.surface,
                Color('yellow'),
                player.get_pos(),
                player.get_size() + 4,
                width=2
            )

    def draw_entity_trail(self, entity: Entity):
        _trail_len = len(entity.trail)
        color_gradient = ColorGradient(Color('black'), entity.get_color())
        for i, pos in enumerate(entity.trail):
            pygame.draw.circle(
                self.surface,
                color_gradient(i / _trail_len),
                pos,
                2.,
                width=1
            )

    def draw_entity_basics(self, entity: Entity):
        pygame.draw.circle(self.surface, entity.get_color(), entity.get_pos(), entity.get_size())
        self.entities_drawn += 1
        if entity.render_trail:
            self.draw_entity_trail(entity)
        if self.debug: self.draw_entity_debug(entity)

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0

import math

import pygame
from pygame import Color, Vector2, freetype
from src.enemy import Enemy
from src.enums import ArtifactType, EnemyType, ProjectileType

from src.game import Game
from src.entity import Entity
from src.utils import Slider, Timer
from front.utils import ColorGradient, Label, TextBox
from config import PLAYER_SHOT_COST, GAME_DEBUG_RECT_SIZE, WAVE_DURATION, BM, ARTIFACT_SHIELD_SIZE, NICER_MAGENTA_HEX

freetype.init()
font = freetype.SysFont('Arial', 20)


NICER_GREEN = Color('#3ce870')
MAGENTA = Color(NICER_MAGENTA_HEX)
LIGHTER_MAGENTA = Color('#a22ac9')
YELLOW = Color('yellow')


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        self.screen_center = Vector2(*surface.get_rect().center)
        debug_rel_rect = pygame.Rect(0, 0, *GAME_DEBUG_RECT_SIZE)
        debug_rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
        self.five_sec_timer = Timer(5.)
        self.boss_soon_slider = Slider(1., 0.)
        top_right = Vector2(*self.surface.get_rect().topright)
        self.debug_textbox = TextBox(['']*5, top_right - Vector2(310., -BM), self.surface)
    
    def render(self):
        for oil_spill in self.game.oil_spills():
            self.draw_entity_basics(oil_spill)
        for aoe_effect in self.game.aoe_effects():
            self.draw_entity_basics(aoe_effect)
        for projectile in self.game.projectiles():
            if projectile.projectile_type == ProjectileType.DEF_TRAJECTORY:
                for def_traj_pos in projectile.render_traj_points: # type: ignore
                    pygame.draw.circle(self.surface, '#202020', def_traj_pos, 2)
            self.draw_entity_basics(projectile)
        for enemy in self.game.enemies():
            self.draw_enemy(enemy)
        for energy_orb in self.game.energy_orbs():
            self.draw_entity_basics(energy_orb)
            self.draw_circular_status_bar(energy_orb.get_pos(), energy_orb._life_timer.get_slider(reverse=True),
                energy_orb.get_size() * 2., color=MAGENTA, draw_full=True, width=1)
        for corpse in self.game.corpses():
            self.draw_entity_basics(corpse)
        for mine in self.game.mines():
            self.draw_mine(mine)
        self.draw_player()

        # "boss spawns in 5 seconds" indicator
        if self.game.one_wave_timer.get_value() > WAVE_DURATION - 5.:
            self.boss_soon_slider.set_percent_full(1. - (self.game.one_wave_timer.get_value() - (WAVE_DURATION - 5.)) / 5.)
            self.draw_circular_status_bar(self.screen_center, self.boss_soon_slider,
                80., color=LIGHTER_MAGENTA, draw_full=True, width=8)
            
        if self.debug:
            ROWS = ['fps', 'entities drawn', 'speed', 'accuracy', 'orbs collected']
            VALUES = [f'{self.game.get_last_fps():.1f}', f'{self.entities_drawn}',
                f'{self.game.player.speed:.1f}',
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

    @staticmethod
    def soon_shooting_coef_function(x: float) -> float:
        return -3.125*x**2 + 2.125 * x+1

    def draw_enemy(self, enemy: Enemy):
        self.draw_entity_basics(enemy)
        self.draw_circular_status_bar(enemy.get_pos(), enemy.get_health(),
            enemy.get_size() * 1.5, 
            color=NICER_GREEN, draw_full=enemy.enemy_type != EnemyType.BASIC, width=2)
        # if less than 1.5 sec left on the cooldown timer, indicate shooting intent
        if enemy.cooldown.get_time_left() < 1.5:
            t = enemy.cooldown.get_time_left() / 1.5
            pygame.draw.circle(
                self.surface,
                Color('white'),
                enemy.get_pos(),
                enemy.get_size() * self.soon_shooting_coef_function(1. - t),
                width=1
            )
        if self.debug: self.draw_enemy_health_debug(enemy)

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
        if player.energy.get_value() > PLAYER_SHOT_COST:
            pygame.draw.circle(
                self.surface,
                YELLOW,
                player.get_pos(),
                player.get_size(),
                width=6
            )
        self.draw_circular_status_bar(player.get_pos(), player.shoot_cooldown_timer.get_slider(), player.get_size()*2)
        # bullet shield:
        if (player.artifacts_handler.is_present(ArtifactType.BULLET_SHIELD) and 
            player.artifacts_handler.get_bullet_shield().is_on()):
            pygame.draw.circle(
                self.surface,
                Color('yellow'),
                player.get_pos(),
                ARTIFACT_SHIELD_SIZE,
                width=2
            )
            self.draw_circular_status_bar(player.get_pos(), 
                player.artifacts_handler.get_bullet_shield().duration_timer.get_slider(reverse=True), ARTIFACT_SHIELD_SIZE + 5., draw_full=True)

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

    def draw_mine(self, mine: Entity):
        """Draws two crossing ellipses"""
        ms = mine.get_size()
        r1 = pygame.Rect(0, 0, ms, 2*ms)
        r2 = pygame.Rect(0, 0, 2*ms, ms)
        r1.center = mine.get_pos()
        r2.center = mine.get_pos()
        pygame.draw.ellipse(self.surface, mine.get_color(), r1, width=2)
        pygame.draw.ellipse(self.surface, mine.get_color(), r2, width=2)
        self.entities_drawn += 1

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0

import math

import pygame
from pygame import Color, Vector2, freetype
from src.artifact_chest import ArtifactChest
from src.artifacts import Artifact
from src.enemy import Enemy
from src.enums import ArtifactType, EnemyType, ProjectileType

from src.game import Game
from src.entity import Entity
from src.utils import Slider, Timer
from front.utils import ColorGradient, Label, TextBox
from config import (PLAYER_SHOT_COST, GAME_DEBUG_RECT_SIZE, 
    WAVE_DURATION, BM, ARTIFACT_SHIELD_SIZE, NICER_MAGENTA_HEX, NICER_GREEN_HEX)

freetype.init()
font = freetype.SysFont('Arial', 20)


NICER_GREEN = Color(NICER_GREEN_HEX)
MAGENTA = Color(NICER_MAGENTA_HEX)
LIGHTER_MAGENTA = Color('#a22ac9')
YELLOW = Color('yellow')
WHITE = Color('white')
RED = Color('#e31243')
GRAY = Color('#808080')


def draw_circular_status_bar(
    surface: pygame.Surface, 
    pos: Vector2,
    slider: Slider, 
    radius: float,
    color: Color = Color('white'),
    draw_full: bool = False,
    width: int = 3
):
    arc_percent = slider.get_percent_full()
    if draw_full or arc_percent < 1.:
        angle = math.pi * (2 * arc_percent + 0.5)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = pos
        pygame.draw.arc(
            surface,
            color,
            rect,
            math.pi / 2,
            angle,
            width=width
        )


OPTION_CIRCLE_SIZE = 50.
class UltimatePicker:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.is_on = False
        self.options: list[Artifact] = []
        self.option_circles_positions = []
        self.options_labels = []

    def set_mouse_pos(self, mouse_pos: Vector2):
        self.mouse_pos = mouse_pos

    def render(self):
        if not self.is_on: return
        if not self.options: return
        player_energy: Slider = self.options[0].player.energy
        pygame.draw.circle(self.surface, MAGENTA, self.pos_to_draw_at, 4, width=1)
        for i in range(len(self.options)):
            this_pos = self.option_circles_positions[i]
            this_width = 5 if (this_pos - self.mouse_pos).magnitude_squared() < OPTION_CIRCLE_SIZE ** 2 else 2
            pygame.draw.circle(self.surface, MAGENTA, this_pos, OPTION_CIRCLE_SIZE, width=this_width)
            color = NICER_GREEN if player_energy.get_value() >= self.options[i].cost else WHITE
            draw_circular_status_bar(self.surface, this_pos, self.options[i].cooldown_timer.get_slider(),
                OPTION_CIRCLE_SIZE + 15., draw_full=True, color=color, width=5)
            self.options_labels[i].update()
    
    def recompute_options(self):
        _len = len(self.options); shift_render = Vector2(20., 0.)
        if _len == 1:
            self.option_circles_positions = [self.pos_to_draw_at]
            self.options_labels = [Label(self.options[0].get_short_string(), self.surface, position=(self.pos_to_draw_at + shift_render))]
        else:
            self.option_circles_positions = [self.pos_to_draw_at + Vector2(OPTION_CIRCLE_SIZE * 1.1, 0.).rotate(360. * i / _len) 
                for i in range(_len)]
            self.options_labels = []
            for art, pos in zip(self.options, self.option_circles_positions):
                self.options_labels.append(Label(art.get_short_string(), self.surface, position=(pos + shift_render)))

    def add_artifact(self, artifact: Artifact):
        if artifact.artifact_type == ArtifactType.STATS: return
        self.options.append(artifact)
    
    def turn_on(self):
        self.is_on = True
        self.pos_to_draw_at = self.mouse_pos.copy()
        self.recompute_options()

    def get_turned_off(self) -> ArtifactType | None:
        self.is_on = False
        for i in range(len(self.options)):
            if (self.option_circles_positions[i] - self.mouse_pos).magnitude_squared() < OPTION_CIRCLE_SIZE ** 2:
                return self.options[i].artifact_type
        return None


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        self.screen_center = Vector2(surface.get_rect().center)
        self.ult_picker = UltimatePicker(surface)
        debug_rel_rect = pygame.Rect(0, 0, *GAME_DEBUG_RECT_SIZE)
        debug_rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
        self.five_sec_timer = Timer(5.)
        self.boss_soon_slider = Slider(1., 0.)
        top_right = Vector2(self.surface.get_rect().topright)
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
            draw_circular_status_bar(self.surface, energy_orb.get_pos(), energy_orb._life_timer.get_slider(reverse=True),
                energy_orb.get_size() * 2., color=energy_orb.color, draw_full=True, width=1)
        for corpse in self.game.corpses():
            self.draw_entity_basics(corpse)
        for mine in self.game.mines():
            self.draw_mine(mine)
        for art_chest in self.game.artifact_chests():
            self.draw_artifact_chest(art_chest)
        self.ult_picker.render()
        self.draw_player()

        # "boss spawns in 5 seconds" indicator
        if self.game.one_wave_timer.get_value() > WAVE_DURATION - 5.:
            self.boss_soon_slider.set_percent_full(1. - (self.game.one_wave_timer.get_value() - (WAVE_DURATION - 5.)) / 5.)
            draw_circular_status_bar(self.surface, self.screen_center, self.boss_soon_slider,
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
        return -5.625*x**2 + 4.625 * x+1

    def draw_artifact_chest(self, art_chest: ArtifactChest):
        can_be_picked_up = art_chest.can_be_picked_up()
        self.draw_entity_basics(art_chest)
        pos = art_chest.get_pos(); size = art_chest.get_size()
        _color = (WHITE if art_chest.artifact.artifact_type == ArtifactType.STATS else RED) if can_be_picked_up else GRAY
        for i in range(3):
            pygame.draw.circle(self.surface, _color, pos, size * i / 3 + 3, width=3)
        if can_be_picked_up:
            draw_circular_status_bar(self.surface, pos, art_chest.life_timer.get_slider(reverse=True),
                size * 1.2, color=WHITE, width=2)
            label = Label(str(art_chest.artifact), self.surface, position=pos + Vector2(-size, -size * 1.5))
            label.update()

    def draw_enemy(self, enemy: Enemy):
        self.draw_entity_basics(enemy)
        draw_circular_status_bar(self.surface, enemy.get_pos(), enemy.get_health(),
            enemy.get_size() * 1.5, 
            color=NICER_GREEN, draw_full=enemy.enemy_type != EnemyType.BASIC, width=2)
        # if less than 1. sec left on the cooldown timer, indicate shooting intent
        if enemy.shoots_player and enemy.cooldown.get_time_left() < 1.:
            t = enemy.cooldown.get_time_left()
            pygame.draw.circle(
                self.surface,
                Color('white'),
                enemy.get_pos(),
                enemy.get_size() * self.soon_shooting_coef_function(1. - t),
                width=2
            )
        if self.debug:
            health_text = f'{enemy.get_health()}'
            label = Label(health_text, self.surface, 
                position=enemy.get_pos() + Vector2(enemy.get_size(), -enemy.get_size() * 1.5))
            label.update()

    def draw_player(self):
        player = self.game.player
        self.draw_entity_basics(player)
        if player.invulnerability_timer.running():
            _indicator_color = RED
        elif player.energy.get_value() > PLAYER_SHOT_COST:
            _indicator_color = YELLOW
        else:
            _indicator_color = WHITE
        if player.effect_flags.IN_DASH:
            _indicator_color = NICER_GREEN
        if player.energy.get_value() > PLAYER_SHOT_COST:
            pygame.draw.circle(
                self.surface,
                _indicator_color,
                player.get_pos(),
                player.get_size(),
                width=6
            )
        draw_circular_status_bar(self.surface, player.get_pos(), player.shoot_cooldown_timer.get_slider(), player.get_size()*2)
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
            draw_circular_status_bar(self.surface, player.get_pos(), 
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

import math
import random

import pygame
from pygame import Color, Vector2, freetype
from src.entities.artifact_chest import ArtifactChest
from src.misc.artifacts import Artifact
from src.entities.enemy import Enemy
from src.utils.enums import ArtifactType, EnemyType, ProjectileType

from src.game import Game
from src.entities.entity import Entity
from src.entities.mine import Mine
from src.entities.bomb import Bomb
from src.entities.projectile import Projectile
from src.utils.utils import Slider, Timer
from front.utils import ColorGradient, Label, TextBox
from config import (
    PLAYER_SHOT_COST,
    PLAYER_DEFAULT_SPEED_RANGE,
    GAME_DEBUG_RECT_SIZE,
    LIGHT_MAGENTA_HEX,
    NICER_RED_HEX,
    GRAY_HEX,
    WAVE_DURATION,
    BM,
    BULLET_SHIELD_SIZE,
    NICER_MAGENTA_HEX,
    NICER_GREEN_HEX,
    BOSS_ENEMY_COLOR_HEX,
    LIGHT_ORANGE_HEX,
    MINER_DETONATION_RADIUS,
)


freetype.init()


NICER_GREEN = Color(NICER_GREEN_HEX)
LIGHT_ORANGE = Color(LIGHT_ORANGE_HEX)
MAGENTA = Color(NICER_MAGENTA_HEX)
LIGHTER_MAGENTA = Color(LIGHT_MAGENTA_HEX)
YELLOW = Color("yellow")
WHITE = Color("white")
RED = Color(NICER_RED_HEX)
GRAY = Color(GRAY_HEX)
DARK_PURPLE = Color("#772277")
BLACK = Color("black")
BOSS_ENEMY_COLOR = Color(BOSS_ENEMY_COLOR_HEX)
ALMOST_BG_COLOR = Color("#080808")


def draw_circular_status_bar(
    surface: pygame.Surface,
    pos: Vector2,
    slider: Slider,
    radius: float,
    color: Color = Color("white"),
    draw_full: bool = False,
    width: int = 3,
):
    arc_percent = slider.get_percent_full()
    if draw_full or arc_percent < 1.0:
        angle = math.pi * (2 * arc_percent + 0.5)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = pos
        pygame.draw.arc(surface, color, rect, math.pi / 2, angle, width=width)


OPTION_CIRCLE_SIZE = 50.0


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
        if not self.is_on:
            return
        if not self.options:
            return
        player_energy: Slider = self.options[0].player.energy
        pygame.draw.circle(self.surface, MAGENTA, self.pos_to_draw_at, 4, width=1)
        for i in range(len(self.options)):
            this_pos = self.option_circles_positions[i]
            this_width = (
                5
                if (this_pos - self.mouse_pos).magnitude_squared()
                < OPTION_CIRCLE_SIZE**2
                else 2
            )
            pygame.draw.circle(
                self.surface, MAGENTA, this_pos, OPTION_CIRCLE_SIZE, width=this_width
            )
            color = (
                NICER_GREEN
                if player_energy.get_value() >= self.options[i].cost
                else WHITE
            )
            draw_circular_status_bar(
                self.surface,
                this_pos,
                self.options[i].cooldown_timer.get_slider(),
                OPTION_CIRCLE_SIZE + 15.0,
                draw_full=True,
                color=color,
                width=5,
            )
            self.options_labels[i].update()

    def recompute_options(self):
        _len = len(self.options)
        shift_render = Vector2(20.0, 0.0)
        if _len == 1:
            self.option_circles_positions = [self.pos_to_draw_at]
            self.options_labels = [
                Label(
                    self.options[0].get_short_string(),
                    self.surface,
                    position=(self.pos_to_draw_at + shift_render),
                )
            ]
        else:
            self.option_circles_positions = [
                self.pos_to_draw_at
                + Vector2(OPTION_CIRCLE_SIZE * (1.0 + 0.1 * _len), 0.0).rotate(
                    360.0 * i / _len
                )
                for i in range(_len)
            ]
            self.options_labels = []
            for art, pos in zip(self.options, self.option_circles_positions):
                self.options_labels.append(
                    Label(
                        art.get_short_string(),
                        self.surface,
                        position=(pos + shift_render),
                    )
                )

    def add_artifact(self, artifact: Artifact):
        if artifact.artifact_type == ArtifactType.STATS:
            return
        self.options.append(artifact)

    def turn_on(self):
        self.is_on = True
        self.pos_to_draw_at = self.mouse_pos.copy()
        self.recompute_options()

    def get_turned_off(self) -> ArtifactType | None:
        self.is_on = False
        for i in range(len(self.options)):
            if (
                self.option_circles_positions[i] - self.mouse_pos
            ).magnitude_squared() < OPTION_CIRCLE_SIZE**2:
                return self.options[i].artifact_type
        return None


class RenderManager:
    HP_COLOR_GRADIENT = (Color("red"), Color("green"))

    def __init__(self, surface: pygame.Surface, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        self.screen_center = Vector2(surface.get_rect().center)
        self.ult_picker = UltimatePicker(surface)
        debug_rel_rect = pygame.Rect(0, 0, *GAME_DEBUG_RECT_SIZE)
        debug_rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
        self.five_sec_timer = Timer(5.0)
        self.boss_soon_slider = Slider(1.0, 0.0)
        top_right = Vector2(self.surface.get_rect().topright)
        self.debug_textbox = TextBox([""] * 6, Vector2(), self.surface)
        self.debug_textbox.set_top_right(top_right - Vector2(100.0, -BM))

    def render(self):
        for oil_spill in self.game.oil_spills():
            self.draw_entity_basics(oil_spill)
        for aoe_effect in self.game.aoe_effects():
            self.draw_entity_basics(aoe_effect)
            pygame.draw.circle(
                self.surface,
                BLACK,
                aoe_effect.get_pos(),
                aoe_effect.get_size(),
                width=5,
            )
        for projectile in self.game.projectiles():
            self.draw_projectile(projectile)
        for enemy in self.game.enemies():
            self.draw_enemy(enemy)
        for energy_orb in self.game.energy_orbs():
            self.draw_entity_basics(energy_orb)
            draw_circular_status_bar(
                self.surface,
                energy_orb.get_pos(),
                energy_orb.i_has_lifetime.timer.get_slider(reverse=True),
                energy_orb.get_size() * 2.0,
                color=energy_orb.color,
                draw_full=True,
                width=1,
            )
        for corpse in self.game.corpses():
            self.draw_entity_basics(corpse)
            draw_circular_status_bar(
                self.surface,
                corpse.get_pos(),
                corpse.give_blocks_timer.get_slider(reverse=True),
                corpse.get_size() * 0.6,
                BLACK,
                width=4,
            )
        for mine in self.game.mines():
            self.draw_mine(mine)
        for art_chest in self.game.artifact_chests():
            self.draw_artifact_chest(art_chest)
        for line in self.game.lines():
            pygame.draw.line(self.surface, line.color, line.p1, line.p2, width=2)
        for magnet in self.game.bombs():
            self.draw_bomb(magnet)
        self.ult_picker.render()
        self.dash_animation()
        self.draw_player()

        # "boss spawns in 5 seconds" indicator
        if self.game.one_wave_timer.get_value() > WAVE_DURATION - 5.0:
            self.boss_soon_slider.set_percent_full(
                1.0
                - (self.game.one_wave_timer.get_value() - (WAVE_DURATION - 5.0)) / 5.0
            )
            draw_circular_status_bar(
                self.surface,
                self.screen_center,
                self.boss_soon_slider,
                80.0,
                color=BOSS_ENEMY_COLOR,
                draw_full=True,
                width=8,
            )

        if self.debug:
            ROWS = [
                "fps",
                "entities drawn",
                "speed",
                "accuracy",
                "orbs collected",
                "damage received",
            ]
            VALUES = [
                f"{self.game.get_last_fps():.1f}",
                f"{self.entities_drawn}",
                f"{self.game.player.speed:.1f}",
                f"{self.game.player.get_stats().get_accuracy():.0%}",
                f"{self.game.player.get_stats().ENERGY_ORBS_COLLECTED}/{self.game.energy_orbs_spawned}",
                f"{self.game.player.get_stats().DAMAGE_TAKEN:.1f}",
            ]
            self.debug_textbox.set_lines(
                [f"[{row:<16} {value:>5}]" for row, value in zip(ROWS, VALUES)]
            )
            self.debug_textbox.update()
        self.reset()

    def draw_entity_debug(self, entity: Entity):
        if entity.speed and entity.vel.magnitude_squared():
            pygame.draw.line(
                self.surface,
                WHITE,
                entity.get_pos(),
                entity.get_pos() + entity.vel.normalize() * entity.speed * 0.1,
                width=2,
            )

    @staticmethod
    def soon_shooting_coef_function(x: float) -> float:
        return -5.625 * x**2 + 4.625 * x + 1

    def draw_bomb(self, bomb: Bomb):
        pygame.draw.circle(
            self.surface,
            bomb.get_color(),
            bomb.get_pos(),
            bomb.get_size(),
            width=4,
        )
        draw_circular_status_bar(
            self.surface,
            bomb.get_pos(),
            bomb.defuse_timer.get_slider(),
            bomb.get_size() * 0.8,
            color=WHITE,
            width=3,
        )
        draw_circular_status_bar(
            self.surface,
            bomb.get_pos(),
            bomb.i_has_lifetime.timer.get_slider(reverse=True),
            bomb.get_size() * 1.0,
            color=RED if bomb.i_has_lifetime.timer.get_percent_full() > 0.75 else MAGENTA,
            width=7,
        )
        p = bomb.get_pos() + Vector2(-bomb.get_size(), 0)
        p_to_center = (bomb.get_pos() - p).normalize()
        pygame.draw.line(
            self.surface,
            WHITE,
            p + p_to_center * 5,
            p - p_to_center * 5,
            width=4,
        )

    def draw_artifact_chest(self, art_chest: ArtifactChest):
        can_be_picked_up = art_chest.can_be_picked_up()
        self.draw_entity_basics(art_chest)
        pos = art_chest.get_pos()
        size = art_chest.get_size()
        _color = (
            (WHITE if art_chest.artifact.artifact_type == ArtifactType.STATS else RED)
            if can_be_picked_up
            else GRAY
        )
        draw_circular_status_bar(
            self.surface,
            pos,
            art_chest.i_has_lifetime.timer.get_slider(reverse=True),
            size * 1.2,
            color=WHITE,
            width=2,
        )
        for i in range(3):
            pygame.draw.circle(self.surface, _color, pos, size * i / 3 + 3, width=3)
        label = Label(
            str(art_chest.artifact),
            self.surface,
            position=pos + Vector2(-size, -size * 1.5),
        )
        label.update()

    def draw_enemy(self, enemy: Enemy):
        self.draw_entity_basics(enemy)
        # do not draw health bar if enemy can always be killed with one shot
        can_one_shot = (
            enemy.health.max_value
            <= self.game.player.get_damage() - self.game.player.damage_spread
        )
        draw_circular_status_bar(
            self.surface,
            enemy.get_pos(),
            enemy.get_health(),
            enemy.get_size() * 1.0,
            color=NICER_GREEN,
            draw_full=not can_one_shot,
            width=3,
        )
        if enemy.has_block:
            block_vec = Vector2(enemy.get_size(), 0.0) * 1.2
            delta = Vector2(0.0, 4)
            pygame.draw.line(
                self.surface,
                LIGHT_ORANGE,
                enemy.get_pos() - block_vec + delta,
                enemy.get_pos() + block_vec + delta,
                width=5,
            )
            pygame.draw.line(
                self.surface,
                LIGHT_ORANGE,
                enemy.get_pos() - block_vec - delta,
                enemy.get_pos() + block_vec - delta,
                width=5,
            )
        if self.game.time_frozen and enemy.enemy_type != EnemyType.GHOST:
            cross_vec = Vector2(enemy.get_size(), enemy.get_size()) * 1.7
            pygame.draw.line(
                self.surface,
                WHITE,
                enemy.get_pos() - cross_vec,
                enemy.get_pos() + cross_vec,
                width=4,
            )
        # if less than 1. sec left on the cooldown timer, indicate shooting intent
        if enemy.shoots_player:
            if (t := enemy.cooldown.get_time_left()) < 1.0:
                pygame.draw.circle(
                    self.surface,
                    WHITE,
                    enemy.get_pos(),
                    enemy.get_size() * self.soon_shooting_coef_function(1.0 - t),
                    width=3,
                )
        if enemy.enemy_type == EnemyType.MINER:
            pygame.draw.circle(
                self.surface,
                ALMOST_BG_COLOR,
                enemy.get_pos(),
                MINER_DETONATION_RADIUS,
                width=2,
            )
        if self.debug:
            health_text = f"{enemy.get_health()}"
            label = Label(
                health_text,
                self.surface,
                position=enemy.get_pos()
                + Vector2(enemy.get_size(), -enemy.get_size() * 1.5),
            )
            label.update()

    def draw_player(self):
        player = self.game.player
        self.draw_entity_basics(player)

        player_indicator_default_color = (
            YELLOW if not self.game.is_victory else LIGHTER_MAGENTA
        )

        if player.invulnerability_timer.running():
            _indicator_color = RED
        elif player.energy.get_value() > PLAYER_SHOT_COST:
            _indicator_color = player_indicator_default_color
        else:
            _indicator_color = WHITE

        # rage:
        if (
            player.artifacts_handler.is_present(ArtifactType.RAGE)
            and player.artifacts_handler.get_rage().is_on()
        ):
            draw_circular_status_bar(
                self.surface,
                player.get_pos(),
                player.artifacts_handler.get_rage().duration_timer.get_slider(
                    reverse=True
                ),
                player.get_size() + 4.0,
                draw_full=True,
                width=7,
            )
            _indicator_color = DARK_PURPLE

        pygame.draw.circle(
            self.surface,
            _indicator_color,
            player.get_pos(),
            player.get_size(),
            width=6,
        )

        # shoot cooldown indicator
        draw_circular_status_bar(
            self.surface,
            player.get_pos(),
            player.shoot_cooldown_timer.get_slider(),
            player.get_size() * 2,
        )

        # move arrow
        if player.vel.magnitude_squared() > 40_000.0:
            move_direction = player.vel.copy()
            _mult = math.exp(-player.speed / PLAYER_DEFAULT_SPEED_RANGE[1])
            angle = 50.0 * _mult
            move_direction.scale_to_length(player.get_size() * 2.0 / _mult)
            move_direction_smaller = move_direction.copy()
            move_direction_smaller.scale_to_length(player.get_size() * 2.0)
            left = move_direction_smaller.rotate(angle)
            right = move_direction_smaller.rotate(-angle)
            mid_point = player.get_pos() + move_direction
            pygame.draw.line(
                self.surface,
                _indicator_color,
                mid_point,
                player.get_pos() + left,
                width=4,
            )
            pygame.draw.line(
                self.surface,
                _indicator_color,
                mid_point,
                player.get_pos() + right,
                width=4,
            )

        # bullet shield:
        if (
            player.artifacts_handler.is_present(ArtifactType.BULLET_SHIELD)
            and player.artifacts_handler.get_bullet_shield().is_on()
        ):
            pygame.draw.circle(
                self.surface, YELLOW, player.get_pos(), BULLET_SHIELD_SIZE, width=2
            )
            draw_circular_status_bar(
                self.surface,
                player.get_pos(),
                player.artifacts_handler.get_bullet_shield().duration_timer.get_slider(
                    reverse=True
                ),
                BULLET_SHIELD_SIZE + 5.0,
                draw_full=True,
            )
        # time slow:
        if (
            player.artifacts_handler.is_present(ArtifactType.TIME_SLOW)
            and player.artifacts_handler.get_time_slow().is_on()
        ):
            draw_circular_status_bar(
                self.surface,
                player.get_pos(),
                player.artifacts_handler.get_time_slow().duration_timer.get_slider(
                    reverse=True
                ),
                player.get_size() + 15.0,
                draw_full=True,
            )

    def draw_projectile(self, projectile: Projectile):
        if projectile.projectile_type == ProjectileType.DEF_TRAJECTORY:
            for def_traj_pos in projectile.render_traj_points:  # type: ignore
                pygame.draw.circle(self.surface, "#202020", def_traj_pos, 2)
        if self.game.time_frozen and projectile.projectile_type != ProjectileType.PLAYER_BULLET:
            cross_vec = Vector2(projectile.get_size(), projectile.get_size()) * 2.0
            pygame.draw.line(
                self.surface,
                WHITE,
                projectile.get_pos() - cross_vec,
                projectile.get_pos() + cross_vec,
                width=2,
            )
        self.draw_entity_basics(projectile)

    def dash_animation(self):
        if self.game.player.artifacts_handler.is_present(ArtifactType.DASH):
            dash = self.game.player.artifacts_handler.get_dash()
            if not dash.path_animation_lingering_timer.running():
                return
            a, b = dash.dash_path_history[-1]
            N = 50
            for i in range(N):
                pygame.draw.circle(self.surface, NICER_GREEN, a + (b - a) * i / N, 2)

    def draw_entity_trail(self, entity: Entity):
        if not entity.i_render_trail:
            return
        _trail_len = len(entity.i_render_trail.get_trail())
        color_gradient = ColorGradient(BLACK, entity.get_color())
        for i, pos in enumerate(entity.i_render_trail.get_trail()):
            pygame.draw.circle(
                self.surface, color_gradient(i / _trail_len), pos, 3.0, width=1
            )

    def draw_entity_basics(self, entity: Entity):
        pygame.draw.circle(
            self.surface, entity.get_color(), entity.get_pos(), entity.get_size()
        )
        self.entities_drawn += 1
        self.draw_entity_trail(entity)
        if self.debug:
            self.draw_entity_debug(entity)

    def draw_mine(self, mine: Mine):
        """Draws two crossing ellipses"""
        ms = mine.get_size()
        r1 = pygame.Rect(0, 0, ms, 2.5 * ms)
        r2 = pygame.Rect(0, 0, 2.5 * ms, ms)
        r1.center = mine.get_pos()
        r2.center = mine.get_pos()
        is_activated = mine.is_activated()
        color = mine.get_color() if is_activated else random.choice([GRAY, WHITE, RED])
        pygame.draw.ellipse(self.surface, color, r1, width=2)
        pygame.draw.ellipse(self.surface, color, r2, width=2)
        self.entities_drawn += 1

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0

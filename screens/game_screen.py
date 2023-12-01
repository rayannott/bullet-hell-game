import math
from typing import Literal, override
import logging

import pygame
from pygame import Color, Vector2
import pygame_gui

from screens import Screen
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, PLAYER_SHOT_COST,
    GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)
from src import Game, Slider, ColorGradient, Entity, EntityType, EnemyType, Player, Timer, Feedback, paint
from src import OnCooldown, NotEnoughEnergy

setup_logging('DEBUG')


class ProgressBar(pygame_gui.elements.UIStatusBar):
    def __init__(self, color_gradient_pair: tuple[Color, Color], **kwargs):
        self.text_to_render = ''
        super().__init__(**kwargs)
        self.percent_full = 0
        self.color_gradient = ColorGradient(*color_gradient_pair)
    
    def status_text(self):
        return self.text_to_render
    
    def update_color(self):
        self.bar_filled_colour = self.color_gradient(self.percent_full)
    
    def set_slider(self, slider: Slider):
        self.text_to_render = str(slider)
        self.percent_full = slider.get_percent_full()
        self.update_color()


class Notification(pygame_gui.elements.UITextBox):
    def __init__(self,
            text: str,
            position: Vector2,
            manager: pygame_gui.UIManager,
            duration: float = 3.,
            color: Color = Color('white'),
            **kwargs):
        super().__init__(
            html_text=paint(text, color, 8),
            relative_rect=pygame.Rect(position.x, position.y, len(text) * 12, 40),
            manager=manager,
            object_id='#notification', #! this doesn't work
            **kwargs)
        self.lifetime_timer = Timer(max_time=duration)
        self._is_alive = True
    
    def update(self, time_delta: float):
        if not self._is_alive: return
        self.lifetime_timer.tick(time_delta)
        self.rect.y -= 3. * time_delta # type: ignore
        if not self.lifetime_timer.running():
            self._is_alive = False
            self.kill()
        super().update(time_delta)


class StatsPanel:
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager):
        self.surface = surface
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
        self.stats_textbox = pygame_gui.elements.UITextBox(
            html_text='',
            relative_rect=pygame.Rect(SM, 2*SM + GAME_HEALTH_BAR_SIZE[1] + GAME_ENERGY_BAR_SIZE[1], *GAME_STATS_TEXTBOX_SIZE),
            manager=manager,
            parent_element=self.panel
        )

    def update(self, game: Game):
        player = game.player
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        STATS_LABELS = ['time', 'enemies killed', 'accuracy', 'orbs collected', 'damage dealt', 'damage taken']
        STATS_VALUES = [game._time, player._stats.ENEMIES_KILLED, player._stats.get_accuracy(), player._stats.ENERGY_ORBS_COLLECTED, player._stats.DAMAGE_DEALT, player._stats.DAMAGE_TAKEN]
        FORMATS = ['.1f', 'd', '.1%', 'd', '.0f', '.0f']
        self.stats_textbox.set_text(
            '<br>'.join((f'{label:<15} {value:{format_}}' for label, value, format_ in zip(STATS_LABELS, STATS_VALUES, FORMATS)))
        )


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, debug: bool = False):
        self.surface = surface
        self.debug = debug
        rel_rect = pygame.Rect(0, 0, 200, 100)
        rel_rect.bottomright = surface.get_rect().bottomright
        self.debug_text_box = pygame_gui.elements.UITextBox(
            html_text='',
            relative_rect=rel_rect,
            manager=manager
        )
        self.entities_drawn = 0
        self.update()

    def update(self):
        self.debug_text_box.visible = self.debug
        if self.debug:
            self.debug_text_box.set_text(f'entities drawn: {self.entities_drawn}')

    def draw_entity_debug(self, entity: Entity):
        if entity._speed and entity._vel.magnitude_squared():
            # print(entity, entity._vel, entity._type)
            pygame.draw.line(
                self.surface,
                Color('white'),
                entity.get_pos(),
                entity.get_pos() + entity._vel.normalize() * entity._speed * 0.1,
                width=2
            )
    
    def draw_entity_circular_status_bar(self, entity: Entity, slider: Slider, 
                                        radius: float, color: Color = Color('white'),
                                        draw_full: bool = False):
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
                width=3
            )

    def draw_player(self, player: Player):
        self.draw_entity_circular_status_bar(player, player._shoot_cooldown_timer.get_slider(), player.get_size()*2)
        if player.get_energy().get_value() > PLAYER_SHOT_COST:
            pygame.draw.circle(
                self.surface,
                Color('yellow'),
                player.get_pos(),
                player.get_size() + 4,
                width=2
            )

    def draw_entity(self, entity: Entity):
        _current_color = entity.get_color()
        color_gradient = ColorGradient(Color('black'), _current_color)
        pygame.draw.circle(self.surface, _current_color, entity.get_pos(), entity.get_size())
        this_ent_type = entity.get_type()
        if this_ent_type == EntityType.PLAYER:
            self.draw_player(entity) # type: ignore
        elif this_ent_type == EntityType.ENEMY:
            self.draw_entity_circular_status_bar(entity, entity.get_health(), # type: ignore
                entity.get_size() * 1.5, color=Color('green'), draw_full=True)
        elif this_ent_type == EntityType.ENERGY_ORB:
            self.draw_entity_circular_status_bar(entity, entity._life_timer.get_slider(reverse=True), # type: ignore
                entity.get_size() * 1.5, color=Color('magenta'), draw_full=True)
        if entity._render_trail:
            _trail_len = len(entity._trail)
            for i, pos in enumerate(entity._trail):
                pygame.draw.circle(
                    self.surface,
                    color_gradient(i / _trail_len),
                    pos,
                    2.,
                    width=1
                )
        self.entities_drawn += 1
        self.update()
        if self.debug: self.draw_entity_debug(entity)

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0


# TODO move everything above this line to other files

class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.screen_rectangle = self.surface.get_rect()
        self.game = Game(self.screen_rectangle)
        self.stats_panel = StatsPanel(surface, self.manager)
        self.debug = False
        self.render_manager = RenderManager(surface=surface, manager=self.manager, debug=self.debug)

        self.game_is_over_window_shown = False
        self.notifications: list[Notification] = []
        self.trail_cache = None

    @override
    def process_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p: self.game.toggle_pause()
        if self.game._paused: return
        if not self.game.is_running(): return
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEMOTION:
            self.game.player.set_gravity_point(pygame.Vector2(mouse_pos))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.game.player_try_shooting()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.debug = not self.debug
                self.render_manager.set_debug(self.debug)
                print(f'changing debug mode: now {self.debug=}')
            elif event.key == pygame.K_d:
                print('--- debug ---')
                print(repr(self.game.player))
                print('-'*10)
    
    @override
    def update(self, time_delta: float):
        self.game.update(time_delta)
        self.game.reflect_entities_vel()
        self.stats_panel.update(
            game=self.game
        )
        self.render()
        if not self.game.is_running() and not self.game_is_over_window_shown:
            self.show_game_is_over_window()
            self.game_is_over_window_shown = True
        self.render_manager.reset()
        self.process_feedback_buffer()

    def process_feedback_buffer(self):
        if len(self.game.feedback_buffer):
            feedback = self.game.feedback_buffer.popleft()
            self.spawn_notification(feedback=feedback)

    def render(self):
        for entity in self.game.all_entities_iter():
            if entity.is_alive():
                self.render_manager.draw_entity(entity)

    def show_game_is_over_window(self):
        self.game_is_over_window = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect(*self.surface.get_rect().center, 300, 200),
            manager=self.manager,
            window_title='Game Over',
            action_long_desc='Ok',
            blocking=True
        )
        print('game over', repr(self.game.player))
    
    def spawn_notification(self,
            text: str = '', 
            duration: float = 3., 
            at_pos: Literal['player', 'cursor'] | Vector2 = 'cursor',
            color: Color = Color('white'),
            feedback: Feedback | None = None,
        ):
        if feedback is not None:
            text = feedback.text
            duration = feedback.duration
            at_pos = feedback.at_pos
            color = feedback.color
        if at_pos == 'player': at_pos = self.game.player.get_pos()
        elif at_pos == 'cursor': at_pos = Vector2(pygame.mouse.get_pos())
        self.notifications.append(
            Notification(
                text=text,
                position=at_pos,
                manager=self.manager,
                duration=duration,
                color=color
            )
        )
        # remove dead notifications
        self.notifications = [notification for notification in self.notifications if notification._is_alive]

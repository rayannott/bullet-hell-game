import math
from typing import Literal, override
import logging

import pygame
from pygame import Color, Vector2
import pygame_gui

from src import Game, Slider, ColorGradient, Entity, EntityType, EnemyType, Player, Timer, Feedback, paint
from screens.screen import Screen
from screens.render_manager import RenderManager
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, PLAYER_SHOT_COST,
    GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)

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

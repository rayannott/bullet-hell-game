import math
from typing import Literal, override
import logging

import pygame
from pygame import Color, Vector2
import pygame_gui

from src import Game, Slider, Entity, EntityType, EnemyType, Player, Timer, Feedback
from front.screen import Screen
from front.render_manager import RenderManager
from front.utils import Notification
from front.stats_panel import StatsPanel
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, PLAYER_SHOT_COST,
    GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)

# setup_logging('DEBUG')


class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.screen_rectangle = self.surface.get_rect()
        self.game = Game(self.screen_rectangle)
        self.stats_panel = StatsPanel(surface, self.manager)
        self.debug = False
        self.render_manager = RenderManager(surface=surface, manager=self.manager, debug=self.debug, game=self.game)

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
            self.show_game_is_over_window(self.game.reason_of_death)
            self.game_is_over_window_shown = True
        self.render_manager.reset()
        self.process_feedback_buffer()
        self.game.set_last_fps(self.clock.get_fps())

    def process_feedback_buffer(self):
        if len(self.game.feedback_buffer):
            feedback = self.game.feedback_buffer.popleft()
            self.spawn_notification(feedback=feedback)

    def render(self):
        self.render_manager.render()

    def show_game_is_over_window(self, death_message: str):
        self.game_is_over_window = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect(*self.surface.get_rect().center, 300, 200),
            manager=self.manager,
            window_title='Game Over',
            action_long_desc=death_message,
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

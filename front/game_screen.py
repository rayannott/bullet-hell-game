from typing import Literal

import pygame
from pygame import Color, Vector2
import pygame_gui
from front.sounds import play_sfx

from src.utils import Feedback
from src.game import Game
from src.enums import EnemyType

from front.screen import Screen
from front.render_manager import RenderManager
from front.utils import Notification
from front.stats_panel import StatsPanel

from config.settings import Settings


class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface, settings: Settings):
        super().__init__(surface)
        self.settings = settings
        self.setup_game(surface)
    
    def setup_game(self, surface: pygame.Surface):
        self.screen_rectangle = self.surface.get_rect()
        self.game = Game(self.screen_rectangle, self.settings)
        self.stats_panel = StatsPanel(surface, self.manager, self.game)
        self.debug = False
        self.render_manager = RenderManager(surface=surface, debug=self.debug, game=self.game)

        self.game_is_over_window_shown = False
        self.notifications: list[Notification] = []

        # TODO: create a class for this
        self.ability_picker = ...

    def process_ui_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p: self.game.toggle_pause()
            elif event.key == pygame.K_F1:
                self.toggle_debug()
            elif event.key == pygame.K_F5:
                self.setup_game(self.surface)
            elif event.key == pygame.K_d:
                print('--- debug ---')
                print(self.game.player.get_stats())
                print('-'*10)
        super().process_ui_event(event)

    def process_event(self, event: pygame.event.Event):
        if self.game.paused: return
        if not self.game.is_running(): return

        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEMOTION:
            self.game.player.set_gravity_point(pygame.Vector2(mouse_pos))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.game.player_try_shooting()
            elif event.button == 3:
                # TODO: pressing opens a wheel menu with options
                ...
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.game.player_try_spawning_energy_orb()
    
    def update(self, time_delta: float):
        self.game.update(time_delta)
        self.game.reflect_entities_vel()
        self.stats_panel.update(time_delta=time_delta)
        self.render()
        if not self.game.is_running() and not self.game_is_over_window_shown:
            self.show_game_is_over_window(self.game.reason_of_death)
            play_sfx('game_over') # TODO: move this to `on_game_over()`
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
    
    def toggle_debug(self):
        self.debug = not self.debug
        self.render_manager.set_debug(self.debug)
        print(f'changing debug mode: now {self.debug=}')

    def show_game_is_over_window(self, death_message: str):
        self.game_is_over_window = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect(*self.surface.get_rect().center, 300, 200),
            manager=self.manager,
            window_title='Game Over',
            action_long_desc=death_message,
            blocking=True
        )
        print('game over', self.game.get_info())
    
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

    def post_run(self):
        # if player quit the game witout dying
        if self.game.player.is_alive():
            # do not write the reason of death to the info
            self.game.reason_of_death = ''

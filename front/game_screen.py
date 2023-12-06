import datetime
import random
from typing import Literal

import pygame
from pygame import Color, Vector2
import pygame_gui
from src.enums import ArtifactType, EnemyType

from src.utils import Feedback, random_unit_vector
from src.game import Game

from front.sounds import play_sfx
from front.screen import Screen
from front.render_manager import RenderManager
from front.utils import Notification
from front.stats_panel import StatsPanel

from config.paths import SAVES_FILE, SAVES_DIR
from config.settings import Settings


class InGameShop(pygame_gui.elements.UIWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: pygame.Surface, game: Game):
        rect = pygame.Rect(0, 0, 400, 400)
        self.surface = surface
        self.game = game
        top_right = surface.get_rect().topright
        rect.topright = (top_right[0] - 50, top_right[1] + 50)
        super().__init__(
            rect=rect,
            manager=manager,
            window_display_title='In-game shop',
        )


class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface, settings: Settings):
        super().__init__(surface)
        self.settings = settings
        self.setup_game(surface)
    
    def setup_game(self, surface: pygame.Surface):
        play_sfx('start_game')
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
            # elif event.key == pygame.K_q:
            #     self.game.toggle_pause()
            #     self.ingame_shop = InGameShop(self.manager, self.surface, self.game)
            # debug:
            elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
                if event.key == pygame.K_1:
                    self.game.spawn_enemy(EnemyType.BASIC)
                elif event.key == pygame.K_2:
                    self.game.spawn_enemy(EnemyType.FAST)
                elif event.key == pygame.K_3:
                    self.game.spawn_enemy(EnemyType.TANK)
                elif event.key == pygame.K_4:
                    self.game.spawn_enemy(EnemyType.ARTILLERY)
                elif event.key == pygame.K_5:
                    self.game.spawn_enemy(EnemyType.BOSS)
                elif event.key == pygame.K_d:
                    print('--- debug ---')
                    print(self.game.player.get_stats())
                    print('-'*10)
                elif event.key == pygame.K_l:
                    self.game.new_level()

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
                # TODO: ??
                pass
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.game.player_try_ultimate(artifact_type=ArtifactType.MINE_SPAWN)
            elif event.key == pygame.K_s:
                self.game.player_try_ultimate(artifact_type=ArtifactType.BULLET_SHIELD)
    
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
        for notification in self.notifications:
            notification.update(time_delta)

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
        print('[game over]', self.game.get_info())
    
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
        random_vector = random_unit_vector() * random.random() * 50
        if at_pos == 'player': at_pos = self.game.player.get_pos() + random_vector
        elif at_pos == 'cursor': at_pos = Vector2(pygame.mouse.get_pos()) + random_vector
        self.notifications.append(
            Notification(
                text=text,
                position=at_pos,
                surface=self.surface,
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
        if not SAVES_DIR.exists():
            SAVES_DIR.mkdir(exist_ok=True, parents=True)
        with open(SAVES_FILE, 'a') as f:
            print({datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S'): self.game.get_info()}, file=f)

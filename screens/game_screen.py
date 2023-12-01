from typing import Literal, override
import logging

import pygame
from pygame import Color, Vector2
import pygame_gui

from screens import Screen
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, 
    GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)
from src import Game, Slider, color_gradient, Entity, EntityType, EnemyType, Player, Timer
from src import OnCooldown, NotEnoughEnergy

setup_logging('DEBUG')


class ProgressBar(pygame_gui.elements.UIStatusBar):
    def __init__(self, color_gradient_pair: tuple[Color, Color], **kwargs):
        self.text_to_render = ''
        super().__init__(**kwargs)
        self.percent_full = 0
        self.color_gradient_pair = color_gradient_pair
    
    def status_text(self):
        return self.text_to_render
    
    def update_color(self):
        self.bar_filled_colour = color_gradient(
            *self.color_gradient_pair,
            self.percent_full
        )
    
    def set_slider(self, slider: Slider):
        self.text_to_render = str(slider)
        self.percent_full = slider.get_percent_full()
        self.update_color()


class Notification(pygame_gui.elements.UILabel):
    def __init__(self,
            text: str,
            position: Vector2,
            manager: pygame_gui.UIManager,
            duration: float = 3.,
            color: Color = Color('white'),
            **kwargs):
        super().__init__(
            text=text,
            relative_rect=pygame.Rect(position.x, position.y, 150, 20),
            manager=manager,
            **kwargs)
        self.text_colour = color
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

    def update(self, player: Player):
        self.health_bar.set_slider(player.get_health())
        self.energy_bar.set_slider(player.get_energy())
        self.stats_textbox.set_text('') # TODO change from debug mode


class RenderManager:
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
        # TODO: add drawing velocity vector and some other things if debug mode is on
        pass

    def draw_entity(self, entity: Entity):
        _current_color = entity.get_color()
        pygame.draw.circle(
            self.surface,
            _current_color,
            entity.get_pos(),
            entity.get_size()
        )
        if entity._render_trail:
            _trail_len = len(entity._trail)
            for i, pos in enumerate(entity._trail):
                pygame.draw.circle(
                    self.surface,
                    color_gradient(Color('black'), _current_color, i / _trail_len),
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
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEMOTION:
            self.game.player.set_gravity_point(pygame.Vector2(mouse_pos))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                try:
                    self.game.player_try_shooting()
                except OnCooldown as e:
                    self.spawn_notification('on cooldown', 2., color=Color('red'))
                    print('on cooldown')
                except NotEnoughEnergy as e:
                    self.spawn_notification('not enough energy', 2., color=Color('red'))
                    print('not enough energy')
                else:
                    self.spawn_notification('pew', 1., at_pos=self.game.player.get_pos())
                    print('player shot')
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                print('spawned basic enemy')
                self.game.spawn_enemy(
                    enemy_type=EnemyType.BASIC,
                )
            elif event.key == pygame.K_h:
                print('spawned tank enemy')
                self.game.spawn_enemy(
                    enemy_type=EnemyType.TANK,
                )
            elif event.key == pygame.K_f:
                print('spawned fast enemy')
                self.game.spawn_enemy(
                    enemy_type=EnemyType.FAST,
                )
            elif event.key == pygame.K_a:
                print('spawned artillery enemy')
                self.game.spawn_enemy(
                    enemy_type=EnemyType.ARTILLERY,
                )
            elif event.key == pygame.K_p:
                self.game.toggle_pause() # TODO: add some label to show that the game is paused
                print(f'changing pause state: now {self.game._paused=}')
            elif event.key == pygame.K_F1:
                self.debug = not self.debug
                self.render_manager.set_debug(self.debug)
                print(f'changing debug mode: now {self.debug=}')
            elif event.key == pygame.K_l:
                self.game.new_level()
            elif event.key == pygame.K_d:
                print('--- debug ---')
                print(repr(self.game.player))
                print('-'*10)
    
    @override
    def update(self, time_delta: float):
        self.game.update(time_delta)
        self.game.reflect_entities_vel()
        self.stats_panel.update(
            player=self.game.player
        )
        self.render()
        if not self.game.is_running() and not self.game_is_over_window_shown:
            self.show_game_is_over_window()
            self.game_is_over_window_shown = True
        self.render_manager.reset()
        self.process_feedback_buffer()

    def process_feedback_buffer(self):
        if len(self.game.feedback_buffer) > 0:
            # TODO: make this a class with color, duration, etc. depending on the event
            feedback = self.game.feedback_buffer.popleft()
            self.spawn_notification(feedback, 1.5, at_pos='player')

    def render(self):
        for entity in self.game.all_entities_iter():
            if entity.is_alive():
                self.render_manager.draw_entity(entity)

    def show_game_is_over_window(self):
        self.game_is_over_window = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect(0, 0, 300, 200),
            manager=self.manager,
            window_title='Game Over',
            action_long_desc='Ok',
            blocking=True
        )
    
    def spawn_notification(self, 
            text: str, 
            duration: float = 3., 
            at_pos: Literal['player', 'cursor'] | Vector2 = 'cursor',
            color: Color = Color('white')
        ):
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

from typing import override
import logging

import pygame
from pygame import Color, Vector2
import pygame_gui

from screens import Screen
from config import (setup_logging, SM, BM,
    MENU_BUTTONS_SIZE, GAME_STATS_PANEL_SIZE, GAME_HEALTH_BAR_SIZE, 
    GAME_ENERGY_BAR_SIZE, GAME_STATS_TEXTBOX_SIZE)
from src import Game, Slider, color_gradient, Entity, EntityType, Player, Timer


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
            color: Color = Color('white'),
            **kwargs):
        super().__init__(
            text=text,
            relative_rect=pygame.Rect(position.x, position.y, 150, 20),
            manager=manager,
            **kwargs)
        self.text_colour = color
        self.lifetime_timer = Timer(max_time=3.)
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
        self.stats_textbox.set_text(repr(player).replace(';', '<br>')) # TODO change from debug mode


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

    def draw_entity(self, entity: Entity):
        pygame.draw.circle(
            self.surface,
            entity.get_color(),
            entity.get_pos(),
            entity.get_size()
        )
        # TODO: add drawing velocity vector if debug mode is on
        if entity._render_trail:
            # print(f'entity {entity} has trail')
            for pos in entity._trail:
                pygame.draw.circle(self.surface, entity.get_color(), pos, 1.5)
        self.entities_drawn += 1
        self.update()

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
        self.render_manager = RenderManager(surface, self.manager, debug=self.debug)

        self.game_is_over_window_shown = False
        self.notifications: list[Notification] = []

    @override
    def process_event(self, event: pygame.event.Event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEMOTION:
            self.game.player.set_gravity_point(pygame.Vector2(mouse_pos))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            is_succesful = self.game.player_try_shooting()
            if not is_succesful:
                self.spawn_notification('not enough energy')
                print('not enough energy')
            else:
                print('player shot')
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.game.player._health.change(-10.)
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
                print('player trail:', self.game.player._trail)
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
    
    def spawn_notification(self, text: str):
        self.notifications.append(Notification(
            text=text,
            position=Vector2(pygame.mouse.get_pos()),
            manager=self.manager
        ))
        # remove dead notifications
        self.notifications = [notification for notification in self.notifications if notification._is_alive]

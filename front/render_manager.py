import math

import pygame, pygame_gui
from pygame import Color, Vector2

from src import Entity, EntityType, Player, Slider, PLAYER_SHOT_COST
from front.utils import ColorGradient


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
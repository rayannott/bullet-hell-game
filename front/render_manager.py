import math

import pygame, pygame_gui
from pygame import Color, freetype

freetype.init()
font = freetype.SysFont('Arial', 20)

from src import Entity, Slider, PLAYER_SHOT_COST, Game
from front.utils import ColorGradient
from src.enums import EntityType, EnemyType


class RenderManager:
    HP_COLOR_GRADIENT = (Color('red'), Color('green'))
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, game: Game, debug: bool = False):
        self.surface = surface
        self.debug = debug
        self.game = game
        self.rel_rect = pygame.Rect(0, 0, 220, 80)
        self.rel_rect.topright = surface.get_rect().topright
        self.entities_drawn = 0
    
    def render(self):
        self.draw_player()
        for entity in self.game.all_entities_iter(with_player=False):
            self.draw_entity(entity)
        if self.debug:
            font.render_to(self.surface, self.rel_rect, 
                f'[fps {self.game.get_last_fps():.1f}] [entd {self.entities_drawn}]',
                Color('white')
            )
        self.reset()

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
                                        draw_full: bool = False, width: int = 3):
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
                width=width
            )

    def draw_player(self):
        player = self.game.player
        self.draw_entity(player)
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
        if this_ent_type == EntityType.ENEMY and entity._health.max_value > self.game.player._damage: # type: ignore
            self.draw_entity_circular_status_bar(entity, entity.get_health(), # type: ignore
                entity.get_size() * 1.5, color=Color('green'), draw_full=True)
        elif this_ent_type == EntityType.ENERGY_ORB:
            self.draw_entity_circular_status_bar(entity, entity._life_timer.get_slider(reverse=True), # type: ignore
                entity.get_size() * 2., color=Color('magenta'), draw_full=True, width=1)
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
        if self.debug: self.draw_entity_debug(entity)

    def set_debug(self, debug: bool):
        self.debug = debug

    def reset(self):
        self.entities_drawn = 0
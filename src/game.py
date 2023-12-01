from collections import defaultdict, deque
import random
from typing import Generator

import pygame
from pygame import Vector2

from config import (REMOVE_DEAD_ENTITIES_EVERY, PLAYER_STARTING_POSITION, ENERGY_ORB_DEFAULT_ENERGY,
    INCREASE_LEVEL_EVERY, GAME_MAX_LEVEL, ENERGY_ORB_SIZE, ENERGY_ORB_COOLDOWN_RANGE)
from src import DummyEntity, Player, Timer, Entity, EntityType, EnergyOrb


class Game:
    def __init__(self, screen_rectangle: pygame.Rect) -> None:
        self._level = 1
        self._time = 0.
        self._paused = False
        self.screen_rectangle = screen_rectangle
        
        self.feedback_buffer: deque[str] = deque()

        self.player = Player(Vector2(*PLAYER_STARTING_POSITION))
        self.entities: defaultdict[EntityType, list[Entity]] = defaultdict(list)

        self.remove_dead_entities_timer = Timer(max_time=REMOVE_DEAD_ENTITIES_EVERY)
        self.increase_level_timer = Timer(max_time=INCREASE_LEVEL_EVERY)
        self.new_energy_orb_timer = Timer(max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
    
    def all_entities_iter(self) -> Generator[Entity, None, None]:
        yield self.player
        for _, entities in self.entities.items():
            for entity in entities:
                if entity.is_alive():
                    yield entity

    def is_running(self) -> bool:
        return self.player.is_alive()
    
    def toggle_pause(self) -> None: self._paused = not self._paused

    def new_level(self):
        if self._level >= GAME_MAX_LEVEL: return False
        self._level += 1
        self.player.new_level()
        return True
    
    def spawn_energy_orb(self):
        self.add_entity(
            EnergyOrb(
                _pos=self.get_random_screen_position_for_entity(entity_size=ENERGY_ORB_SIZE),
                _lifetime=8.,
                _energy=ENERGY_ORB_DEFAULT_ENERGY + 10 * (self._level - 1)
            )
        )

    def process_timers(self, time_delta: float) -> None:
        """Process events that happen periodically."""
        self.remove_dead_entities_timer.tick(time_delta)
        if not self.remove_dead_entities_timer.running():
            self.remove_dead_entities()
            self.remove_dead_entities_timer.reset()
            print('Removed dead entities')
        self.increase_level_timer.tick(time_delta)
        if not self.increase_level_timer.running():
            self.new_level()
            self.increase_level_timer.reset()
            print('Increased level')
        self.new_energy_orb_timer.tick(time_delta)
        if not self.new_energy_orb_timer.running():
            self.spawn_energy_orb()
            self.new_energy_orb_timer.reset(with_max_time=random.uniform(*ENERGY_ORB_COOLDOWN_RANGE))
            print('Spawned energy orb')

    def update(self, time_delta: float) -> None:
        if not self.is_running() or self._paused: return
        self._time += time_delta
        for entity in self.all_entities_iter():
            entity.update(time_delta)
        self.process_timers(time_delta)
        self.process_collisions()
    
    def player_try_shooting(self) -> bool:
        new_projectile = self.player.shoot()
        if new_projectile is not None:
            self.add_entity(new_projectile)
            return True
        else:
            return False

    def reflect_entity_vel(self, entity: Entity) -> None:
        """
        Reflect the velocity of all entities that are outside of the screen.
        """
        pos_ = entity.get_pos()
        if entity.is_alive() and not self.screen_rectangle.collidepoint(pos_):
            if pos_.x < self.screen_rectangle.left or pos_.x > self.screen_rectangle.right:
                entity._vel.x *= -1.
            if pos_.y < self.screen_rectangle.top or pos_.y > self.screen_rectangle.bottom:
                entity._vel.y *= -1.

    def reflect_entities_vel(self,) -> None:
        """
        Reflect the velocity of all entities that are outside of the screen.
        """
        self.reflect_entity_vel(self.player)
        for entity_type, entities in self.entities.items():
            for entity in entities:
                self.reflect_entity_vel(entity)
    
    def process_collisions(self) -> None:
        # player colldes with anything:
        # add energy if energy orb
        # deal damage if anything else
        for entity in self.all_entities_iter():
            if entity.intersects(self.player):
                if entity.get_type() == EntityType.ENERGY_ORB:
                    energy_collected: float = entity.energy_left() # type: ignore
                    self.player._energy.change(energy_collected) # type: ignore
                    entity.kill()
                    self.feedback_buffer.append(f'+{energy_collected:.0f}e')
                elif entity.get_type() == EntityType.PROJECTILE:
                    damage_taken: float = entity._damage # type: ignore
                    self.player._health.change(-damage_taken) # type: ignore
                    self.player.get_stats().BULLETS_CAUGHT += 1
                    self.player.get_stats().DAMAGE_TAKEN += damage_taken

                    entity.kill()
                    self.feedback_buffer.append(f'-{damage_taken}hp')
                else:
                    print('player collided with something else:', entity)

        # bullets collide with enemies -> enemies die, player gets energy:

        ...

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.get_type()].append(entity)

    def remove_dead_entities(self):
        """
        Remove all dead entities.
        This function is called every REMOVE_DEAD_ENTITIES_EVERY seconds.
        """
        new_entities = defaultdict(list)
        for entity_type, entities in self.entities.items():
            for entity in entities:
                if entity.is_alive():
                    new_entities[entity_type].append(entity)
        self.entities = new_entities
        # print('Removed dead entities')

    def get_random_screen_position_for_entity(self, entity_size: float) -> Vector2:
        """
        Get a random position inside the screen.
        Try a position and return it if it doesn't collide with any other entity.
        """
        while True:
            pos_candidate = self.get_random_screen_position()
            if not any(entity.intersects(DummyEntity(pos_candidate)) for entity in self.all_entities_iter()):
                return pos_candidate
    
    def get_random_screen_position(self) -> Vector2:
        x = random.uniform(self.screen_rectangle.left, self.screen_rectangle.right)
        y = random.uniform(self.screen_rectangle.top, self.screen_rectangle.bottom)
        return Vector2(x, y)
        
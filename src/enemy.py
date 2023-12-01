from collections import deque
from dataclasses import dataclass
import random
from pygame import Vector2, Color

from src import Entity, EntityType, EnemyType, Slider, Player, Timer, Projectile, ProjectileType
from config import (ENEMY_DEFAULT_SPEED, ENEMY_DEFAULT_SIZE, PROJECTILE_DEFAULT_SPEED, 
    ENEMY_DEFAULT_MAX_HEALTH, ENEMY_DEFAULT_SHOOT_COOLDOWN, ENEMY_DEFAULT_REWARD)


@dataclass
class EnemyStats:
    size: float
    color: Color
    speed: float
    health: float
    shoot_cooldown: float
    reward: float


ENEMY_STATS_MAP = {
    # size, color, speed, health, shoot_cooldown, reward
    EnemyType.BASIC: EnemyStats(
        size=ENEMY_DEFAULT_SIZE, color=Color('red'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN, reward=ENEMY_DEFAULT_REWARD),
    EnemyType.FAST: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 0.9, color=Color('#912644'), speed=ENEMY_DEFAULT_SPEED * 1.8, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 0.8, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN, reward=ENEMY_DEFAULT_REWARD * 1.2),
    EnemyType.TANK: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 1.8, color=Color('#9e401e'), speed=ENEMY_DEFAULT_SPEED * 0.8, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 2.5, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN, reward=ENEMY_DEFAULT_REWARD * 1.8),
    EnemyType.ARTILLERY: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2, color=Color('#005c22'), speed=0., 
        health=ENEMY_DEFAULT_MAX_HEALTH * 4, shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 2.3, reward=ENEMY_DEFAULT_REWARD * 2.5),
    EnemyType.BOSS: EnemyStats(
        size=ENEMY_DEFAULT_SIZE * 2.7, color=Color('#510e78'), speed=ENEMY_DEFAULT_SPEED, 
        health=ENEMY_DEFAULT_MAX_HEALTH * 5., shoot_cooldown=ENEMY_DEFAULT_SHOOT_COOLDOWN * 0.5, reward=ENEMY_DEFAULT_REWARD * 5.),
}
# TODO: split these types into different classes (they have different behaviors)


class Enemy(Entity):
    def __init__(self, 
            _pos: Vector2,
            _enemy_type: EnemyType,
            _player: Player,
        ):
        stats = ENEMY_STATS_MAP[_enemy_type]
        super().__init__(
            _pos=_pos,
            _type=EntityType.ENEMY,
            _size=stats.size,
            _speed=stats.speed, 
            _color=stats.color,
            _can_spawn_entities=True,
            _homing_target=_player,
        )
        self._health = Slider(stats.health)
        self._cooldown = Timer(max_time=stats.shoot_cooldown)
        self._reward = stats.reward
        self._enemy_type = _enemy_type
    
    def shoot(self):
        direction = (self._vel.rotate(random.uniform(-.1, .1))).normalize()
        return Projectile(
            _pos=self._pos.copy() + direction * self._size * 1.5,
            _vel=direction,
            _projectile_type=ProjectileType.NORMAL,
            _speed=self._speed + PROJECTILE_DEFAULT_SPEED,
        )
    
    def update(self, time_delta: float):
        if not self._health.is_alive(): self.kill()
        if not self.is_alive(): return
        super().update(time_delta)
        self._cooldown.tick(time_delta)
        if not self._cooldown.running():
            self._entities_buffer.append(self.shoot())
            self._cooldown.reset()

    def get_health(self): return self._health

    def get_reward(self): return self._reward

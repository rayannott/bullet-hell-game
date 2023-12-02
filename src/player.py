from dataclasses import dataclass
import random

from pygame import Vector2

from src.entity import Entity
from src.enums import EntityType, ProjectileType
from src.exceptions import NotEnoughEnergy, OnCooldown, ShootingDirectionUndefined
from src.projectile import Projectile
from src.utils import Stats, Slider, Timer

from config import (PLAYER_SIZE, PLAYER_DEFAULT_MAX_HEALTH, PLAYER_DEFAULT_SPEED_RANGE, PLAYER_DEFAULT_REGEN_RATE,
    OIL_SPILL_DAMAGE_PER_SECOND, OIL_SPILL_SPEED_MULTIPLIER,
    PLAYER_DEFAULT_ENERGY_DECAY_RATE, PLAYER_DEFAULT_SHOOT_COOLDOWN, PLAYER_DEFAULT_DAMAGE_AVG, PLAYER_DEFAULT_DAMAGE_SPREAD,
    PLAYER_DEFAULT_MAX_ENERGY, PLAYER_STARTING_ENERGY, PROJECTILE_DEFAULT_SPEED, PLAYER_SHOT_COST)


@dataclass
class EffectFlags:
    """
    Flags for effects that can be applied to the player.
    """
    OIL_SPILL: bool = False    

    def reset(self):
        self.OIL_SPILL = False


class Player(Entity):
    def __init__(self, _pos: Vector2):
        super().__init__(
            _pos=_pos,
            _type=EntityType.PLAYER,
            _size=PLAYER_SIZE,
            _speed=PLAYER_DEFAULT_SPEED_RANGE[0],
            _render_trail=True
        )
        self._gravity_point: Vector2 = _pos
        self._health = Slider(PLAYER_DEFAULT_MAX_HEALTH)
        self._regeneration_rate = PLAYER_DEFAULT_REGEN_RATE
        self._energy_decay_rate = PLAYER_DEFAULT_ENERGY_DECAY_RATE
        self._speed_range = PLAYER_DEFAULT_SPEED_RANGE
        self._level = 1
        self._energy = Slider(PLAYER_DEFAULT_MAX_ENERGY, PLAYER_STARTING_ENERGY)
        self._stats = Stats()
        self._shoot_cooldown = PLAYER_DEFAULT_SHOOT_COOLDOWN
        self._shoot_cooldown_timer = Timer(max_time=self._shoot_cooldown)
        self._damage = PLAYER_DEFAULT_DAMAGE_AVG
        self._damage_spread = PLAYER_DEFAULT_DAMAGE_SPREAD
        self.effect_flags = EffectFlags()

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        if not self._health.is_alive(): self.kill()

        # this t is a parameter that controls the speed of the player based on the distance from the gravity point
        # it is non-linear so that it's the player is not too slow when close to the gravity point
        towards_gravity_point = (self._gravity_point - self._pos)
        dist_to_gravity_point = towards_gravity_point.magnitude()
        t = (dist_to_gravity_point / 1500.) ** 0.4
        self._speed = self._speed_range[0] + (self._speed_range[1] - self._speed_range[0]) * t *\
            (OIL_SPILL_SPEED_MULTIPLIER if self.effect_flags.OIL_SPILL else 1.)

        # this code sets the velocity of the player towards the gravity point;
        # the closer the player is to the gravity point, the slower it moves to avoid dancing
        if dist_to_gravity_point > self._size * 1.5:
            self._vel = (towards_gravity_point).normalize() * self._speed
        else:
            self._vel = Vector2()
        self.health_energy_evolution(time_delta)
        self.effect_flags.reset()

    def health_energy_evolution(self, time_delta: float):
        # TODO decay enery when moving or regenerating health
        e_percent = self._energy.get_percent_full()
        h_percent = self._health.get_percent_full()
        # regenerate only if energy is not low:
        low_health_multiplier = 1. if h_percent > 0.3 else 2.
        # decay energy and regenerate health faster when health is low
        if e_percent > 0.: self._health.change(self._regeneration_rate * low_health_multiplier * time_delta) 
        self._energy.change(-self._energy_decay_rate * low_health_multiplier * time_delta)
        if self.effect_flags.OIL_SPILL:
            self._health.change(-OIL_SPILL_DAMAGE_PER_SECOND * time_delta)
        self._shoot_cooldown_timer.tick(time_delta)

    def is_on_cooldown(self) -> bool:
        return self._shoot_cooldown_timer.running()

    def shoot(self) -> Projectile:
        if self.is_on_cooldown():
            raise OnCooldown('on cooldown')
        if self._energy.get_value() < PLAYER_SHOT_COST:
            raise NotEnoughEnergy('not enough energy')
        if self._vel == Vector2():
            self._vel = self._gravity_point - self._pos
            if self._vel.magnitude_squared() == 0.:
                raise ShootingDirectionUndefined('direction undefined')
        self._energy.change(-PLAYER_SHOT_COST)
        direction = self._vel.normalize()
        self._stats.PROJECTILES_FIRED += 1
        self._shoot_cooldown_timer.reset(with_max_time=self._shoot_cooldown)
        return Projectile(
            _pos=self._pos.copy() + direction * self._size * 1.5,
            _vel=direction,
            _damage=random.uniform(self._damage - self._damage_spread, self._damage + self._damage_spread),
            _projectile_type=ProjectileType.PLAYER_BULLET,
            _speed=self._speed + PROJECTILE_DEFAULT_SPEED,
        )
    
    def new_level(self):
        self._level += 1
        print('new level:', self._level)
        self._speed_range = (PLAYER_DEFAULT_SPEED_RANGE[0], PLAYER_DEFAULT_SPEED_RANGE[1] + 130. * (self._level - 1))
        old_percentage = self._health.get_percent_full()
        self._health = Slider(PLAYER_DEFAULT_MAX_HEALTH + 10. * (self._level - 1)) # health keeps percentage full
        self._health.set_percent_full(old_percentage)
        self._energy = Slider(PLAYER_DEFAULT_MAX_ENERGY + 100. * (self._level - 1)) # energy sets to 60%
        self._energy.set_percent_full(0.6)
        self._shoot_cooldown = max(PLAYER_DEFAULT_SHOOT_COOLDOWN - 0.05 * (self._level - 1), 0.3)
        self._energy_decay_rate = PLAYER_DEFAULT_ENERGY_DECAY_RATE + 1.5 * (self._level - 1)
        self._damage = PLAYER_DEFAULT_DAMAGE_AVG + 5. * (self._level - 1)

    def set_gravity_point(self, gravity_point: Vector2):
        self._gravity_point = gravity_point
    
    def get_health(self) -> Slider: return self._health

    def get_energy(self) -> Slider: return self._energy
    
    def get_stats(self) -> Stats: return self._stats

    def get_level(self) -> int: return self._level

    def __repr__(self) -> str:
        def pretty_vector2(v: Vector2) -> str:
            return f'({v.x:.2f}, {v.y:.2f})'
        return f'Player(level={self._level}; pos={pretty_vector2(self._pos)}; vel={pretty_vector2(self._vel)}; speed={self._speed:.2f}; health={self._health}; cooldown={self._shoot_cooldown}; speed_range={self._speed_range}; gravity_point={pretty_vector2(self._gravity_point)}; stats={self._stats})'
    
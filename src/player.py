from dataclasses import dataclass
import random

from pygame import Vector2
from config.settings import Settings

from src.energy_orb import EnergyOrb
from src.entity import Entity
from src.enums import EntityType, ProjectileType
from src.exceptions import NotEnoughEnergy, OnCooldown, ShootingDirectionUndefined, ShieldRunning
from src.projectile import ExplosiveProjectile, Projectile
from src.utils import Stats, Slider, Timer

from config import (PLAYER_SIZE, PLAYER_DEFAULT_MAX_HEALTH, PLAYER_DEFAULT_SPEED_RANGE, PLAYER_DEFAULT_REGEN_RATE,
    OIL_SPILL_DAMAGE_PER_SECOND, OIL_SPILL_SPEED_MULTIPLIER, ENERGY_ORB_SPAWNED_BY_PLAYER_LIFETIME,
    PLAYER_SPAWN_ENERGY_ORB_COST, PLAYER_SPAWN_ENERGY_ORB_REQUIRED_ENERGY,
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


@dataclass
class Achievements:
    """
    Achievement flags.
    """
    KILL_BOSS_RICOCHET: bool = False


class Player(Entity):
    def __init__(self, pos: Vector2, settings: Settings):
        super().__init__(
            pos=pos,
            type=EntityType.PLAYER,
            size=PLAYER_SIZE,
            speed=PLAYER_DEFAULT_SPEED_RANGE[0],
            render_trail=True
        )
        self.level = 1
        self.settings = settings
        self.gravity_point: Vector2 = pos
        self.health = Slider(PLAYER_DEFAULT_MAX_HEALTH)
        self.regeneration_rate = PLAYER_DEFAULT_REGEN_RATE
        self.energy_decay_rate = PLAYER_DEFAULT_ENERGY_DECAY_RATE
        self.speed_range = PLAYER_DEFAULT_SPEED_RANGE
        self.energy = Slider(PLAYER_DEFAULT_MAX_ENERGY, PLAYER_STARTING_ENERGY)
        self.stats = Stats()
        self.shoot_cooldown = PLAYER_DEFAULT_SHOOT_COOLDOWN
        self.shoot_cooldown_timer = Timer(max_time=self.shoot_cooldown)
        self.damage = PLAYER_DEFAULT_DAMAGE_AVG
        self.damage_spread = PLAYER_DEFAULT_DAMAGE_SPREAD
        self.effect_flags = EffectFlags()
        self.achievements = Achievements()

        self.shield_duration_timer = Timer(max_time=5.)
        self.shield_duration_timer.turn_off()
        self.shield_cooldown_timer = Timer(max_time=20.)

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        if not self.health.is_alive(): self.kill()

        # this t is a parameter that controls the speed of the player based on the distance from the gravity point
        # it is non-linear so that it's the player is not too slow when close to the gravity point
        towards_gravity_point = (self.gravity_point - self.pos)
        dist_to_gravity_point = towards_gravity_point.magnitude()
        t = (dist_to_gravity_point / 1500.) ** 0.4
        self.speed = self.speed_range[0] + (self.speed_range[1] - self.speed_range[0]) * t *\
            (OIL_SPILL_SPEED_MULTIPLIER if self.effect_flags.OIL_SPILL else 1.)

        # this code sets the velocity of the player towards the gravity point;
        # the closer the player is to the gravity point, the slower it moves to avoid dancing
        if dist_to_gravity_point > self.size * 0.2:
            self.vel = (towards_gravity_point).normalize() * self.speed
        else:
            self.vel = Vector2()
            self.speed = 0.
        self.health_energy_evolution(time_delta)
        self.shield_duration_timer.tick(time_delta)
        self.shield_cooldown_timer.tick(time_delta)
        self.effect_flags.reset()

    def health_energy_evolution(self, time_delta: float):
        e_percent = self.energy.get_percent_full()
        h_percent = self.health.get_percent_full()

        # moving contributes 20% of the energy decay 
        energy_decay_rate_velocity = 0.8 * PLAYER_DEFAULT_ENERGY_DECAY_RATE * (self.vel.magnitude_squared() > 0.)
        # regenerating health contributes 80% of the energy decay
        if h_percent == 1.:
            energy_decay_rate_health = 0.
            low_health_multiplier = 1.
        elif h_percent > 0.4:
            energy_decay_rate_health = 0.8 * PLAYER_DEFAULT_ENERGY_DECAY_RATE
            low_health_multiplier = 1.
        else:
            # unless health is low
            # then it contributes 160% of the energy decay if energy is low and 240% if high
            low_health_multiplier = 2. if e_percent < 0.6 else 3.
            energy_decay_rate_health = 0.8 * PLAYER_DEFAULT_ENERGY_DECAY_RATE * low_health_multiplier

        # decay energy and regenerate health faster when health is low
        if e_percent > 0.: self.health.change(
            self.regeneration_rate * low_health_multiplier * time_delta
        )

        self.energy.change(
            -(energy_decay_rate_velocity + energy_decay_rate_health) * time_delta
        )

        # other effects
        if self.effect_flags.OIL_SPILL:
            self.health.change(-OIL_SPILL_DAMAGE_PER_SECOND * time_delta)
            self.get_stats().OIL_SPILL_TIME_SPENT += time_delta
        self.shoot_cooldown_timer.tick(time_delta)

    def is_on_cooldown(self) -> bool:
        return self.shoot_cooldown_timer.running()

    def shoot(self) -> Projectile:
        if self.is_on_cooldown():
            raise OnCooldown('on cooldown')
        if self.energy.get_value() < PLAYER_SHOT_COST:
            raise NotEnoughEnergy('not enough energy')
        if self.vel == Vector2():
            self.vel = self.gravity_point - self.pos
            if self.vel.magnitude_squared() == 0.:
                raise ShootingDirectionUndefined('direction undefined')
        self.energy.change(-PLAYER_SHOT_COST)
        self.shoot_cooldown_timer.reset(with_max_time=self.shoot_cooldown)
        self.stats.PROJECTILES_FIRED += 1
        direction = self.vel.normalize()
        return Projectile(
            pos=self.pos.copy() + direction * self.size * 1.5,
            vel=direction,
            damage=self.damage + self.damage_spread * random.uniform(-1, 1),
            projectile_type=ProjectileType.PLAYER_BULLET,
            speed=self.speed + PROJECTILE_DEFAULT_SPEED,
        )

    def spawn_energy_orb(self) -> EnergyOrb:
        if self.energy.get_value() < PLAYER_SPAWN_ENERGY_ORB_REQUIRED_ENERGY:
            raise NotEnoughEnergy(f'energy lower than {PLAYER_SPAWN_ENERGY_ORB_REQUIRED_ENERGY}')
        self.energy.change(-PLAYER_SPAWN_ENERGY_ORB_COST)
        self.stats.ENERGY_ORBS_SPAWNED += 1
        return EnergyOrb(
            pos=self.gravity_point,
            energy=PLAYER_SPAWN_ENERGY_ORB_COST,
            lifetime=ENERGY_ORB_SPAWNED_BY_PLAYER_LIFETIME,
            spawned_by_player=True
        )

    def shield_on(self):
        if self.energy.get_value() < 300.:
            raise NotEnoughEnergy('not enough energy for shield')
        if self.is_shield_on():
            raise ShieldRunning('shield already running')
        if self.shield_cooldown_timer.running():
            raise OnCooldown('shield on cooldown')
        self.energy.change(-300.)
        self.shield_duration_timer.reset(with_max_time=5.)
        self.shield_cooldown_timer.reset()

    def ultimate_ability(self):
        # TODO: implement different ultimates
        self.shield_on()
    
    def new_level(self):
        self.level += 1
        self.speed_range = (PLAYER_DEFAULT_SPEED_RANGE[0], PLAYER_DEFAULT_SPEED_RANGE[1] + 150. * (self.level - 1))
        old_percentage = self.health.get_percent_full()
        self.health = Slider(PLAYER_DEFAULT_MAX_HEALTH + 10. * (self.level - 1)) # health keeps percentage full
        self.health.set_percent_full(old_percentage)
        self.energy = Slider(PLAYER_DEFAULT_MAX_ENERGY + 100. * (self.level - 1))
        self.energy.set_percent_full(0.6) # energy sets to 60%
        self.shoot_cooldown = max(PLAYER_DEFAULT_SHOOT_COOLDOWN - 0.05 * (self.level - 1), 0.2)
        self.energy_decay_rate = PLAYER_DEFAULT_ENERGY_DECAY_RATE + 1.5 * (self.level - 1)
        self.damage = PLAYER_DEFAULT_DAMAGE_AVG + 10. * (self.level - 1)

    def set_gravity_point(self, gravity_point: Vector2):
        self.gravity_point = gravity_point
    
    def get_health(self) -> Slider: return self.health

    def get_energy(self) -> Slider: return self.energy
    
    def get_stats(self) -> Stats: return self.stats

    def get_achievements(self) -> Achievements: return self.achievements

    def get_level(self) -> int: return self.level

    def get_gravity_point(self) -> Vector2: return self.gravity_point

    def is_shield_on(self) -> bool: return self.shield_duration_timer.running()

    def __repr__(self) -> str:
        def pretty_vector2(v: Vector2) -> str:
            return f'({v.x:.2f}, {v.y:.2f})'
        return f'Player(level={self.level}; pos={pretty_vector2(self.pos)}; vel={pretty_vector2(self.vel)}; speed={self.speed:.2f}; health={self.health}; cooldown={self.shoot_cooldown}; speed_range={self.speed_range}; gravity_point={pretty_vector2(self.gravity_point)}; stats={self.stats}; achievements={self.achievements})'
    
import random

from pygame import Vector2, Color
from config.settings import Settings
from front.sounds import play_sfx
from src.misc.artifacts import ArtifactsHandler, Artifact, Rage
from src.entities.artifact_chest import ArtifactChestGenerator

from src.entities.entity import Entity
from src.utils.enums import ArtifactType, EntityType, ProjectileType
from src.utils.exceptions import ArtifactMissing, NotEnoughEnergy, OnCooldown, ShootingDirectionUndefined, ArtifactCollected
from src.entities.projectile import Projectile
from src.utils.utils import Slider, Timer
from src.utils.player_utils import Stats, Achievements, EffectFlags

from config import (PLAYER_SIZE, PLAYER_DEFAULT_MAX_HEALTH, PLAYER_DEFAULT_SPEED_RANGE, PLAYER_DEFAULT_REGEN_RATE,
    OIL_SPILL_DAMAGE_PER_SECOND, OIL_SPILL_SPEED_MULTIPLIER, PLAYER_INVULNERABILITY_TIME, PLAYER_SPEED_INCREASE,
    PLAYER_DEFAULT_ENERGY_DECAY_RATE, PLAYER_DEFAULT_SHOOT_COOLDOWN, PLAYER_DEFAULT_DAMAGE_AVG, PLAYER_DEFAULT_DAMAGE_SPREAD,
    PLAYER_DEFAULT_MAX_ENERGY, PLAYER_STARTING_ENERGY, PROJECTILE_DEFAULT_SPEED, PLAYER_SHOT_COST, PLAYER_EXTRA_BULLET_SHOT_MULT,
    NICER_GREEN_HEX, PLAYER_DEFAULT_MAX_EXTRA_BULLETS, PLAYER_ENERGY_INCREASE,
)


WHITE = Color('white')
NICER_GREEN = Color(NICER_GREEN_HEX)


class Player(Entity):
    def __init__(self, pos: Vector2, settings: Settings):
        super().__init__(
            pos=pos,
            type=EntityType.PLAYER,
            size=PLAYER_SIZE,
            speed=PLAYER_DEFAULT_SPEED_RANGE[0],
            render_trail=True,
            can_spawn_entities=True
        )
        self._id = 0
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
        self.invulnerability_timer = Timer(max_time=PLAYER_INVULNERABILITY_TIME)
        self.damage = PLAYER_DEFAULT_DAMAGE_AVG
        self.damage_spread = PLAYER_DEFAULT_DAMAGE_SPREAD
        self.effect_flags = EffectFlags()
        self.achievements = Achievements()
        self.artifacts_handler = ArtifactsHandler(player=self)
        self.artifacts_generator = ArtifactChestGenerator(self)
        self.boosts = self.artifacts_handler.get_total_stats_boost()
        self.max_extra_bullets = PLAYER_DEFAULT_MAX_EXTRA_BULLETS + self.boosts.add_max_extra_bullets

        self.dash_needs_processing = False
        self.extra_bullets = 0

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        if not self.health.is_alive(): self.kill()
        self.boosts = self.artifacts_handler.get_total_stats_boost()
        self.max_extra_bullets = PLAYER_DEFAULT_MAX_EXTRA_BULLETS + self.boosts.add_max_extra_bullets

        self.speed_velocity_evolution()
        self.health_energy_evolution(time_delta)
        self.shoot_cooldown_timer.tick(time_delta)
        self.invulnerability_timer.tick(time_delta)
        self.artifacts_handler.update(time_delta)
        self.effect_flags.reset()
    
    def add_extra_bullets(self, num_to_add: int) -> int:
        """Returns the number of extra bullets that were actually added."""
        curr = self.extra_bullets
        self.extra_bullets += num_to_add
        self.extra_bullets = min(self.extra_bullets, self.max_extra_bullets)
        return self.extra_bullets - curr
    
    def speed_velocity_evolution(self):
        towards_gravity_point = (self.gravity_point - self.pos)
        dist_to_gravity_point = towards_gravity_point.magnitude()
        t = (dist_to_gravity_point / 1500.) ** 0.8
        self.speed = (self.speed_range[0] + (self.get_max_speed() - self.speed_range[0]) * t * self.effect_flags.SLOWNESS)
        if dist_to_gravity_point > self.get_size() * 0.2:
            self.vel = (towards_gravity_point).normalize() * self.speed
        else:
            self.vel = Vector2()
            self.speed = 0.

    def health_energy_evolution(self, time_delta: float):
        e_percent = self.energy.get_percent_full()
        h_percent = self.health.get_percent_full()
        # moving contributes 20% of the energy decay 
        energy_decay_rate_velocity = 0.2 * PLAYER_DEFAULT_ENERGY_DECAY_RATE * (self.vel.magnitude_squared() > 0.)
        # regenerating health contributes 80% of the energy decay
        if h_percent == 1.:
            energy_decay_rate_health = 0.
            low_health_multiplier = 1.
        elif h_percent > 0.4:
            low_health_multiplier = 1. if e_percent < 0.8 else 2.
            energy_decay_rate_health = 0.8 * PLAYER_DEFAULT_ENERGY_DECAY_RATE * (low_health_multiplier + 2.5)
        else:
            # unless health is low
            # then it depends on the energy levels
            low_health_multiplier = 1.5 if e_percent < 0.6 else 2.5
            energy_decay_rate_health = 0.8 * PLAYER_DEFAULT_ENERGY_DECAY_RATE * (low_health_multiplier + 2.5)
        # decay energy and regenerate health faster when health is low
        if e_percent > 0.: self.health.change(self.get_regen() * low_health_multiplier * time_delta)
        self.energy.change(
            -(energy_decay_rate_velocity + energy_decay_rate_health) * time_delta
        )
        # other effects
        if self.effect_flags.OIL_SPILL:
            oil_spill_damage_per_sec = OIL_SPILL_DAMAGE_PER_SECOND * (self.settings.difficulty > 3)
            oil_spill_damage_dealt = -self.health.change(-oil_spill_damage_per_sec * time_delta)
            self.get_stats().OIL_SPILL_TIME_SPENT += time_delta
            self.get_stats().DAMAGE_TAKEN += oil_spill_damage_dealt

    def is_on_cooldown(self) -> bool:
        return self.shoot_cooldown_timer.running()

    def shoot(self):
        used_extra_bullet = False
        if self.is_on_cooldown():
            if self.extra_bullets > 0:
                if self.energy.get_value() < PLAYER_SHOT_COST * PLAYER_EXTRA_BULLET_SHOT_MULT:
                    raise NotEnoughEnergy('not enough energy for extra')
                self.extra_bullets -= 1
                used_extra_bullet = True
            else:
                raise OnCooldown('on cooldown')
        if self.energy.get_value() < PLAYER_SHOT_COST:
            raise NotEnoughEnergy('not enough energy')
        if self.vel == Vector2():
            self.vel = self.gravity_point - self.pos
            if self.vel.magnitude_squared() == 0.:
                raise ShootingDirectionUndefined('direction undefined')
        self.energy.change(-PLAYER_SHOT_COST * (PLAYER_EXTRA_BULLET_SHOT_MULT if used_extra_bullet else 1.))
        self.shoot_cooldown_timer.reset(with_max_time=self.get_shoot_coolodown())
        self.get_stats().PROJECTILES_FIRED += 1
        direction = self.vel.normalize()
        assert self.i_can_spawn_entities
        self.i_can_spawn_entities.add(self.get_projectile(direction))

    def get_projectile(self, direction: Vector2) -> Projectile:
        return Projectile(
            pos=self.pos.copy() + direction * self.get_size() * 1.5,
            vel=direction,
            damage=self.get_damage() + self.damage_spread * random.uniform(-1, 1),
            projectile_type=ProjectileType.PLAYER_BULLET,
            speed=self.speed + PROJECTILE_DEFAULT_SPEED,
        )

    def ultimate_ability(self, artifact_type: ArtifactType):
        if artifact_type == ArtifactType.BULLET_SHIELD:
            self.artifacts_handler.get_bullet_shield().turn_on()
            self.get_stats().BULLET_SHIELDS_ACTIVATED += 1
            play_sfx('bullet_shield_on')
            return
        if artifact_type == ArtifactType.MINE_SPAWN:
            self.artifacts_handler.get_mine_spawn().spawn()
            self.get_stats().MINES_PLANTED += 1
            play_sfx('mine_planted')
            return
        if artifact_type == ArtifactType.DASH:
            self.artifacts_handler.get_dash().dash(self.gravity_point)
            self.dash_needs_processing = True
            self.get_stats().DASHES_ACTIVATED += 1
            play_sfx('player_dash')
            return
        if artifact_type == ArtifactType.TIME_STOP:
            self.artifacts_handler.get_time_stop().time_stop()
            self.get_stats().TIME_STOPS_ACTIVATED += 1
            play_sfx('time_stop')
            return
        if artifact_type == ArtifactType.SHRAPNEL:
            self.artifacts_handler.get_shrapnel().shoot()
            # self.get_stats().SHRAPNELS_ACTIVATED += 1
            # play_sfx('shrapnel')
            return
        if artifact_type == ArtifactType.RAGE:
            self.artifacts_handler.get_rage().rage()
            # TODO
            # self.get_stats().RAGES_ACTIVATED += 1
            # play_sfx('rage')
            return
        raise ArtifactMissing(f'artifact missing for {artifact_type.name.title()}')
    
    def add_artifact(self, artifact: Artifact):
        is_successful = self.artifacts_generator.check_artifact(artifact)
        if not is_successful:
            raise ArtifactCollected(f'artifact {artifact} already collected')
        self.artifacts_handler.add_artifact(artifact)
    
    def new_level(self):
        self.level += 1
        self.speed_range = (PLAYER_DEFAULT_SPEED_RANGE[0], PLAYER_DEFAULT_SPEED_RANGE[1] + 
            PLAYER_SPEED_INCREASE * (self.level - 1))
        old_percentage_health = self.health.get_percent_full()
        self.health = Slider(PLAYER_DEFAULT_MAX_HEALTH + 10. * (self.level - 1)) # health keeps percentage full
        self.health.set_percent_full(old_percentage_health)
        self.regeneration_rate = PLAYER_DEFAULT_REGEN_RATE + 0.08 * (self.level - 1)
        old_percentage_energy = self.energy.get_percent_full()
        self.energy = Slider(PLAYER_DEFAULT_MAX_ENERGY + PLAYER_ENERGY_INCREASE * (self.level - 1))
        self.energy.set_percent_full(old_percentage_energy)
        self.shoot_cooldown = max(PLAYER_DEFAULT_SHOOT_COOLDOWN - 0.05 * (self.level - 1), 0.25)
        self.energy_decay_rate = PLAYER_DEFAULT_ENERGY_DECAY_RATE + 1.5 * (self.level - 1)
        self.damage = PLAYER_DEFAULT_DAMAGE_AVG + 15. * (self.level - 1)

    def set_gravity_point(self, gravity_point: Vector2):
        self.gravity_point = gravity_point
    
    def get_health(self) -> Slider: return self.health

    def get_energy(self) -> Slider: return self.energy

    def get_damage(self) -> float: return self.damage + self.boosts.damage

    def get_regen(self) -> float: return self.regeneration_rate + self.boosts.regen

    def get_shoot_coolodown(self) -> float: return max(self.shoot_cooldown - self.boosts.cooldown, 0.2)

    def get_size(self) -> float: return self.size - self.boosts.size

    def get_max_speed(self) -> float: return self.speed_range[1] + self.boosts.speed
    
    def get_stats(self) -> Stats: return self.stats

    def get_achievements(self) -> Achievements: return self.achievements

    def get_level(self) -> int: return self.level

    def get_gravity_point(self) -> Vector2: return self.gravity_point

    def set_pos(self, set_to: Vector2) -> None: self.pos = set_to

    def __repr__(self) -> str:
        def pretty_vector2(v: Vector2) -> str:
            return f'({v.x:.2f}, {v.y:.2f})'
        return f'Player(level={self.level}; pos={pretty_vector2(self.pos)}; vel={pretty_vector2(self.vel)}; speed={self.speed:.2f}; health={self.health}; cooldown={self.shoot_cooldown}; speed_range={self.speed_range}; gravity_point={pretty_vector2(self.gravity_point)}; stats={self.stats}; achievements={self.achievements})'
    
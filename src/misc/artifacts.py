from abc import ABC, abstractmethod
from dataclasses import dataclass
import random

from pygame import Vector2
from config.back import PROJECTILE_DEFAULT_SPEED

from src.entities.entity import Entity
from src.entities.mine import Mine
from src.entities.projectile import Projectile
from src.utils.enums import ArtifactType, ProjectileType
from src.utils.exceptions import (
    NotEnoughEnergy,
    OnCooldown,
    ShieldRunning,
    ArtifactMissing,
    TimeStopRunning,
)
from src.utils.utils import Timer, random_unit_vector
from config import (
    BULLET_SHIELD_SIZE,
    BULLET_SHIELD_COOLDOWN,
    BULLET_SHIELD_DURATION,
    BULLET_SHIELD_COST,
    MINE_COOLDOWN,
    MINE_COST,
    MINE_DEFAULT_DAMAGE,
    TIME_STOP_DEFAULT_DURATION,
    TIME_STOP_COOLDOWN,
    TIME_STOP_COST,
    DASH_COOLDOWN,
    DASH_COST,
    SHRAPNEL_COOLDOWN,
    SHRAPNEL_COST,
)


@dataclass(frozen=True)
class StatsBoost:
    health: float = 0.0
    regen: float = 0.0
    damage: float = 0.0
    speed: float = 0.0
    cooldown: float = 0.0
    size: float = 0.0
    bullet_shield_size: float = 0.0
    bullet_shield_duration: float = 0.0
    mine_cooldown: float = 0.0
    add_max_extra_bullets: int = 0
    time_stop_duration: float = 0.0
    shrapnel_extra_shards: int = 0
    shrapnel_cooldown: float = 0.0

    def __iter__(self):
        yield from (
            self.health,
            self.regen,
            self.damage,
            self.speed,
            self.cooldown,
            self.size,
            self.bullet_shield_size,
            self.bullet_shield_duration,
            self.mine_cooldown,
            self.add_max_extra_bullets,
            self.time_stop_duration,
            self.shrapnel_extra_shards,
            self.shrapnel_cooldown,
        )

    def __str__(self) -> str:
        formats = (
            "+{:.0f}hp",
            "+{:.1f}reg",
            "+{:.0f}dmg",
            "+{:.0f}spd",
            "-{:.2f}cd",
            "-{:.0f}size",
            "+{:.0f}shld size",
            "+{:.0f}shld dur",
            "-{:.0f}mine cd",
            "+{}max eb",
            "+{:.0f}ts dur",
            "+{}shrapnel shards",
            "-{:.0f}shrapnel cd",
        )
        res = "|".join(
            format_.format(val)
            for format_, val in zip(formats, self, strict=True)
            if val
        )
        return res if res else "no boosts"

    def __add__(self, other: "StatsBoost"):
        return StatsBoost(
            health=self.health + other.health,
            regen=self.regen + other.regen,
            damage=self.damage + other.damage,
            speed=self.speed + other.speed,
            cooldown=self.cooldown + other.cooldown,
            size=self.size + other.size,
            bullet_shield_size=self.bullet_shield_size + other.bullet_shield_size,
            bullet_shield_duration=self.bullet_shield_duration
            + other.bullet_shield_duration,
            mine_cooldown=self.mine_cooldown + other.mine_cooldown,
            add_max_extra_bullets=self.add_max_extra_bullets
            + other.add_max_extra_bullets,
            time_stop_duration=self.time_stop_duration + other.time_stop_duration,
            shrapnel_extra_shards=self.shrapnel_extra_shards
            + other.shrapnel_extra_shards,
            shrapnel_cooldown=self.shrapnel_cooldown + other.shrapnel_cooldown,
        )


class Artifact(ABC):
    def __init__(
        self, artifact_type: ArtifactType, player, cooldown: float, cost: float
    ):
        self.artifact_type = artifact_type
        self.player = player
        if self.player:
            self.total_stats_boost: StatsBoost = self.player.boosts
        self.cooldown = cooldown
        self.cooldown_timer = Timer(max_time=self.cooldown)
        self.cooldown_timer.set_percent_full(0.5)
        self.cost = cost

    def update(self, time_delta: float):
        if self.player:
            self.total_stats_boost: StatsBoost = self.player.boosts
        self.cooldown_timer.tick(time_delta)

    def __str__(self) -> str:
        return "Artifact::" + self.__class__.__name__

    @abstractmethod
    def get_short_string(self) -> str:
        raise NotImplementedError(f"{self} doesn't implement get_short_string()")

    @abstractmethod
    def get_verbose_string(self) -> str:
        raise NotImplementedError(f"{self} doesn't implement get_verbose_string()")

    @staticmethod
    def get_artifact_type() -> ArtifactType:
        raise NotImplementedError(
            "This artifact doesn't implement get_artifact_type()"
        )


class BulletShield(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.BULLET_SHIELD,
            player=player,
            cooldown=BULLET_SHIELD_COOLDOWN,
            cost=BULLET_SHIELD_COST,
        )
        self.duration = (
            BULLET_SHIELD_DURATION + self.total_stats_boost.bullet_shield_duration
        )
        self.duration_timer = Timer(max_time=self.duration)
        self.duration_timer.turn_off()

    @staticmethod
    def get_artifact_type():
        return ArtifactType.BULLET_SHIELD

    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration = (
            BULLET_SHIELD_DURATION + self.total_stats_boost.bullet_shield_duration
        )
        self.duration_timer.tick(time_delta)

    def is_on(self) -> bool:
        return self.duration_timer.running()

    def turn_on(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for shield")
        if self.is_on():
            raise ShieldRunning("shield already running")
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"shield on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )
        self.player.energy.change(-self.cost)
        self.duration_timer.reset(self.duration)
        self.cooldown_timer.reset()

    def get_size(self) -> float:
        return BULLET_SHIELD_SIZE + self.total_stats_boost.bullet_shield_size

    def point_inside_shield(self, pos: Vector2) -> bool:
        return (
            self.is_on()
            and (pos - self.player.pos).magnitude_squared() < self.get_size() ** 2
        )

    def get_short_string(self):
        return "Shield"

    def get_verbose_string(self) -> str:
        return f"Shield({self.duration:.0f}dur {self.get_size():.0f}size)"


class MineSpawn(Artifact):
    def __init__(self, player):
        # TODO: __future__ import annotations and add type hinting for player
        super().__init__(
            artifact_type=ArtifactType.MINE_SPAWN,
            player=player,
            cooldown=MINE_COOLDOWN,
            cost=MINE_COST,
        )

    def update(self, time_delta: float):
        super().update(time_delta)
        self.cooldown = MINE_COOLDOWN - self.total_stats_boost.mine_cooldown

    @staticmethod
    def get_artifact_type():
        return ArtifactType.MINE_SPAWN

    def spawn(self):
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"mine spawner on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for a mine")
        self.player.energy.change(-self.cost)
        vel: Vector2 = self.player.get_vel() + random_unit_vector()
        vel.scale_to_length(20.0)
        pos: Vector2 = self.player.get_pos()
        self.player.i_can_spawn_entities.add(
            Mine(
                pos=pos - vel,
                damage=MINE_DEFAULT_DAMAGE + 20.0 * (self.player.level - 1),
            )
        )
        self.cooldown_timer.reset(self.cooldown)

    def get_short_string(self):
        return "Mine"

    def get_verbose_string(self):
        return f"MineSpawn({self.cooldown:.0f}cd)"


class Dash(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.DASH,
            player=player,
            cooldown=DASH_COOLDOWN,
            cost=DASH_COST,
        )
        self.dash_path_history: list[tuple[Vector2, Vector2]] = []
        self.path_animation_lingering_timer = Timer(max_time=0.8)
        self.path_animation_lingering_timer.turn_off()

    def update(self, time_delta: float):
        super().update(time_delta)
        self.path_animation_lingering_timer.tick(time_delta)

    @staticmethod
    def get_artifact_type():
        return ArtifactType.DASH

    def get_short_string(self) -> str:
        return "Dash"

    def get_verbose_string(self) -> str:
        return "Dash"

    def dash(self, pos_dash_to: Vector2):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for dash")
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"dash on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )

        self.dash_path_history.append((self.player.get_pos(), pos_dash_to.copy()))
        self.player.energy.change(-self.cost)
        self.cooldown_timer.reset()
        self.path_animation_lingering_timer.reset()
        self.player.set_pos(pos_dash_to)

    def dash_path_intersects_enemy(self, enemy: Entity) -> bool:
        """Checks if the enemy is affected by the dash.
        Should be called only after self.dash is called."""
        # check if the line segment a->b intersects the circle c_r
        c = enemy.get_pos()
        r = enemy.get_size()
        a, b = self.dash_path_history[-1]
        d = b - a
        f = a - c
        # quadratic equation coefficients
        a_ = d.dot(d)
        b_ = 2 * f.dot(d)
        c_ = f.dot(f) - r**2
        discriminant = b_**2 - 4 * a_ * c_
        return discriminant >= 0


class TimeStop(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.TIME_STOP,
            player=player,
            cooldown=TIME_STOP_COOLDOWN,
            cost=TIME_STOP_COST,
        )
        self.duration = (
            TIME_STOP_DEFAULT_DURATION + self.total_stats_boost.time_stop_duration
        )
        self.duration_timer = Timer(max_time=self.duration)
        self.duration_timer.turn_off()

    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration = (
            TIME_STOP_DEFAULT_DURATION + self.total_stats_boost.time_stop_duration
        )
        self.duration_timer.tick(time_delta)

    @staticmethod
    def get_artifact_type():
        return ArtifactType.TIME_STOP

    def get_short_string(self) -> str:
        return "Time Stop"

    def get_verbose_string(self) -> str:
        return f"TimeStop({self.duration:.0f}dur)"

    def time_stop(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for time stop")
        if self.is_on():
            raise TimeStopRunning("time stop already running")
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"time stop on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )
        self.player.energy.change(-self.cost)
        self.duration_timer.reset(self.duration)
        self.cooldown_timer.reset()

    def is_on(self) -> bool:
        return self.duration_timer.running()


class Shrapnel(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.SHRAPNEL,
            player=player,
            cooldown=SHRAPNEL_COOLDOWN,
            cost=SHRAPNEL_COST,
        )
        self.num_shards = 4 + self.total_stats_boost.shrapnel_extra_shards

    def update(self, time_delta: float):
        super().update(time_delta)
        self.num_shards = 4 + self.total_stats_boost.shrapnel_extra_shards
        self.cooldown = SHRAPNEL_COOLDOWN - self.total_stats_boost.shrapnel_cooldown

    def shoot(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for shrapnel")
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"shrapnel on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )
        self.player.energy.change(-self.cost)
        self.cooldown_timer.reset(self.cooldown)
        direction: Vector2 = (
            self.player.gravity_point - self.player.get_pos()
        ).normalize()
        for _ in range(self.num_shards + 2 * self.player.extra_bullets):
            direction_ = direction.rotate(random.uniform(-9, 9))
            self.player.i_can_spawn_entities.add(
                Projectile(
                    pos=self.player.get_pos()
                    + direction_ * self.player.get_size() * 1.5,
                    vel=direction_,
                    projectile_type=ProjectileType.PLAYER_BULLET,
                    damage=self.player.get_damage() * 0.3,
                    lifetime=1.5,
                    speed=self.player.speed + PROJECTILE_DEFAULT_SPEED,
                )
            )
        self.player.get_stats().PROJECTILES_FIRED += (
            self.num_shards + self.player.extra_bullets
        )
        self.player.extra_bullets = 0

    @staticmethod
    def get_artifact_type():
        return ArtifactType.SHRAPNEL

    def get_short_string(self) -> str:
        return "Shrapnel"

    def get_verbose_string(self) -> str:
        return f"Shrapnel({self.num_shards}shards {self.cooldown:.0f}cd)"


class Rage(Artifact):
    def __init__(self, player, cooldown=35, cost=300):
        super().__init__(ArtifactType.RAGE, player, cooldown, cost)
        self.duration = 8
        self.duration_timer = Timer(max_time=self.duration)
        self.duration_timer.turn_off()

    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration_timer.tick(time_delta)
        if self.duration_timer.running():
            self.player.boosts += StatsBoost(damage=15, speed=1500, cooldown=1)
            self.player.health.change(-6 * time_delta)
            # TODO: make this count towards the player's stats
            # and affect the reason of death

    def rage(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy("not enough energy for rage")
        if self.cooldown_timer.running():
            raise OnCooldown(
                f"rage on cooldown: {self.cooldown_timer.get_time_left():.1f}"
            )
        self.player.energy.change(-self.cost)
        self.duration_timer.reset(self.duration)
        self.cooldown_timer.reset()

    def is_on(self) -> bool:
        return self.duration_timer.running()

    def get_short_string(self) -> str:
        return "Rage"

    def get_verbose_string(self) -> str:
        return f"Rage({self.duration:.0f}dur)"


class InactiveArtifact(Artifact):
    def __init__(self, stats_boost: StatsBoost):
        super().__init__(
            artifact_type=ArtifactType.STATS, player=None, cooldown=0, cost=0
        )
        self.stats_boost = stats_boost

    def update(self, time_delta: float):
        ...

    def __repr__(self) -> str:
        return f"InactiveArtifact({self.stats_boost})"

    def get_short_string(self) -> str:
        return "Stats"

    def get_verbose_string(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"[{self.stats_boost}]"


class ArtifactsHandler:
    def __init__(self, player):
        self.player = player
        self.inactive_artifacts: list[InactiveArtifact] = []

        self.bullet_shield: BulletShield | None = None
        self.mine_spawn: MineSpawn | None = None
        self.dash: Dash | None = None
        self.time_stop: TimeStop | None = None
        self.shrapnel: Shrapnel | None = None
        self.rage: Rage | None = None

    def get_total_stats_boost(self) -> StatsBoost:
        return sum(
            (artifact.stats_boost for artifact in self.inactive_artifacts), StatsBoost()
        )

    def update(self, time_delta: float):
        for artifact in self.iterate_active():
            artifact.update(time_delta)

    def iterate_active(self):
        if self.bullet_shield is not None:
            yield self.bullet_shield
        if self.mine_spawn is not None:
            yield self.mine_spawn
        if self.dash is not None:
            yield self.dash
        if self.time_stop is not None:
            yield self.time_stop
        if self.shrapnel is not None:
            yield self.shrapnel
        if self.rage is not None:
            yield self.rage

    def add_artifact(self, artifact: Artifact):
        if isinstance(artifact, InactiveArtifact):
            self.inactive_artifacts.append(artifact)
        elif isinstance(artifact, BulletShield):
            self.bullet_shield = artifact
        elif isinstance(artifact, MineSpawn):
            self.mine_spawn = artifact
        elif isinstance(artifact, Dash):
            self.dash = artifact
        elif isinstance(artifact, TimeStop):
            self.time_stop = artifact
        elif isinstance(artifact, Shrapnel):
            self.shrapnel = artifact
        elif isinstance(artifact, Rage):
            self.rage = artifact
        else:
            raise NotImplementedError(
                f"unknown artifact type: {artifact.artifact_type}"
            )

    def is_present(self, artifact_type: ArtifactType) -> bool:
        if artifact_type == ArtifactType.BULLET_SHIELD:
            return self.bullet_shield is not None
        elif artifact_type == ArtifactType.MINE_SPAWN:
            return self.mine_spawn is not None
        elif artifact_type == ArtifactType.DASH:
            return self.dash is not None
        elif artifact_type == ArtifactType.TIME_STOP:
            return self.time_stop is not None
        elif artifact_type == ArtifactType.SHRAPNEL:
            return self.shrapnel is not None
        elif artifact_type == ArtifactType.RAGE:
            return self.rage is not None
        else:
            raise NotImplementedError(f"unknown artifact type: {artifact_type}")

    def get_bullet_shield(self) -> BulletShield:
        if self.bullet_shield is None:
            raise ArtifactMissing("[?] bullet shield is missing")
        return self.bullet_shield

    def get_mine_spawn(self) -> MineSpawn:
        if self.mine_spawn is None:
            raise ArtifactMissing("[?] mine spawn is missing")
        return self.mine_spawn

    def get_dash(self) -> Dash:
        if self.dash is None:
            raise ArtifactMissing("[?] dash is missing")
        return self.dash

    def get_time_stop(self) -> TimeStop:
        if self.time_stop is None:
            raise ArtifactMissing("[?] time stop is missing")
        return self.time_stop

    def get_shrapnel(self) -> Shrapnel:
        if self.shrapnel is None:
            raise ArtifactMissing("[?] shrapnel is missing")
        return self.shrapnel

    def get_rage(self) -> Rage:
        if self.rage is None:
            raise ArtifactMissing("[?] rage is missing")
        return self.rage

    def __repr__(self) -> str:
        active_artivacts = " | ".join(map(str, self.iterate_active()))
        return f"ArtifactsHandler({active_artivacts}; {self.inactive_artifacts})"

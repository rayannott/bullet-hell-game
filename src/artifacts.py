from abc import ABC, abstractmethod
from dataclasses import dataclass

from pygame import Vector2

from src.entity import Mine
from src.enums import ArtifactType
from src.exceptions import DashRunning, NotEnoughEnergy, OnCooldown, ShieldRunning, ArtifactMissing
from src.utils import Timer, random_unit_vector
from config import (ARTIFACT_SHIELD_SIZE, ARTIFACT_SHIELD_COOLDOWN,
    ARTIFACT_SHIELD_DURATION, ARTIFACT_SHIELD_COST, MINE_COOLDOWN, MINE_COST, MINE_DEFAULT_DAMAGE
)


@dataclass(frozen=True)
class StatsBoost:
    health: float = 0.
    regen: float = 0.
    damage: float = 0.
    speed: float = 0.
    cooldown: float = 0.
    size: float = 0.
    bullet_shield_size: float = 0.
    bullet_shield_duration: float = 0.
    mine_cooldown: float = 0.
    add_max_extra_bullets: int = 0

    def __iter__(self):
        yield from (self.health, self.regen, self.damage,
            self.speed, self.cooldown, self.size, self.bullet_shield_size, 
            self.bullet_shield_duration, self.mine_cooldown, self.add_max_extra_bullets)

    def __str__(self) -> str:
        formats = ('+{:.0f}hp', '+{:.1f}reg', '+{:.0f}dmg', 
            '+{:.0f}spd', '-{:.2f}cd', '-{:.0f}size', 
            '+{:.0f}shld size', '+{:.1f}shld dur', '-{:.1f}mine cd', '+{}max eb')
        res = '|'.join(
            format_.format(val) for format_, val in zip(formats, self, strict=True) if val
        )
        return res if res else 'no-boosts'

    def __add__(self, other: 'StatsBoost'):
        return StatsBoost(
            health=self.health + other.health,
            regen=self.regen + other.regen,
            damage=self.damage + other.damage,
            speed=self.speed + other.speed,
            cooldown=self.cooldown + other.cooldown,
            size=self.size + other.size,
            bullet_shield_size=self.bullet_shield_size + other.bullet_shield_size,
            bullet_shield_duration=self.bullet_shield_duration + other.bullet_shield_duration,
            mine_cooldown=self.mine_cooldown + other.mine_cooldown,
            add_max_extra_bullets=self.add_max_extra_bullets + other.add_max_extra_bullets,
        )


class Artifact(ABC):
    def __init__(self,
        artifact_type: ArtifactType,
        player,
        cooldown: float,
        cost: float
    ):
        self.artifact_type = artifact_type
        self.player = player
        if player:
            self.total_stats_boost: StatsBoost = player.boosts
        self.cooldown = cooldown
        self.cooldown_timer = Timer(max_time=self.cooldown)
        self.cooldown_timer.set_percent_full(0.5)
        self.cost = cost

    def update(self, time_delta: float):
        self.cooldown_timer.tick(time_delta)
    
    def __str__(self) -> str:
        return 'Artifact::' + self.__class__.__name__
    
    @abstractmethod
    def get_short_string(self) -> str:
        raise NotImplementedError(f'{self} doesn\'t implement get_short_string()')

    @staticmethod
    def get_artifact_type() -> ArtifactType:
        raise NotImplementedError(f'This artifact doesn\'t implement get_artifact_type()')


class BulletShield(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.BULLET_SHIELD, 
            player=player,
            cooldown=ARTIFACT_SHIELD_COOLDOWN,
            cost=ARTIFACT_SHIELD_COST
        )
        self.duration_timer = Timer(max_time=ARTIFACT_SHIELD_DURATION + self.total_stats_boost.bullet_shield_duration)
        self.duration_timer.turn_off()
    
    @staticmethod
    def get_artifact_type():
        return ArtifactType.BULLET_SHIELD
        
    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration_timer.tick(time_delta)

    def is_on(self) -> bool:
        return self.duration_timer.running()

    def turn_on(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy('not enough energy for shield')
        if self.is_on():
            raise ShieldRunning('shield already running')
        if self.cooldown_timer.running():
            raise OnCooldown(f'shield on cooldown: {self.cooldown_timer.get_time_left():.1f}')
        self.player.energy.change(-self.cost)
        self.duration_timer.reset()
        self.cooldown_timer.reset()

    def get_size(self) -> float:
        return ARTIFACT_SHIELD_SIZE + self.total_stats_boost.bullet_shield_size

    def point_inside_shield(self, pos: Vector2) -> bool:
        return self.is_on() and (pos - self.player.pos).magnitude_squared() < self.get_size() ** 2
    
    def get_short_string(self):
        return 'Shield'


class MineSpawn(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.MINE_SPAWN, 
            player=player,
            cooldown=MINE_COOLDOWN,
            cost=MINE_COST
        )
        self.cooldown -= self.total_stats_boost.mine_cooldown
    
    @staticmethod
    def get_artifact_type():
        return ArtifactType.MINE_SPAWN

    def spawn(self):
        if self.cooldown_timer.running():
            raise OnCooldown(f'mine spawner on cooldown: {self.cooldown_timer.get_time_left():.1f}')
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy('not enough energy for a mine')
        self.player.energy.change(-self.cost)
        vel: Vector2 = self.player.get_vel() + random_unit_vector()
        vel.scale_to_length(20.)
        pos: Vector2 = self.player.get_pos()
        self.player.entities_buffer.append(Mine(pos=pos-vel, 
                                    damage=MINE_DEFAULT_DAMAGE + 10. * (self.player.level - 1)))
        self.cooldown_timer.reset()
    
    def get_short_string(self):
        return 'Mine'


class Dash(Artifact):
    def __init__(self, player):
        super().__init__(
            artifact_type=ArtifactType.DASH,
            player=player,
            cooldown=5.,
            cost=300,
        )
        self.duration_timer = Timer(max_time=0.5)
        self.duration_timer.turn_off()
    
    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration_timer.tick(time_delta)
    
    @staticmethod
    def get_artifact_type():
        return ArtifactType.DASH
    
    def get_short_string(self) -> str:
        return 'Dash'

    def dash(self):
        if self.player.energy.get_value() < self.cost:
            raise NotEnoughEnergy('not enough energy for dash')
        if self.is_on():
            raise DashRunning('dash already running')
        if self.cooldown_timer.running():
            raise OnCooldown(f'dash on cooldown: {self.cooldown_timer.get_time_left():.1f}')
        self.player.energy.change(-self.cost)
        self.duration_timer.reset()
        self.cooldown_timer.reset()
    
    def is_on(self) -> bool:
        return self.duration_timer.running()


class InactiveArtifact(Artifact):
    def __init__(self, stats_boost: StatsBoost):
        super().__init__(artifact_type=ArtifactType.STATS, player=None, cooldown=0, cost=0)
        self.stats_boost = stats_boost
    
    def update(self, time_delta: float):
        ...
    
    def __repr__(self) -> str:
        return f'InactiveArtifact({self.stats_boost})'
    
    def get_short_string(self) -> str:
        return 'Stats'
    
    def __str__(self) -> str:
        return f'[{self.stats_boost}]'


class ArtifactsHandler:
    def __init__(self, player):
        self.player = player
        self.inactive_artifacts: list[InactiveArtifact] = []

        self.bullet_shield: BulletShield | None = None
        self.mine_spawn: MineSpawn | None = None
        self.dash: Dash | None = None

    def get_total_stats_boost(self) -> StatsBoost:
        return sum((artifact.stats_boost for artifact in self.inactive_artifacts), StatsBoost())
    
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
    
    def add_artifact(self, artifact: Artifact):
        if isinstance(artifact, InactiveArtifact):
            self.inactive_artifacts.append(artifact)
        elif isinstance(artifact, BulletShield):
            self.bullet_shield = artifact
        elif isinstance(artifact, MineSpawn):
            self.mine_spawn = artifact
        elif isinstance(artifact, Dash):
            self.dash = artifact
        else:
            raise NotImplementedError(f'unknown artifact type: {artifact.artifact_type}')
    
    def is_present(self, artifact_type: ArtifactType) -> bool:
        if artifact_type == ArtifactType.BULLET_SHIELD:
            return self.bullet_shield is not None
        elif artifact_type == ArtifactType.MINE_SPAWN:
            return self.mine_spawn is not None
        elif artifact_type == ArtifactType.DASH:
            return self.dash is not None
        else:
            raise NotImplementedError(f'unknown artifact type: {artifact_type}')
    
    def get_bullet_shield(self) -> BulletShield:
        if self.bullet_shield is None:
            raise ArtifactMissing('[?] bullet shield is missing')
        return self.bullet_shield
    def get_mine_spawn(self) -> MineSpawn:
        if self.mine_spawn is None:
            raise ArtifactMissing('[?] mine spawn is missing')
        return self.mine_spawn
    def get_dash(self) -> Dash:
        if self.dash is None:
            raise ArtifactMissing('[?] dash is missing')
        return self.dash
    
    def __repr__(self) -> str:
        active_artivacts = ' | '.join(map(str, self.iterate_active()))
        return f'ArtifactsHandler({active_artivacts}; {self.inactive_artifacts})'
    
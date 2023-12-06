from abc import ABC, abstractmethod

from pygame import Vector2

from src.entity import Mine
from src.enums import ArtifactType
from src.exceptions import NotEnoughEnergy, OnCooldown, ShieldRunning, ArtifactMissing
from src.utils import Timer, random_unit_vector
from config import (ARTIFACT_SHIELD_SIZE, ARTIFACT_SHIELD_COOLDOWN,
    ARTIFACT_SHIELD_DURATION, ARTIFACT_SHIELD_COST, MINE_COOLDOWN, MINE_COST, MINE_DEFAULT_DAMAGE
)


class Artifact(ABC):
    def __init__(self,
        active: bool,
        artifact_type: ArtifactType,
        player,
        cooldown: float
    ):
        self.active = active
        self.artifact_type = artifact_type
        self.player = player
        self.cooldown = cooldown
        self.cooldown_timer = Timer(max_time=self.cooldown)
        self.cooldown_timer.set_percent_full(0.5)

    def update(self, time_delta: float):
        self.cooldown_timer.tick(time_delta)        
    
    def __str__(self) -> str:
        return 'Artifact::' + self.__class__.__name__


class BulletShield(Artifact):
    def __init__(self, player):
        super().__init__(
            active=True, 
            artifact_type=ArtifactType.BULLET_SHIELD, 
            player=player,
            cooldown=ARTIFACT_SHIELD_COOLDOWN
        )
        self.duration_timer = Timer(max_time=ARTIFACT_SHIELD_DURATION)
        self.duration_timer.turn_off()
        
    def update(self, time_delta: float):
        super().update(time_delta)
        self.duration_timer.tick(time_delta)

    def is_on(self) -> bool:
        return self.duration_timer.running()

    def turn_on(self):
        if self.player.energy.get_value() < ARTIFACT_SHIELD_COST:
            raise NotEnoughEnergy('not enough energy for shield')
        if self.is_on():
            raise ShieldRunning('shield already running')
        if self.cooldown_timer.running():
            raise OnCooldown(f'shield on cooldown: {self.cooldown_timer.get_time_left():.1f}')
        self.player.energy.change(-ARTIFACT_SHIELD_COST)
        self.duration_timer.reset()
        self.cooldown_timer.reset()

    def point_inside_shield(self, pos: Vector2) -> bool:
        return self.is_on() and (pos - self.player.pos).magnitude_squared() < ARTIFACT_SHIELD_SIZE ** 2


class MineSpawn(Artifact):
    def __init__(self, player):
        super().__init__(
            active=True, 
            artifact_type=ArtifactType.MINE_SPAWN, 
            player=player,
            cooldown=MINE_COOLDOWN
        )

    def spawn(self):
        if self.cooldown_timer.running():
            raise OnCooldown(f'mine spawner on cooldown: {self.cooldown_timer.get_time_left():.1f}')
        if self.player.energy.get_value() < MINE_COST:
            raise NotEnoughEnergy('not enough energy for a mine')
        self.player.energy.change(-MINE_COST)
        vel: Vector2 = self.player.get_vel() + random_unit_vector()
        vel.scale_to_length(20.)
        pos: Vector2 = self.player.get_pos()
        self.player.entities_buffer.append(Mine(pos=pos-vel, 
                                    damage=MINE_DEFAULT_DAMAGE + 10. * (self.player.level - 1)))
        self.cooldown_timer.reset()


class BaitSpawn(Artifact):
    def __init__(self, player):
        super().__init__(active=True, artifact_type=ArtifactType.BAIT, player=player, cooldown=12.)


class ArtifactsHandler:
    def __init__(self, player):
        self.player = player
        self.inactive_artifacts: list[Artifact] = []

        self.bullet_shield: BulletShield | None = None
        self.mine_spawn: MineSpawn | None = None
        self.bait_spawn: BaitSpawn | None = None

        # self.artifact_flags = {
        #     ArtifactType.BULLET_SHIELD: False,
        #     ArtifactType.MINE_SPAWN: False,
        #     ArtifactType.BAIT: False,
        # }
    
    def update(self, time_delta: float):
        for artifact in self.iterate_active():
            artifact.update(time_delta)
    
    def iterate_active(self):
        if self.bullet_shield is not None:
            yield self.bullet_shield
        if self.mine_spawn is not None:
            yield self.mine_spawn
        if self.bait_spawn is not None:
            yield self.bait_spawn
    
    def add_artifact(self, artifact: Artifact):
        if not artifact.active:
            self.inactive_artifacts.append(artifact)
            return
        if isinstance(artifact, BulletShield):
            self.bullet_shield = artifact
        elif isinstance(artifact, MineSpawn):
            self.mine_spawn = artifact
        elif isinstance(artifact, BaitSpawn):
            self.bait_spawn = artifact
        else:
            raise NotImplementedError(f'unknown artifact type: {artifact.artifact_type}')
    
    def is_present(self, artifact_type: ArtifactType) -> bool:
        if artifact_type == ArtifactType.BULLET_SHIELD:
            return self.bullet_shield is not None
        elif artifact_type == ArtifactType.MINE_SPAWN:
            return self.mine_spawn is not None
        elif artifact_type == ArtifactType.BAIT:
            return self.bait_spawn is not None
        else:
            raise NotImplementedError(f'unknown artifact type: {artifact_type}')
    
    def get_bullet_shield(self) -> BulletShield:
        if self.bullet_shield is None:
            raise ArtifactMissing('[!] bullet shield is missing')
        return self.bullet_shield
    def get_mine_spawn(self) -> MineSpawn:
        if self.mine_spawn is None:
            raise ArtifactMissing('[!] mine spawn is missing')
        return self.mine_spawn
    def get_bait(self) -> BaitSpawn:
        if self.bait_spawn is None:
            raise ArtifactMissing('[!] bait spawn is missing')
        return self.bait_spawn
    
    def __repr__(self) -> str:
        active_artivacts = ' | '.join(map(str, self.iterate_active()))
        return f'ArtifactsHandler({active_artivacts}; {self.inactive_artifacts})'
    
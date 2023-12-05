from abc import ABC, abstractmethod

from pygame import Vector2

from src.enums import ArtifactType
from src.exceptions import NotEnoughEnergy, OnCooldown, ShieldRunning
from src.player import Player
from src.utils import Timer
from config import (ARTIFACT_SHIELD_SIZE, ARTIFACT_SHIELD_COOLDOWN,
    ARTIFACT_SHIELD_DURATION, ARTIFACT_SHIELD_COST,
)


class Artifact(ABC):
    def __init__(self,
        active: bool,
        artifact_type: ArtifactType,
        player: Player,
    ):
        self.active = active
        self.artifact_type = artifact_type
        self.player = player

    @abstractmethod
    def update(self, time_delta: float):
        ...


class ArtifactsHandler:
    def __init__(self, player: Player):
        self.player = player
        self.artifacts: list[Artifact] = [] # ? should this be a list?
    
    def append(self, artifact: Artifact):
        self.artifacts.append(artifact)


class BulletShield(Artifact):
    def __init__(self, player: Player):
        super().__init__(active=True, artifact_type=ArtifactType.BULLET_SHIELD, player=player)
        self.duration_timer = Timer(max_time=ARTIFACT_SHIELD_DURATION)
        self.duration_timer.turn_off()
        self.cooldown_timer = Timer(max_time=ARTIFACT_SHIELD_COOLDOWN)
        self.cooldown_timer.set_percent_full(0.8)

    def update(self, time_delta: float):
        self.duration_timer.tick(time_delta)
        self.cooldown_timer.tick(time_delta)

    def is_on(self) -> bool:
        return self.duration_timer.running()

    def turn_on(self):
        if self.player.energy.get_value() < ARTIFACT_SHIELD_COST:
            raise NotEnoughEnergy('not enough energy for shield')
        if self.is_on():
            raise ShieldRunning('shield already running')
        if self.cooldown_timer.running():
            raise OnCooldown('shield on cooldown')
        self.player.energy.change(-ARTIFACT_SHIELD_COST)
        self.duration_timer.reset()
        self.cooldown_timer.reset()

    def point_inside_shield(self, pos: Vector2) -> bool:
        return self.is_on() and (pos - self.player.pos).magnitude_squared() < ARTIFACT_SHIELD_SIZE ** 2
    
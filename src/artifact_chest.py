import math
import random
from itertools import repeat

from pygame import Vector2, Color

from src.entity import Entity
from src.utils import Timer
from src.enums import EntityType, ArtifactType
from src.artifacts import Artifact, ArtifactsHandler, BulletShield, Dash, MineSpawn, InactiveArtifact, StatsBoost
from config import ARTIFACT_CHEST_SIZE, ARTIFACT_CHEST_LIFETIME


class ArtifactChest(Entity):
    """Shows what's inside on hover.
    Is picked up on collision with player."""
    def __init__(self,
        pos: Vector2,
        artifact: Artifact,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.ARTIFACT_CHEST,
            size=ARTIFACT_CHEST_SIZE,
            color=Color('yellow'),
        )
        self.init_pos = pos.copy()
        self.artifact = artifact
        self.life_timer = Timer(max_time=ARTIFACT_CHEST_LIFETIME)
        self.t = 0

    def get_artifact(self) -> Artifact:
        return self.artifact

    def update(self, time_delta: float):
        if not self._is_alive: return
        super().update(time_delta)
        self.life_timer.tick(time_delta)
        self.t += time_delta
        self.pos = 15 * Vector2(math.cos(self.t), math.sin(self.t)) + self.init_pos

    def __str__(self) -> str:
        return f'ArtifactChest({self.artifact})'


class ArtifactChestGenerator:
    def __init__(self):
        # each of these can be collected only once
        active_art_types = list(ArtifactType)
        random.shuffle(active_art_types)
        self.active_artifacts = dict(zip(active_art_types, repeat(False)))
        del self.active_artifacts[ArtifactType.STATS]
        # and these too
        _inactive_artifacts = [
            StatsBoost(regen=1.5),
            StatsBoost(speed=400.),
            StatsBoost(damage=15.),
            StatsBoost(regen=2., speed=450),
            StatsBoost(bullet_shield_duration=1.),
            StatsBoost(size=2.),
            StatsBoost(mine_cooldown=1.5),
            StatsBoost(bullet_shield_size=15.),
            StatsBoost(cooldown=0.15),
        ]
        self.inactive_artifacts_stats_boosts = dict(zip(_inactive_artifacts, repeat(False)))

    def check_artifact(self, artifact: Artifact) -> bool:
        """Returns True if successful. False if already collected."""
        _type = artifact.artifact_type
        if isinstance(artifact, InactiveArtifact):
            if self.inactive_artifacts_stats_boosts[artifact.stats_boost]:
                return False
            self.inactive_artifacts_stats_boosts[artifact.stats_boost] = True
            return True
        if self.active_artifacts[_type]: return False
        self.active_artifacts[_type] = True
        return True
    
    def get_first_n_absent_inactive_stats(self, n: int) -> list[StatsBoost]:
        return [k for k, v in self.inactive_artifacts_stats_boosts.items() if not v][:n]
    
    def get_positions_for(self, n_chests: int) -> list[Vector2]:
        ...

    def get_artifact_chests(self, player_level: int) -> list[ArtifactChest]:
        """
        Returns a list of ArtifactChests with the artifacts that player does not yet have.
        """
        return []

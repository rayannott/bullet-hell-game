import math
import random
from itertools import repeat

from pygame import Vector2, Color

from src.entity import Entity
from src.utils import Timer
from src.enums import EntityType, ArtifactType
from src.artifacts import Artifact, ArtifactsHandler, BulletShield, Dash, MineSpawn, InactiveArtifact, StatsBoost, TimeStop
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
    
    def can_be_picked_up(self) -> bool:
        return self.t > 1.

    def get_artifact(self) -> Artifact:
        return self.artifact
    
    def set_pos(self, pos: Vector2):
        self.init_pos = pos.copy()

    def get_pos(self) -> Vector2:
        return self.init_pos

    def update(self, time_delta: float):
        if not self._is_alive: return
        super().update(time_delta)
        self.life_timer.tick(time_delta)
        self.t += time_delta
        self.pos = 15 * Vector2(math.cos(self.t), math.sin(self.t)) + self.init_pos

    def __repr__(self) -> str:
        return f'ArtifactChest({self.artifact})'


class ArtifactChestGenerator:
    def __init__(self, player):
        # each of these can be collected only once
        self.player = player
        active_art_types = list(ArtifactType)
        random.shuffle(active_art_types)
        self.active_artifacts = dict(zip(active_art_types, repeat(False)))
        del self.active_artifacts[ArtifactType.STATS]

        # and these too
        _inactive_artifacts = [
            StatsBoost(speed=400.),
            StatsBoost(regen=1.5),
            StatsBoost(damage=15.),
            StatsBoost(regen=0.8, speed=200.),
            StatsBoost(size=1., add_max_extra_bullets=2),
            StatsBoost(damage=30.),
            StatsBoost(add_max_extra_bullets=5),
            StatsBoost(bullet_shield_duration=2.),
            StatsBoost(time_stop_duration=2.),
            StatsBoost(regen=2.5),
            StatsBoost(mine_cooldown=2.),
            StatsBoost(bullet_shield_size=20.),
            StatsBoost(cooldown=0.15),
        ]
        self.inactive_artifacts_stats_boosts = dict(zip(_inactive_artifacts, repeat(False)))

        # Maps the player level to the artifact types to be spawned: S - stats, A - active.
        self.ARTIFACT_SCHEDULE = {
            2: 'SSS', 3: 'SAA', 4: 'SSS', 5: 'SSA',
            6: 'SSS', 7: 'SSA', 8: 'SSS', 9: 'SSA', 10: 'SSA',
        }
    
    def get_random_absent_stats_boost_artifact_chest(self, at: Vector2) -> ArtifactChest | None:
        absent_stats = [k for k, v in self.inactive_artifacts_stats_boosts.items() if not v]
        if not absent_stats: return None
        stats_boost = random.choice(absent_stats)
        return ArtifactChest(at, InactiveArtifact(stats_boost))
    
    def get_artifact(self, artifact_type: ArtifactType) -> Artifact:
        if artifact_type == ArtifactType.BULLET_SHIELD:
            return BulletShield(self.player)
        elif artifact_type == ArtifactType.DASH:
            return Dash(self.player)
        elif artifact_type == ArtifactType.MINE_SPAWN:
            return MineSpawn(self.player)
        elif artifact_type == ArtifactType.TIME_STOP:
            return TimeStop(self.player)
        else:
            raise NotImplementedError(f'Unknown artifact type: {artifact_type}')

    def check_artifact(self, artifact: Artifact) -> bool:
        """Returns True if successful. False if already collected.
        Sets the artifact as collected."""
        _type = artifact.artifact_type
        if isinstance(artifact, InactiveArtifact):
            if self.inactive_artifacts_stats_boosts[artifact.stats_boost]:
                return False
            self.inactive_artifacts_stats_boosts[artifact.stats_boost] = True
            return True
        if self.active_artifacts[_type]: return False
        self.active_artifacts[_type] = True
        return True

    def get_artifact_chests(self, player_level: int) -> list[ArtifactChest]:
        """
        Returns a list of ArtifactChests with the artifacts that player does not yet have.
        """
        to_spawn: list[ArtifactChest] = []
        absent_stats = [k for k, v in self.inactive_artifacts_stats_boosts.items() if not v]
        absent_active = [k for k, v in self.active_artifacts.items() if not v]
        random.shuffle(absent_active)
        this_level_schedule = self.ARTIFACT_SCHEDULE[player_level]
        num_stats_to_spawn, num_active_to_spawn = this_level_schedule.count('S'), this_level_schedule.count('A')
        num_active_to_spawn = min(num_active_to_spawn, len(absent_active))
        num_stats_to_spawn = min(num_stats_to_spawn, len(absent_stats))
        if num_active_to_spawn + num_stats_to_spawn == 0: return []

        active_to_spawn = absent_active[:num_active_to_spawn] # active artifact types
        to_spawn.extend([ArtifactChest(Vector2(), self.get_artifact(_type)) for _type in active_to_spawn])
    
        skip = 2 * player_level // 3 - 1
        if num_stats_to_spawn <= 4:
            stats_to_spawn = absent_stats[skip:skip+num_stats_to_spawn]
        else:
            stats_to_spawn = random.sample(absent_stats[skip:skip+4], num_stats_to_spawn)
        to_spawn.extend(
            [ArtifactChest(Vector2(), InactiveArtifact(stats_boost)) for stats_boost in stats_to_spawn]
        )

        return to_spawn

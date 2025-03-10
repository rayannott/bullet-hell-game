from __future__ import annotations
import itertools
import math
import random
from itertools import repeat

from pygame import Vector2, Color

import src.entities.player
from src.entities.entity import Entity
from src.utils.enums import EntityType, ArtifactType
from src.misc.artifacts import (
    Artifact,
    BulletShield,
    Dash,
    MineSpawn,
    InactiveArtifact,
    StatsBoost,
    TimeSlow,
    Shrapnel,
    Rage,
)
from config import ARTIFACT_CHEST_SIZE, ARTIFACT_CHEST_LIFETIME


class ArtifactChest(Entity):
    """Shows what's inside on hover.
    Is picked up on collision with player."""

    def __init__(
        self,
        pos: Vector2,
        artifact: Artifact,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.ARTIFACT_CHEST,
            size=ARTIFACT_CHEST_SIZE,
            color=Color("yellow"),
            lifetime=ARTIFACT_CHEST_LIFETIME,
        )
        self.init_pos = pos.copy()
        self.artifact = artifact
        self.t = 0

    def can_be_picked_up(self) -> bool:
        return self.t > 1.0

    def get_artifact(self) -> Artifact:
        return self.artifact

    def set_pos(self, pos: Vector2):
        self.init_pos = pos.copy()

    def get_pos(self) -> Vector2:
        return self.init_pos

    def update(self, time_delta: float):
        if not self._is_alive:
            return
        super().update(time_delta)
        self.t += time_delta
        self.pos = 15 * Vector2(math.cos(self.t), math.sin(self.t)) + self.init_pos

    def __repr__(self) -> str:
        return f"ArtifactChest({self.artifact})"


class ArtifactChestGenerator:
    def __init__(self, player: src.entities.player.Player):
        # each of these can be collected only once
        self.player = player
        active_art_types = list(ArtifactType)
        random.shuffle(active_art_types)
        self.active_artifacts = dict(zip(active_art_types, repeat(False)))
        del self.active_artifacts[ArtifactType.STATS]

        # and these too
        self._inactive_artifacts = [
            StatsBoost(speed=600.0),
            StatsBoost(regen=1.5),
            StatsBoost(damage=15.0),
            StatsBoost(regen=0.5, speed=300.0),
            StatsBoost(bullet_shield_duration=2.0),
            StatsBoost(size=2.0),
            StatsBoost(add_max_extra_bullets=4),
            StatsBoost(damage=20.0),
            StatsBoost(shrapnel_extra_shards=5),
            StatsBoost(mine_cooldown=3.0),
            StatsBoost(damage=20.0, cooldown=0.07),
            StatsBoost(shrapnel_cooldown=5.0),
            StatsBoost(time_slow_duration=5.0),
            StatsBoost(bullet_shield_size=30.0),
            StatsBoost(size=3.0, regen=1.0),
            StatsBoost(cooldown=0.1),
        ]
        self.inactive_artifacts_stats_boosts = dict(
            zip(self._inactive_artifacts, repeat(False))
        )

        # Maps the player level to the artifact types to be spawned: S - stats, A - active.
        self.ARTIFACT_SCHEDULE = {
            2: "SSS",
            3: "SAA",
            4: "SSS",
            5: "SSA",
            6: "SSS",
            7: "SSA",
            8: "SSA",
            9: "SSA",
            10: "SSS",
        }

    def should_include_stats_boost(self, sb: StatsBoost) -> bool:
        if sb.bullet_shield_duration or sb.bullet_shield_size:
            if not self.player.artifacts_handler.is_present(ArtifactType.BULLET_SHIELD):
                return False
        # no dash-related stats boosts yet
        if sb.mine_cooldown:
            if not self.player.artifacts_handler.is_present(ArtifactType.MINE_SPAWN):
                return False
        if sb.time_slow_duration:
            if not self.player.artifacts_handler.is_present(ArtifactType.TIME_SLOW):
                return False
        if sb.shrapnel_extra_shards or sb.shrapnel_cooldown:
            if not self.player.artifacts_handler.is_present(ArtifactType.SHRAPNEL):
                return False
        return True

    def get_artifact(self, artifact_type: ArtifactType) -> Artifact:
        if artifact_type == ArtifactType.BULLET_SHIELD:
            return BulletShield(self.player)
        elif artifact_type == ArtifactType.DASH:
            return Dash(self.player)
        elif artifact_type == ArtifactType.MINE_SPAWN:
            return MineSpawn(self.player)
        elif artifact_type == ArtifactType.TIME_SLOW:
            return TimeSlow(self.player)
        elif artifact_type == ArtifactType.SHRAPNEL:
            return Shrapnel(self.player)
        elif artifact_type == ArtifactType.RAGE:
            return Rage(self.player)
        else:
            raise NotImplementedError(f"Unknown artifact type: {artifact_type}")

    def check_artifact(self, artifact: Artifact) -> bool:
        """Returns True if successful. False if already collected.
        Sets the artifact as collected."""
        _type = artifact.artifact_type
        if isinstance(artifact, InactiveArtifact):
            self.inactive_artifacts_stats_boosts[artifact.stats_boost] = True
            return True
        if self.active_artifacts[_type]:
            return False
        self.active_artifacts[_type] = True
        return True

    def get_n_uniqie_stat_boost_chests(self, n: int) -> list[ArtifactChest]:
        return [
            ArtifactChest(Vector2(), InactiveArtifact(stat_boost))
            for stat_boost in random.sample(
                list(filter(self.should_include_stats_boost, self._inactive_artifacts)),
                n,
            )
        ]

    def get_artifact_chests(self, player_level: int) -> list[ArtifactChest]:
        """
        Returns a list of ArtifactChests with the artifacts that player does not yet have.
        """
        to_spawn: list[ArtifactChest] = []
        # absent_stats = [k for k, v in self.inactive_artifacts_stats_boosts.items() if not v and self.should_include_stats_boost(k)]
        absent_active = [k for k, v in self.active_artifacts.items() if not v]
        random.shuffle(absent_active)
        this_level_schedule = self.ARTIFACT_SCHEDULE.get(player_level, 'AAA')
        num_stats_to_spawn, num_active_to_spawn = (
            this_level_schedule.count("S"),
            this_level_schedule.count("A"),
        )
        num_active_to_spawn = min(num_active_to_spawn, len(absent_active))
        # num_stats_to_spawn = min(num_stats_to_spawn, len(absent_stats))
        if num_active_to_spawn + num_stats_to_spawn == 0:
            return []

        active_to_spawn = absent_active[:num_active_to_spawn]  # active artifact types
        to_spawn.extend(
            [
                ArtifactChest(Vector2(), self.get_artifact(_type))
                for _type in active_to_spawn
            ]
        )

        skip = player_level - 2
        to_sample_from = []
        if player_level < 11:
            for k, v in itertools.islice(
                self.inactive_artifacts_stats_boosts.items(), skip, skip + 5
            ):
                if not v and self.should_include_stats_boost(k):
                    to_sample_from.append(k)
        if len(to_sample_from) <= num_stats_to_spawn:
            stats_to_spawn = to_sample_from[:]
        else:
            stats_to_spawn = random.sample(to_sample_from, num_stats_to_spawn)
        to_spawn.extend(
            [
                ArtifactChest(Vector2(), InactiveArtifact(stats_boost))
                for stats_boost in stats_to_spawn
            ]
        )
        missing_num = 3 - len(to_spawn)
        to_spawn.extend(self.get_n_uniqie_stat_boost_chests(missing_num))
        # TODO: fix spawning duplicate stat boosts
        return to_spawn

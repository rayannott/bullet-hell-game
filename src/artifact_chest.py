import math
from pygame import Vector2, Color

from src.entity import Entity
from src.utils import Timer
from src.enums import EntityType, ArtifactType
from src.artifacts import Artifact, BulletShield, MineSpawn
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


def get_artifact_chests_for_level(level: int, collected_types_map: dict[ArtifactType, bool]) -> list[ArtifactChest]:
    # if level == 2:
    #     ...
    ...


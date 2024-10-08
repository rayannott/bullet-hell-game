from enum import Enum, auto


class EntityType(Enum):
    """
    Enumeration of all entity types.
    """

    DUMMY = auto()
    OIL_SPILL = auto()
    CORPSE = auto()
    PLAYER = auto()
    PROJECTILE = auto()
    ENERGY_ORB = auto()
    ENEMY = auto()
    MINE = auto()
    CRATER = auto()
    ARTIFACT_CHEST = auto()
    BOMB = auto()


class EnemyType(Enum):
    """
    Enumeration of all enemy types.
    """

    BASIC = auto()
    FAST = auto()
    TANK = auto()
    ARTILLERY = auto()
    BOSS = auto()
    MINER = auto()
    JESTER = auto()


class ProjectileType(Enum):
    """
    Enumeration of all projectile types.
    """

    PLAYER_BULLET = auto()
    NORMAL = auto()
    HOMING = auto()
    EXPLOSIVE = auto()
    DEF_TRAJECTORY = auto()


class ArtifactType(Enum):
    STATS = auto()
    BULLET_SHIELD = auto()
    MINE_SPAWN = auto()
    DASH = auto()
    TIME_STOP = auto()
    SHRAPNEL = auto()
    RAGE = auto()


class AnimationType(Enum):
    ACCURATE_SHOT = auto()
    ENEMY_SPAWNED = auto()
    BOSS_DIED = auto()
    ENERGY_ORB_COLLECTED = auto()


class AOEEffectEffectType(Enum):
    DAMAGE = auto()
    ENEMY_BLOCK_ON = auto()

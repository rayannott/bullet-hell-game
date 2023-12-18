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


class EnemyType(Enum):
    """
    Enumeration of all enemy types.
    """
    BASIC = auto()
    FAST = auto()
    TANK = auto()
    ARTILLERY = auto()
    BOSS = auto()


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
    # ROTATING_BULLETS = auto()

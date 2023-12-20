REMOVE_DEAD_ENTITIES_EVERY = 3.5 # seconds
GAME_MAX_LEVEL = 10
WAVE_DURATION = 45. # seconds
TRAIL_MAX_LENGTH = 100 # positions
SPAWN_ENEMY_EVERY = 7. # seconds


# player
PLAYER_SIZE = 12.
PLAYER_DEFAULT_SPEED_RANGE = (100., 3000.) # min, max: depends on the distance to the gravity point
PLAYER_SPEED_INCREASE = 250.
PLAYER_DEFAULT_MAX_HEALTH = 100.
PLAYER_DEFAULT_REGEN_RATE = 1.2 # hp per second
PLAYER_DEFAULT_MAX_ENERGY = 1000.
PLAYER_ENERGY_INCREASE = 50.
PLAYER_DEFAULT_ENERGY_DECAY_RATE = 6. # energy per second
PLAYER_STARTING_ENERGY = PLAYER_DEFAULT_MAX_ENERGY // 2
PLAYER_DEFAULT_SHOOT_COOLDOWN = 0.95
PLAYER_DEFAULT_DAMAGE_AVG = 40.
PLAYER_DEFAULT_DAMAGE_SPREAD = 15.
PLAYER_INVULNERABILITY_TIME = 0.5
PLAYER_DEFAULT_MAX_EXTRA_BULLETS = 3

PLAYER_SHOT_COST = 130
PLAYER_EXTRA_BULLET_SHOT_MULT = 1.75


# artifacts
ARTIFACT_SHIELD_SIZE = 100.
ARTIFACT_SHIELD_DURATION = 5.
ARTIFACT_SHIELD_COOLDOWN = 20.
ARTIFACT_SHIELD_COST = 400.


# artifact chests
ARTIFACT_CHEST_SIZE = 35.
ARTIFACT_CHEST_LIFETIME = 100.

# enemy
ENEMY_DEFAULT_SIZE = 12.
ENEMY_DEFAULT_SPEED = 220.
ENEMY_DEFAULT_MAX_HEALTH = 30.
ENEMY_DEFAULT_SHOOT_COOLDOWN = 3.
ENEMY_DEFAULT_REWARD = 180.
ENEMY_DEFAULT_LIFETIME = 20.
ENEMY_DEFAULT_DAMAGE = 40.
ENEMY_DEFAULT_DAMAGE_SPREAD = 10.
ENEMY_DEFAULT_COLLISION_DAMAGE = 60.
ENEMY_DEFAULT_SHOOTING_SPREAD = 0.5 # radians
BOSS_DEFAULT_OIL_SPILL_SPAWN_COOLDOWN = 18.
BOSS_DEFAULT_REGEN_RATE = 0.6
PROBABILITY_SPAWN_EXTRA_BULLET_ORB = 0.7


# projectile
PROJECTILE_DEFAULT_SIZE = 6.
PROJECTILE_DEFAULT_SPEED = 250. # added to the speed of the entity that shot it
PROJECTILE_DEFAULT_LIFETIME = 8. # seconds
PROJECTILE_DEFAULT_DAMAGE = 40.


# energy orb
ENERGY_ORB_SIZE = 8.
ENERGY_ORB_LIFETIME_RANGE = (2., 7.)
ENERGY_ORB_DEFAULT_ENERGY = 100.
ENERGY_ORB_COOLDOWN_RANGE = (0.5, 3.0)
ENERGY_ORB_SPAWNED_BY_PLAYER_LIFETIME = 150.


# oil spill
OIL_SPILL_SIZE = 80.
OIL_SPILL_LIFETIME = 12.
OIL_SPILL_SPEED_MULTIPLIER = 0.1
OIL_SPILL_DAMAGE_PER_SECOND = 15.
OIL_SPILL_SIZE_GROWTH_RATE = 15.


# mine
MINE_SIZE = 10.
MINE_LIFETIME = 10.
MINE_DEFAULT_DAMAGE = 50.
MINE_COOLDOWN = 7.
MINE_COST = 230.
MINE_AOE_EFFECT_SIZE = 120.
MINE_ACTIVATION_TIME = 1.

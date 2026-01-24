# GAME CONSTANTS

# Dimensions
TILE_SIZE = 32
MAP_WIDTH = 80
MAP_HEIGHT = 50
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

# Physics Constants (Player team to edit please)
FPS = 60
GRAVITY = 0.5
MAX_FALL_SPEED = 12
JUMP_POWER = -10  # Negative because Y goes down
THRUST_POWER = 0.8
FRICTION = 0.9
AIR_RESISTANCE = 0.98

# Movement Constants (Player team to edit please)
WALK_SPEED = 4
RUN_SPEED = 6
CROUCH_SPEED = 2
PRONE_SPEED = 1
MAX_VELOCITY = 15

# Game Rules
MAX_HP = 100
MAX_FUEL = 100
FUEL_REGEN = 1
FUEL_USAGE_FLY = 2
FUEL_USAGE_BOOST = 3
RESPAWN_TIME = 3  # seconds
INVULNERABILITY_TIME = 1  # seconds after respawn

# Player Constants (Player team to edit please)
PLAYER_WIDTH = 24
PLAYER_HEIGHT = 32
PLAYER_HITBOX_RADIUS = 12

# Weapon Constants (Gun team to edit please)
WEAPON_SWITCH_TIME = 0.5  # seconds
RELOAD_ANIMATION_TIME = 1.5  # seconds
MELEE_RANGE = 40
MELEE_DAMAGE = 50

# Weapon Stats (damage, fire_rate, ammo, reload_time) (Gun team to import from scripts please)
WEAPONS = {
    "pistol": {"damage": 20, "fire_rate": 0.3, "ammo": 12, "reload_time": 1.5, "range": 500},
    "smg": {"damage": 15, "fire_rate": 0.1, "ammo": 30, "reload_time": 2.0, "range": 400},
    "sniper": {"damage": 80, "fire_rate": 1.5, "ammo": 5, "reload_time": 3.0, "range": 1000},
    "shotgun": {"damage": 60, "fire_rate": 0.8, "ammo": 6, "reload_time": 2.5, "range": 200},
    "rocket": {"damage": 100, "fire_rate": 2.0, "ammo": 3, "reload_time": 4.0, "range": 800, "splash_radius": 80},
}

# Combat Constants (Gun team to edit please)
HEADSHOT_MULTIPLIER = 2.0
CRITICAL_HIT_CHANCE = 0.05
KNOCKBACK_FORCE = 5

# Team Settings
MAX_TEAMS = 5
MAX_TROOPS_PER_TEAM = 10
TEAM_COLORS = [
    (255, 50, 50),    # Red
    (50, 100, 255),   # Blue
    (50, 255, 50),    # Green
    (255, 200, 50),   # Yellow
    (200, 50, 255),   # Purple
]

# Match Settings
MATCH_TIME_LIMIT = 300  # seconds (5 minutes)
KILL_LIMIT = 50  # first team to reach wins
SUDDEN_DEATH_TIME = 30  # seconds of sudden death after time limit

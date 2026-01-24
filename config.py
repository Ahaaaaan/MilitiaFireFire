from teams import a, b, c, d, e

# Teams participating
TEAM_MODULES = [a, b, c, d, e]

# Expected team API
EXPECTED_VARIABLES = {"team_name", "troops", "deploy_list", "team_signal"}
EXPECTED_CLASSES = {"Troops", "Utils"}

# Game flags
DEBUG = True
STRICT_VALIDATION = True
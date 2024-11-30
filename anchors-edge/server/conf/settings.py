r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "anchors-edge"

# Path to the default room typeclass
BASE_ROOM_TYPECLASS = "typeclasses.rooms.WeatherAwareRoom"

# Default home location for new characters. This should be a valid dbref
# (limbo #2 is created by default) or None for allowing character creation
# anywhere. Can be overridden by buildworld command.
DEFAULT_HOME = "#2"
# Remove or comment out the CLIENT_DEFAULT_WIDTH setting since we're not using it
# CLIENT_DEFAULT_WIDTH = 80

######################################################################
# Weather System Settings
######################################################################

# Whether to show weather debug info in room descriptions
SHOW_WEATHER_DEBUG = False  # Set to False in production

# Maximum width for wrapped text in room descriptions
ROOM_DESCRIPTION_WIDTH = 78  # Standard terminal width is 80, leaving room for margins

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")

# Add the weather script as a global script
GLOBAL_SCRIPTS = {
    'weather_controller': {
        'typeclass': 'typeclasses.scripts.IslandWeatherScript',
        'repeats': -1,  # Repeat indefinitely 
        'interval': 900,  # 15 minutes between updates
        'desc': 'Global weather system controller',
        'persistent': True,
        'start_delay': False  # Start immediately
    }
}

# LLM Settings
LLM_HOST = "http://127.0.0.1:5000"
LLM_PATH = "/api/v1/generate"
LLM_HEADERS = {"Content-Type": "application/json"}
LLM_PROMPT_KEYNAME = "prompt"
LLM_REQUEST_BODY = {
    "max_new_tokens": 250,
    "temperature": 0.7,
}

# Disable automatic character creation
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False

# Define available races and their stat modifiers
AVAILABLE_RACES = {
    "Human": {
        "subraces": ["normal", "halfling"],
        "modifiers": {
            "normal": {"DEX": 1, "CHA": 1},
            "halfling": {"DEX": 1, "CHA": 1}
        }
    },
    "Elf": {
        "subraces": ["high", "wood", "half"],
        "modifiers": {
            "high": {"INT": 2, "CON": -1, "WIS": 1},
            "wood": {"DEX": 2, "INT": -1, "WIS": 1},
            "half": {"CHA": 2, "CON": -1, "WIS": 1}
        }
    },
    "Dwarf": {
        "subraces": ["mountain", "hill"],
        "modifiers": {
            "mountain": {"STR": 2, "DEX": -1, "CON": 1},
            "hill": {"CON": 2, "DEX": -1, "WIS": 1}
        }
    },
    "Gnome": {
        "modifiers": {"INT": 2, "STR": -1, "DEX": 1}
    },
    "Kobold": {
        "modifiers": {"DEX": 2, "STR": -1, "INT": 1}
    },
    "Feline": {
        "modifiers": {"DEX": 2, "INT": -1, "CHA": 1}
    },
    "Ashenkin": {
        "modifiers": {"CHA": 2, "WIS": -1, "INT": 1}
    }
}

# Base stats for all characters
BASE_CHARACTER_STATS = {
    "STR": 10,
    "CON": 10,
    "DEX": 10,
    "INT": 10,
    "WIS": 10,
    "CHA": 10
}

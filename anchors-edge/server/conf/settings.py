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

# Maximum number of characters per account
MAX_CHARACTERS_PER_ACCOUNT = 5

# Character backgrounds and their descriptions/effects
CHARACTER_BACKGROUNDS = {
    "Slave": {
        "desc": "Brought to the island in chains, you've managed to win or buy your freedom. Though the scars remain, you're determined to build a new life far from your past."
    },
    "Prisoner": {
        "desc": "Given a choice between execution and serving your sentence helping build this colony, you chose life. Your crimes may be behind you, but trust is hard to come by."
    },
    "Conscript": {
        "desc": "Drafted into service by the colony's militia, you patrol the wilderness and defend against threats. The pay is poor, but it beats prison or poverty."
    },
    "Enlisted": {
        "desc": "You signed up with the colony's military force willingly, seeking structure and purpose. The island's dangers ensure you'll never lack for work."
    },
    "Immigrant": {
        "desc": "Fleeing war, famine, or persecution, you've come seeking refuge. The island may be dangerous, but anything is better than what you left behind."
    },
    "Adventurer": {
        "desc": "Tales of the island's mysteries and riches drew you here. Whether seeking fortune, fame, or just a good fight, you're ready for whatever comes."
    },
    "Laborer": {
        "desc": "The promise of steady work and fair pay brought you here. The colony always needs strong backs and skilled hands to help it grow."
    }
}

# Add gender options
CHARACTER_GENDERS = {
    "Male": {
        "desc": "Masculine form and pronouns (he/him)",
    },
    "Female": {
        "desc": "Feminine form and pronouns (she/her)",
    }
}

# Height ranges for races (in total inches)
RACE_HEIGHT_RANGES = {
    "Human": {
        "normal": {
            "male": {
                "min": 60,  # 5'0"
                "max": 82   # 6'10"
            },
            "female": {
                "min": 57,  # 4'9"
                "max": 79   # 6'7"
            }
        },
        "halfling": {
            "male": {
                "min": 36,  # 3'0"
                "max": 48   # 4'0"
            },
            "female": {
                "min": 33,  # 2'9"
                "max": 45   # 3'9"
            }
        }
    },
    "Elf": {
        "wood": {
            "male": {
                "min": 68,  # 5'8"
                "max": 88   # 7'4"
            },
            "female": {
                "min": 65,  # 5'5"
                "max": 85   # 7'1"
            }
        },
        "high": {
            "male": {
                "min": 66,  # 5'6"
                "max": 84   # 7'0"
            },
            "female": {
                "min": 63,  # 5'3"
                "max": 81   # 6'9"
            }
        },
        "half": {
            "male": {
                "min": 66,  # 5'6"
                "max": 82   # 6'10"
            },
            "female": {
                "min": 63,  # 5'3"
                "max": 79   # 6'7"
            }
        }
    },
    "Dwarf": {
        "hill": {
            "male": {
                "min": 48,  # 4'0"
                "max": 60   # 5'0"
            },
            "female": {
                "min": 45,  # 3'9"
                "max": 57   # 4'9"
            }
        },
        "mountain": {
            "male": {
                "min": 44,  # 3'8"
                "max": 56   # 4'8"
            },
            "female": {
                "min": 41,  # 3'5"
                "max": 53   # 4'5"
            }
        }
    },
    "Gnome": {
        "male": {
            "min": 36,  # 3'0"
            "max": 42   # 3'6"
        },
        "female": {
            "min": 33,  # 2'9"
            "max": 39   # 3'3"
        }
    },
    "Kobold": {
        "male": {
            "min": 24,  # 2'0"
            "max": 30   # 2'6"
        },
        "female": {
            "min": 21,  # 1'9"
            "max": 27   # 2'3"
        }
    },
    "Feline": {
        "male": {
            "min": 60,  # 5'0"
            "max": 78   # 6'6"
        },
        "female": {
            "min": 57,  # 4'9"
            "max": 75   # 6'3"
        }
    },
    "Ashenkin": {
        "male": {
            "min": 66,  # 5'6"
            "max": 84   # 7'0"
        },
        "female": {
            "min": 63,  # 5'3"
            "max": 81   # 6'9"
        }
    }
}

# Import the race descriptions from the JSON file
import json
from pathlib import Path

# Load race descriptions
with open(Path("data/descriptions/body_parts.json"), 'r') as f:
    RACE_DESCRIPTIONS = json.load(f)

# Command set configuration
CMDSET_CHARACTER = "commands.default_cmdsets.CharacterCmdSet"
CMDSET_ACCOUNT = "commands.default_cmdsets.AccountCmdSet"
CMDSET_SESSION = "commands.default_cmdsets.SessionCmdSet"
CMDSET_UNLOGGEDIN = "commands.default_cmdsets.UnloggedinCmdSet"

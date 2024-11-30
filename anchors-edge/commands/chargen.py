"""
Character generation commands
"""
from evennia import Command
from evennia.utils.evmenu import EvMenu
from evennia.utils import create
from django.conf import settings
from evennia.utils.search import search_object

def _check_name(caller, name):
    """Check if name is valid and unique."""
    if len(name.split()) > 1:
        caller.msg("Character names must be a single word.")
        return False
        
    # Check for existing character with same name
    existing = search_object(name)
    if existing:
        caller.msg("That name is already taken.")
        return False
        
    return True

def node_race_select(caller):
    """Select character race."""
    text = """
|c== Character Creation - Race Selection ==|n

Choose your race carefully, as it will determine your starting attributes 
and abilities in the world.

|wAvailable Races and Subraces:|n"""
    
    # Add each race with its basic description and subraces
    race_info = {
        "Human": {
            "desc": "Versatile and adaptable",
            "stats": "",
            "subraces": {
                "normal": "(+1 DEX, +1 CHA) - Balanced and adaptable",
                "halfling": "(+1 DEX, +1 CHA) - Small but lucky"
            }
        },
        "Elf": {
            "desc": "Graceful and long-lived",
            "stats": "",
            "subraces": {
                "high": "(+2 INT, -1 CON, +1 WIS) - Magically attuned",
                "wood": "(+2 DEX, -1 INT, +1 WIS) - One with nature",
                "half": "(+2 CHA, -1 CON, +1 WIS) - Best of both worlds"
            }
        },
        "Dwarf": {
            "desc": "Hardy and strong",
            "stats": "",
            "subraces": {
                "mountain": "(+2 STR, -1 DEX, +1 CON) - Strong and hardy",
                "hill": "(+2 CON, -1 DEX, +1 WIS) - Wise and resilient"
            }
        },
        "Gnome": {
            "desc": "Small but intelligent",
            "stats": "(+2 INT, -1 STR, +1 DEX)",
            "subraces": {}
        },
        "Kobold": {
            "desc": "Quick and cunning",
            "stats": "(+2 DEX, -1 STR, +1 INT)",
            "subraces": {}
        },
        "Feline": {
            "desc": "Agile and charismatic",
            "stats": "(+2 DEX, -1 INT, +1 CHA)",
            "subraces": {}
        },
        "Ashenkin": {
            "desc": "Mysterious and compelling",
            "stats": "(+2 CHA, -1 WIS, +1 INT)",
            "subraces": {}
        }
    }
    
    # Display races and their descriptions
    for race, info in race_info.items():
        if info['subraces']:
            text += f"\n\n|y{race}|n - {info['desc']} {info['stats']}"
            for subrace, subdesc in info['subraces'].items():
                text += f"\n    - |w{subrace}|n {subdesc}"
        else:
            text += f"\n\n|y{race}|n - {info['desc']} {info['stats']}"
    
    text += "\n\n|wEnter your choice (e.g. 'gnome' or 'elf high'):|n"

    def _set_race(caller, raw_string):
        """Handle race selection."""
        args = raw_string.strip().lower().split()
        if not args:
            caller.msg("Please enter a race choice.")
            return None
            
        race = args[0].capitalize()
        if race not in settings.AVAILABLE_RACES:
            caller.msg(f"Invalid race: {race}")
            return None
            
        # Store race on the menu
        caller.ndb._menutree.race = race
            
        # Handle races with subraces
        if settings.AVAILABLE_RACES[race].get("subraces"):
            if len(args) < 2:
                caller.msg(f"Please specify a subrace for {race}. Available subraces: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
                return None
            subrace = args[1]
            if subrace not in settings.AVAILABLE_RACES[race]["subraces"]:
                caller.msg(f"Invalid subrace for {race}. Available subraces: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
                return None
            # Store subrace on the menu
            caller.ndb._menutree.subrace = subrace
            
        return "node_race_confirm"
    
    options = {"key": "_default", "goto": _set_race}
    return text, options

def node_race_confirm(caller):
    """Confirm race selection."""
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
    
    text = f"""
|c== Character Creation - Race Confirmation ==|n

You have selected:
Race: |y{race}|n
{f"Subrace: |y{subrace}|n" if subrace else ""}

Are you sure you want to play as {f"a {race} ({subrace})" if subrace else f"a {race}"}?

|wEnter |gyes|w to confirm or |rno|w to choose again:|n
"""
    
    def _confirm_race(caller, raw_string):
        """Handle race confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_background_select"
        elif choice == "no":
            # Clear the stored race/subrace
            if hasattr(caller.ndb._menutree, 'race'):
                del caller.ndb._menutree.race
            if hasattr(caller.ndb._menutree, 'subrace'):
                del caller.ndb._menutree.subrace
            return "node_race_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_race}
    return text, options

def node_background_select(caller):
    """Select character background."""
    text = """
|c== Character Creation - Background Selection ==|n

Your background represents your history and reason for coming to the island.
This choice will affect your starting location and initial relationships.

|wAvailable Backgrounds:|n"""
    
    # Display backgrounds and their descriptions
    for bg, info in settings.CHARACTER_BACKGROUNDS.items():
        text += f"\n\n|y{bg}|n"
        text += f"\n    {info['desc']}"
        text += f"\n    Stat Changes: "
        for stat, mod in info['stats'].items():
            text += f"{stat} {'+' if mod > 0 else ''}{mod} "
    
    text += "\n\n|wEnter the name of your chosen background:|n"
    
    def _set_background(caller, raw_string):
        """Handle background selection."""
        background = raw_string.strip().title()
        if background not in settings.CHARACTER_BACKGROUNDS:
            caller.msg(f"Invalid background. Please choose from: {', '.join(settings.CHARACTER_BACKGROUNDS.keys())}")
            return None
            
        # Store background on the menu
        caller.ndb._menutree.background = background
        return "node_background_confirm"
    
    options = {"key": "_default", "goto": _set_background}
    return text, options

def node_background_confirm(caller):
    """Confirm background selection."""
    background = caller.ndb._menutree.background
    bg_info = settings.CHARACTER_BACKGROUNDS[background]
    
    text = f"""
|c== Character Creation - Background Confirmation ==|n

You have selected: |y{background}|n

{bg_info['desc']}

This background will modify your stats: """
    
    for stat, mod in bg_info['stats'].items():
        text += f"{stat} {'+' if mod > 0 else ''}{mod} "
    
    text += "\n\n|wEnter |gyes|w to confirm or |rno|w to choose again:|n"
    
    def _confirm_background(caller, raw_string):
        """Handle background confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_name_select"
        elif choice == "no":
            if hasattr(caller.ndb._menutree, 'background'):
                del caller.ndb._menutree.background
            return "node_background_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_background}
    return text, options

def node_name_select(caller):
    """Select character name."""
    text = """
|c== Character Creation - Name Selection ==|n

Choose a name for your character. This name will identify you in the game world.

|wRequirements:|n
- Must be a single word
- Must be unique
- Should fit the game's setting

|wEnter your character's name:|n"""
    
    def _set_name(caller, raw_string):
        """Handle name input"""
        name = raw_string.strip()
        if _check_name(caller, name):
            caller.ndb._menutree.charname = name
            return "node_name_confirm"
        return None
    
    options = {"key": "_default", "goto": _set_name}
    return text, options

def node_name_confirm(caller):
    """Confirm name selection."""
    name = caller.ndb._menutree.charname
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, 'subrace') else None
    
    text = f"""
|c== Character Creation - Name Confirmation ==|n

You have chosen the name: |y{name}|n
For your {f"{race} ({subrace})" if subrace else race} character.

Are you sure you want to use this name?

|wEnter |gyes|w to confirm or |rno|w to choose again:|n
"""
    
    def _confirm_name(caller, raw_string):
        """Handle name confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_create_char"
        elif choice == "no":
            # Clear the stored name
            if hasattr(caller.ndb._menutree, 'charname'):
                del caller.ndb._menutree.charname
            return "node_name_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_name}
    return text, options

def node_create_char(caller):
    """Create the character."""
    menu = caller.ndb._menutree
    
    # Verify we have all required attributes
    if not hasattr(menu, 'race') or not hasattr(menu, 'charname') or not hasattr(menu, 'background'):
        caller.msg("Error: Missing required character information.")
        return "node_race_select"
    
    race = menu.race
    subrace = menu.subrace if hasattr(menu, 'subrace') else None
    charname = menu.charname
    background = menu.background
    
    # Check character limit again (in case limit was reached during creation)
    if len(caller.db._playable_characters) >= settings.MAX_CHARACTERS_PER_ACCOUNT:
        caller.msg("|rYou have reached the maximum number of characters allowed (5).|n")
        return None
    
    # Ensure _playable_characters exists
    if not hasattr(caller.db, '_playable_characters'):
        caller.db._playable_characters = []
    elif caller.db._playable_characters is None:
        caller.db._playable_characters = []
    
    # Create character
    try:
        # First check if character already exists
        existing = search_object(charname)
        if existing:
            caller.msg(f"Character {charname} already exists.")
            return None

        # Create new character
        char = create.create_object(
            settings.BASE_CHARACTER_TYPECLASS,
            key=charname,
            location=settings.DEFAULT_HOME,
            home=settings.DEFAULT_HOME)
            
        # Set up character permissions
        char.locks.add("puppet:id(%i) or pid(%i) or perm(Immortals) or pperm(Immortals);delete:id(%i) or perm(Wizards)" % 
                      (char.id, caller.id, caller.id))
        char.permissions.add("Player")
            
        # Apply racial modifiers
        char.apply_racial_modifiers(race, subrace)
        
        # Apply background modifiers
        bg_info = settings.CHARACTER_BACKGROUNDS[background]
        for stat, mod in bg_info['stats'].items():
            current = getattr(char.db, stat.lower())
            setattr(char.db, stat.lower(), current + mod)
        
        # Set background
        char.db.background = background
        
        # Add character to the list (don't overwrite)
        caller.db._playable_characters.append(char)
        caller.msg(f"Added {charname} to your playable characters.")
        
        # Set account reference on character
        char.db.account = caller
        
        text = f"""
|c== Character Creation Complete! ==|n

|wCharacter Details:|n
Name: |y{charname}|n
Race: |y{race}{f" ({subrace})" if subrace else ""}|n
Background: |y{background}|n

Your character has been created and is ready to enter the world.
Use |wcharselect {charname}|n to begin your adventure!

You have {settings.MAX_CHARACTERS_PER_ACCOUNT - len(caller.db._playable_characters)} character slots remaining.
"""
        return text, None
        
    except Exception as e:
        caller.msg(f"Error creating character: {e}")
        # Clean up any partial creation
        if 'char' in locals() and char:
            char.delete()
        return None

class CmdCreateCharacter(Command):
    """
    Create a new character
    
    Usage:
        charcreate
    """
    key = "charcreate"
    locks = "cmd:pperm(Player) and not puppeting"
    help_category = "Character"
    
    def func(self):
        """Start character creation menu."""
        # Check character limit
        if len(self.caller.db._playable_characters) >= settings.MAX_CHARACTERS_PER_ACCOUNT:
            self.caller.msg("|rYou have reached the maximum number of characters allowed (5).|n")
            self.caller.msg("You must delete a character before creating a new one.")
            return
            
        # Clean up any existing character creation data
        if hasattr(self.caller.ndb, '_menutree'):
            del self.caller.ndb._menutree
            
        def custom_formatter(optionlist):
            """
            Don't display the options - they're already in the node text
            """
            return ""
            
        def node_formatter(nodetext, optionstext):
            """
            Simply return the node text without any formatting
            """
            return nodetext
            
        # Start the menu with custom formatting
        EvMenu(self.caller,
               {
                   "node_race_select": node_race_select,
                   "node_race_confirm": node_race_confirm,
                   "node_background_select": node_background_select,
                   "node_background_confirm": node_background_confirm,
                   "node_name_select": node_name_select,
                   "node_name_confirm": node_name_confirm,
                   "node_create_char": node_create_char
               },
               startnode="node_race_select",
               cmd_on_exit=None,
               options_formatter=custom_formatter,
               node_formatter=node_formatter,
               options_separator="")
  
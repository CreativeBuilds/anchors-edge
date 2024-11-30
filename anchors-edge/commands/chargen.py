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
            "stats": "(+1 DEX, +1 CHA)",
            "subraces": {
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
                text += f"\n  ├─ |w{subrace}|n {subdesc}"
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
            
        return "node_name_select"
    
    options = {"key": "_default", "goto": _set_race}
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
            return "node_create_char"
        return None
    
    options = {"key": "_default", "goto": _set_name}
    return text, options

def node_create_char(caller):
    """Create the character."""
    menu = caller.ndb._menutree
    
    # Verify we have all required attributes
    if not hasattr(menu, 'race') or not hasattr(menu, 'charname'):
        caller.msg("Error: Missing required character information.")
        return "node_race_select"
    
    race = menu.race
    subrace = menu.subrace if hasattr(menu, 'subrace') else None
    charname = menu.charname
    
    # Create character
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
    
    # Link character to account
    caller.db._playable_characters.append(char)
    
    # Set account reference on character
    char.db.account = caller
    
    text = f"""
|c== Character Creation Complete! ==|n

|wCharacter Details:|n
Name: |y{charname}|n
Race: |y{race}{f" ({subrace})" if subrace else ""}|n

Your character has been created and is ready to enter the world.
Use |wcharselect {charname}|n to begin your adventure!
"""
    return text, None

class CmdCreateCharacter(Command):
    """
    Create a new character
    
    Usage:
        charcreate
    """
    key = "charcreate"
    locks = "cmd:pperm(Player)"
    help_category = "Character"
    
    def func(self):
        """Start character creation menu."""
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
                   "node_name_select": node_name_select,
                   "node_create_char": node_create_char
               },
               startnode="node_race_select",
               cmd_on_exit=None,
               options_formatter=custom_formatter,  # Use our custom formatter
               node_formatter=node_formatter,     # Use our custom node formatter
               options_separator="")    # This removes the separator line
  
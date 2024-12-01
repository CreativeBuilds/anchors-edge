"""
Character generation commands
"""
from evennia import Command
from evennia.utils.evmenu import EvMenu
from evennia.utils import create
from django.conf import settings
from evennia.utils.search import search_object
from textwrap import TextWrapper

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

def wrap_text(text, width=78):
    """Helper function to wrap text consistently."""
    wrapper = TextWrapper(width=width, expand_tabs=True, 
                         replace_whitespace=False,
                         break_long_words=False,
                         break_on_hyphens=False)
    
    # Split into lines, wrap each line separately to preserve formatting
    lines = text.split('\n')
    wrapped_lines = []
    
    for line in lines:
        if line.strip():  # Only wrap non-empty lines
            wrapped_lines.append(wrapper.fill(line))
        else:
            wrapped_lines.append(line)
            
    # Rejoin the lines
    return '\n'.join(wrapped_lines)

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
                # If they only entered the race name, go to subrace selection
                return "node_subrace_select"
            subrace = args[1]
            if subrace not in settings.AVAILABLE_RACES[race]["subraces"]:
                caller.msg(f"Invalid subrace for {race}. Available subraces: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
                return None
            # Store subrace on the menu
            caller.ndb._menutree.subrace = subrace
            
        return "node_background_select"
    
    options = {"key": "_default", "goto": _set_race}
    return wrap_text(text), options

def node_subrace_select(caller):
    """Select a subrace for the chosen race."""
    race = caller.ndb._menutree.race
    
    text = f"""
|c== Character Creation - Subrace Selection ==|n

You have chosen to play as a |y{race}|n.
Please select a subrace from the following options:

|wAvailable Subraces:|n"""
    
    # Display available subraces with their stats
    race_info = {
        "Human": {
            "normal": "(+1 DEX, +1 CHA) - Balanced and adaptable",
            "halfling": "(+1 DEX, +1 CHA) - Small but lucky"
        },
        "Elf": {
            "high": "(+2 INT, -1 CON, +1 WIS) - Magically attuned",
            "wood": "(+2 DEX, -1 INT, +1 WIS) - One with nature",
            "half": "(+2 CHA, -1 CON, +1 WIS) - Best of both worlds"
        },
        "Dwarf": {
            "mountain": "(+2 STR, -1 DEX, +1 CON) - Strong and hardy",
            "hill": "(+2 CON, -1 DEX, +1 WIS) - Wise and resilient"
        }
    }
    
    for subrace, desc in race_info[race].items():
        text += f"\n    - |w{subrace}|n {desc}"
    
    text += "\n\n|wEnter your choice:|n"
    
    def _set_subrace(caller, raw_string):
        """Handle subrace selection."""
        subrace = raw_string.strip().lower()
        if subrace not in settings.AVAILABLE_RACES[race]["subraces"]:
            caller.msg(f"Invalid subrace. Please choose from: {', '.join(settings.AVAILABLE_RACES[race]['subraces'])}")
            return None
            
        # Store subrace on the menu
        caller.ndb._menutree.subrace = subrace
        return "node_background_select"
    
    options = {"key": "_default", "goto": _set_subrace}
    return wrap_text(text), options

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
        text += f"\n    |wStat Changes:|n "
        for stat, mod in info['stats'].items():
            text += f"|W{stat} {'+' if mod > 0 else ''}{mod}|n "
    
    text += "\n\n|wEnter the name of your chosen background:|n"
    
    def _set_background(caller, raw_string):
        """Handle background selection."""
        background = raw_string.strip().title()
        if background not in settings.CHARACTER_BACKGROUNDS:
            caller.msg(f"Invalid background. Please choose from: {', '.join(settings.CHARACTER_BACKGROUNDS.keys())}")
            return None
            
        # Store background on the menu
        caller.ndb._menutree.background = background
        return "node_name_select"
    
    options = {"key": "_default", "goto": _set_background}
    return wrap_text(text), options

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
    return wrap_text(text), options

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
            return "node_final_confirm"
        elif choice == "no":
            if hasattr(caller.ndb._menutree, 'charname'):
                del caller.ndb._menutree.charname
            return "node_name_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _confirm_name}
    return wrap_text(text), options

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
    
    try:
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
            
        # Store race and background as tags
        char.tags.add(race.lower(), category="race")
        if subrace:
            char.tags.add(subrace.lower(), category="subrace")
        char.tags.add(background.lower(), category="background")
        
        # Store these for display purposes
        char.db.race = race
        char.db.subrace = subrace
        char.db.background = background
        
        # Add character to the list
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
        return wrap_text(text), None
        
    except Exception as e:
        caller.msg(f"Error creating character: {e}")
        if 'char' in locals() and char:
            char.delete()
        return None

def node_final_confirm(caller):
    """Final confirmation showing total stats."""
    menu = caller.ndb._menutree
    race = menu.race
    subrace = menu.subrace if hasattr(menu, 'subrace') else None
    charname = menu.charname
    background = menu.background
    
    # Create a temporary character to calculate stats
    temp_char = create.create_object(
        settings.BASE_CHARACTER_TYPECLASS,
        key="temp_" + charname,
        location=None,  # Don't place it in the game
        home=None
    )
    
    try:
        # Add the tags that will determine stats
        temp_char.tags.add(race.lower(), category="race")
        if subrace:
            temp_char.tags.add(subrace.lower(), category="subrace")
        temp_char.tags.add(background.lower(), category="background")
        
        # Get the calculated stats
        stats = temp_char.calculate_stats()
        
        text = f"""
|c== Character Creation - Final Review ==|n

Please review your character details carefully:

|wName:|n {charname}
|wRace:|n {race}{f" ({subrace})" if subrace else ""}
|wBackground:|n {background}

|wFinal Stats:|n
"""
        
        # Add stats with color coding
        for stat, value in stats.items():
            # Color code based on value compared to base stat (10)
            if value > 10:
                text += f"  |g{stat}: {value}|n"  # Green for above average
            elif value < 10:
                text += f"  |r{stat}: {value}|n"  # Red for below average
            else:
                text += f"  |w{stat}: {value}|n"  # White for average
            text += "\n"
        
        text += "\n|wAre you ready to create this character?|n"
        text += "\n|wEnter |gyes|w to create or |rno|w to start over:|n"
        
    finally:
        # Clean up the temporary character
        temp_char.delete()
    
    def _final_confirm(caller, raw_string):
        """Handle final confirmation."""
        choice = raw_string.strip().lower()
        if choice == "yes":
            return "node_create_char"
        elif choice == "no":
            # Clear all stored data
            if hasattr(caller.ndb._menutree, 'race'):
                del caller.ndb._menutree.race
            if hasattr(caller.ndb._menutree, 'subrace'):
                del caller.ndb._menutree.subrace
            if hasattr(caller.ndb._menutree, 'background'):
                del caller.ndb._menutree.background
            if hasattr(caller.ndb._menutree, 'charname'):
                del caller.ndb._menutree.charname
            return "node_race_select"
        else:
            caller.msg("Please enter 'yes' or 'no'.")
            return None
    
    options = {"key": "_default", "goto": _final_confirm}
    return wrap_text(text), options

class CmdCreateCharacter(Command):
    """
    Create a new character
    
    Usage:
        charcreate
    """
    key = "charcreate"
    locks = "cmd:all()"  # Allow all accounts to use this command
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
                   "node_subrace_select": node_subrace_select,
                   "node_background_select": node_background_select,
                   "node_name_select": node_name_select,
                   "node_name_confirm": node_name_confirm,
                   "node_final_confirm": node_final_confirm,
                   "node_create_char": node_create_char
               },
               startnode="node_race_select",
               cmd_on_exit=None,
               options_formatter=custom_formatter,
               node_formatter=node_formatter,
               options_separator="")
  
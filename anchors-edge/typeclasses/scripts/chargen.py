from evennia import Command, CmdSet
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
    text = "Choose your race:\n"
    for race in settings.AVAILABLE_RACES:
        text += f"\n|w{race}|n"
        
    options = []
    for race in settings.AVAILABLE_RACES:
        options.append({"key": race.lower(),
                       "desc": race,
                       "goto": "node_subrace_select" if settings.AVAILABLE_RACES[race].get("subraces") else "node_name_select"})
    
    return text, options

def node_subrace_select(caller, raw_string):
    """Select character subrace if applicable."""
    race = caller.ndb._menutree.race.capitalize()
    
    text = f"Choose your {race} subrace:\n"
    for subrace in settings.AVAILABLE_RACES[race]["subraces"]:
        text += f"\n|w{subrace}|n"
        
    options = []
    for subrace in settings.AVAILABLE_RACES[race]["subraces"]:
        options.append({"key": subrace.lower(),
                       "desc": subrace,
                       "goto": "node_name_select"})
    
    return text, options

def node_name_select(caller):
    """Select character name."""
    text = "Choose your character name (single word):"
    
    def _callback(caller, raw_string):
        if _check_name(caller, raw_string):
            caller.ndb._menutree.charname = raw_string
            return "node_create_char"
        return "node_name_select"
    
    return text, _callback

def node_create_char(caller):
    """Create the character."""
    race = caller.ndb._menutree.race
    subrace = caller.ndb._menutree.subrace if hasattr(caller.ndb._menutree, "subrace") else None
    charname = caller.ndb._menutree.charname
    
    # Create character
    char = create.create_object(
        settings.BASE_CHARACTER_TYPECLASS,
        key=charname,
        location=settings.DEFAULT_HOME,
        home=settings.DEFAULT_HOME,
        permissions=["Player"])
        
    # Apply racial modifiers
    char.apply_racial_modifiers(race, subrace)
    
    # Link character to account
    caller.db._playable_characters.append(char)
    
    text = f"""
Character created!
Name: {charname}
Race: {race}{f" ({subrace})" if subrace else ""}

You can now enter the game with your new character.
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
    help_category = "General"
    
    def func(self):
        """Start character creation menu."""
        EvMenu(self.caller, "typeclasses.scripts.chargen",
               startnode="node_race_select",
               cmd_on_exit=None) 
"""
Character selection and management commands
"""

from evennia import Command
from evennia.utils import search
from evennia.utils.evmenu import EvMenu

class CmdCharList(Command):
    """
    List available characters

    Usage:
        charlist
    """
    key = "charlist"
    locks = "cmd:pperm(Player)"
    help_category = "Character"

    def func(self):
        """Show available characters"""
        caller = self.caller
        characters = caller.db._playable_characters
        
        if not characters:
            caller.msg("You have no characters. Use |wcharcreate|n to make one!")
            return
            
        caller.msg("|wYour available characters:|n")
        for char in characters:
            status = "  (Online)" if char.has_account else ""
            caller.msg(f"- |c{char.key}|n [{char.db.race}{f' - {char.db.subrace}' if char.db.subrace else ''}]{status}")
        caller.msg("\nUse |wcharselect <name>|n to play as a character.")

class CmdCharSelect(Command):
    """
    Select a character to play

    Usage:
        charselect <character name>
    """
    key = "charselect"
    locks = "cmd:pperm(Player)"
    help_category = "Character"

    def func(self):
        """Handle character selection"""
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: charselect <character name>")
            return
            
        # Find character
        char_name = self.args.strip()
        characters = [char for char in caller.db._playable_characters 
                     if char.key.lower() == char_name.lower()]
        
        if not characters:
            caller.msg("You don't have a character by that name.")
            return
            
        char = characters[0]
        
        # Check if character is already being played
        if char.has_account:
            if char.has_account == caller:
                caller.msg("You are already playing this character!")
            else:
                caller.msg("This character is already being played.")
            return
            
        # Try to puppet the character
        try:
            caller.puppet_object(session=self.session, obj=char)
            char.msg("|gYou become |c%s|n." % char.name)
            
            # If successful, move character to their proper location
            if not char.location:
                char.location = char.home
            
            # Show the room to the character
            char.execute_cmd('look')
            
        except RuntimeError as err:
            caller.msg("|rError assuming character:|n %s" % err) 
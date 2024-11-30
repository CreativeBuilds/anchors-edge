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
    locks = "cmd:pperm(Player) and not puppeting"
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
    locks = "cmd:pperm(Player) and not puppeting"
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

class CmdSignout(Command):
    """
    Stop playing your current character and return to character selection.
    
    Usage:
        signout
    """
    key = "signout"
    locks = "cmd:pperm(Player) and puppeting"
    help_category = "Character"
    
    def func(self):
        """Handle the signout"""
        caller = self.caller
        
        if not caller.account:
            caller.msg("You're not currently playing a character.")
            return
            
        # Get the account and session
        account = caller.account
        session = self.session
        
        # Unpuppet the character
        account.unpuppet_object(session)
        
        # Show the character selection screen
        selection_room = search_object('Character Selection', typeclass='typeclasses.rooms.character_select.CharacterSelectRoom')
        if selection_room:
            selection_room = selection_room[0]
            session.msg("\n" * 20)  # Clear screen
            session.msg(selection_room.return_appearance(session))
            
            # Show character list
            characters = account.db._playable_characters
            if characters:
                session.msg("\n|wYour available characters:|n")
                for char in characters:
                    status = "  (Online)" if char.has_account else ""
                    session.msg(f"- |c{char.key}|n [{char.db.race}{f' - {char.db.subrace}' if char.db.subrace else ''}]{status}")
                session.msg("\nUse |wcharselect <name>|n to play as a character or |wcharcreate|n to make a new one.")
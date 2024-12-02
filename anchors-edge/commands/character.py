"""
Character selection and management commands
"""

from evennia import Command
from evennia.utils import search
from evennia.utils.evmenu import EvMenu
from evennia.utils.utils import string_similarity

class CmdCharList(Command):
    """
    List available characters

    Usage:
        charlist
    """
    key = "charlist"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        """Show available characters"""
        caller = self.caller
        
        # Initialize _playable_characters if it doesn't exist or is None
        if not hasattr(caller.db, '_playable_characters') or caller.db._playable_characters is None:
            caller.db._playable_characters = []
        
        # Ensure it's a list
        if not isinstance(caller.db._playable_characters, list):
            caller.db._playable_characters = list(caller.db._playable_characters)
        
        # Filter for valid character objects
        valid_characters = []
        for char in caller.db._playable_characters:
            if (char and 
                hasattr(char, 'is_typeclass') and 
                char.is_typeclass('typeclasses.characters.Character')):
                valid_characters.append(char)
        
        # Update the list to only include valid characters
        caller.db._playable_characters = valid_characters
        
        if not valid_characters:
            caller.msg("You have no characters. Use |wcharcreate|n to make one!")
            return
            
        caller.msg("|wYour available characters:|n")
        for char in valid_characters:
            race_info = f"[{char.db.race}{f' - {char.db.subrace}' if hasattr(char.db, 'subrace') and char.db.subrace else ''}]"
            status = "  (Online)" if char.has_account else ""
            caller.msg(f"- |c{char.key}|n {race_info}{status}")
        caller.msg("\nUse |wcharselect <name>|n to play as a character.")

class CmdCharSelect(Command):
    """
    Select a character to play

    Usage:
        charselect <character name>
    """
    key = "charselect"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        """Handle character selection"""
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: charselect <character name>")
            return
            
        # Get input name and convert to lowercase for comparison
        input_name = self.args.strip()
        
        # Debug output
        caller.msg(f"Debug: Looking for character '{input_name}'")
        caller.msg(f"Debug: Available characters: {[char.key for char in caller.db._playable_characters if char]}")
        
        # Find character by exact name first
        matches = [char for char in caller.db._playable_characters 
                  if char and char.key == input_name]
        
        # If no exact match, try case-insensitive
        if not matches:
            matches = [char for char in caller.db._playable_characters 
                      if char and char.key.lower() == input_name.lower()]
            
        # If still no match, try partial match
        if not matches:
            matches = [char for char in caller.db._playable_characters 
                      if char and input_name.lower() in char.key.lower()]
        
        if not matches:
            caller.msg("You don't have a character by that name.")
            return
            
        if len(matches) > 1:
            # Multiple matches - show options
            caller.msg("Multiple matches found:")
            for char in matches:
                caller.msg(f"- {char.key}")
            caller.msg("Please be more specific.")
            return
            
        # We have exactly one match
        char = matches[0]
        
        # Debug output
        caller.msg(f"Debug: Found character: {char.key}")
        
        # Check if character is already being played
        if char.has_account:
            if char.has_account == caller:
                caller.msg("You are already playing this character!")
            else:
                caller.msg("This character is already being played.")
            return
            
        # Get the account object
        account = caller
        if hasattr(caller, 'account'):
            account = caller.account
            
        # Try to puppet the character
        try:
            account.puppet_object(session=self.session, obj=char)
            # Store this as the last played character
            account.db.last_puppet = char
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
        logout
        signout
    """
    key = "logout"
    aliases = ["signout"]
    locks = "cmd:puppeting"
    help_category = "Character"
    
    def func(self):
        """Handle the signout"""
        caller = self.caller
        
        if hasattr(caller, 'account') and caller.account:
            account = caller.account
            session = self.session
        else:
            self.msg("You're not currently playing a character.")
            return
            
        # Store the last puppet before unpuppeting
        account.db.last_puppet = caller
        
        # Unpuppet the character
        account.unpuppet_object(session)
        
        # Show the character selection screen
        selection_room = search_object('Character Selection', typeclass='typeclasses.rooms.character_select.CharacterSelectRoom')
        if selection_room:
            selection_room = selection_room[0]
            session.msg("\n" * 20)  # Clear screen
            session.msg(selection_room.return_appearance(account))  # Changed from session to account
            
            # Show character list
            characters = account.db._playable_characters
            if characters:
                session.msg("\n|wYour available characters:|n")
                for char in characters:
                    if char:  # Make sure character exists
                        status = "  (Online)" if char.has_account else ""
                        session.msg(f"- |c{char.key}|n [{char.db.race}{f' - {char.db.subrace}' if hasattr(char.db, 'subrace') and char.db.subrace else ''}]{status}")
                session.msg("\nUse |wcharselect <name>|n to play as a character or |wcharcreate|n to make a new one.")

class CmdIC(Command):
    """
    Enter the game as your last played character.
    If no last character exists, shows your available characters.
    
    Usage:
        ic
    """
    key = "ic"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Handle the IC command"""
        caller = self.caller
        
        # Get the last played character
        last_char = caller.db.last_puppet
        
        if not last_char:
            # No last character, show character list
            caller.msg("No recent character found. Please select one:")
            caller.execute_cmd("charlist")
            return
            
        # Check if character still exists and is valid
        if not (last_char and hasattr(last_char, 'is_typeclass') and 
                last_char.is_typeclass('typeclasses.characters.Character')):
            caller.msg("Your last character is no longer available.")
            caller.execute_cmd("charlist")
            return
            
        # Try to puppet the character
        try:
            caller.puppet_object(session=self.session, obj=last_char)
            last_char.msg("|gYou become |c%s|n." % last_char.name)
            
            # If successful, move character to their proper location
            if not last_char.location:
                last_char.location = last_char.home
            
            # Show the room to the character
            last_char.execute_cmd('look')
            
        except RuntimeError as err:
            caller.msg("|rError assuming character:|n %s" % err)
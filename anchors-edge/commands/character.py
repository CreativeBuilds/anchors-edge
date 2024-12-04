"""
Character commands module.
"""

from evennia import Command
from evennia.utils.evmenu import EvMenu
from typeclasses.relationships import KnowledgeLevel, get_brief_description, get_basic_description, get_full_description
from difflib import SequenceMatcher

def string_similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

class CmdCharList(Command):
    """
    List available characters
    
    Usage:
        charlist
        cl
    """
    key = "charlist"
    aliases = ["characters", "cl"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute command."""
        characters = self.caller.db._playable_characters
        if not characters:
            self.caller.msg("You have no characters. Use |wcharcreate|n to make one!")
            return
            
        # Show list of characters
        string = "\n|wYour available characters:|n\n"
        for char in characters:
            string += f"\n - {char.key}"
        self.caller.msg(string)

class CmdCharSelect(Command):
    """
    select a character to play
    
    Usage:
      charselect <character>
      ic <character>
      cs <character>
      
    Switch to play the given character, if you have created it.
    You can use partial names - the system will try to match the closest character.
    """
    key = "charselect"
    aliases = ["charselect", "ic", "cs"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("Usage: charselect <character>")
            return
            
        # Find character
        characters = self.caller.db._playable_characters
        char_name = self.args.strip()
        
        char = None
        for test_char in characters:
            if test_char.key.lower() == char_name.lower():
                char = test_char
                break
                
        if not char:
            # Try fuzzy matching
            matches = []
            for test_char in characters:
                ratio = string_similarity(char_name, test_char.key)
                if ratio > 0.2:  # Even lower threshold for more lenient matching
                    matches.append((test_char, ratio))
                    
            # Sort matches by ratio, highest first
            matches.sort(key=lambda x: x[1], reverse=True)
            
            if matches:
                if len(matches) == 1 or matches[0][1] > 0.5:  # Lower confidence threshold
                    char = matches[0][0]
                else:
                    self.caller.msg("Multiple matches found. Please be more specific:")
                    for match, ratio in matches:
                        self.caller.msg(f" - {match.key}")
                    return
                    
        if not char:
            self.caller.msg(f"No character found named '{char_name}'")
            return
            
        # Try to puppet/control the character
        try:
            self.caller.puppet_object(self.session, char)
            self.caller.msg(f"\nYou become |w{char.name}|n.\n")
        except RuntimeError as err:
            self.caller.msg("|rError assuming character:|n %s" % err)

class CmdSignout(Command):
    """
    Stop puppeting the current character and go OOC, or disconnect from the game
    
    Usage:
        signout
        quit
    """
    key = "signout"
    aliases = ["quit"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute command."""
        if hasattr(self.caller, 'account') and self.caller.account:
            # We're a character object
            charname = self.caller.name
            account = self.caller.account
            account.unpuppet_object(self.session)
            account.msg(f"\nYou stop being |w{charname}|n.\n")
        else:
            # We're an account or something else, disconnect from the game
            self.caller.msg("\nGoodbye! Disconnecting...\n")
            self.caller.disconnect_session_from_account(self.session)

class CmdIntro(Command):
    """
    Introduce yourself to another character.
    
    Usage:
        intro <character description>
        
    This will reveal your name to the character and allow them
    to see more details about your appearance. You can use partial
    descriptions to find characters, like "ta fe fel" for "tall female feline".
    If multiple characters match, you'll need to be more specific.
    """
    
    key = "intro"
    aliases = ["introduce"]
    locks = "cmd:puppeted()"
    help_category = "Social"
    
    def func(self):
        # Check if the caller is a character
        if not self.caller.has_account:
            self.caller.msg("You must be controlling a character to use this command.")
            return
            
        if not self.args:
            self.caller.msg("Usage: intro <character description>")
            return
            
        # Try to find the character based on description
        target = self.caller.find_character_by_desc(self.args)
        
        if target is None:
            self.caller.msg(f"Could not find '{self.args}'.")
            return
            
        if target == "ambiguous":
            self.caller.msg("Multiple characters match that description. Please be more specific.")
            # Show numbered descriptions if they exist
            chars = [obj for obj in self.caller.location.contents 
                    if hasattr(obj, 'get_display_name') and obj != self.caller]
            numbered_descs = [getattr(char, 'temp_numbered_desc', char.get_display_name(self.caller)) 
                            for char in chars if hasattr(char, 'temp_numbered_desc')]
            if numbered_descs:
                self.caller.msg("Matching characters: " + ", ".join(numbered_descs))
            return
            
        # Can't introduce to yourself
        if target == self.caller:
            self.caller.msg("You already know yourself!")
            return
            
        # Initialize relationships dicts if they don't exist
        if not self.caller.db.known_by:
            self.caller.db.known_by = {}
        if not target.db.known_by:
            target.db.known_by = {}
            
        # Perform the introduction
        self.caller.introduce_to(target)
        
        # Check if this is a mutual introduction
        is_mutual = target.knows_character(self.caller)
        
        # Get the appropriate display name based on mutual status
        target_display = target.name if is_mutual else target.get_display_name(self.caller)
        
        # Notify both parties
        self.caller.msg(f"You introduce yourself to {target.get_display_name(self.caller)}.")
        target.msg(f"{self.caller.get_display_name(target)} introduces themselves to you.")
        
        # Notify the room
        self.caller.location.msg_contents(
            f"{self.caller.get_display_name(target)} introduces themselves to {target.get_display_name(self.caller)}.",
            exclude=[self.caller, target]
        )
        
        # If mutual introduction, notify both parties
        if is_mutual:
            self.caller.msg(f"As they have already introduced themselves to you, you now know them as {target.name}.")
            target.msg(f"Having already introduced yourself to them, they now know you as {target.name}.")

class CmdLongIntro(Command):
    """
    Formally introduce yourself to another character.
    
    Usage:
        longintro <character>
        
    This establishes a deeper connection with the character,
    allowing you to see their full description and message
    them from anywhere. Both characters must be mutually
    introduced first, and both must use longintro for the
    full connection to be established.
    """
    
    key = "longintro"
    locks = "cmd:puppeted()"
    help_category = "Social"
    
    def func(self):
        if not self.args:
            self.caller.msg("Usage: longintro <character>")
            return
            
        target = self.caller.search(self.args)
        if not target:
            return
            
        # Check if target is a character
        if not hasattr(target, 'is_character') or not target.is_character:
            self.caller.msg("You can only introduce yourself to other characters.")
            return
            
        # Initialize relationships dicts if they don't exist
        if not self.caller.db.known_by:
            self.caller.db.known_by = {}
        if not target.db.known_by:
            target.db.known_by = {}
            
        # Check if they're mutually introduced
        if not (target.id in self.caller.db.known_by and self.caller.id in target.db.known_by):
            self.caller.msg(f"You need to be mutually introduced with {target.name} first.")
            return
            
        # Check if they're already friends
        if (target.id in self.caller.db.known_by and 
            self.caller.db.known_by[target.id] == KnowledgeLevel.FRIEND):
            self.caller.msg(f"You've already formally introduced yourself to {target.name}.")
            return
            
        # Set knowledge level to FRIEND for caller's side
        self.caller.db.known_by[target.id] = KnowledgeLevel.FRIEND
        
        # Check if this completes a mutual formal introduction
        is_mutual_formal = (target.id in self.caller.db.known_by and 
                          self.caller.id in target.db.known_by and
                          target.db.known_by[self.caller.id] == KnowledgeLevel.FRIEND)
        
        # Notify both parties
        self.caller.msg(f"You formally introduce yourself to {target.name}.")
        target.msg(f"{self.caller.name} formally introduces themselves to you.")
        
        if is_mutual_formal:
            self.caller.msg(f"|gYou and {target.name} are now formally introduced and can message each other from anywhere.|n")
            target.msg(f"|gYou and {self.caller.name} are now formally introduced and can message each other from anywhere.|n")

class CmdQuit(Command):
    """
    quit from the game
    
    Usage:
        quit
        ooc
        
    This will disconnect you from the game. Reconnect to select a different character.
    """
    key = "quit"
    aliases = ["q", "ooc", "@ooc"]
    locks = "cmd:all()"

    def func(self):
        """Hook function"""
        account = self.account
        session = self.session
        
        # Send a goodbye message
        self.msg("\nDisconnecting from the game. Goodbye!")
        
        # Disconnect all sessions for this account
        for session in account.sessions.all():
            session.sessionhandler.disconnect(session)

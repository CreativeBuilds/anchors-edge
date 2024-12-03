"""
Character commands module.
"""

from evennia import Command
from evennia.utils.evmenu import EvMenu
from evennia.utils.utils import string_similarity
from typeclasses.relationships import KnowledgeLevel, get_brief_description, get_basic_description, get_full_description

class CmdCharList(Command):
    """
    List available characters
    
    Usage:
        charlist
    """
    key = "charlist"
    aliases = ["characters"]
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
    Select a character to play
    
    Usage:
        charselect <character>
    """
    key = "charselect"
    aliases = ["select"]
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
                if ratio > 0.7:
                    matches.append(test_char)
                    
            if len(matches) == 1:
                char = matches[0]
            elif len(matches) > 1:
                self.caller.msg("Multiple matches found. Please be more specific:")
                for match in matches:
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
    Stop puppeting the current character and go OOC
    
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
            # We're already an account or something else
            self.caller.msg("You're not currently playing a character!")
            return

class CmdIC(Command):
    """
    Control a character
    
    Usage:
        ic <character>
    """
    key = "ic"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("Usage: ic <character>")
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
            self.caller.msg(f"No character found named '{char_name}'")
            return
            
        # Try to puppet/control the character
        try:
            self.caller.puppet_object(self.session, char)
            self.caller.msg(f"\nYou become |w{char.name}|n.\n")
        except RuntimeError as err:
            self.caller.msg("|rError assuming character:|n %s" % err)

class CmdIntro(Command):
    """
    Introduce yourself to another character.
    
    Usage:
        intro <character>
        
    This will reveal your name to the character and allow them
    to see more details about your appearance. For full mutual
    introduction, both characters need to introduce themselves.
    """
    
    key = "intro"
    locks = "cmd:puppeted()"
    help_category = "Social"
    
    def func(self):
        if not self.args:
            self.caller.msg("Usage: intro <character>")
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
            
        # Set knowledge level to ACQUAINTANCE
        self.caller.db.known_by[target.id] = KnowledgeLevel.ACQUAINTANCE
        
        # Check if this is a mutual introduction
        is_mutual = (target.id in self.caller.db.known_by and 
                    self.caller.id in target.db.known_by)
        
        # Notify both parties
        self.caller.msg(f"You introduce yourself to {target.name}.")
        target.msg(f"{self.caller.name} introduces themselves to you.")
        
        if is_mutual:
            self.caller.msg(f"You and {target.name} are now mutually introduced.")
            target.msg(f"You and {self.caller.name} are now mutually introduced.")

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

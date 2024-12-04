"""
Character commands module.
"""

from evennia import Command
from evennia.utils.evmenu import EvMenu
from typeclasses.relationships import KnowledgeLevel, get_brief_description, get_basic_description, get_full_description
from difflib import SequenceMatcher
from django.conf import settings
import re
from unicodedata import normalize

def string_similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def sanitize_input(text):
    """
    Sanitize input text by:
    - Normalizing Unicode characters
    - Removing control characters
    - Removing invalid characters
    
    Args:
        text (str): Input text to sanitize
    
    Returns:
        str: Sanitized text
        bool: Whether text was valid
    """
    if not text:
        return "", False
        
    try:
        # Normalize Unicode characters
        normalized = normalize('NFKC', text)
        
        # Remove control characters except newlines
        cleaned = ''.join(char for char in normalized 
                         if char == '\n' or (ord(char) >= 32 and ord(char) != 127))
                         
        # Check for invalid characters
        invalid_pattern = r'[^\w\s\-\'"]'
        if re.search(invalid_pattern, cleaned):
            return "", False
            
        return cleaned.strip(), True
        
    except UnicodeError:
        return "", False

def validate_name(name):
    """
    Validate a character name.
    
    Args:
        name (str): Name to validate
    
    Returns:
        tuple: (cleaned_name, error_message)
    """
    # Sanitize input
    cleaned, valid = sanitize_input(name)
    if not valid:
        return "", "Name contains invalid characters. Please use only letters, numbers, and basic punctuation."
        
    # Check length
    if len(cleaned) < 2 or len(cleaned) > 20:
        return "", "Name must be between 2 and 20 characters long."
        
    # Check for single word
    if len(cleaned.split()) > 1:
        return "", "Name must be a single word."
        
    # Additional name validation rules can be added here
        
    return cleaned, None

def validate_description(desc):
    """
    Validate a character description.
    
    Args:
        desc (str): Description to validate
    
    Returns:
        tuple: (cleaned_desc, error_message)
    """
    # Sanitize input
    cleaned, valid = sanitize_input(desc)
    if not valid:
        return "", "Description contains invalid characters. Please use only letters, numbers, and basic punctuation."
        
    # Check length
    if len(cleaned) < 10:
        return "", "Description must be at least 10 characters long."
        
    if len(cleaned) > 1000:
        return "", "Description must be less than 1000 characters."
        
    return cleaned, None

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
        
        # Get current time for idle calculation
        from time import time
        current_time = time()
        
        # Get idle timeout from settings (default to 600 if not set)
        idle_timeout = getattr(settings, 'CHARACTER_IDLE_TIMEOUT', 600)
        
        for char in characters:
            # Get last command time from the character's session
            if char.sessions.all():
                session = char.sessions.all()[0]
                idle_time = current_time - session.cmd_last_visible
                # Show (idle) if more than idle_timeout with no activity
                if idle_time > idle_timeout:
                    string += f"\n - {char.key} |w(idle)|n"
                else:
                    string += f"\n - {char.key}"
            else:
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
    locks = "cmd:puppet()"
    help_category = "Social"
    
    def match_description(self, desc, obj):
        """Check if description matches object"""
        if not hasattr(obj, 'get_display_name'):
            return False
        display = obj.get_display_name(self.caller).lower()
        desc_parts = desc.lower().split()
        return all(part in display for part in desc_parts)
    
    def func(self):
        # Check if the caller is a character
        if not self.caller.has_account:
            self.caller.msg("You must be controlling a character to use this command.")
            return
            
        if not self.args:
            self.caller.msg("Usage: intro <character description>")
            return
            
        # Find all characters in the room that match the description
        matches = []
        for obj in self.caller.location.contents:
            if obj != self.caller and hasattr(obj, 'has_account') and obj.has_account:
                if self.match_description(self.args, obj):
                    matches.append(obj)
        
        if not matches:
            self.caller.msg(f"Could not find anyone matching '{self.args}'.")
            return
            
        if len(matches) > 1:
            self.caller.msg("Multiple characters match that description. Please be more specific:")
            for char in matches:
                display = char.get_display_name(self.caller)
                display = display[0].lower() + display[1:].rstrip('.')
                self.caller.msg(f" - {display}")
            return
            
        target = matches[0]
        
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
        is_mutual = self.caller.knows_character(target) and target.knows_character(self.caller)
        
        # Get the appropriate display name based on mutual status
        target_display = target.name if is_mutual else target.generate_basic_description()
        target_display = target_display[0].lower() + target_display[1:].rstrip('.')
        caller_display = self.caller.generate_basic_description().rstrip('.')
        target_basic = target.generate_basic_description().rstrip('.')
        
        # Notify both parties
        self.caller.msg(f"You introduce yourself to {target_display}.")
        target.msg(f"{caller_display} introduces themselves to you as {self.caller.name}.")
        
        
        
        # Notify the room
        self.caller.location.msg_contents(
            f"{caller_display} introduces themselves to {target_basic}.",
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
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        # If we're a character, get our account
        account = self.caller.account if hasattr(self.caller, 'account') else self.caller
        
        # Check if we're a character without an account
        if not hasattr(self.caller, 'account') or not self.caller.account:
            self.caller.msg("You need to select a character first!")
            return
            
        if not self.args:
            self.caller.msg("Usage: longintro <character>")
            return
        
        target = self.caller.search(self.args)
        if not target:
            return
        
        # Check if target is a character
        if not target.is_typeclass('typeclasses.characters.Character'):
            self.caller.msg("You can only introduce yourself to other characters.")
            return
            
        # Initialize relationships dicts if they don't exist
        if not self.caller.db.known_by:
            self.caller.db.known_by = {}
        if not target.db.known_by:
            target.db.known_by = {}
            
        target_basic = target.generate_basic_description().rstrip('.')
            
        # Check if they have at least acquaintance status with each other
        if not (target.id in self.caller.db.known_by and 
                self.caller.db.known_by[target.id] >= KnowledgeLevel.ACQUAINTANCE and
                self.caller.id in target.db.known_by and 
                target.db.known_by[self.caller.id] >= KnowledgeLevel.ACQUAINTANCE):
            self.caller.msg(f"You need to be at least acquainted with the {target_basic} first.")
            return
            
        # Check if target is already friends with caller
        if (self.caller.id in target.db.known_by and 
            target.db.known_by[self.caller.id] == KnowledgeLevel.FRIEND):
            self.caller.msg(f"You've already formally introduced yourself to {target.name}.")
            return
            
        # Set knowledge level to FRIEND for target's side
        target.db.known_by[self.caller.id] = KnowledgeLevel.FRIEND
        
        # Check if this completes a mutual formal introduction
        is_mutual_formal = (target.id in self.caller.db.known_by and 
                          self.caller.id in target.db.known_by and
                          target.db.known_by[self.caller.id] == KnowledgeLevel.FRIEND and
                          self.caller.db.known_by[target.id] == KnowledgeLevel.FRIEND)
        
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

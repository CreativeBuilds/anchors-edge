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
from utils.text_formatting import format_sentence

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

def get_pronoun(character, pronoun_type="reflexive"):
    """
    Get the appropriate pronoun based on character's gender.
    
    Args:
        character: The character object
        pronoun_type (str): Type of pronoun to return:
            - "reflexive" (e.g., himself/herself/themselves)
            - "subjective" (e.g., he/she/they)
            - "objective" (e.g., him/her/them)
            - "possessive" (e.g., his/her/their)
    
    Returns:
        str: The appropriate pronoun
    """
    gender = character.db.gender.lower() if hasattr(character.db, 'gender') else "their"
    
    pronouns = {
        "male": {
            "reflexive": "himself",
            "subjective": "he",
            "objective": "him",
            "possessive": "his"
        },
        "female": {
            "reflexive": "herself",
            "subjective": "she",
            "objective": "her",
            "possessive": "her"
        },
        "their": {
            "reflexive": "themselves",
            "subjective": "they",
            "objective": "them",
            "possessive": "their"
        }
    }
    
    return pronouns.get(gender, pronouns["their"])[pronoun_type]

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
        # Check if we're already puppeting a character
        if hasattr(self.caller, 'character') and self.caller.character:
            self.caller.msg("You are already playing a character.")
            return
            
        if not self.args:
            self.caller.msg("Usage: charselect <character>")
            return
            
        # Find character
        characters = self.caller.db._playable_characters or []
        char_name = self.args.strip()
        
        char = None
        for test_char in characters:
            if test_char and hasattr(test_char, 'key') and test_char.key and test_char.key.lower() == char_name.lower():
                char = test_char
                break
                
        if not char:
            # Try fuzzy matching
            matches = []
            for test_char in characters:
                if test_char and hasattr(test_char, 'key') and test_char.key:
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
        
        # Check if caller has already introduced their self to target
        if target.knows_character(self.caller):
            self.caller.msg(f"You have already introduced yourself to them.")
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
        target_display = target.name if is_mutual else get_brief_description(target)
        target_display = target_display[0].lower() + target_display[1:].rstrip('.')
        caller_display = get_brief_description(self.caller).rstrip('.')
        target_basic = get_brief_description(target).rstrip('.')
        
        # Get pronouns for both characters
        caller_reflexive = get_pronoun(self.caller, "reflexive")
        target_reflexive = get_pronoun(target, "reflexive")
        
        # Notify both parties
        self.caller.msg(f"You introduce yourself to {target_display}.")
        target.msg(f"{caller_display} introduces {caller_reflexive} to you as {self.caller.name}.")
        
        # Notify the room with custom messages based on knowledge level
        for obj in self.caller.location.contents:
            if obj not in [self.caller, target] and hasattr(obj, 'has_account') and obj.has_account:
                # Get display names based on observer's knowledge
                caller_name = self.caller.get_display_name(obj) if obj.knows_character(self.caller) else caller_display
                target_name = target.get_display_name(obj) if obj.knows_character(target) else target_basic
                
                # Format names to start lowercase
                caller_name = caller_name[0].lower() + caller_name[1:].rstrip('.')
                target_name = target_name[0].lower() + target_name[1:].rstrip('.')
                
                # Send customized message
                obj.msg(format_sentence(f"{caller_name} introduces {caller_reflexive} to {target_name}."))
        
        # If mutual introduction, notify both parties
        if is_mutual:
            self.caller.msg(f"As they have already introduced {target_reflexive} to you, you now know them as {target.name}.")
            target.msg(f"Having already introduced {target_reflexive} to them, they now know you as {target.name}.")

class CmdIntroLong(Command):
    """
    Give a longer introduction to someone, sharing more details about yourself.
    
    Usage:
      introlong <character>
    """
    key = "introlong"
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        """Handle the long introduction."""
        try:
            if not self.args:
                self.caller.msg("Usage: introlong <character>")
                return
                
            # Find target
            target = self.caller.search(self.args)
            if not target:
                return
                
            # Can't introduce to yourself
            if target == self.caller:
                self.caller.msg("You already know yourself!")
                return
                
            # Get descriptions for messages
            caller_basic = get_brief_description(self.caller)
            target_basic = get_brief_description(target)
            
            # Get pronouns using the get_pronoun function
            caller_reflexive = get_pronoun(self.caller, "reflexive")
            target_reflexive = get_pronoun(target, "reflexive")
            
            # Check if target already knows caller
            if target.knows_character(self.caller):
                self.caller.msg(f"They already know who you are.")
                return
                
            # Set knowledge level to FAMILIAR
            target.set_knowledge(self.caller, KnowledgeLevel.FAMILIAR)
            
            # Notify both parties
            self.caller.msg(f"You share more details about yourself with {target_basic}.")
            target.msg(f"{caller_basic} shares more details about {caller_reflexive} with you.")
            
            # Notify the room
            for obj in self.caller.location.contents:
                if obj not in [self.caller, target] and hasattr(obj, 'msg'):
                    obj.msg(format_sentence(f"{caller_basic} shares more details about {caller_reflexive} with {target_basic}."))
        except Exception as err:
            from utils.error_handler import handle_error
            handle_error(self.caller, err)
            return

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

class CmdIntroList(Command):
    """
    List all characters you know at the acquaintance level or higher.

    Usage:
      intro list
      introlist
    """
    key = "intro list"
    aliases = ["introlist"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        """List known characters with brief descriptions."""
        if not hasattr(self.caller.db, 'known_by') or not self.caller.db.known_by:
            self.caller.msg("You haven't been introduced to anyone yet.")
            return

        # Get all characters you know at acquaintance level or higher
        known_chars = []
        from evennia.objects.models import ObjectDB
        for char_id, knowledge_level in self.caller.db.known_by.items():
            if knowledge_level >= KnowledgeLevel.ACQUAINTANCE:
                char = ObjectDB.objects.get_id(char_id)
                if char:
                    known_chars.append((char, knowledge_level))

        if not known_chars:
            self.caller.msg("You haven't been introduced to anyone yet.")
            return

        # Sort by knowledge level (highest first) then name
        known_chars.sort(key=lambda x: (-x[1], x[0].name if hasattr(x[0], 'name') else ''))

        from evennia.utils.evtable import EvTable
        table = EvTable("|wName|n", "|wLevel|n", table=None, border="header")

        for char, level in known_chars:
            level_name = KnowledgeLevel(level).name.capitalize()
            table.add_row(char.name, level_name)

        self.caller.msg("|wCharacters you know:|n")
        self.caller.msg(table)

class CmdIntroLongList(Command):
    """
    List all characters you know with detailed descriptions.

    Usage:
      intro long list
      introlonglist
    """
    key = "intro long list"
    aliases = ["introlonglist", "introlong list"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        """List known characters with detailed descriptions."""
        if not hasattr(self.caller.db, 'known_by') or not self.caller.db.known_by:
            self.caller.msg("You haven't been introduced to anyone yet.")
            return

        # Get all characters you know at acquaintance level or higher
        known_chars = []
        from evennia.objects.models import ObjectDB
        for char_id, knowledge_level in self.caller.db.known_by.items():
            if knowledge_level >= KnowledgeLevel.ACQUAINTANCE:
                char = ObjectDB.objects.get_id(char_id)
                if char:
                    known_chars.append((char, knowledge_level))

        if not known_chars:
            self.caller.msg("You haven't been introduced to anyone yet.")
            return

        # Sort by knowledge level (highest first) then name
        known_chars.sort(key=lambda x: (-x[1], x[0].name if hasattr(x[0], 'name') else ''))

        # Display each character with appropriate description based on knowledge level
        self.caller.msg("|wCharacters you know:|n")
        for char, level in known_chars:
            level_name = KnowledgeLevel(level).name.capitalize()
            
            # Get appropriate description based on knowledge level
            if level >= KnowledgeLevel.FRIEND:
                desc = get_full_description(char)
            else:
                desc = get_basic_description(char)
                
            # Add roleplay status if available
            if hasattr(char, 'get_rstatus'):
                rstatus = char.get_rstatus()
                if rstatus:
                    desc += f"\n|w(Currently: {rstatus})|n"
                    
            self.caller.msg(f"\n|c{char.name}|n - |w{level_name}|n\n{desc}")

# Add to command set
def add_character_commands(cmdset):
    """Add character commands to the command set"""
    # ... existing commands ...
    cmdset.add(CmdIntroList())
    cmdset.add(CmdIntroLongList())

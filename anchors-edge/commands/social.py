"""
Social commands module for common emotes and gestures.
"""

from evennia import Command
from commands.emote import CmdEmote
from typeclasses.relationships import get_brief_description
from utils.text_formatting import format_sentence

class EmoteCommandBase(Command):
    """Base class for simple emote commands"""
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        # Parse target from args
        target = None
        emote_args = ""
        
        if self.args:
            args = self.args.strip().split()
            
            # Get target name/description to search for
            search_term = ""
            if len(args) >= 2 and args[0].lower() in ["to", "at"]:
                search_term = " ".join(args[1:]).lower()
            else:
                search_term = args[0].lower()
                
            # Search for character in room
            matches = []
            for obj in self.caller.location.contents:
                if (obj != self.caller and 
                    hasattr(obj, 'has_account') and 
                    obj.has_account):
                    
                    # If we know them, match against their name
                    if self.caller.knows_character(obj) and search_term in obj.name.lower():
                        matches.append((obj, obj))
                    # Always try matching against description too
                    elif search_term in get_brief_description(obj).lower():
                        matches.append((obj, obj))
                    
            # Handle matches
            if len(matches) == 1:
                target = matches[0][1]  # Use the actual object
            elif len(matches) > 1:
                # Multiple matches found
                self.caller.msg("Multiple characters match that description. Please be more specific:")
                for char, _ in matches:
                    # Show name if known, otherwise description
                    if self.caller.knows_character(char):
                        display = char.name
                    else:
                        display = get_brief_description(char)
                    self.caller.msg(f"- {display}")
                return
        
        location = self.caller.location
        if not location:
            return
            
        # Send personalized messages to each observer
        for observer in location.contents:
            if hasattr(observer, 'msg'):  # Make sure it can receive messages
                # Check if observer is a character that can know other characters
                is_character = hasattr(observer, 'knows_character')
                
                # Determine how to show the caller's name/description
                if is_character and observer.knows_character(self.caller):
                    caller_name = self.caller.name
                else:
                    caller_name = get_brief_description(self.caller)
                    
                # Build the personalized message
                if target:
                    # Targeted emote
                    if is_character and observer.knows_character(target):
                        target_name = target.name
                    else:
                        target_name = get_brief_description(target)
                        
                    if observer == self.caller:
                        msg = f"You {self.emote_text.rstrip('s')} at {target_name}"
                    elif observer == target:
                        msg = f"{caller_name} {self.emote_text} at you"
                    else:
                        msg = f"{caller_name} {self.emote_text} at {target_name}"
                else:
                    # Non-targeted emote
                    if observer == self.caller:
                        msg = f"You {self.emote_text.rstrip('s')}"
                    else:
                        msg = f"{caller_name} {self.emote_text}"
                        
                observer.msg(format_sentence(msg))

# Smile variants
class CmdSmile(EmoteCommandBase):
    """
    Smile, optionally at someone.
    
    Usage:
      smile [<person>]
    """
    key = "smile"
    emote_text = "smiles"

class CmdGrin(EmoteCommandBase):
    """
    Grin, optionally at someone.
    
    Usage:
      grin [<person>]
    """
    key = "grin"
    emote_text = "grins"

# Laughter variants
class CmdLaugh(EmoteCommandBase):
    """
    Laugh, optionally at someone.
    
    Usage:
      laugh [<person>]
    """
    key = "laugh"
    emote_text = "laughs"

class CmdChuckle(EmoteCommandBase):
    """
    Chuckle, optionally at someone.
    
    Usage:
      chuckle [<person>]
    """
    key = "chuckle"
    emote_text = "chuckles"

class CmdGiggle(EmoteCommandBase):
    """
    Giggle, optionally at someone.
    
    Usage:
      giggle [<person>]
    """
    key = "giggle"
    emote_text = "giggles"

# Gestures
class CmdWave(EmoteCommandBase):
    """
    Wave, optionally at someone.
    
    Usage:
      wave [<person>]
    """
    key = "wave"
    emote_text = "waves"

class CmdBow(EmoteCommandBase):
    """
    Bow, optionally to someone.
    
    Usage:
      bow [<person>]
    """
    key = "bow"
    emote_text = "bows"

class CmdNod(EmoteCommandBase):
    """
    Nod, optionally at someone.
    
    Usage:
      nod [<person>]
    """
    key = "nod"
    emote_text = "nods"

# Facial expressions
class CmdWink(EmoteCommandBase):
    """
    Wink, optionally at someone.
    
    Usage:
      wink [<person>]
    """
    key = "wink"
    emote_text = "winks"

class CmdFrown(EmoteCommandBase):
    """
    Frown, optionally at someone.
    
    Usage:
      frown [<person>]
    """
    key = "frown"
    emote_text = "frowns"

# Add these commands to the character command set
def add_social_commands(cmdset):
    """Add all social commands to a command set"""
    cmdset.add(CmdSmile())
    cmdset.add(CmdGrin())
    cmdset.add(CmdLaugh())
    cmdset.add(CmdChuckle())
    cmdset.add(CmdGiggle())
    cmdset.add(CmdWave())
    cmdset.add(CmdBow())
    cmdset.add(CmdNod())
    cmdset.add(CmdWink())
    cmdset.add(CmdFrown())
"""
Social commands module for common emotes and gestures.
"""

from evennia import Command
from commands.emote import CmdEmote

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
            
            # Check for "to" targeting first
            if len(args) >= 2 and args[0].lower() == "to":
                target = " ".join(args[1:])
            # Otherwise treat first word as potential target
            else:
                target = args[0]
                
        # Create an emote command instance
        emote = CmdEmote()
        emote.caller = self.caller
        
        # Build emote text with target if provided
        if target:
            emote.args = f"{self.emote_text} at {target}"
        else:
            emote.args = self.emote_text
            
        # Execute the emote
        emote.func()

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
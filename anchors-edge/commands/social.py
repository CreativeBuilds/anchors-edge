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
        # Create an emote command instance
        emote = CmdEmote()
        emote.caller = self.caller
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
    emote_text = "smile"

class CmdGrin(EmoteCommandBase):
    """
    Grin, optionally at someone.
    
    Usage:
      grin [<person>]
    """
    key = "grin"
    emote_text = "grin"

# Laughter variants
class CmdLaugh(EmoteCommandBase):
    """
    Laugh, optionally at someone.
    
    Usage:
      laugh [<person>]
    """
    key = "laugh"
    emote_text = "laugh"

class CmdChuckle(EmoteCommandBase):
    """
    Chuckle, optionally at someone.
    
    Usage:
      chuckle [<person>]
    """
    key = "chuckle"
    emote_text = "chuckle"

class CmdGiggle(EmoteCommandBase):
    """
    Giggle, optionally at someone.
    
    Usage:
      giggle [<person>]
    """
    key = "giggle"
    emote_text = "giggle"

# Gestures
class CmdWave(EmoteCommandBase):
    """
    Wave, optionally at someone.
    
    Usage:
      wave [<person>]
    """
    key = "wave"
    emote_text = "wave"

class CmdBow(EmoteCommandBase):
    """
    Bow, optionally to someone.
    
    Usage:
      bow [<person>]
    """
    key = "bow"
    emote_text = "bow"

class CmdNod(EmoteCommandBase):
    """
    Nod, optionally at someone.
    
    Usage:
      nod [<person>]
    """
    key = "nod"
    emote_text = "nod"

# Facial expressions
class CmdWink(EmoteCommandBase):
    """
    Wink, optionally at someone.
    
    Usage:
      wink [<person>]
    """
    key = "wink"
    emote_text = "wink"

class CmdFrown(EmoteCommandBase):
    """
    Frown, optionally at someone.
    
    Usage:
      frown [<person>]
    """
    key = "frown"
    emote_text = "frown"

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
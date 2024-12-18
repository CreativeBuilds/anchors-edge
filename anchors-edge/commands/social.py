"""
Social commands module for common emotes and gestures.
"""

from evennia import Command
from typeclasses.relationships import get_brief_description
from utils.text_formatting import format_sentence
from .character import get_pronoun
from .base_social import EmoteCommandBase, TargetType
from enum import Enum

# Smile variants
class CmdSmile(EmoteCommandBase):
    """
    Smile, optionally at someone and with a modifier.
    
    Usage:
      smile [<person>] [<modifier>]
      
    Examples:
      smile
      smile Gad
      smile sweetly
      smile Gad warmly
    """
    key = "smile"
    emote_text = "smiles"

class CmdGrin(EmoteCommandBase):
    """
    Grin, optionally at someone and with a modifier.
    
    Usage:
      grin [<person>] [<modifier>]
      
    Examples:
      grin
      grin Gad
      grin mischievously
      grin Gad wickedly
    """
    key = "grin"
    emote_text = "grins"

# Laughter variants
class CmdLaugh(EmoteCommandBase):
    """
    Laugh, optionally at someone and with a modifier.
    
    Usage:
      laugh [<person>] [<modifier>]
      
    Examples:
      laugh
      laugh Gad
      laugh heartily
      laugh Gad uncontrollably
    """
    key = "laugh"
    emote_text = "laughs"

class CmdChuckle(EmoteCommandBase):
    """
    Chuckle, optionally at someone and with a modifier.
    
    Usage:
      chuckle [<person>] [<modifier>]
      
    Examples:
      chuckle
      chuckle Gad
      chuckle softly
      chuckle Gad knowingly
    """
    key = "chuckle"
    emote_text = "chuckles"

class CmdGiggle(EmoteCommandBase):
    """
    Giggle, optionally at someone and with a modifier.
    
    Usage:
      giggle [<person>] [<modifier>]
      
    Examples:
      giggle
      giggle Gad
      giggle nervously
      giggle Gad uncontrollably
    """
    key = "giggle"
    emote_text = "giggles"

# Gestures
class CmdWave(EmoteCommandBase):
    """
    Wave, optionally at someone and with a modifier.
    
    Usage:
      wave [<person>] [<modifier>]
      
    Examples:
      wave
      wave Gad
      wave wildly
      wave Gad enthusiastically
    """
    key = "wave"
    emote_text = "waves"

class CmdBow(EmoteCommandBase):
    """
    Bow, optionally to someone and with a modifier.
    
    Usage:
      bow [<person>] [<modifier>]
      
    Examples:
      bow
      bow Gad
      bow deeply
      bow Gad respectfully
    """
    key = "bow"
    emote_text = "bows"

class CmdNod(EmoteCommandBase):
    """
    Nod, optionally at someone and with a modifier.
    
    Usage:
      nod [<person>] [<modifier>]
      
    Examples:
      nod
      nod Gad
      nod slowly
      nod Gad in agreement
    """
    key = "nod"
    emote_text = "nods"

# Facial expressions
class CmdWink(EmoteCommandBase):
    """
    Wink, optionally at someone and with a modifier.
    
    Usage:
      wink [<person>] [<modifier>]
      
    Examples:
      wink
      wink Gad
      wink playfully
      wink Gad conspiratorially
    """
    key = "wink"
    emote_text = "winks"

class CmdFrown(EmoteCommandBase):
    """
    Frown, optionally at someone and with a modifier.
    
    Usage:
      frown [<person>] [<modifier>]
      
    Examples:
      frown
      frown Gad
      frown deeply
      frown Gad in disapproval
    """
    key = "frown"
    emote_text = "frowns"
    
class CmdShrug(EmoteCommandBase):
    """
    Shrug, optionally at someone and with a modifier.
    
    Usage:
      shrug [<person>] [<modifier>]
      
    Examples:
      shrug
      shrug Gad
      shrug helplessly
      shrug Gad indifferently
    """
    key = "shrug"
    emote_text = "shrugs"
    
class CmdPout(EmoteCommandBase):
    """
    Pout, optionally at someone and with a modifier.
    
    Usage:
      pout [<person>] [<modifier>]
      
    Examples:
      pout
      pout Gad
      pout sadly
      pout Gad dramatically
    """
    key = "pout"
    emote_text = "pouts"

# New Basic Emotes
class CmdGreet(EmoteCommandBase):
    """
    Greet, optionally at someone and with a modifier.
    
    Usage:
      greet [<person>] [<modifier>]
      
    Examples:
      greet
      greet Gad
      greet warmly
      greet Gad cheerfully
    """
    key = "greet"
    emote_text = "greets"

class CmdBlush(EmoteCommandBase):
    """
    Blush, optionally at someone and with a modifier.
    
    Usage:
      blush [<person>] [<modifier>]
      
    Examples:
      blush
      blush Gad
      blush deeply
      blush Gad furiously
    """
    key = "blush"
    emote_text = "blushes"

class CmdSigh(EmoteCommandBase):
    """
    Sigh, optionally at someone and with a modifier.
    
    Usage:
      sigh [<person>] [<modifier>]
      
    Examples:
      sigh
      sigh Gad
      sigh heavily
      sigh Gad wearily
    """
    key = "sigh"
    emote_text = "sighs"

class CmdClap(EmoteCommandBase):
    """
    Clap, optionally for someone and with a modifier.
    
    Usage:
      clap [<person>] [<modifier>]
      
    Examples:
      clap
      clap Gad
      clap enthusiastically
      clap Gad appreciatively
    """
    key = "clap"
    emote_text = "claps"

class CmdSmirk(EmoteCommandBase):
    """
    Smirk, optionally at someone and with a modifier.
    
    Usage:
      smirk [<person>] [<modifier>]
      
    Examples:
      smirk
      smirk Gad
      smirk knowingly
      smirk Gad mischievously
    """
    key = "smirk"
    emote_text = "smirks"

class CmdSneer(EmoteCommandBase):
    """
    Sneer, optionally at someone and with a modifier.
    
    Usage:
      sneer [<person>] [<modifier>]
      
    Examples:
      sneer
      sneer Gad
      sneer disdainfully
      sneer Gad with contempt
    """
    key = "sneer"
    emote_text = "sneers"

class CmdEye(EmoteCommandBase):
    """
    Eye someone or something, optionally with a modifier.
    
    Usage:
      eye [<person>] [<modifier>]
      
    Examples:
      eye
      eye Gad
      eye suspiciously
      eye Gad carefully
    """
    key = "eye"
    emote_text = "eyes"

class CmdChortle(EmoteCommandBase):
    """
    Chortle, optionally at someone and with a modifier.
    
    Usage:
      chortle [<person>] [<modifier>]
      
    Examples:
      chortle
      chortle Gad
      chortle gleefully
      chortle Gad with amusement
    """
    key = "chortle"
    emote_text = "chortles"

class CmdBeam(EmoteCommandBase):
    """
    Beam brightly, optionally at someone and with a modifier.
    
    Usage:
      beam [<person>] [<modifier>]
      
    Examples:
      beam
      beam Gad
      beam happily
      beam Gad with joy
    """
    key = "beam"
    emote_text = "beams"

class CmdPoke(EmoteCommandBase):
    """
    Poke someone with your finger.
    
    Usage:
      poke <person> [<modifier>]
    """
    key = "poke"
    emote_text = "pokes {them} with {their} finger"
    targetable = TargetType.REQUIRED

class CmdBrow(EmoteCommandBase):
    """
    Arch an eyebrow questioningly.
    
    Usage:
      brow [<person>] [<modifier>]
    """
    key = "brow"
    emote_text = "arches {their} eyebrow"

class CmdAck(EmoteCommandBase):
    """
    Make an acknowledging sound, optionally at someone and with a modifier.
    
    Usage:
      ack [<person>] [<modifier>]
      
    Examples:
      ack
      ack Gad
      ack dubiously
      ack Gad in agreement
    """
    key = "ack"
    emote_text = "acks"

class CmdTup(EmoteCommandBase):
    """
    Give a thumbs up, optionally to someone and with a modifier.
    
    Usage:
      tup [<person>] [<modifier>]
      
    Examples:
      tup
      tup Gad
      tup enthusiastically
      tup Gad approvingly
    """
    key = "tup"
    emote_text = "gives a thumbs up"

class CmdTdown(EmoteCommandBase):
    """
    Give a thumbs down, optionally to someone and with a modifier.
    
    Usage:
      tdown [<person>] [<modifier>]
      
    Examples:
      tdown
      tdown Gad
      tdown sadly
      tdown Gad disapprovingly
    """
    key = "tdown"
    emote_text = "gives a thumbs down"

class CmdTongue(EmoteCommandBase):
    """
    Stick out your tongue, optionally at someone and with a modifier.
    
    Usage:
      tongue [<person>] [<modifier>]
    """
    key = "tongue"
    emote_text = "sticks out {their} tongue"

# Add after CmdGrin
class CmdMgrin(EmoteCommandBase):
    """
    Grin mischievously, optionally at someone and with a modifier.
    
    Usage:
      mgrin [<person>] [<modifier>]
      
    Examples:
      mgrin
      mgrin Gad
      mgrin wickedly
      mgrin Gad with a twinkle in their eye
    """
    key = "mgrin"
    emote_text = "grins mischievously"

# Add after CmdClap
class CmdApplaud(EmoteCommandBase):
    """
    Applaud, optionally with a modifier.
    
    Usage:
      applaud [<modifier>]
      
    Examples:
      applaud
      applaud enthusiastically
      applaud the performance
    """
    key = "applaud"
    emote_text = "applauds"

class CmdLapplaud(EmoteCommandBase):
    """
    Applaud loudly, optionally with a modifier.
    
    Usage:
      lapplaud [<modifier>]
      
    Examples:
      lapplaud
      lapplaud enthusiastically
      lapplaud the amazing performance
    """
    key = "lapplaud"
    emote_text = "applauds loudly"

# Add after CmdChortle
class CmdSnort(EmoteCommandBase):
    """
    Snort, optionally at someone and with a modifier.
    
    Usage:
      snort [<person>] [<modifier>]
      
    Examples:
      snort
      snort Gad
      snort derisively
      snort Gad in amusement
    """
    key = "snort"
    emote_text = "snorts"

# Add new action emotes
class CmdHipcheck(EmoteCommandBase):
    """
    Give someone a friendly hipcheck.
    
    Usage:
      hipcheck <person> [<modifier>]
      
    Examples:
      hipcheck Gad
      hipcheck Gad playfully
    """
    key = "hipcheck"
    emote_text = "gives {them} a friendly hipcheck"
    targetable = TargetType.REQUIRED

class CmdShouldercheck(EmoteCommandBase):
    """
    Shouldercheck someone as you pass by.
    
    Usage:
      shouldercheck <person> [<modifier>]
      
    Examples:
      shouldercheck Gad
      shouldercheck Gad harshly
    """
    key = "shouldercheck"
    emote_text = "shoulderchecks {them} on {their} way by"
    targetable = TargetType.REQUIRED
    
    def func(self):
        """Handle the shouldercheck command."""
        if not self.args:
            self.caller.msg("Usage: shouldercheck <person> [<modifier>]\nExample: shouldercheck Gad harshly")
            return
            
        # Parse target from args
        args = self.args.strip()
        
        # Try to find targets
        found_targets, failed_targets = self.caller.find_targets(args)
        
        if not found_targets:
            if failed_targets:
                self.caller.msg(f"Could not find anyone matching: {', '.join(failed_targets)}")
            else:
                self.caller.msg("Who do you want to shouldercheck?\nExample: shouldercheck Gad")
            return
            
        # Continue with normal emote processing
        super().func()

class CmdBounce(EmoteCommandBase):
    """
    Bounce around excitedly.
    
    Usage:
      bounce [<modifier>]
      
    Examples:
      bounce
      bounce happily
      bounce with joy
    """
    key = "bounce"
    emote_text = "bounces around excitedly"
    targetable = TargetType.NONE

class CmdHmm(EmoteCommandBase):
    """
    Hum thoughtfully.
    
    Usage:
      hmm [<modifier>]
      
    Examples:
      hmm
      hmm curiously
      hmm in contemplation
    """
    key = "hmm"
    emote_text = "hums thoughtfully to {themselves}"


class CmdYawn(EmoteCommandBase):
    """
    Yawn, optionally at someone and with a modifier.
    
    Usage:
      yawn [<person>] [<modifier>]
      
    Examples:
      yawn
      yawn Gad
      yawn sleepily
      yawn Gad tiredly
    """
    key = "yawn"
    emote_text = "covers {their} mouth and yawns"

class CmdAgree(EmoteCommandBase):
    """
    Nod in agreement.
    
    Usage:
      agree [<person>] [<modifier>]
      
    Examples:
      agree
      agree Gad
      agree wholeheartedly
      agree Gad enthusiastically
    """
    key = "agree"
    emote_text = "nods {their} head in agreement"

class CmdFacepalm(EmoteCommandBase):
    """
    Put face in hands and sigh.
    
    Usage:
      facepalm [<person>] [<modifier>]
      
    Examples:
      facepalm
      facepalm Gad
      facepalm dramatically
      facepalm Gad in exasperation
    """
    key = "facepalm"
    emote_text = "puts {their} face in {their} hands and sighs"

class CmdHeaddesk(EmoteCommandBase):
    """
    Beat head against the nearest wall.
    
    Usage:
      headdesk [<modifier>]
      
    Examples:
      headdesk
      headdesk repeatedly
      headdesk in frustration
    """
    key = "headdesk"
    emote_text = "beats {their} head against the nearest wall"
    targetable = TargetType.NONE

class CmdTired(EmoteCommandBase):
    """
    Rub eyes tiredly.
    
    Usage:
      tired [<person>] [<modifier>]
      
    Examples:
      tired
      tired Gad
      tired wearily
      tired Gad with exhaustion
    """
    key = "tired"
    emote_text = "rubs {their} eyes tiredly"

class CmdShh(EmoteCommandBase):
    """
    Put finger to lips to shush.
    
    Usage:
      shh [<person>] [<modifier>]
      
    Examples:
      shh
      shh Gad
      shh quietly
      shh Gad insistently
    """
    key = "shh"
    emote_text = "puts {their} finger to {their} lips"

# Add after all emote commands but before add_social_commands

class CmdEmoteList(Command):
    """
    List all available social emotes.
    
    Usage:
      emotelist
      socials
      
    Shows all available social commands in a table format with:
    - Command name and aliases
    - Example usage
    - How it appears in chat
    """
    key = "emotelist"
    aliases = ["socials"]
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        """Show list of all social commands with examples"""
        from evennia.utils import evtable
        
        # Get all command classes from this module that inherit from EmoteCommandBase
        emote_commands = []
        for name, obj in globals().items():
            if (isinstance(obj, type) and 
                issubclass(obj, EmoteCommandBase) and 
                obj != EmoteCommandBase):
                emote_commands.append(obj)
        
        # Sort commands by key
        emote_commands.sort(key=lambda x: x.key)
        
        # Get caller's name and pronouns
        caller_name = self.caller.key
        their = get_pronoun(self.caller, "possessive")
        they = get_pronoun(self.caller, "subjective")
        them = get_pronoun(self.caller, "objective")
        themselves = get_pronoun(self.caller, "reflexive")
        
        # Create table
        table = evtable.EvTable(
            "|wCommand|n",
            "|wAppears as|n",
            table=None,
            border="cells",
            width=80
        )
        
        for cmd in emote_commands:
            # Get the emote text and check targeting type
            emote_text = cmd.emote_text
            target_type = getattr(cmd, 'targetable', TargetType.OPTIONAL)
            
            # Format command name with usage indicators
            command_name = f"|c{cmd.key}|n"
            if target_type == TargetType.REQUIRED:
                command_name += " |w<target>|n"
            elif target_type == TargetType.OPTIONAL:
                command_name += " |w[<target>]|n"
            command_name += " |w[<mod>]|n"
            
            # Format the emote text with pronouns for display
            display_text = emote_text.format(
                char=caller_name,
                their=their,
                them="<target>" if target_type == TargetType.REQUIRED else them,
                they=they,
                theirs=their,
                themselves=themselves
            )
            
            # Format the display text
            other_output = f"{caller_name} {display_text}"
            
            # Add target text for optional targets
            if target_type == TargetType.OPTIONAL:
                other_output += " (at/to <target>)"
            
            # Add command and examples to table
            table.add_row(
                command_name,
                other_output
            )
            
            # Add aliases if any
            if hasattr(cmd, 'aliases') and cmd.aliases:
                aliases = ', '.join(cmd.aliases)
                if aliases:
                    table.add_row(
                        f"└─ {aliases}",
                        ""
                    )
        
        # Send the table to the caller
        self.caller.msg("|wSocial Commands:|n")
        self.caller.msg(table)
        self.caller.msg("\nUse |whelp <command>|n for more details on any command.")
        self.caller.msg("|w<target>|n is required, |w[<target>]|n and |w[<mod>]|n are optional")

def add_social_commands(cmdset):
    """Add all social commands to a command set"""
    cmdset.add(CmdSmile())
    cmdset.add(CmdGrin())
    cmdset.add(CmdMgrin())  # Added
    cmdset.add(CmdLaugh())
    cmdset.add(CmdChuckle())
    cmdset.add(CmdGiggle())
    cmdset.add(CmdWave())
    cmdset.add(CmdBow())
    cmdset.add(CmdNod())
    cmdset.add(CmdWink())
    cmdset.add(CmdFrown())
    cmdset.add(CmdShrug())
    cmdset.add(CmdPout())
    cmdset.add(CmdGreet())
    cmdset.add(CmdBlush())
    cmdset.add(CmdSigh())
    cmdset.add(CmdClap())
    cmdset.add(CmdApplaud())  # Added
    cmdset.add(CmdLapplaud())  # Added
    cmdset.add(CmdSmirk())
    cmdset.add(CmdSneer())
    cmdset.add(CmdEye())
    cmdset.add(CmdChortle())
    cmdset.add(CmdSnort())  # Added
    cmdset.add(CmdBeam())
    cmdset.add(CmdPoke())
    cmdset.add(CmdBrow())
    cmdset.add(CmdAck())
    cmdset.add(CmdTup())
    cmdset.add(CmdTdown())
    cmdset.add(CmdTongue())
    cmdset.add(CmdHipcheck())  # Added
    cmdset.add(CmdShouldercheck())  # Added
    cmdset.add(CmdBounce())  # Added
    cmdset.add(CmdHmm())  # Added
    cmdset.add(CmdYawn())  # Added
    cmdset.add(CmdAgree())  # Added
    cmdset.add(CmdFacepalm())  # Added
    cmdset.add(CmdHeaddesk())  # Added
    cmdset.add(CmdTired())  # Added
    cmdset.add(CmdShh())  # Added
    cmdset.add(CmdEmoteList())  # Add the new emotelist command
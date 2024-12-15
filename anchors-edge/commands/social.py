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
    
    def get_pronouns(self, character):
        """
        Get pronouns for a character based on their gender.
        Returns dict with: subjective (he/she/they), objective (him/her/them),
        possessive (his/her/their), reflexive (himself/herself/themselves)
        """
        gender = character.db.gender.lower() if hasattr(character.db, 'gender') else None
        
        if gender == "female":
            return {
                "subjective": "she",
                "objective": "her",
                "possessive": "her",
                "reflexive": "herself"
            }
        elif gender == "male":
            return {
                "subjective": "he",
                "objective": "him",
                "possessive": "his",
                "reflexive": "himself"
            }
        else:  # Default to neutral pronouns
            return {
                "subjective": "they",
                "objective": "them",
                "possessive": "their",
                "reflexive": "themselves"
            }

    def format_emote_text(self, is_self=False, char=None):
        """Format emote text with proper pronouns"""
        if is_self:
            # Convert third-person to second-person
            # e.g., "{char} sticks out {their} tongue" -> "stick out your tongue"
            text = self.emote_text.format(
                char="you",
                their="your",
                them="you",
                they="you",
                theirs="yours",
                themselves="yourself"
            )
            # Convert to second person (remove 's' from verb)
            words = text.split()
            if words and words[0].endswith('s'):
                words[0] = words[0][:-1]
            return ' '.join(words)
        else:
            # Use character's pronouns
            pronouns = self.get_pronouns(char)
            return self.emote_text.format(
                char="{char}",  # Placeholder for name/description
                their=pronouns["possessive"],
                them=pronouns["objective"],
                they=pronouns["subjective"],
                theirs=pronouns["possessive"],
                themselves=pronouns["reflexive"]
            )

    def conjugate_for_you(self, verb):
        """
        Conjugate the verb for 'you' as the subject.
        Handles special cases like 'gives' -> 'give'
        Takes a string and conjugates only the first word.
        """
        # Split into words and get first word
        words = verb.split()
        if not words:
            return verb
            
        first_word = words[0]
        
        # Conjugate first word - just remove trailing 's'
        if first_word.endswith('s'):
            conjugated = first_word[:-1]
        else:
            conjugated = first_word
            
        # Reconstruct full string with conjugated first word
        if len(words) > 1:
            return conjugated + ' ' + ' '.join(words[1:])
        return conjugated

    def func(self):
        """Handle the emote command."""
        # Parse target from args
        targets = []
        modifier = ""
        preposition = "at"  # Default preposition
        
        if self.args:
            args = self.args.strip()
            
            # Check for prepositions first
            words = args.split()
            if len(words) >= 2 and words[0].lower() in ["at", "with", "to"]:
                preposition = words[0].lower()
                args = " ".join(words[1:])  # Remove preposition from args
            
            # First try to find a target in the room
            potential_target = self.caller.search(args, location=self.caller.location, quiet=True)
            if potential_target:
                # If we found a target, the whole remaining args was a target
                targets = [potential_target]
                modifier = ""
            else:
                # No direct target found, split on first space to check for target + modifier
                parts = args.split(None, 1)
                if parts:
                    first_word = parts[0]
                    # Try to find target with just the first word
                    potential_target = self.caller.search(first_word, location=self.caller.location, quiet=True)
                    if potential_target:
                        # First word was a target, rest is modifier
                        targets = [potential_target]
                        modifier = parts[1] if len(parts) > 1 else ""
                    else:
                        # No target found, treat everything as modifier
                        modifier = args

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
                if targets:
                    # Get target names/descriptions based on observer's knowledge
                    target_names = []
                    is_observer_target = False
                    
                    for target in targets:
                        if observer == target:
                            is_observer_target = True
                            continue  # Skip adding "you" to the list
                        if is_character and observer.knows_character(target):
                            target_names.append(target.name)
                        else:
                            target_names.append(get_brief_description(target))
                    
                    # Format target list
                    if target_names:
                        if is_observer_target:
                            if len(target_names) > 0:
                                if len(target_names) == 1:
                                    targets_str = f"you and {target_names[0]}"
                                else:
                                    targets_str = f"you, {', '.join(target_names[:-1])} and {target_names[-1]}"
                            else:
                                targets_str = "you"
                        else:
                            if len(target_names) == 1:
                                targets_str = target_names[0]
                            else:
                                targets_str = f"{', '.join(target_names[:-1])} and {target_names[-1]}"
                    else:
                        targets_str = "you" if is_observer_target else ""
                    
                    # Build final message
                    if observer == self.caller:
                        msg = f"You {self.format_emote_text(is_self=True)} {preposition} {targets_str}"
                    elif is_observer_target:
                        msg = f"{caller_name} {self.format_emote_text(char=self.caller)} {preposition} {targets_str}"
                    else:
                        msg = f"{caller_name} {self.format_emote_text(char=self.caller)} {preposition} {targets_str}"
                else:
                    # Non-targeted emote
                    if observer == self.caller:
                        msg = f"You {self.format_emote_text(is_self=True)}"
                    else:
                        msg = f"{caller_name} {self.format_emote_text(char=self.caller)}"
                
                # Add modifier if present
                if modifier:
                    msg = f"{msg} {modifier}"
                        
                observer.msg(format_sentence(msg))

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
    cmdset.add(CmdShrug())
    cmdset.add(CmdPout())
    cmdset.add(CmdGreet())
    cmdset.add(CmdBlush())
    cmdset.add(CmdSigh())
    cmdset.add(CmdClap())
    cmdset.add(CmdSmirk())
    cmdset.add(CmdSneer())
    cmdset.add(CmdEye())
    cmdset.add(CmdChortle())
    cmdset.add(CmdBeam())
    cmdset.add(CmdPoke())
    cmdset.add(CmdBrow())
    cmdset.add(CmdAck())
    cmdset.add(CmdTup())
    cmdset.add(CmdTdown())
    cmdset.add(CmdTongue())
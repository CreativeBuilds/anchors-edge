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
        
        # Conjugate first word
        if first_word.endswith('ies'):
            conjugated = first_word[:-3] + 'y'
        elif first_word.endswith('es'):
            conjugated = first_word[:-2]
        elif first_word.endswith('s'):
            conjugated = first_word[:-1]
        else:
            conjugated = first_word
            
        # Reconstruct full string with conjugated first word
        if len(words) > 1:
            return conjugated + ' ' + ' '.join(words[1:])
        return conjugated

    def func(self):
        # Parse target from args
        targets = []
        modifier = ""
        
        if self.args:
            args = self.args.strip()
            
            # First try to find targets
            search_terms = []
            
            # Split on first space to separate potential targets from modifier
            parts = args.split(None, 1)
            if parts:
                # Split potential targets by commas
                potential_targets = parts[0].split(',')
                search_terms = [term.strip().lower() for term in potential_targets]
                if len(parts) > 1:
                    modifier = parts[1].strip()
            
            # Search for characters in room for each search term
            for search_term in search_terms:
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
                
                # Handle matches for this search term
                if len(matches) == 1:
                    targets.append(matches[0][1])  # Use the actual object
                elif len(matches) > 1:
                    # Multiple matches found for this term
                    self.caller.msg(f"Multiple characters match '{search_term}'. Please be more specific:")
                    for char, _ in matches:
                        if self.caller.knows_character(char):
                            display = char.name
                        else:
                            display = get_brief_description(char)
                        self.caller.msg(f"- {display}")
                    return
            
            # If no targets found, treat entire args as modifier
            if not targets and args:
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
                                targets_str = f"you and {', '.join(target_names[:-1])}"
                                if len(target_names) > 1:
                                    targets_str += f" and {target_names[-1]}"
                            else:
                                targets_str = "you"
                        else:
                            targets_str = f"{', '.join(target_names[:-1])}"
                            if len(target_names) > 1:
                                targets_str += f" and {target_names[-1]}"
                            else:
                                targets_str = target_names[0]
                    else:
                        targets_str = "you" if is_observer_target else ""
                    
                    # Build final message
                    if observer == self.caller:
                        msg = f"You {self.conjugate_for_you(self.emote_text)} at {targets_str}"
                    elif is_observer_target:
                        msg = f"{caller_name} {self.emote_text} at {targets_str}"
                    else:
                        msg = f"{caller_name} {self.emote_text} at {targets_str}"
                else:
                    # Non-targeted emote
                    if observer == self.caller:
                        msg = f"You {self.conjugate_for_you(self.emote_text)}"
                    else:
                        msg = f"{caller_name} {self.emote_text}"
                
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
    Poke someone, optionally with a modifier.
    
    Usage:
      poke <person> [<modifier>]
      
    Examples:
      poke Gad
      poke Gad playfully
      poke Gad in the ribs
    """
    key = "poke"
    emote_text = "pokes"

class CmdBrow(EmoteCommandBase):
    """
    Arch an eyebrow, optionally at someone and with a modifier.
    
    Usage:
      brow [<person>] [<modifier>]
      
    Examples:
      brow
      brow Gad
      brow quizzically
      brow Gad skeptically
    """
    key = "brow"
    emote_text = "arches an eyebrow"

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
      
    Examples:
      tongue
      tongue Gad
      tongue playfully
      tongue Gad teasingly
    """
    key = "tongue"
    emote_text = "sticks out their tongue"

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
    
    # New commands
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
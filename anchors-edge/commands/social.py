"""
Social commands module for common emotes and gestures.
"""

from evennia import Command
from typeclasses.relationships import get_brief_description
from utils.text_formatting import format_sentence
from .character import get_pronoun

class EmoteCommandBase(Command):
    """Base class for simple emote commands"""
    locks = "cmd:all()"
    help_category = "Social"
    auto_help = False  # This will hide all social commands from help
    
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
            
            # Split remaining args into potential target and modifier
            # Look for the first space after any commas to separate targets from modifier
            target_end = -1
            in_target = True
            for i, char in enumerate(args):
                if char == ',':
                    continue
                if char == ' ' and not args[i-1].isalnum():  # Space after punctuation
                    target_end = i
                    break
            
            if target_end != -1:
                target_string = args[:target_end].strip()
                modifier = args[target_end:].strip()
            else:
                target_string = args
                modifier = ""
                
            # Try to find targets
            found_targets, failed_targets = self.caller.find_targets(target_string)
            
            if failed_targets:
                if len(failed_targets) == len(target_string.split(",")):
                    self.caller.msg(f"Could not find anyone matching: {', '.join(failed_targets)}")
                    return
                else:
                    self.caller.msg(f"Warning: Could not find: {', '.join(failed_targets)}")
            
            targets.extend(found_targets)
            
            # If no targets found and we have args, treat everything as modifier
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

class CmdShouldercheck(EmoteCommandBase):
    """
    Shouldercheck someone harshly.
    
    Usage:
      shouldercheck <person> [<modifier>]
      
    Examples:
      shouldercheck Gad
      shouldercheck Gad angrily
    """
    key = "shouldercheck"
    emote_text = "shoulderchecks {them} harshly on the way by"

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
        
        # Get caller's name and pronouns - use key (name) instead of display_name to avoid rstatus
        caller_name = self.caller.key
        their = get_pronoun(self.caller, "possessive")
        they = get_pronoun(self.caller, "subjective")
        them = get_pronoun(self.caller, "objective")
        
        # Example variations for more natural demonstrations
        examples = {
            "smile": ("smile Gad warmly", f"{caller_name} smiles warmly at Gad."),
            "grin": ("grin wickedly", f"{caller_name} grins wickedly."),
            "mgrin": ("mgrin mischievously", f"{caller_name} grins mischievously."),
            "laugh": ("laugh Gad heartily", f"{caller_name} laughs heartily at Gad."),
            "chuckle": ("chuckle knowingly", f"{caller_name} chuckles knowingly."),
            "giggle": ("giggle uncontrollably", f"{caller_name} giggles uncontrollably."),
            "wave": ("wave Gad cheerfully", f"{caller_name} waves cheerfully at Gad."),
            "bow": ("bow deeply", f"{caller_name} bows deeply."),
            "nod": ("nod Gad sagely", f"{caller_name} nods sagely at Gad."),
            "wink": ("wink Gad playfully", f"{caller_name} winks playfully at Gad."),
            "frown": ("frown thoughtfully", f"{caller_name} frowns thoughtfully."),
            "shrug": ("shrug helplessly", f"{caller_name} shrugs helplessly."),
            "pout": ("pout adorably", f"{caller_name} pouts adorably."),
            "greet": ("greet Gad warmly", f"{caller_name} greets Gad warmly."),
            "blush": ("blush furiously", f"{caller_name} blushes furiously."),
            "sigh": ("sigh wearily", f"{caller_name} sighs wearily."),
            "clap": ("clap enthusiastically", f"{caller_name} claps enthusiastically."),
            "applaud": ("applaud Gad enthusiastically", f"{caller_name} applauds Gad enthusiastically."),
            "lapplaud": ("lapplaud loudly", f"{caller_name} applauds loudly."),
            "smirk": ("smirk Gad deviously", f"{caller_name} smirks deviously at Gad."),
            "sneer": ("sneer disdainfully", f"{caller_name} sneers disdainfully."),
            "eye": ("eye Gad suspiciously", f"{caller_name} eyes Gad suspiciously."),
            "chortle": ("chortle gleefully", f"{caller_name} chortles gleefully."),
            "snort": ("snort derisively", f"{caller_name} snorts derisively."),
            "beam": ("beam Gad brightly", f"{caller_name} beams brightly at Gad."),
            "poke": ("poke Gad playfully", f"{caller_name} pokes Gad playfully."),
            "brow": ("brow curiously", f"{caller_name} arches {their} eyebrow curiously."),
            "ack": ("ack", f"{caller_name} makes an acknowledging sound."),
            "tup": ("tup Gad encouragingly", f"{caller_name} gives a thumbs up to Gad encouragingly."),
            "tdown": ("tdown Gad", f"{caller_name} gives a thumbs down to Gad."),
            "tongue": ("tongue Gad", f"{caller_name} sticks out {their} tongue at Gad."),
            "hipcheck": ("hipcheck Gad playfully", f"{caller_name} gives Gad a playful hipcheck."),
            "shouldercheck": ("shouldercheck Gad roughly", f"{caller_name} shoulderchecks Gad roughly."),
            "bounce": ("bounce excitedly", f"{caller_name} bounces around excitedly."),
            "hmm": ("hmm thoughtfully", f"{caller_name} hums thoughtfully."),
            "yawn": ("yawn sleepily", f"{caller_name} yawns sleepily."),
            "agree": ("agree Gad", f"{caller_name} nods {their} head in agreement with Gad."),
            "facepalm": ("facepalm dramatically", f"{caller_name} puts {their} face in {their} hands dramatically."),
            "headdesk": ("headdesk repeatedly", f"{caller_name} beats {their} head against the nearest wall repeatedly."),
            "tired": ("tired", f"{caller_name} rubs {their} eyes tiredly."),
            "shh": ("shh Gad", f"{caller_name} puts {their} finger to {their} lips at Gad.")
        }
        
        # Create table
        table = evtable.EvTable(
            "|wCommand|n",
            "|wExample Usage|n",
            "|wAppears as|n",
            table=None,
            border="cells",
            width=80
        )
        
        # Get list of actual command keys
        available_commands = {cmd.key for cmd in emote_commands}
        
        # Filter examples to only include available commands
        filtered_examples = {k: v for k, v in examples.items() if k in available_commands}
        
        for cmd in emote_commands:
            # Get example from our filtered dictionary, or generate a default one
            if cmd.key in filtered_examples:
                example, other_output = filtered_examples[cmd.key]
            else:
                # Get the docstring for help text
                doc = cmd.__doc__.strip().split('\n')[0] if cmd.__doc__ else ""
                
                # Generate example based on command key and docstring
                if "at <target>" in doc:
                    example = f"{cmd.key} Gad"
                    other_output = f"{caller_name} {cmd.key}s at Gad."
                else:
                    example = f"{cmd.key}"
                    other_output = f"{caller_name} {cmd.key}s."
            
            # Add command and examples to table
            table.add_row(
                f"|c{cmd.key}|n",
                example,
                other_output
            )
            
            # Add aliases if any
            if hasattr(cmd, 'aliases') and cmd.aliases:
                aliases = ', '.join(cmd.aliases)
                if aliases:
                    table.add_row(
                        f"└─ {aliases}",
                        "",
                        ""
                    )
        
        # Send the table to the caller
        self.caller.msg("|wSocial Commands:|n")
        self.caller.msg(table)
        self.caller.msg("\nUse |whelp <command>|n for more details on any command.")

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
"""
Emote command module for different types of emotes.
"""
from evennia import Command, InterruptCommand
from evennia.utils import inherits_from
from typing import Dict, List
import re
from utils.text_formatting import format_sentence

# Helper functions
def get_possessive(name: str) -> str:
    """Returns the possessive form of a name (e.g., "Bob's" or "James'")"""
    if name.lower().endswith('s'):
        return f"{name}'"
    return f"{name}'s"

def get_name_or_description(viewer, character) -> str:
    """
    Returns either the character's name if known to the viewer,
    or their description if not.
    
    Args:
        viewer: The character viewing the message
        character: The character being referenced
    
    Returns:
        str: Either the name or description based on familiarity
    """
    # Skip description for self
    if viewer == character:
        return "you"
    
    # Check if viewer knows the character using existing recognition system
    if hasattr(viewer, "knows_character") and viewer.knows_character(character):
        return character.name
    
    # Return the character's basic description
    if hasattr(character, "generate_basic_description"):
        return character.generate_basic_description()
    else:
        # Fallback to a basic description if method not available
        race = character.db.race if hasattr(character.db, 'race') else "person"
        gender = character.db.gender if hasattr(character.db, 'gender') else ""
        return format_sentence(f"a {gender} {race}")

def format_target_list(targets: List[str], viewer=None) -> str:
    """
    Formats a list of targets grammatically, replacing names with
    descriptions for unknown characters.
    
    Args:
        targets: List of target objects
        viewer: The character viewing the message
    """
    if not targets:
        return ""
    
    # Convert targets to names/descriptions
    target_names = []
    for target in targets:
        if viewer:
            name = get_name_or_description(viewer, target)
        else:
            name = target.name
        target_names.append(name)
    
    if len(target_names) == 1:
        return target_names[0]
    elif len(target_names) == 2:
        return format_sentence(f"{target_names[0]} and {target_names[1]}")
    else:
        return format_sentence(f"{', '.join(target_names[:-1])}, and {target_names[-1]}")

STANDARD_EMOTES: Dict[str, Dict[str, str]] = {
    # Basic expressions
    "wave": {
        "self": "wave",
        "other": "waves",
        "targeted": "waves at"
    },
    "greet": {
        "self": "greet everyone",
        "other": "greets everyone",
        "targeted": "greets"
    },
    "blush": {
        "self": "blush",
        "other": "blushes",
        "targeted": "blushes at"
    },
    "sigh": {
        "self": "sigh",
        "other": "sighs",
        "targeted": "sighs at"
    },
    "shrug": {
        "self": "shrug",
        "other": "shrugs",
        "targeted": "shrugs at"
    },
    "clap": {
        "self": "clap",
        "other": "claps",
        "targeted": "claps for"
    },
    "applaud": {
        "self": "applaud",
        "other": "applauds"
    },
    "lapplaud": {
        "self": "applaud loudly",
        "other": "applauds loudly"
    },
    
    # Facial expressions
    "smirk": {
        "self": "smirk",
        "other": "smirks",
        "targeted": "smirks at"
    },
    "sneer": {
        "self": "sneer",
        "other": "sneers",
        "targeted": "sneers at"
    },
    "eye": {
        "self": "eye everyone",
        "other": "eyes everyone",
        "targeted": "eyes"
    },
    "smile": {
        "self": "smile",
        "other": "smiles",
        "targeted": "smiles at"
    },
    "grin": {
        "self": "grin",
        "other": "grins",
        "targeted": "grins at"
    },
    "mgrin": {
        "self": "grin mischievously",
        "other": "grins mischievously",
        "targeted": "grins mischievously at"
    },
    
    # Laughter
    "laugh": {
        "self": "laugh",
        "other": "laughs",
        "targeted": "laughs at"
    },
    "llaugh": {
        "self": "laugh loudly",
        "other": "laughs loudly",
        "targeted": "laughs loudly at"
    },
    "laughw": {
        "self": "laugh with everyone",
        "other": "laughs with everyone",
        "targeted": "laughs with"
    },
    "chuckle": {
        "self": "chuckle",
        "other": "chuckles",
        "targeted": "chuckles at"
    },
    "schuckle": {
        "self": "chuckle softly",
        "other": "chuckles softly",
        "targeted": "chuckles softly at"
    },
    "giggle": {
        "self": "giggle",
        "other": "giggles",
        "targeted": "giggles at"
    },
    "chortle": {
        "self": "chortle",
        "other": "chortles",
        "targeted": "chortles at"
    },
    "snort": {
        "self": "snort",
        "other": "snorts",
        "targeted": "snorts at"
    },
    
    # Actions
    "poke": {
        "self": "poke",
        "other": "pokes",
        "targeted": "pokes"
    },
    "hipcheck": {
        "self": "give a friendly hipcheck to",
        "other": "gives a friendly hipcheck to",
        "targeted": "gives a friendly hipcheck to"
    },
    "shouldercheck": {
        "self": "shouldercheck harshly on the way by",
        "other": "shoulderchecks harshly on the way by",
        "targeted": "shoulderchecks harshly on the way by"
    },
    "point": {
        "self": "point",
        "other": "points",
        "targeted": "points at",
        "directional": "points to the {direction}"
    },
    "bounce": {
        "self": "bounce around like a fucking idiot",
        "other": "bounces around like a fucking idiot"
    },
    "hmm": {
        "self": "hum thoughtfully",
        "other": "hums thoughtfully"
    },
    "?": {
        "self": "look curious",
        "other": "looks curious",
        "targeted": "looks curiously at"
    },
    "glare": {
        "self": "glare",
        "other": "glares",
        "targeted": "glares at"
    },
    "yawn": {
        "self": "yawn",
        "other": "yawns",
        "targeted": "yawns at"
    },
    "beam": {
        "self": "beam brightly",
        "other": "beams brightly",
        "targeted": "beams brightly at"
    },
    "brow": {
        "self": "arch an eyebrow",
        "other": "arches an eyebrow",
        "targeted": "arches an eyebrow at"
    },
    "nod": {
        "self": "nod",
        "other": "nods",
        "targeted": "nods at"
    },
    "agree": {
        "self": "agree",
        "other": "agrees",
        "targeted": "agrees with"
    },
    
    # Special emotes with pronouns
    "facepalm": {
        "self": "put {their} face in {their} hands and sigh",
        "other": "puts {their} face in {their} hands and sighs",
        "targeted": "puts {their} face in {their} hands and sighs at"
    },
    "headdesk": {
        "self": "beat {their} head against the nearest wall",
        "other": "beats {their} head against the nearest wall"
    },
    "tired": {
        "self": "am tired",
        "other": "is tired",
        "targeted": "makes {target} tired"
    },
    
    # Gestures
    "tup": {
        "self": "give a thumbs up",
        "other": "gives a thumbs up",
        "targeted": "gives {target} a thumbs up"
    },
    "tdown": {
        "self": "give a thumbs down",
        "other": "gives a thumbs down",
        "targeted": "gives {target} a thumbs down"
    },
    "tongue": {
        "self": "stick out {their} tongue",
        "other": "sticks out {their} tongue",
        "targeted": "sticks out {their} tongue at"
    },
    "shh": {
        "self": "shush",
        "other": "shushes",
        "targeted": "shushes"
    },
    "ack": {
        "self": "ack",
        "other": "acks"
    }
}

class CmdEmoteList(Command):
    """
    List all available automatic emotes.
    
    Usage:
      emotelist [category]
      
    Categories:
      basic    - Simple emotes like smile, laugh
      social   - Interactive emotes like wave, bow
      targeted - Emotes that work well with targets
    """
    key = "emotelist"
    aliases = ["emotes"]
    locks = "cmd:all()"
    
    CATEGORIES = {
        "basic": ["smile", "grin", "laugh", "chuckle", "giggle", "cry", "sob"],
        "social": ["wave", "bow", "curtsey", "dance"],
        "targeted": ["highfive", "hug", "wave", "bow"]
    }
    
    def func(self):
        category = self.args.strip().lower() if self.args else None
        
        if category and category not in self.CATEGORIES:
            self.caller.msg(f"Available categories: {', '.join(self.CATEGORIES.keys())}")
            return
            
        table = self.styled_table("Emote", "Solo Action", "Targeted Action")
        
        emotes_to_show = (
            self.CATEGORIES.get(category, STANDARD_EMOTES.keys())
            if category else STANDARD_EMOTES.keys()
        )
        
        for emote in sorted(emotes_to_show):
            if emote in STANDARD_EMOTES:
                emote_data = STANDARD_EMOTES[emote]
                solo_action = f"{self.caller.name} {emote_data['other']}"
                targeted = f"{self.caller.name} {emote_data['targeted']} <target>"
                table.add_row(emote, solo_action, targeted)
        
        self.caller.msg("|wAvailable automatic emotes:|n")
        if category:
            self.caller.msg(f"|y{category.title()} emotes:|n")
        self.caller.msg(table)

class CmdEmote(Command):
    """
    Perform an emote/pose.
    
    Usage:
      emote <text>
      ;<text>
      emote <emote> <target1> [target2...]
    
    Examples:
      emote stretches out, relaxing in their chair.
      ;stretches out, relaxing in their chair.
      emote smile
      emote wave Bob Jane    (waves to both Bob and Jane)
      
    Channel usage:
      chat ;waves hello
      chat ;smile
    """
    key = "emote"
    aliases = [";"]
    locks = "cmd:all()"
    
    def create_message(self, base_msg: str, targets: List = None, viewer = None) -> str:
        """
        Creates a message with proper name/description substitutions.
        
        Args:
            base_msg: The base message text
            targets: Optional list of target objects
            viewer: The character who will see this message
        """
        message = base_msg
        
        # Replace the emoting character's name
        if viewer:
            actor_name = get_name_or_description(viewer, self.caller)
            message = message.replace(self.caller.name, actor_name)
        
        # Replace target names if any
        if targets:
            for target in targets:
                if viewer:
                    target_name = get_name_or_description(viewer, target)
                    message = message.replace(target.name, target_name)
        
        return format_sentence(message)
    
    def func(self):
        if not self.args:
            self.caller.msg("What do you want to emote?")
            return
        
        args = self.args.strip()
        words = args.split()
        emote_word = words[0].lower()
        potential_targets = words[1:] if len(words) > 1 else []
        
        # Handle automatic emotes
        if emote_word in STANDARD_EMOTES:
            emote_data = STANDARD_EMOTES[emote_word]
            
            # Check if this emote supports directional variants
            has_directional = "directional" in emote_data
            
            if potential_targets:
                # First try to find targets as objects
                valid_targets = []
                for target_name in potential_targets:
                    target = self.caller.search(target_name)
                    if target:
                        valid_targets.append(target)
                
                if valid_targets:
                    # Handle normal targeted emote
                    base_msg = f"{self.caller.name} {emote_data['targeted']}"
                    
                    # Send personalized messages to each observer
                    for observer in self.caller.location.contents:
                        if hasattr(observer, 'msg'):  # Ensure it's a messageable object
                            personalized_msg = self.create_message(
                                base_msg, 
                                valid_targets,
                                observer
                            )
                            if observer != self.caller:
                                observer.msg(personalized_msg)
                    
                    # Message for the caller
                    caller_msg = self.create_message(base_msg, valid_targets, self.caller)
                    self.caller.msg(caller_msg)
                    return
                
                elif has_directional and len(potential_targets) == 1:
                    # Try to handle as a directional emote
                    direction = potential_targets[0].lower()
                    if direction in ["north", "south", "east", "west"]:
                        base_msg = f"{self.caller.name} {emote_data['directional'].format(direction=direction)}"
                        
                        # Send to room
                        for observer in self.caller.location.contents:
                            if hasattr(observer, 'msg'):
                                personalized_msg = self.create_message(base_msg, viewer=observer)
                                observer.msg(personalized_msg)
                        return
            
            # Non-targeted automatic emote
            base_msg = f"{self.caller.name} {emote_data['other']}"
            
            # Handle channel emotes
            if hasattr(self, "channel"):
                # For channels, we might want to keep names visible
                self.channel.msg(base_msg)
                return
            
            # Send personalized messages to each observer
            for observer in self.caller.location.contents:
                if hasattr(observer, 'msg'):
                    personalized_msg = self.create_message(base_msg, viewer=observer)
                    observer.msg(personalized_msg)
            return
        
        # Handle regular emotes
        base_msg = f"{self.caller.name} {args}"
        
        if hasattr(self, "channel"):
            self.channel.msg(base_msg)
            return
        
        # Send personalized messages to each observer
        for observer in self.caller.location.contents:
            if hasattr(observer, 'msg'):
                personalized_msg = self.create_message(base_msg, viewer=observer)
                observer.msg(personalized_msg)

class CmdPmote(Command):
    """
    Perform a possessive emote.
    
    Usage:
      pmote <text>
      
    Example:
      pmote hand rests on their hip.
    """
    key = "pmote"
    locks = "cmd:all()"
    
    def func(self):
        if not self.args:
            self.caller.msg("What do you want to emote?")
            return
        
        # Create personalized messages for each observer
        for observer in self.caller.location.contents:
            if hasattr(observer, 'msg'):
                # Get appropriate name display for this observer
                char_name = get_name_or_description(observer, self.caller)
                message = format_sentence(f"{get_possessive(char_name)} {self.args.strip()}")
                if observer != self.caller:
                    observer.msg(message)
        
        # Message for the caller (always sees their own name)
        caller_msg = format_sentence(f"{get_possessive(self.caller.name)} {self.args.strip()}")
        self.caller.msg(caller_msg)

class CmdOmote(Command):
    """
    Perform an optional emote with name placement.
    
    Usage:
      omote <text> (use ; where you want your name)
      
    Example:
      omote Relaxing against the wall, ; stares out the window.
    """
    key = "omote"
    locks = "cmd:all()"
    
    def func(self):
        if not self.args:
            self.caller.msg("What do you want to emote?")
            return
        
        if ";" not in self.args:
            self.caller.msg("You must include ; where you want your name to appear.")
            return
        
        # Create personalized messages for each observer
        for observer in self.caller.location.contents:
            if hasattr(observer, 'msg'):
                # Get appropriate name display for this observer
                char_name = get_name_or_description(observer, self.caller)
                message = format_sentence(self.args.strip().replace(";", char_name, 1))
                if observer != self.caller:
                    observer.msg(message)
        
        # Message for the caller (always sees their own name)
        caller_msg = format_sentence(self.args.strip().replace(";", self.caller.name, 1))
        self.caller.msg(caller_msg)

class CmdTmote(Command):
    """
    Perform a targeted emote.
    
    Usage:
      tmote <target1>[,target2,target3...] <text>
      (use ; for your name and - for target names)
      
    Examples:
      tmote kobold walking in the room ; nods at -.
      tmote tall,short ; waves to - and -.
      tmote kobold ; waves at -    (targets someone by description)
    """
    key = "tmote"
    locks = "cmd:all()"
    
    def func(self):
        if not self.args:
            self.caller.msg("Usage: tmote <target(s)> <text>")
            return
        
        try:
            targets_str, emote = self.args.split(None, 1)
        except ValueError:
            self.caller.msg("Usage: tmote <target(s)> <text>")
            return
            
        if ";" not in emote:
            self.caller.msg("You must include ; where you want your name to appear.")
            return
        
        # Handle multiple targets
        target_names = [t.strip() for t in targets_str.split(",")]
        targets = []
        failed_targets = []
        
        for target_name in target_names:
            # Try to find target using description matching
            target = self.caller.find_character_by_desc(target_name)
            if target:
                targets.append(target)
            else:
                # Fallback to exact search
                target = self.caller.search(target_name, quiet=True)
                if target and len(target) == 1:
                    targets.append(target[0])
                else:
                    failed_targets.append(target_name)
        
        if failed_targets:
            if len(failed_targets) == len(target_names):
                # All targets failed
                self.caller.msg(f"Could not find anyone matching: {', '.join(failed_targets)}")
                return
            else:
                # Some targets failed but others succeeded
                self.caller.msg(f"Warning: Could not find: {', '.join(failed_targets)}")
        
        if not targets:
            return
        
        # Create the base message with placeholder for actor's name
        base_message = emote.replace(";", "{actor}", 1)
        
        # Send different messages to different recipients
        for observer in self.caller.location.contents:
            if not hasattr(observer, 'msg'):
                continue
                
            # Get appropriate name for the actor based on observer's knowledge
            actor_name = get_name_or_description(observer, self.caller)
            
            # Create message with proper names for this observer
            observer_message = base_message.format(actor=actor_name)
            
            # Replace target placeholders with appropriate names based on observer's knowledge
            for i, target in enumerate(targets):
                if observer == target:
                    # If observer is the target, use "you"
                    observer_message = observer_message.replace("-", "you", 1)
                elif observer == self.caller:
                    # If observer is the actor, use target's name if known, otherwise description
                    target_display = target.name if self.caller.knows_character(target) else get_brief_description(target)
                    observer_message = observer_message.replace("-", target_display, 1)
                else:
                    # For third-party observers, use names only if they know both characters
                    knows_actor = observer.knows_character(self.caller) if hasattr(observer, 'knows_character') else False
                    knows_target = observer.knows_character(target) if hasattr(observer, 'knows_character') else False
                    
                    if knows_actor and knows_target:
                        # If observer knows both, use target's name
                        target_display = target.name
                    else:
                        # If observer doesn't know either character, use brief descriptions
                        target_display = get_brief_description(target)
                    
                    observer_message = observer_message.replace("-", target_display, 1)
            
            if observer != self.caller:
                observer.msg(format_sentence(observer_message))
        
        # Message for the caller (sees names if known, descriptions if not)
        caller_message = base_message.format(actor=self.caller.name)
        for target in targets:
            target_display = target.name if self.caller.knows_character(target) else get_brief_description(target)
            caller_message = caller_message.replace("-", target_display, 1)
        self.caller.msg(format_sentence(caller_message))

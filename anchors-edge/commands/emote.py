"""
Emote command module for different types of emotes.
"""
from evennia import Command
from typing import List
from utils.text_formatting import format_sentence
from typeclasses.relationships import (
    get_brief_description,
)


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
    # Always return name for self
    if viewer == character:
        return character.name
    
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

class CmdEmote(Command):
    """
    Simple emote command for visible actions.

    Usage:
      emote <action>
      pose <action>
      ; <action>

    Example:
      emote waves.
      emote scratches their head in confusion.
      ; grins mischievously.
    """
    key = "emote"
    aliases = ["pose", ";"]
    locks = "cmd:all()"

    def format_emote_message(self, caller, message):
        """
        Format emote messages for all observers.
        
        Args:
            caller: The character performing the emote
            message: The emote message
            
        Returns:
            tuple: (self_message, observer_message)
            where observer_message is a lambda that takes an observer
        """
        # Message for the emoting character - use their name instead of "You"
        self_message = format_sentence(f"{caller.name}{' ' if not message.startswith(' ') else ''}{message}")

        # Message for other observers - will be formatted per-observer
        observer_message = lambda observer: format_sentence(f"{caller.get_display_name(looker=observer)}{' ' if not message.startswith(' ') else ''}{message}")

        return self_message, observer_message

    def func(self):
        """Hook function"""
        if not self.args:
            self.caller.msg("What do you want to do?")
            return

        # Format the emote messages
        self_message, observer_message = self.format_emote_message(self.caller, self.args)

        # Send message to the character performing the emote
        self.caller.msg(self_message)

        # Send messages to other observers
        for observer in self.caller.location.contents:
            if observer != self.caller and hasattr(observer, 'msg'):
                observer.msg(observer_message(observer))

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
                # Get appropriate name based on knowledge
                actor_name = get_name_or_description(observer, self.caller)
                
                # Create possessive form based on whether it's "you" or a name/description
                if actor_name == "you":
                    possessive = "your"
                else:
                    possessive = get_possessive(actor_name)
                
                message = format_sentence(f"{possessive} {self.args.strip()}")
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
                # Get appropriate name based on knowledge
                actor_name = get_name_or_description(observer, self.caller)
                message = format_sentence(self.args.strip().replace(";", actor_name, 1))
                
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

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

def add_social_commands(cmdset):
    """Add all social commands to a command set"""
    # This is now empty since we're using register_standard_emotes instead
    pass
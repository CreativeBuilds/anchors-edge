"""
Base social command module containing the EmoteCommandBase class.
"""

from evennia import Command
from typeclasses.relationships import get_brief_description
from utils.text_formatting import format_sentence

class EmoteCommandBase(Command):
    """Base class for simple emote commands"""
    locks = "cmd:all()"
    help_category = "Social"
    auto_help = False  # This will hide all social commands from help
    uses_target_in_emote = False  # Set to True for emotes that handle their own targeting
    
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

    def format_emote_text(self, is_self=False, char=None, target=None, use_target_name=False, observer=None):
        """Format emote text with proper pronouns"""
        if is_self:
            # Get target pronouns if we have a target
            target_pronouns = self.get_pronouns(target) if target else None
            
            # For self view, use target's name only if we know them
            target_text = target.name if (target and hasattr(self.caller, 'knows_character') and 
                                        self.caller.knows_character(target)) else get_brief_description(target)
            
            # Convert third-person to second-person
            # e.g., "{char} sticks out {their} tongue" -> "stick out your tongue"
            text = self.emote_text.format(
                char="you",
                their="your",
                them=target_text if target else "you",  # Use target's name or description based on knowledge
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
            
            # For target text, use name if observer knows them, otherwise use brief description
            if use_target_name and target:
                target_text = target.name
            elif observer and target == observer:  # Special case when target is the observer
                target_text = "you"
            elif observer and hasattr(observer, 'knows_character') and observer.knows_character(target):
                target_text = target.name
            else:
                target_text = get_brief_description(target)
                
            return self.emote_text.format(
                char="{char}",  # Placeholder for name/description
                their=pronouns["possessive"],
                them=target_text,
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

    def check_self_targeting(self, targets):
        """
        Check if the caller is trying to target themselves.
        Returns True if self-targeting is detected.
        """
        if self.caller in targets:
            self.caller.msg("You cannot target yourself with this emote.")
            return True
        return False

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
            
            # Split target and modifier more robustly
            # First normalize spaces to single spaces
            args = ' '.join(args.split())
            
            # Try to find the first word that could be a modifier
            parts = args.split(' ')
            target_end = 0
            
            # If we have multiple parts, try to find where the modifier starts
            if len(parts) > 1:
                potential_target = parts[0]
                # Try to find the target with just the first word
                found_targets, failed = self.caller.find_targets(potential_target)
                if found_targets:
                    target_string = potential_target
                    modifier = ' '.join(parts[1:])
                else:
                    # If no target found with first word, treat everything as modifier
                    target_string = ""
                    modifier = args
            else:
                # Single word - try it as a target
                target_string = args
                modifier = ""
                
            # Try to find targets
            if target_string:
                found_targets, failed_targets = self.caller.find_targets(target_string)
                
                # If we got any failed targets, stop here - don't continue with the emote
                if failed_targets:
                    return
                    
                targets.extend(found_targets)
                
                # Check for self-targeting
                if self.check_self_targeting(targets):
                    return
            
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
                    target_for_emote = None
                    
                    for target in targets:
                        if observer == target:
                            is_observer_target = True
                            target_for_emote = target
                            continue  # Skip adding "you" to the list
                        if is_character and observer.knows_character(target):
                            target_names.append(target.name)
                            if not target_for_emote:
                                target_for_emote = target
                        else:
                            target_names.append(get_brief_description(target))
                            if not target_for_emote:
                                target_for_emote = target
                    
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
                        msg = f"You {self.format_emote_text(is_self=True, target=target_for_emote, observer=observer)}"
                    elif is_observer_target:
                        msg = f"{caller_name} {self.format_emote_text(char=self.caller, target=observer, observer=observer)}"
                    else:
                        # For observers who aren't involved, use names if they know both parties
                        if is_character and target_for_emote:
                            if observer.knows_character(self.caller) and observer.knows_character(target_for_emote):
                                # Use actual names since observer knows both
                                msg = f"{caller_name} {self.format_emote_text(char=self.caller, target=target_for_emote, use_target_name=True, observer=observer)}"
                            else:
                                # Use descriptions for those they don't know
                                msg = f"{caller_name} {self.format_emote_text(char=self.caller, target=target_for_emote, observer=observer)}"
                        else:
                            msg = f"{caller_name} {self.format_emote_text(char=self.caller, target=target_for_emote, observer=observer)}"
                        
                    # Only add preposition and target if the emote doesn't handle its own targeting
                    if not self.uses_target_in_emote:
                        msg = f"{msg} {preposition} {targets_str}"
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
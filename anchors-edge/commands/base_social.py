"""
Base social command module containing the EmoteCommandBase class.
"""

from evennia import Command
from typeclasses.relationships import get_brief_description
from utils.text_formatting import format_sentence
from enum import Enum

class TargetType(Enum):
    NONE = 0      # No targeting allowed
    OPTIONAL = 1  # Can target but not required
    REQUIRED = 2  # Must have a target

class EmoteCommandBase(Command):
    """Base class for social emote commands"""
    locks = "cmd:all()"
    help_category = "Social"
    auto_help = False  # This will hide all social commands from help
    targetable = TargetType.OPTIONAL  # Default to optional targeting
    
    def get_pronouns(self, character):
        """
        Get pronouns for a character based on their gender.
        Returns dict with: subjective (he/she/they), objective (him/her/them),
        possessive (his/her/their), reflexive (himself/herself/themselves)
        """
        # Handle None character
        if not character or not hasattr(character, 'db'):
            return {
                "subjective": "they",
                "objective": "them",
                "possessive": "their",
                "reflexive": "themselves"
            }
            
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
            target_text = target.name if (target and hasattr(target, 'name') and hasattr(self.caller, 'knows_character') and 
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
            if use_target_name and target and hasattr(target, 'name'):
                target_text = target.name
            elif observer and target == observer:  # Special case when target is the observer
                target_text = "you"
            elif observer and hasattr(observer, 'knows_character') and target and observer.knows_character(target):
                target_text = target.name if hasattr(target, 'name') else get_brief_description(target)
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

    def format_target_list(self, targets):
        """
        Format a list of targets into a grammatically correct string.
        
        Args:
            targets (list): List of target objects
            
        Returns:
            str: Formatted string like "X", "X and Y" or "X, Y and Z"
        """
        if not targets:
            return ""
            
        # Get visible names for each target based on viewer's knowledge
        target_names = []
        for target in targets:
            # This should use get_visible_name or similar that handles
            # what name the caller sees for each target
            name = target.get_display_name(self.caller)
            target_names.append(name)
            
        if len(target_names) == 1:
            return target_names[0]
        elif len(target_names) == 2:
            return f"{target_names[0]} and {target_names[1]}"
        else:
            return f"{', '.join(target_names[:-1])} and {target_names[-1]}"

    def find_target(self, search_term):
        """
        Find a target based on the caller's knowledge of them.
        Takes into account relationships and knowledge levels.
        
        Args:
            search_term (str): The term to search for
            
        Returns:
            Object or None: The found target or None if not found
        """
        search_term = search_term.lower()
        possible_targets = self.caller.location.contents
        
        for obj in possible_targets:
            if not hasattr(obj, 'db'):  # Skip non-character objects
                continue
                
            # If caller knows the character, check their name
            if hasattr(self.caller, 'knows_character') and self.caller.knows_character(obj):
                if search_term in obj.key.lower():
                    return obj
            
            # Otherwise check their visible description
            desc = get_brief_description(obj).lower()
            if search_term in desc:
                return obj
                
        return None

    def func(self):
        """Handle the emote command."""
        if not self.args:
            # No targets or modifiers, just show the base emote
            emote = self.emote_text.format(
                char=self.caller.key,
                their=get_pronoun(self.caller, "possessive"),
                them=get_pronoun(self.caller, "objective"),
                they=get_pronoun(self.caller, "subjective"),
                theirs=get_pronoun(self.caller, "possessive"),
                themselves=get_pronoun(self.caller, "reflexive")
            )
            self.caller.location.msg_contents(format_sentence(f"{self.caller.key} {emote}"))
            return

        # Split args into potential targets and modifier
        args = self.args.strip()
        targets_str = None
        modifier = None
        
        if " " in args:
            targets_str, modifier = args.rsplit(" ", 1)
        else:
            targets_str = args
            
        # Split potential targets by commas and handle multi-word names
        if targets_str:
            target_names = [t.strip() for t in targets_str.split(",")]
            found_targets = []
            failed_targets = []
            
            for target_name in target_names:
                target = self.find_target(target_name)
                
                if target:
                    # Check for self-targeting
                    if target == self.caller:
                        self.caller.msg("You cannot target yourself with this emote.")
                        return
                    found_targets.append(target)
                else:
                    failed_targets.append(target_name)
                    
            if failed_targets:
                self.caller.msg(f"Could not find: {', '.join(failed_targets)}")
                if not found_targets:
                    return
                    
            # Format the target list
            target_string = self.format_target_list(found_targets)
            
            # Determine if this emote requires a target or if it's optional
            requires_target = "{them}" in self.emote_text
            
            if requires_target:
                # Use the emote text as-is since it has {them} built in
                emote = self.emote_text.format(
                    char=self.caller.key,
                    their=get_pronoun(self.caller, "possessive"),
                    them=target_string,
                    they=get_pronoun(self.caller, "subjective"),
                    theirs=get_pronoun(self.caller, "possessive"),
                    themselves=get_pronoun(self.caller, "reflexive")
                )
            else:
                # Add "at" or "to" based on the emote
                preposition = "to" if self.key in ["wave", "bow", "nod"] else "at"
                emote = f"{self.emote_text} {preposition} {target_string}"
            
            # Add modifier if present
            if modifier:
                emote = f"{emote} {modifier}"
                    
            self.caller.location.msg_contents(format_sentence(f"{self.caller.key} {emote}"))
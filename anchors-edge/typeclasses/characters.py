"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent
import random
from datetime import datetime
import os
import requests
from time import time
from dotenv import load_dotenv
import re
from server.conf.settings import START_LOCATION 
from django.conf import settings
import json
from pathlib import Path
from typeclasses.relationships import (
    KnowledgeLevel, 
    get_brief_description,
    get_basic_description, 
    get_full_description
)
from evennia.utils import inherits_from
from utils.text_formatting import format_sentence
from django.utils.translation import gettext as _
from utils.text_formatting import capitalize_first_letter

# Load environment variables from .env file
load_dotenv()

# Get environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Intoxication level thresholds
INTOX_SOBER = 0
INTOX_TIPSY = 15  # 1-15
INTOX_DRUNK = 30  # 16-30
INTOX_VERY_DRUNK = 45  # 31-45
INTOX_PASS_OUT = 50  # 46-50

def get_intoxication_description(intoxication):
    """Helper function to get description based on intoxication level"""
    if not intoxication or intoxication <= INTOX_SOBER:
        return ""
    elif intoxication <= INTOX_TIPSY:
        return "|/|yThey appear slightly tipsy.|n"
    elif intoxication <= INTOX_DRUNK:
        return "|/|yThey are noticeably drunk.|n"
    elif intoxication <= INTOX_VERY_DRUNK:
        return "|/|rThey are very drunk and unsteady on their feet.|n"
    else:
        return "|/|RThey are completely intoxicated and can barely stand.|n"

class Character(ObjectParent, DefaultCharacter):
    """Base character class"""
    def at_object_creation(self):
        """Called when character is first created"""
        super().at_object_creation()
        
        # Initialize currency for all characters
        self.db.currency = {
            "gold": 2,     # Starting amount
            "silver": 5,   # Starting amount
            "copper": 10   # Starting amount
        }
        
        # Initialize basic description attributes
        self.db.height = None      # Height in inches (e.g., 74 for 6'2")
        self.db.build = None       # muscular, slim, stocky, etc.
        self.db.basic_desc = None  # Generated basic description
        self.db.descriptions = {}  # Initialize empty descriptions dict
        
        # Initialize roleplay and optional status
        self.db.rstatus = None     # Roleplay status (max 50 chars)
        self.db.ostatus = None     # Optional status (max 180 chars)
        
        # Initialize introduction tracking
        self.db.introduced_to = set()  # Set of character IDs this character has been introduced to
        
        # Initialize intoxication system
        self.db.intoxication = 0    # Current intoxication level
        self.db.max_intoxication = INTOX_PASS_OUT  # Pass out at this level
        
        # Start the sobriety ticker (checks every minute)
        from evennia import TICKER_HANDLER
        TICKER_HANDLER.add(60, self.process_sobriety)
        
        # Add rate limiting attributes
        self.db.last_consume_message = 0  # Timestamp of last consume message
        self.db.consume_cooldown = 5  # Seconds between consume messages
        
        # Basic attributes
        self.db.race = None
        self.db.subrace = None
        
        # Initialize base stats
        for stat, value in settings.BASE_CHARACTER_STATS.items():
            setattr(self.db, stat.lower(), value)
            
    def initialize_descriptions(self):
        """Initialize character descriptions based on race and gender."""
        if not self.db.race or not self.db.gender:
            return
        
        # Load descriptions from JSON
        with open(Path("data/descriptions/body_parts.json"), 'r') as f:
            race_descriptions = json.load(f)
        
        # Get descriptions for race and gender
        if self.db.race in race_descriptions:
            gender = self.db.gender.lower()
            if gender in race_descriptions[self.db.race]:
                descriptions = {}
                for part, descs in race_descriptions[self.db.race][gender].items():
                    if isinstance(descs, list) and descs:
                        descriptions[part] = random.choice(descs)
                    else:
                        descriptions[part] = descs
                self.db.descriptions = descriptions

    def normalize_currency(self):
        """Convert currency to its most efficient form"""
        currency = self.get_currency()
        
        # Convert copper to silver
        if currency["copper"] >= 10:
            silver_from_copper = currency["copper"] // 10
            currency["copper"] = currency["copper"] % 10
            currency["silver"] += silver_from_copper
            
        # Convert silver to gold
        if currency["silver"] >= 10:
            gold_from_silver = currency["silver"] // 10
            currency["silver"] = currency["silver"] % 10
            currency["gold"] += gold_from_silver
            
    def get_currency(self):
        """Get the character's current currency amounts"""
        if not hasattr(self.db, "currency"):
            self.db.currency = {"gold": 0, "silver": 0, "copper": 0}
        return self.db.currency
        
    def add_currency(self, gold=0, silver=0, copper=0):
        """Add currency to the character and normalize"""
        currency = self.get_currency()
        currency["gold"] += gold
        currency["silver"] += silver
        currency["copper"] += copper
        self.normalize_currency()
        
    def remove_currency(self, gold=0, silver=0, copper=0):
        """
        Remove currency from the character if they have enough.
        Automatically converts higher denominations if needed.
        """
        currency = self.get_currency()
        
        # Convert everything to copper for easy comparison
        total_copper_needed = (gold * 100) + (silver * 10) + copper
        total_copper_has = (currency["gold"] * 100) + (currency["silver"] * 10) + currency["copper"]
        
        if total_copper_has >= total_copper_needed:
            # Remove the copper amount
            remaining_copper = total_copper_has - total_copper_needed
            
            # Convert back to gold/silver/copper
            currency["gold"] = remaining_copper // 100
            remaining_copper = remaining_copper % 100
            
            currency["silver"] = remaining_copper // 10
            currency["copper"] = remaining_copper % 10
            
            # Store the updated currency
            self.db.currency = currency
            
            return True
        return False
        
    def add_intoxication(self, amount):
        """Add to character's intoxication level"""
        # Initialize intoxication if it doesn't exist
        if not hasattr(self.db, "intoxication"):
            self.db.intoxication = 0
        if not hasattr(self.db, "max_intoxication"):
            self.db.max_intoxication = INTOX_PASS_OUT
            
        old_level = self.get_intoxication_level()
        self.db.intoxication = max(0, min(self.db.max_intoxication, self.db.intoxication + amount))
        new_level = self.get_intoxication_level()
        
        # Notify of state changes
        if old_level != new_level:
            self.msg(self.get_intoxication_message())
            
        # Pass out if too drunk
        if self.db.intoxication >= self.db.max_intoxication:
            self.msg("You pass out from too much drink!")
            self.location.msg_contents(f"{self.name} passes out drunk!", exclude=[self])
            # TODO: Add any pass out effects here
            
    def process_sobriety(self, *args, **kwargs):
        """Process recovery from intoxication"""
        if self.db.intoxication > 0:
            old_level = self.get_intoxication_level()
            self.db.intoxication = max(0, self.db.intoxication - 1)
            new_level = self.get_intoxication_level()
            
            # Notify if state has changed
            if old_level != new_level:
                self.msg(self.get_intoxication_message())
                
    def get_intoxication_level(self):
        """Get the current intoxication state"""
        # Initialize if needed
        if not hasattr(self.db, "intoxication") or self.db.intoxication is None:
            self.db.intoxication = 0
            
        intox = self.db.intoxication
        if intox <= INTOX_SOBER:
            return 0  # Sober
        elif intox <= INTOX_TIPSY:
            return 1  # Tipsy
        elif intox <= INTOX_DRUNK:
            return 2  # Drunk
        elif intox <= INTOX_VERY_DRUNK:
            return 3  # Very drunk
        else:
            return 4  # About to pass out
            
    def get_intoxication_message(self):
        """Get a message describing current intoxication state"""
        level = self.get_intoxication_level()
        if level == 0:
            return "You feel completely sober."
        elif level == 1:
            return "You feel slightly tipsy."
        elif level == 2:
            return "You are definitely drunk."
        elif level == 3:
            return "You are very drunk and having trouble standing straight."
        else:
            return "You are barely conscious and should probably stop drinking."

    def format_description(self):
        """
        Format the character's stored descriptions into a readable format.
        Returns a string with all descriptions formatted.
        """
        if not self.db.descriptions:
            return "You see nothing special."
            
        # Define the order we want to show parts in
        part_order = [
            'eyes', 'hair', 'face', 'hands', 'arms', 'chest', 
            'stomach', 'back', 'legs', 'feet'
        ]
        
        # Add race-specific parts
        if hasattr(self.db, 'race'):
            if self.db.race in ["Kobold", "Ashenkin"]:
                part_order.extend(["horns", "tail"])
            elif self.db.race == "Feline":
                part_order.append("tail")
        
        # Build the description string
        desc_lines = []
        for part in part_order:
            if part in self.db.descriptions:
                desc_lines.append(f"|w{part}:|n {self.db.descriptions[part]}")
                
        return "\n".join(desc_lines)

    def return_appearance(self, looker, **kwargs):
        """
        This formats what another character sees when looking
        at this character.
        """
        if not looker:
            return ""
        
        # Check if the looker knows this character or is looking at themselves
        is_self = (looker == self)
        knows_character = is_self or (looker.knows_character(self) if hasattr(looker, 'knows_character') else False)
        
        # Get the appropriate description based on knowledge level
        if is_self:
            name_display = f"|c{self.name}|n"
            description = get_full_description(self, include_rstatus=False, include_ostatus=True)
        elif knows_character:
            knowledge_level = looker.db.known_by.get(self.id, KnowledgeLevel.STRANGER)
            name_display = f"|c{self.name}|n"
            
            if knowledge_level >= KnowledgeLevel.FRIEND:
                description = get_full_description(self, include_rstatus=False, include_ostatus=True)
            elif knowledge_level >= KnowledgeLevel.ACQUAINTANCE:
                description = get_basic_description(self, include_rstatus=False, include_ostatus=True)
            else:
                description = get_brief_description(self, include_rstatus=False, include_ostatus=True)
        else:
            brief_desc = get_brief_description(self, include_rstatus=False, include_ostatus=True)
            name_display = f"|c{brief_desc}|n"
            description = brief_desc

        # Add intoxication description if any
        if hasattr(self.db, 'intoxication') and self.db.intoxication > 0:
            intox_desc = get_intoxication_description(self.db.intoxication)
            if intox_desc:
                description += f"\n\n{intox_desc}"

        return f"{name_display}\n\n{description}"

    def can_show_consume_message(self):
        """Check if enough time has passed to show another consume message"""
        current_time = time()
        
        # Initialize attributes if they don't exist
        if not hasattr(self.db, 'last_consume_message'):
            self.db.last_consume_message = 0
        if not hasattr(self.db, 'consume_cooldown'):
            self.db.consume_cooldown = 5

        # Ensure we have valid values
        if self.db.last_consume_message is None:
            self.db.last_consume_message = 0
        if self.db.consume_cooldown is None:
            self.db.consume_cooldown = 5
        
        if current_time - self.db.last_consume_message >= self.db.consume_cooldown:
            self.db.last_consume_message = current_time
            return True
        return False

    def calculate_stats(self):
        """
        Calculate current stats based on race, subrace, and background modifiers.
        """
        # Start with base stats
        stats = dict(settings.BASE_CHARACTER_STATS)
        
        # Get race and subrace
        race_tags = self.tags.get(category="race")
        subrace_tags = self.tags.get(category="subrace")
        background_tags = self.tags.get(category="background")
        
        race = race_tags[0] if race_tags else None
        subrace = subrace_tags[0] if subrace_tags else None
        background = background_tags[0] if background_tags else None
        
        if race:
            race = race.capitalize()
            # Apply racial modifiers
            if subrace:
                subrace = subrace.lower()
                if subrace in settings.AVAILABLE_RACES[race]["modifiers"]:
                    racial_mods = settings.AVAILABLE_RACES[race]["modifiers"][subrace]
                    for stat, mod in racial_mods.items():
                        stats[stat] += mod
            else:
                if "modifiers" in settings.AVAILABLE_RACES[race]:
                    racial_mods = settings.AVAILABLE_RACES[race]["modifiers"]
                    for stat, mod in racial_mods.items():
                        stats[stat] += mod
        
        if background:
            background = background.capitalize()
            # Apply background modifiers
            if background in settings.CHARACTER_BACKGROUNDS:
                bg_mods = settings.CHARACTER_BACKGROUNDS[background]["stats"]
                for stat, mod in bg_mods.items():
                    stats[stat] += mod
        
        return stats

    def get_stat(self, stat):
        """
        Get a specific stat's current value.
        
        Args:
            stat (str): The stat to get (STR, DEX, etc.)
        
        Returns:
            int: The calculated stat value
        """
        stats = self.calculate_stats()
        return stats.get(stat, 10)  # Default to 10 if stat not found

    def format_height(self):
        """
        Formats the height from inches to a readable format (e.g., 6'2")
        Returns None if no height is set
        """
        if self.db.height is None:
            return None
            
        feet = self.db.height // 12
        inches = self.db.height % 12
        
        if inches == 0:
            return f"{feet}'"
        return f"{feet}'{inches}"

    def generate_basic_description(self):
        """
        Generates a basic description based on character's attributes.
        Returns a string like 'A 6'2" female wood elf' or 'A stocky male dwarf'
        """
        if not all([self.db.gender, self.db.race]):
            return "an unknown person."
            
        parts = ["a"]
        
        # Add height if set
        height_str = self.format_height()
        if height_str:
            parts.append(height_str)
            
        # Add build if set
        if self.db.build:
            parts.append(self.db.build)
            
        # Add gender and race
        gender = self.db.gender.lower()
        race = self.db.race
        
        if gender in ['male', 'female']:
            parts.append(gender)
            
        # Add subrace if it exists and isn't "normal"
        if self.db.subrace and self.db.subrace.lower() != "normal":
            parts.append(self.db.subrace.lower())
            
        parts.append(race.lower())
        
        # Join parts and ensure proper sentence formatting
        return " ".join(parts)

    def at_post_create(self):
        """Called after character is created."""
        super().at_post_create()
        
        # Set height from menu data if available
        if hasattr(self.db.account, 'ndb') and hasattr(self.db.account.ndb, '_menutree'):
            menu = self.db.account.ndb._menutree
            if hasattr(menu, 'height'):
                self.db.height = menu.height
        
        # Initialize descriptions
        self.initialize_descriptions()

    def knows_character(self, character):
        """
        Check if this character knows another character.
        Args:
            character: The character to check if known
        Returns:
            bool: True if the character is known, False otherwise
        """
        # Always know yourself
        if character == self:
            return True
        
        # NPCs are generally known by their role/title
        if hasattr(character.db, 'is_npc') and character.db.is_npc:
            return True
        
        # Initialize known_by if it doesn't exist
        if not hasattr(self.db, 'known_by') or self.db.known_by is None:
            self.db.known_by = {}
        
        # Return knowledge level >= ACQUAINTANCE
        return character.id in self.db.known_by and self.db.known_by[character.id] >= KnowledgeLevel.ACQUAINTANCE

    def get_display_name(self, looker=None, include_rstatus=False, **kwargs):
        """
        Get the display name of this character based on whether the looker knows them.
        Args:
            looker: The character looking at this character
            include_rstatus: Whether to include roleplay status (defaults to True)
        Returns:
            str: The name to display
        """
        # Get base name/description
        if looker == self:
            base_name = capitalize_first_letter(self.name)
        elif looker and hasattr(looker, 'knows_character'):
            if looker.knows_character(self):
                knowledge_level = looker.db.known_by.get(self.id, KnowledgeLevel.STRANGER)
                if knowledge_level >= KnowledgeLevel.ACQUAINTANCE:
                    base_name = capitalize_first_letter(self.name)
                else:
                    base_name = get_brief_description(self)
            else:
                base_name = get_brief_description(self)
        else:
            base_name = get_brief_description(self)

        # Add roleplay status if requested and available
        if include_rstatus and hasattr(self.db, 'rstatus') and self.db.rstatus:
            return f"{base_name} ({self.db.rstatus})"
        
        return base_name

    def announce_move_from(self, destination, msg=None, mapping=None, **kwargs):
        """
        Called when the object moves away from its current location.
        Args:
            destination (Object): Where we're going.
            msg (str, optional): Custom message.
            mapping (dict, optional): Additional mapping for msg.
            **kwargs: Additional parameters for future expansion.
        """
        if not self.location:
            return
        
        location = self.location
        exits = [o for o in location.contents if o.destination == destination]
        if not mapping:
            mapping = {}

        # Get all characters in the room
        characters = [o for o in location.contents if hasattr(o, 'has_account') or (hasattr(o.db, 'is_npc') and o.db.is_npc)]
        
        # Send personalized messages to each character
        for char in characters:
            if char == self:  # Skip the moving character
                continue
            
            # Check if this character knows the one leaving
            knows_char = char.knows_character(self) if hasattr(char, 'knows_character') else False
            
            # Create the message text
            if knows_char:
                message = f"{capitalize_first_letter(self.name)} leaves {exits[0].name if exits else 'somewhere'}."
            else:
                message = format_sentence(f"{self.generate_basic_description().rstrip('.')} leaves {exits[0].name if exits else 'somewhere'}.")
            
            # Send the message
            char.msg(text=(message, {"type": "room"}))

    def announce_move_to(self, source_location, msg=None, mapping=None, **kwargs):
        """
        Called when the object arrives at its new location.
        Args:
            source_location (Object): Where we came from.
            msg (str, optional): Custom message.
            mapping (dict, optional): Additional mapping for msg.
            **kwargs: Additional parameters for future expansion.
        """
        if not self.location:
            return
        
        location = self.location
        exits = [o for o in location.contents if o.destination == source_location]
        if not mapping:
            mapping = {}

        # Get all characters in the room
        characters = [o for o in location.contents if hasattr(o, 'has_account') or (hasattr(o.db, 'is_npc') and o.db.is_npc)]
        
        # Send personalized messages to each character
        for char in characters:
            if char == self:  # Skip the moving character
                continue
            
            # Check if this character knows the one arriving
            knows_char = char.knows_character(self) if hasattr(char, 'knows_character') else False
            
            # Create the message text
            if knows_char:
                message = f"{capitalize_first_letter(self.name)} arrives from {exits[0].name if exits else 'somewhere'}."
            else:
                message = format_sentence(f"{self.generate_basic_description().rstrip('.')} arrives from {exits[0].name if exits else 'somewhere'}.")
            
            # Send the message
            char.msg(text=(message, {"type": "room"}))

    def introduce_to(self, character):
        """
        Introduce this character to another character.
        Args:
            character: The character to introduce to
        """
        # Initialize known_by as a dict if it doesn't exist or is None
        if not hasattr(self.db, 'known_by') or self.db.known_by is None:
            self.db.known_by = {}
        if not hasattr(character.db, 'known_by') or character.db.known_by is None:
            character.db.known_by = {}
        
        # Set knowledge level to ACQUAINTANCE for the target character
        # This means the target character now knows this character
        character.db.known_by[self.id] = KnowledgeLevel.ACQUAINTANCE

    def find_character_by_desc(self, search_text):
        """
        Find a character in the same location based on their description or name.
        Uses fuzzy string matching to find the best match.
        
        Args:
            search_text (str): Text to search for in descriptions/names
            
        Returns:
            Character or None: Matching character if found, None if not found or ambiguous
        """
        if not self.location:
            return None
        
        # Get all characters in the room except self, excluding non-character objects
        chars = [obj for obj in self.location.contents 
                if (inherits_from(obj, "typeclasses.characters.Character") or 
                    inherits_from(obj, "typeclasses.characters.NPC"))
                and obj != self
                and not inherits_from(obj, "evennia.objects.objects.DefaultExit")]
        
        if not chars:
            return None
        
        from difflib import SequenceMatcher
        
        # Normalize search text
        search_text = search_text.lower().strip()
        
        # Find matches using fuzzy string matching
        matches = []
        for char in chars:
            # Check both name and description
            if hasattr(self, 'knows_character') and self.knows_character(char):
                name_match = SequenceMatcher(None, search_text, char.name.lower()).ratio()
                matches.append((char, name_match))
            else:
                desc = char.generate_basic_description().lower()
                # Remove "a" or "an" from the start for matching
                desc = ' '.join(desc.split()[1:]) if desc.split()[0] in ['a', 'an'] else desc
                
                # Check if search text appears in description
                if search_text in desc:
                    matches.append((char, 0.9))  # High confidence for direct substring match
                else:
                    # Fallback to fuzzy matching
                    desc_match = SequenceMatcher(None, search_text, desc).ratio()
                    matches.append((char, desc_match))
            
        # Sort matches by ratio, highest first
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Return best match if it's good enough
        if matches and matches[0][1] > 0.4:  # Lower threshold for more lenient matching
            return matches[0][0]
            
        return None

    def at_post_puppet(self, **kwargs):
        """
        Called just after puppeting has been completed and all
        Account<->Object links have been established.

        Args:
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        # Send initial messages
        self.msg(_("\nYou become |c{name}|n.\n").format(name=capitalize_first_letter(self.key)))
        self.msg((self.at_look(self.location), {"type": "look"}), options=None)

        def message(obj, from_obj):
            obj.msg(
                format_sentence(_("{name} has entered the game.").format(name=self.get_display_name(obj))),
                from_obj=from_obj,
            )
            
        # Announce to room
        if self.location:
            self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """
        We stove away the character when the account goes ooc/logs off,
        otherwise the character object will remain in the room also
        after the account logged off ("headless", so to say).

        Args:
            account (DefaultAccount): The account object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        Keyword Args:
            reason (str): If given, adds a reason for the unpuppet. This
                is set when the user is auto-unpuppeted due to being link-dead.
            **kwargs: Arbitrary, optional arguments for users
                overriding the call (unused by default).

        """
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:

                def message(obj, from_obj):
                    obj.msg(
                        format_sentence(_("{name} has left the game{reason}.").format(
                            name=self.get_display_name(obj),
                            reason=kwargs.get("reason", ""),
                        )),
                        from_obj=from_obj,
                    )

                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                self.location = None

    def get_rstatus(self):
        """Get the character's roleplay status."""
        if not hasattr(self.db, 'rstatus'):
            return None
        return self.db.rstatus

    def set_rstatus(self, status=None):
        """
        Set the character's roleplay status.
        Args:
            status (str, optional): The status to set. If None, clears the status.
        Returns:
            tuple: (success, message)
        """
        old_status = self.db.rstatus
        
        if status:
            if len(status) > 50:  # Max length check
                return False, "Status description cannot exceed 50 characters."
                
            # Only allow safe characters for text display
            allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_,.!? '-")
            sanitized_status = ''.join(char for char in status if char in allowed_chars)
            
            # Remove multiple consecutive spaces
            sanitized_status = ' '.join(sanitized_status.split())
            
            # Strip leading/trailing whitespace
            sanitized_status = sanitized_status.strip()
            
            # If the status was modified during sanitization, inform the user
            if sanitized_status != status:
                self.db.rstatus = sanitized_status
                # Notify online friends
                if old_status != sanitized_status:
                    # Get all online characters
                    from evennia.objects.models import ObjectDB
                    online_chars = [obj for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters.Character')
                                  if obj.has_account and obj.sessions.count()]
                    # Filter to only friends and notify them
                    for char in online_chars:
                        if char != self and hasattr(char.db, 'known_by') and char.db.known_by.get(self.id, 0) >= 2:  # KnowledgeLevel.FRIEND
                            char.msg(f"{self.name} set their status to {sanitized_status}")
                return True, f"Your roleplay status has been set to: {sanitized_status} (invalid characters were removed)"
            else:
                self.db.rstatus = status
                # Notify online friends
                if old_status != status:
                    # Get all online characters
                    from evennia.objects.models import ObjectDB
                    online_chars = [obj for obj in ObjectDB.objects.filter(db_typeclass_path__contains='typeclasses.characters.Character')
                                  if obj.has_account and obj.sessions.count()]
                    # Filter to only friends and notify them
                    for char in online_chars:
                        if char != self and hasattr(char.db, 'known_by') and char.db.known_by.get(self.id, 0) >= 2:  # KnowledgeLevel.FRIEND
                            char.msg(f"{self.name} set their status to {status}")
                return True, f"Your roleplay status has been set to: {status}"
        else:
            # Just clear the status without notifying anyone
            self.db.rstatus = None
            return True, "Your roleplay status has been cleared."

    def get_ostatus(self):
        """Get the character's optional status."""
        if not hasattr(self.db, 'ostatus'):
            return None
        return self.db.ostatus

    def set_ostatus(self, status=None):
        """
        Set the character's optional status.
        Args:
            status (str, optional): The status to set. If None, clears the status.
        Returns:
            tuple: (success, message)
        """
        if status:
            if len(status) > 180:  # Max length check
                return False, "Optional status description cannot exceed 180 characters."
            self.db.ostatus = status
            return True, f"Your optional status has been set to: {status}"
        else:
            self.db.ostatus = None
            return True, "Your optional status has been cleared."

    def clear_rstatus(self):
        """Clear the character's roleplay status."""
        self.db.rstatus = None

    def at_pre_move(self, destination, **kwargs):
        """Called before moving the object."""
        # Clear rstatus when moving
        self.clear_rstatus()
        return super().at_pre_move(destination, **kwargs)

    def format_target_list(self, targets, observer=None, include_you=False):
        """
        Format a list of targets with proper conjunctions.
        
        Args:
            targets (list): List of target objects
            observer (Object, optional): The character viewing the list
            include_you (bool): Whether to include "you" in the list for the observer
            
        Returns:
            str: Formatted list like "Bob, Alice and Charlie" or "you, Bob and Charlie"
        """
        if not targets:
            return ""

        # Build list of names/descriptions
        names = []
        for target in targets:
            if not hasattr(target, 'name'):
                continue
                
            # If this target is the observer, skip it - we'll handle it separately
            if observer and target == observer:
                continue
                
            if observer and hasattr(observer, 'knows_character') and observer.knows_character(target):
                names.append(target.name)
            else:
                names.append(get_brief_description(target))

        if not names:
            return "you" if observer and observer in targets else ""
            
        # If observer is one of the targets, format differently
        if observer and observer in targets:
            if len(names) == 0:
                return "you"
            elif len(names) == 1:
                return f"you and {names[0]}"
            else:
                return f"you, {', '.join(names[:-1])} and {names[-1]}"
        
        # Standard formatting for non-target observers
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} and {names[1]}"
        else:
            return f"{', '.join(names[:-1])} and {names[-1]}"

    def find_targets(self, target_string, location=None, quiet=False):
        """
        Find targets by name or description using simple string matching.
        """
        if not target_string:
            return [], []
            
        # Use current location if none provided
        location = location or self.location
        if not location:
            return [], []
            
        # Split target string by commas
        target_strings = [t.strip() for t in target_string.split(",")]
        targets = []
        failed_targets = []
        
        for search_term in target_strings:
            found = False
            search_term = search_term.lower().strip()
            
            # Skip empty search terms
            if not search_term:
                continue
            
            # Get all potential targets in the room
            potential_targets = [obj for obj in location.contents 
                              if (hasattr(obj, 'has_account') and obj.has_account) or 
                                 (hasattr(obj.db, 'is_npc') and obj.db.is_npc)]
            
            matches = []
            for obj in potential_targets:
                if obj == self:  # Skip self
                    continue
                    
                # Match against name if we know them, description if we don't
                match_text = obj.name.lower() if self.knows_character(obj) else get_brief_description(obj).lower()
                
                if search_term in match_text:
                    matches.append(obj)
            
            # If we found exactly one match, use it
            if len(matches) == 1:
                targets.append(matches[0])
                found = True
            # If we found multiple matches, add to failed targets
            elif len(matches) > 1:
                if not quiet:
                    match_descriptions = []
                    for obj in matches:
                        if self.knows_character(obj):
                            match_descriptions.append(f"  {obj.name}")
                        else:
                            match_descriptions.append(f"  {get_brief_description(obj)}")
                    self.msg(f"Multiple matches for '{search_term}':|/{'|/'.join(match_descriptions)}|/Please be more specific.")
                failed_targets.append(search_term)  # Add to failed targets
            
            if not found:
                failed_targets.append(search_term)
                
        return targets, failed_targets

class NPC(Character):
    """Base NPC class with conversation memory"""
    def at_object_creation(self):
        """Called when NPC is first created"""
        # Initialize currency first
        self.db.currency = {
            "gold": 0,
            "silver": 0,
            "copper": 0
        }
        
        # Then call parent's at_object_creation which might modify the currency
        super().at_object_creation()
        
        # Initialize conversation attributes
        self.db.responses = {}  # Dictionary to store responses
        self.db.default_responses = []  # List of default responses when no match
        self.db.is_npc = True  # Flag to identify as NPC
        
        # Initialize basic currency responses
        self.db.currency_responses = {
            "copper": [f"{self.name} accepts the copper coins."],
            "silver": [f"{self.name} accepts the silver coins."],
            "gold": [f"{self.name} accepts the gold coins."]
        }
        
        # Initialize basic item responses
        self.db.item_responses = {
            "default": [f"{self.name} accepts the item."],
            "coin": [f"{self.name} accepts the coins."],
            "food": [f"{self.name} accepts the food."],
            "drink": [f"{self.name} accepts the drink."]
        }
        
        # Initialize conversation memory
        self.db.conversation_memory = {
            "per_player": {},      # Dictionary to store interactions per player
            "memory_length": 10    # How many interactions to remember per player
        }
        
    def remember_interaction(self, speaker, message, response):
        """
        Store a conversation interaction in memory.
        
        Args:
            speaker (Character): Who spoke to the NPC
            message (str): What they said
            response (str): How the NPC responded
        """
        timestamp = datetime.now()
        
        # Create memory entry
        memory = {
            "message": message,
            "response": response,
            "timestamp": timestamp
        }
        
        # Initialize player's conversation history if it doesn't exist
        if speaker.key not in self.db.conversation_memory["per_player"]:
            self.db.conversation_memory["per_player"][speaker.key] = {
                "recent_interactions": [],
                "last_interaction": None
            }
            
        player_memory = self.db.conversation_memory["per_player"][speaker.key]
        
        # Add to player's recent interactions
        player_memory["recent_interactions"].append(memory)
        player_memory["last_interaction"] = timestamp
        
        # Keep only the most recent interactions for this player
        if len(player_memory["recent_interactions"]) > self.db.conversation_memory["memory_length"]:
            player_memory["recent_interactions"].pop(0)
            
        # Log the entire conversation history for this player
        print(f"|/Conversation history between {self.name} and {speaker.key}:")
        print("-" * 50)
        for interaction in player_memory["recent_interactions"]:
            print(f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"Player: {interaction['message']}")
            print(f"{self.name}: {interaction['response']}")
            print("-" * 50)
        
    def get_player_memory(self, player_key):
        """
        Get a specific player's conversation history
        
        Args:
            player_key (str): The player's identifier
            
        Returns:
            dict: The player's conversation history or None if no history exists
        """
        return self.db.conversation_memory["per_player"].get(player_key, None)
        
    def handle_conversation(self, speaker, message):
        """
        Handle incoming conversation and return appropriate response.
        
        Args:
            speaker (Character): The character speaking to this NPC
            message (str): The message being told to this NPC
            
        Returns:
            str: The NPC's response
        """
        # If no specific responses are set, use defaults
        if not self.db.responses and not self.db.default_responses:
            response = f"{self.name} listens but doesn't respond."
            self.remember_interaction(speaker, message, response)
            return response
            
        # Check for specific keyword responses
        for keyword, responses in self.db.responses.items():
            if keyword.lower() in message.lower():
                # Convert _SaverList to regular list before using random.choice
                try:
                    response_list = list(responses)
                except TypeError:
                    response_list = [responses]
                response = random.choice(response_list).strip()
                self.remember_interaction(speaker, message, response)
                return response
                
        # If no keyword match, use default response
        if self.db.default_responses:
            # Convert _SaverList to regular list
            default_list = list(self.db.default_responses)
            response = random.choice(default_list).strip()
            self.remember_interaction(speaker, message, response)
            return response
            
        response = f"{self.name} listens but doesn't respond."
        self.remember_interaction(speaker, message, response)
        return response

    def parse_last_offer(self, speaker):
        """Parse the most recent response for pending transactions."""
        player_memory = self.db.conversation_memory["per_player"].get(speaker.key, {"recent_interactions": []})
        if not player_memory or not player_memory["recent_interactions"]:
            return None
            
        last_interaction = player_memory["recent_interactions"][-1]
        response = last_interaction["response"].lower()
        
        if "accepts the payment and hands you" in response:
            return None
        
        # Look for transaction tags first
        offers = []
        drink_matches = re.findall(r"<drink name='([^']+)' cp='(\d+)' intoxication='(\d+)'/>", response)
        food_matches = re.findall(r"<food name='([^']+)' cp='(\d+)'/>", response)
        
        for name, cost, intoxication in drink_matches:
            offers.append(("drink", name, int(cost), int(intoxication)))
        for name, cost in food_matches:
            offers.append(("food", name, int(cost)))
            
        # If no explicit tags, look for natural language price mentions
        if not offers:
            # First look for the total price
            price_match = re.search(r"(?:that'?s?|that(?:'?s| is|ll be)) (\d+) copper", response)
            if price_match:
                total_stated_price = int(price_match.group(1))
                
                # Define costs and intoxication levels
                drink_costs = {"ale": 5, "beer": 4, "wine": 10, "mead": 15, "coffee": 2}
                drink_intox = {"ale": 3, "beer": 2, "wine": 5, "mead": 7, "coffee": 0}
                food_costs = {"bread": 1, "meat": 5, "stew": 8}
                
                # Look for all quantity + item mentions
                found_items = []
                
                # Pattern for "X item" mentions
                quantity_matches = re.finditer(r"(\d+)\s+(?:(?:cups?|mugs?|glasses?|tankards?|bottles?|plates?|servings?|portions?)\s+(?:of\s+)?)?(\w+)", response)
                for match in quantity_matches:
                    quantity = int(match.group(1))
                    item = match.group(2).rstrip('s')  # Remove plural
                    found_items.append((quantity, item))
                
                # Calculate total cost and create offers
                total_calculated_cost = 0
                temp_offers = []
                
                for quantity, item in found_items:
                    if item in drink_costs:
                        item_cost = drink_costs[item]
                        total_calculated_cost += quantity * item_cost
                        for _ in range(quantity):
                            temp_offers.append(("drink", item, item_cost, drink_intox[item]))
                    elif item in food_costs:
                        item_cost = food_costs[item]
                        total_calculated_cost += quantity * item_cost
                        for _ in range(quantity):
                            temp_offers.append(("food", item, item_cost))
                
                # Only use the offers if the total price matches what was stated
                if total_calculated_cost == total_stated_price:
                    offers = temp_offers
        
        return offers if offers else None

    def parse_conversation_for_purchase(self, source, amount, currency_type):
        """Use AI to determine what the player was trying to purchase based on recent conversation"""
        if not OPENROUTER_API_KEY:
            return None

        # Get recent conversation history
        player_memory = self.db.conversation_memory["per_player"].get(source.key, {"recent_interactions": []})
        recent_interactions = player_memory.get("recent_interactions", [])[-3:]  # Last 3 interactions

        # Build conversation context
        context = (
            f"Recent conversation between {source.name} and {self.name}:|/|/"
        )
        
        for interaction in recent_interactions:
            context += f"{source.name}: {interaction['message']}|/"
            context += f"{self.name}: {interaction['response']}|/"

        context += f"|/{source.name} just gave {amount} {currency_type} to {self.name}.|/"

        # Prepare the prompt
        prompt = (
            f"{context}|/|/"
            "Based on this conversation and payment, what is the customer trying to purchase?|/"
            "Respond using ONLY these formats for items:|/"
            "<drink name='ale' cp='5' intoxication='3'/>|/"
            "<drink name='beer' cp='4' intoxication='2'/>|/"
            "<drink name='wine' cp='10' intoxication='5'/>|/"
            "<drink name='mead' cp='15' intoxication='7'/>|/"
            "<food name='bread' cp='1'/>|/"
            "<food name='meat' cp='5'/>|/"
            "<food name='stew' cp='8'/>|/"
            "|/If multiple items could match, choose the most likely based on:|/"
            "1. Recent conversation context|/"
            "2. Amount of money given|/"
            "3. Common tavern orders|/"
            "|/Respond with ONLY the item tag, nothing else."
        )

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4001",
            "X-Title": f"A.E. {source.key}" if source.has_account else "A.E. NPC Purchase Intent"
        }

        data = {
            "model": "x-ai/grok-vision-beta",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 100,
            "n": getattr(self.db, 'n', 1)  # Get number of responses to generate, default to 1
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                # Check each response in order until we find valid item tags
                for choice in response.json()['choices']:
                    content = choice['message']['content'].strip()
                    
                    # Parse the response for item tags
                    import re
                    drink_matches = re.findall(r"<drink name='([^']+)' cp='(\d+)' intoxication='(\d+)'/>", content)
                    food_matches = re.findall(r"<food name='([^']+)' cp='(\d+)'/>", content)
                    
                    offers = []
                    for name, cost, intox in drink_matches:
                        offers.append(("drink", name, int(cost), int(intox)))
                    for name, cost in food_matches:
                        offers.append(("food", name, int(cost)))
                        
                    if offers:  # If we found any offers, return them all
                        return offers
                
        except Exception as e:
            print(f"Error parsing purchase intent: {e}")
        
        return None

    def at_receive_currency(self, amount, currency_type, source):
        """Called when receiving currency"""
        if not source or not hasattr(source, 'msg'):
            return
            
        # Convert currency to copper for comparison
        copper_value = {
            "gold": 100,
            "silver": 10,
            "copper": 1
        }
        total_copper = amount * copper_value[currency_type]
        
        # Check for pending transactions
        pending_offers = self.parse_last_offer(source)
        
        if pending_offers:
            # Calculate total cost for offered items
            total_cost = sum(offer[2] for offer in pending_offers)  # item[2] is the cost
            
            if total_copper == total_cost:
                # Create and give all items
                items_given = []
                item_counts = {}  # Track quantities of each item
                
                # First count quantities of each item
                for offer in pending_offers:
                    item_name = offer[1]  # item[1] is the name
                    item_counts[item_name] = item_counts.get(item_name, 0) + 1
                
                # Then create and give items
                for offer in pending_offers:
                    if len(offer) == 4:  # Drink
                        item_type, item_name, item_cost, intoxication = offer
                    else:  # Food
                        item_type, item_name, item_cost = offer
                        intoxication = None
                        
                    item = self.create_ordered_item(item_type, item_name, intoxication)
                    if item:
                        item.move_to(source, quiet=True)
                        # Only add to items_given if it's the first of its kind
                        if item_name not in items_given:
                            items_given.append(item_name)
                
                if items_given:
                    # Create response with quantities
                    item_descriptions = []
                    for item_name in items_given:
                        quantity = item_counts[item_name]
                        if quantity > 1:
                            item_descriptions.append(f"{quantity} {item_name}s")
                        else:
                            item_descriptions.append(f"{item_name}")
                    
                    # Create message using proper Evennia inline functions
                    if len(item_descriptions) == 1:
                        text = f"$You() $conj(accept) the payment and $conj(hand) $you({source.key}) {item_descriptions[0]}."
                        self.location.msg_contents(text, from_obj=self, mapping={source.key: source})
                    else:
                        items_list = ", ".join(item_descriptions[:-1]) + f" and {item_descriptions[-1]}"
                        text = f"$You() $conj(accept) the payment and $conj(hand) $you({source.key}) {items_list}."
                        self.location.msg_contents(text, from_obj=self, mapping={source.key: source})
                    
                    # Remember the interaction from source's perspective
                    if hasattr(source, 'has_account') and source.has_account:
                        self.remember_interaction(
                            source,
                            f"*gives {amount} {currency_type} to {self.key}*",
                            f"{self.name} accepts the payment and hands you {items_list if len(item_descriptions) > 1 else item_descriptions[0]}."
                        )
                    return
                else:
                    # Error messages don't need actor stance since they're just NPC dialogue
                    source.add_currency(**{currency_type: amount})
                    self.location.msg_contents(f"{self.name} frowns, 'I'm sorry, something seems to be wrong with that order.'")
                    return
            else:
                # Wrong amount, return the money
                source.add_currency(**{currency_type: amount})
                self.location.msg_contents(f"{self.name} hands the coins back, 'For those items I'll need {total_cost} copper pieces.'")
                return
        else:
            # No pending offers or purchase intent found
            source.add_currency(**{currency_type: amount})
            self.location.msg_contents(f"{self.name} hands the coins back, 'I'm sorry, what would you like to order?'")

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """Called when this object receives another object"""
        super().at_object_receive(moved_obj, source_location, **kwargs)
        
        if not source_location or not hasattr(source_location, 'msg'):
            return

        # Check if this is a currency transaction
        if hasattr(moved_obj, 'key') and any(currency in moved_obj.key.lower() for currency in ['gold', 'silver', 'copper']):
            # Extract amount and type from the coin object's key
            import re
            match = re.match(r'(\d+)\s*(gold|silver|copper)', moved_obj.key.lower())
            if match:
                amount = int(match.group(1))
                currency_type = match.group(2)
                # Delete the coin object as it's being converted to currency
                moved_obj.delete()
                # Handle the currency transaction
                self.at_receive_currency(amount, currency_type, source_location)
                return
            
        # If not currency, handle as regular item
        item_type = "default"
        if "coin" in moved_obj.key.lower():
            item_type = "coin"
        elif any(food in moved_obj.key.lower() for food in ["bread", "meat", "stew", "food"]):
            item_type = "food"
        elif any(drink in moved_obj.key.lower() for drink in ["ale", "wine", "mead", "drink"]):
            item_type = "drink"
            
        # Get appropriate response list
        responses = self.db.item_responses.get(item_type, self.db.item_responses["default"])
        
        # Choose and send response
        response = random.choice(list(responses))  # Convert _SaverList to list
        self.location.msg_contents(response)
        
        if hasattr(source_location, 'has_account') and source_location.has_account:
            self.remember_interaction(
                source_location,
                f"*gives {moved_obj.key} to {self.key}*",
                response
            )

class OpenrouterCharacter(NPC):
    """
    An NPC that uses OpenRouter's AI for dynamic conversation fallbacks.
    """
    def at_object_creation(self):
        """Called when NPC is first created"""
        super().at_object_creation()
        
        # Add AI-specific attributes
        self.db.personality = ""  # Personality description for AI context
        self.db.conversation_style = ""  # How the character typically speaks
        self.db.knowledge = ""  # What the character knows about
        self.db.max_tokens = 420  # Maximum number of tokens in AI responses
        self.db.temperature = 0.5  # AI response randomness
        self.db.model = "x-ai/grok-vision-beta"  # AI model to use
        
    def get_ai_response(self, speaker, message, conversation_history):
        """
        Get an AI-generated response when no keyword matches are found.
        """
        if not OPENROUTER_API_KEY:
            return random.choice(self.db.default_responses)
            
        # Get room context
        room = self.location
        room_desc = room.db.desc if room and hasattr(room, 'db') else "unknown location"
        time_period = room.get_time_period() if hasattr(room, 'get_time_period') else "unknown time"
        
        # Get list of characters and their descriptions in the room
        character_info = []
        if room:
            for char in room.contents:
                if hasattr(char, 'has_account') or (hasattr(char.db, 'is_npc') and char.db.is_npc):
                    if char != self:  # Don't include self in the list
                        desc = char.db.desc if hasattr(char.db, 'desc') and char.db.desc else "no description"
                        character_info.append(f"{char.key}: {desc}")
        
        # Build conversation context
        context = (
            f"You are roleplaying as {self.key}, {self.db.personality}|/"
            f"Conversation style: {self.db.conversation_style}|/"
            f"Knowledge: {self.db.knowledge}|/|/"
            f"Time of day: {time_period}|/"
            f"The room's current state: {room_desc}|/|/"
            "People currently in the room:|/"
        )
        
        # Add character descriptions
        if character_info:
            for info in character_info:
                context += f"- {info}|/"
        else:
            context += "- No one else is here|/"
        
        context += "|/Example responses for specific topics:|/"
        
        # Add example responses
        for triggers, responses in self.db.responses.items():
            trigger_words = [t.strip() for t in triggers.split(',')]
            example_responses = list(responses)  # Convert _SaverList to list
            context += f"When someone mentions {' or '.join(trigger_words)}, you might say:|/"
            for response in example_responses:
                context += f"- {response}|/"
            context += "|/"
            
        context += f"|/In a conversation with {speaker.key}:|/"
        
        # Add recent conversation history
        for interaction in conversation_history[-3:]:
            context += (
                f"{speaker.key}: {interaction['message']}|/"
                f"{self.key}: {interaction['response']}|/"
            )
            
        # Add current message
        context += f"|/{speaker.key}: {message}|/{self.key}:"
        
        # Prepare API request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4001",
            "X-Title": f"A.E. {speaker.key}"
        }
        
        data = {
            "model": self.db.model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{context}|/|/"
                        f"{self.append_to_context()}"
                        "Respond in character with a single short response (max 100 tokens). "
                        "Include basic emotes or actions that fit the current room's state. "
                        "Stay consistent with the character's personality and knowledge. "
                        "|/|/Make your responses interesting and engaging but short and concise."
                        f"{self.append_to_prompt()}"
                    )
                }
            ],
            "temperature": self.db.temperature,
            "max_tokens": self.db.max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                ai_response = response.json()['choices'][0]['message']['content'].strip()
                return ai_response
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            
        # Fallback to default responses if API fails
        return random.choice(self.db.default_responses)
        
    def handle_conversation(self, speaker, message):
        """All conversations now go through the AI with examples as context"""
        player_memory = self.db.conversation_memory["per_player"].get(speaker.key, {"recent_interactions": []})
        full_response = self.get_ai_response(speaker, message, player_memory["recent_interactions"])
        
        # Extract the visible message from the response
        import re
        visible_message = ""
        message_match = re.search(r"<message>(.*?)</message>", full_response, re.DOTALL)
        if message_match:
            visible_message = message_match.group(1).strip()
        else:
            visible_message = full_response
        
        # Store the full response (with tags) in memory
        self.remember_interaction(speaker, message, full_response)
        
        # Return only the visible part to be displayed
        return visible_message
    
    def append_to_context(self):
        """Append additional context to the AI's context of the world"""
        return ""

    def update_desc(self):
        """
        Updates the character's description based on current room conditions.
        Called when room weather changes.
        """
        # Get base description
        if not hasattr(self.db, 'base_desc'):
            self.db.base_desc = self.db.desc or "You see nothing special."
        
        # Get room context
        room = self.location
        if not room:
            self.db.desc = self.db.base_desc
            return
        
        # Get time and weather data
        time_period = room.get_time_period() if hasattr(room, 'get_time_period') else None
        weather_data = room.db.weather_data if hasattr(room.db, 'weather_data') else {}
        
        # Atmospheric descriptions based on conditions
        time_descriptions = {
            "dawn": [
                "The soft light of dawn highlights their features.",
                "Early morning light casts gentle shadows across their form.",
                "Dawn's first rays give them an ethereal glow."
            ],
            "morning": [
                "Morning light brings out the warmth in their features.",
                "The bright morning sun illuminates their presence.",
                "Clear morning light shows them in sharp detail."
            ],
            "noon": [
                "The midday sun casts sharp shadows around them.",
                "Bright daylight reveals every detail of their appearance.",
                "They stand clearly visible in the full light of day."
            ],
            "afternoon": [
                "The afternoon sun bathes them in golden light.",
                "Warm afternoon light softens their features.",
                "They are outlined by the slanting afternoon sun."
            ],
            "dusk": [
                "The fading light of dusk softens their silhouette.",
                "Twilight shadows play across their features.",
                "The last rays of sun give them a mysterious air."
            ],
            "night": [
                "Shadows of night cloak their form in mystery.",
                "Darkness shrouds their features in intrigue.",
                "The night's darkness leaves only their silhouette visible."
            ]
        }
        
        # Select atmospheric descriptions
        atmospheric_desc = []
        
        # Add time-based description
        if time_period and time_period in time_descriptions:
            atmospheric_desc.append(random.choice(time_descriptions[time_period]))
        
        # Combine descriptions
        final_desc = self.db.base_desc
        if atmospheric_desc:
            final_desc += "|/|/" + " ".join(atmospheric_desc)
        
        self.db.desc = final_desc

    def at_pre_create(self):
        """
        Called before character is created.
        """
        # Get spawn location from settings.py
        spawn_location = START_LOCATION
        if spawn_location:
            self.home = spawn_location
            self.location = spawn_location
        else:
            # Fallback to limbo (#2) if no spawn location is set
            from evennia.objects.models import ObjectDB
            self.home = ObjectDB.objects.get_id(2)
            self.location = ObjectDB.objects.get_id(2)


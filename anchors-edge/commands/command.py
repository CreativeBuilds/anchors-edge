"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia import Command
from evennia.commands.command import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.mirror import Mirror
from evennia.commands.default.general import CmdLook
from evennia import default_cmds
import random
import os
import requests
from time import time
import logging
from difflib import SequenceMatcher
from evennia.utils import logger
from evennia import SESSION_HANDLER
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB
from typeclasses.relationships import KnowledgeLevel, get_brief_description, get_basic_description, get_full_description
from utils.text_formatting import format_sentence

class CmdDescribeSelf(MuxCommand):
    """
    Describe yourself while looking in the mirror
    
    Usage:
      describe <description>
      desc <description>
    
    Sets your character's description that others see when looking at you.
    This command only works when looking in a mirror.
    """
    key = "describe"
    aliases = ["desc"]
    locks = "cmd:all()"
    
    def func(self):
        """Handle the description setting"""
        caller = self.caller
        
        # First check if there's a mirror in the room
        mirror = caller.location.search("mirror", typeclass=Mirror)
        if not mirror:
            caller.msg("You need to be near a mirror to describe yourself.")
            return
            
        if not self.args:
            caller.msg("Usage: describe <description>")
            return
            
        # Set the description
        desc = self.args.strip()
        caller.db.desc = desc
        caller.msg(f"You look in the mirror and see: {desc}")

class BriefCommand(MuxCommand):
    """
    Toggle brief room descriptions
    
    Usage:
      brief
    
    Switches between normal and brief room descriptions.
    Brief descriptions show only essential information about the room.
    """
    key = "brief"
    aliases = ["br"]
    locks = "cmd:all()"
    
    def func(self):
        """Toggle brief mode"""
        caller = self.caller
        
        # Initialize brief_mode if it doesn't exist
        if not hasattr(caller.db, "brief_mode"):
            caller.db.brief_mode = False
            
        # Toggle brief mode
        if caller.db.brief_mode:
            caller.db.brief_mode = False
            caller.msg("|GBrief mode disabled.|n Room descriptions will now show full details.")
        else:
            caller.db.brief_mode = True
            caller.msg("|GBrief mode enabled.|n Room descriptions will now be shortened.")

class CmdRegenRoom(MuxCommand):
    """
    Force regenerate a room's descriptions
    
    Usage:
      regen [room]
    
    Forces a weather-aware room to regenerate all its descriptions
    and clear its caches. If no room is specified, regenerates the
    current room.
    
    Admin only command.
    """
    key = "regen"
    aliases = ["regenerate"]
    locks = "cmd:perm(Admin)"
    
    def func(self):
        """Handle the regeneration"""
        caller = self.caller
        
        # Get the target room
        if self.args:
            target = caller.search(self.args.strip())
            if not target:
                return
        else:
            target = caller.location
            
        # Check if it's a weather-aware room
        if not hasattr(target, 'update_weather'):
            caller.msg("This room is not weather-aware.")
            return
            
        # Clear all caches and force update
        target.db.cached_descriptions = {
            "dawn": None,
            "day": None,
            "dusk": None,
            "night": None
        }
        target.db.cache_timestamps = {
            "dawn": 0,
            "day": 0,
            "dusk": 0,
            "night": 0
        }
        target.db.brief_desc = None
        target.db.weather_data = {}
        
        # Force an update
        target.update_description()
        
        caller.msg(f"|GForced regeneration of descriptions for {target.key}.|n")

class CmdSay(default_cmds.MuxCommand):
    """
    Speak in the room or to specific people.

    Usage:
      say <message>
      say to <person1>[,person2,person3...] <message>
      say <person> <message>

    Examples:
      say Hello everyone!
      say to Bob Can I get a drink?
      say to Bob,Jane,Tom Hey folks!
      say Gad Hello there!  (same as "say to Gad Hello there!")
    """

    key = "say"
    aliases = ["'"]
    locks = "cmd:all()"
    help_category = "Communication"

    def modify_drunk_speech(self, message, intoxication_level):
        """Modify speech based on intoxication level using AI"""
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        if not OPENROUTER_API_KEY:
            return message

        # Only modify speech if character is noticeably drunk or more
        if intoxication_level <= 1:  # Skip if sober or just tipsy
            return message

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4001",
            "X-Title": "Anchors Edge MUD"
        }

        # Adjust prompt based on intoxication level
        if intoxication_level == 2:
            instructions = (
                "Convert this message to show mild intoxication by adding slight slurs "
                "and occasional word stumbles. Keep the message the same length and meaning. "
                "Don't add extra words or context."
                "Example: 'How's it going?' becomes 'Howsh it goin?'"
            )
        elif intoxication_level == 3:
            instructions = (
                "Convert this message to show moderate intoxication with more pronounced slurring "
                "and word confusion. Keep the message the same length and meaning. "
                "Don't add extra words or context."
                "Example: 'how's it going?'  becomes 'howsh it goinn? *hic*'"
            )
        else:
            instructions = (
                "Convert this message to show heavy intoxication with strong slurring "
                "and word confusion. Keep the message the same length and meaning. "
                "Don't add extra words or context."
                "Example: 'how's it going?' becomes 'howsh et gooinnn?'"
            )

        data = {
            "model": "x-ai/grok-vision-beta",
            "messages": [
                {
                    "role": "user", 
                    "content": (
                        f"Convert exactly: '{message}'|/"
                        f"To drunk speech. {instructions}|/"
                        "Rules:|/"
                        "1. Keep exactly the same length and meaning|/"
                        "2. Don't add any new words or context|/"
                        "3. Only modify pronunciation and spelling|/"
                        "4. Return only the modified text"
                    )
                }
            ],
            "temperature": 0.4,
            "max_tokens": 256
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                drunk_message = response.json()['choices'][0]['message']['content'].strip()
                # Clean up any quotes or extra spaces
                drunk_message = drunk_message.strip("'\"").strip()
                # Add occasional hiccups based on intoxication
                if intoxication_level >= 3 and len(message) > 10:
                    drunk_message = drunk_message.replace(". ", ". *hic* ")
                return drunk_message
        except Exception as e:
            print(f"Error modifying drunk speech: {e}")

        return message  # Return original message if API call fails

    def get_drunk_action_text(self, intoxication_level, is_self=False, message="", has_targets=False):
        """
        Get appropriate action text based on intoxication level and message punctuation.
        
        Args:
            intoxication_level (int): The speaker's intoxication level
            is_self (bool): Whether this is for the speaker's own message
            message (str): The message being spoken, used to determine speech type
            has_targets (bool): Whether there are targets in the message
        """
        # Determine base verb based on message ending
        if message.rstrip().endswith('!'):
            base_verb = "exclaim" if is_self else "exclaims"
            needs_to = has_targets
        elif message.rstrip().endswith('?'):
            base_verb = "ask" if is_self else "asks"
            needs_to = False  # Questions don't need "to"
        else:
            base_verb = "say" if is_self else "says"
            needs_to = has_targets  # Only add "to" if there are targets

        # Add drunk modifiers based on intoxication
        if intoxication_level <= 1:
            verb = base_verb
        elif intoxication_level == 2:
            verb = f"slurringly {base_verb}"
        elif intoxication_level == 3:
            verb = f"drunkenly {base_verb}"
        else:
            verb = f"very drunkenly {base_verb}"

        # Add "to" if needed
        if needs_to:
            verb = f"{verb} to"

        return verb

    def parse_targets_and_message(self, args):
        """Parse input to extract targets and message."""
        # Handle empty input
        if not args:
            return [], ""

        args = args.strip()

        # Handle incomplete "say to" command
        if args.lower() == "to":
            return None, None

        # Handle "say to <target> <message>"
        if args.lower().startswith("to "):
            try:
                _, target_and_message = args.split(" ", 1)
            except ValueError:
                return None, None
        else:
            target_and_message = args

        # Look for the first space that's not part of a comma-separated list
        target_end = -1
        in_target_list = True
        for i, char in enumerate(target_and_message):
            if char == ',':
                continue
            if char == ' ' and (i == 0 or target_and_message[i-1] not in ','):
                # Check if this space is followed by punctuation (like "!")
                if (i + 1 < len(target_and_message) and 
                    target_and_message[i + 1] in '!?.'):
                    continue
                target_end = i
                break

        if target_end != -1:
            target_string = target_and_message[:target_end].strip()
            message = target_and_message[target_end:].strip()
            
            # If we started with "to", verify we got both parts
            if args.lower().startswith("to ") and not message:
                return None, None
                
            # Check if any potential target is too short (less than 2 chars)
            if any(len(t.strip()) < 2 for t in target_string.split(",")):
                return "", target_and_message
                
            # Try to find at least one target
            targets, failed = self.caller.find_targets(target_string, location=self.caller.location, quiet=True)
            if targets:
                return target_string, message
        
        # If no target pattern is matched, treat entire input as message
        return "", args

    def capitalize_first_letter(self, msg):
        """Ensure the first letter of a message is capitalized."""
        if not msg:
            return msg
        return msg[0].upper() + msg[1:]

    def format_speech_messages(self, caller, message, targets=None, action_prefix=""):
        """
        Format speech messages for all observers.
        
        Args:
            caller: The character speaking
            message: The message being spoken
            targets: Optional list of specific targets
            action_prefix: Optional prefix to add to the action (e.g., "loudly")
            
        Returns:
            tuple: (self_message, target_messages, observer_message)
            where target_messages is a dict mapping targets to their messages
        """
        # Get intoxication level and action text
        intoxication_level = caller.get_intoxication_level() if hasattr(caller, 'get_intoxication_level') else 0
        # Pass targets to get_drunk_action_text to help determine if "to" is needed
        action_text_others = self.get_drunk_action_text(intoxication_level, is_self=False, message=message, has_targets=bool(targets))
        action_text_self = self.get_drunk_action_text(intoxication_level, is_self=True, message=message, has_targets=bool(targets))

        # Add any prefix to the action text
        if action_prefix:
            action_text_others = f"{action_prefix} {action_text_others}"
            action_text_self = f"{action_prefix} {action_text_self}"

        # Capitalize and format the message
        message = self.capitalize_first_letter(message)

        # Modify speech if drunk
        if intoxication_level > 1:
            message = self.modify_drunk_speech(message, intoxication_level)
            message = self.capitalize_first_letter(message)

        # Format messages for different observers
        target_messages = {}
        observer_message = None

        if targets:
            # Format target string for speaker
            if len(targets) > 1:
                target_str = f"{', '.join(t.name if (hasattr(caller, 'knows_character') and caller.knows_character(t)) else get_brief_description(t) for t in targets[:-1])} and {targets[-1].name if (hasattr(caller, 'knows_character') and caller.knows_character(targets[-1])) else get_brief_description(targets[-1])}"
            else:
                target_str = targets[0].name if (hasattr(caller, 'knows_character') and caller.knows_character(targets[0])) else get_brief_description(targets[0])

            # Message for the speaker
            connector = " " if action_text_self.endswith(" to") else " "
            self_message = format_sentence(f'You {action_text_self}{connector}{target_str}, "{format_sentence(message)}"', no_period=True)

            # Format messages for targets
            for target in targets:
                other_targets = [t for t in targets if t != target]
                if other_targets:
                    if len(other_targets) > 1:
                        others_str = f", {', '.join(t.name if (hasattr(target, 'knows_character') and target.knows_character(t)) else get_brief_description(t) for t in other_targets[:-1])} and {other_targets[-1].name if (hasattr(target, 'knows_character') and target.knows_character(other_targets[-1])) else get_brief_description(other_targets[-1])}"
                    else:
                        others_str = f" and {other_targets[0].name if (hasattr(target, 'knows_character') and target.knows_character(other_targets[0])) else get_brief_description(other_targets[0])}"
                else:
                    others_str = ""

                # Get caller display name based on whether target knows them
                caller_display = caller.get_display_name(looker=target)

                connector = " " if action_text_others.endswith(" to") else " "
                target_messages[target] = format_sentence(f'{caller_display} {action_text_others}{connector}you{others_str}, "{format_sentence(message)}"', no_period=True)

            # Message for other observers
            # Use get_display_name to handle knowledge level for observers
            # This will be formatted per-observer in msg_contents
            observer_message = lambda observer: format_sentence(f'{caller.get_display_name(looker=observer)} {action_text_others}{connector}{target_str}, "{format_sentence(message)}"', no_period=True)

        else:
            # Regular untargeted speech
            self_message = format_sentence(f'You {action_text_self}, "{format_sentence(message)}"', no_period=True)
            # Use get_display_name to handle knowledge level for observers
            # This will be formatted per-observer in msg_contents
            observer_message = lambda observer: format_sentence(f'{caller.get_display_name(looker=observer)} {action_text_others}, "{format_sentence(message)}"', no_period=True)

        return self_message, target_messages, observer_message

    def func(self):
        """Implements the command"""
        caller = self.caller

        if not self.args:
            caller.msg("Say what?")
            return

        # Parse the input
        target_string, message = self.parse_targets_and_message(self.args)
        
        # Handle incomplete or invalid "say to" command
        if target_string is None:
            caller.msg("Usage: say <message> OR say to <person> <message>")
            return

        # Get targets if specified
        targets = None
        if target_string:
            targets, failed_targets = caller.find_targets(target_string)
            if failed_targets:
                if len(failed_targets) == len(target_string.split(",")):
                    caller.msg(f"Could not find anyone matching: {', '.join(failed_targets)}")
                    return
                else:
                    caller.msg(f"Warning: Could not find: {', '.join(failed_targets)}")
            if not targets:
                return

        # Format all messages
        self_message, target_messages, observer_message = self.format_speech_messages(caller, message, targets)

        # Send messages
        caller.msg(self_message)
        
        # Send messages to targets
        for target, msg in target_messages.items():
            target.msg(msg)

        # Send message to other observers
        if observer_message:
            exclude = [caller] + (list(target_messages.keys()) if target_messages else [])
            # For each observer, format the message with their specific view
            for observer in caller.location.contents:
                if observer not in exclude and hasattr(observer, 'msg'):
                    observer.msg(observer_message(observer))

class CmdLsay(CmdSay):
    """
    Speak loudly in the room or to specific people.

    Usage:
      lsay <message>
      lsay to <person1>[,person2,person3...] <message>
      lsay <person> <message>

    Something in between say and yell. You might need it for 
    subtle effect maybe. It simply shows you saying something 
    loudly.

    Example:  
      lsay Excuse me, but I do not like steak.
      You say loudly, "Excuse me, but I do not like steak."
    """

    key = "lsay"
    aliases = ['"']
    locks = "cmd:all()"
    help_category = "Communication"

    def func(self):
        """Implements the command"""
        caller = self.caller

        if not self.args:
            caller.msg("Say what?")
            return

        # Parse the input
        target_string, message = self.parse_targets_and_message(self.args)
        
        # Handle incomplete or invalid "say to" command
        if target_string is None:
            caller.msg("Usage: lsay <message> OR lsay to <person> <message>")
            return

        # Get targets if specified
        targets = None
        if target_string:
            targets, failed_targets = caller.find_targets(target_string)
            if failed_targets:
                if len(failed_targets) == len(target_string.split(",")):
                    caller.msg(f"Could not find anyone matching: {', '.join(failed_targets)}")
                    return
                else:
                    caller.msg(f"Warning: Could not find: {', '.join(failed_targets)}")
            if not targets:
                return

        # Format all messages with "loudly" prefix
        self_message, target_messages, observer_message = self.format_speech_messages(
            caller, message, targets, action_prefix="loudly"
        )

        # Send messages
        caller.msg(self_message)
        
        # Send messages to targets
        for target, msg in target_messages.items():
            target.msg(msg)

        # Send message to other observers
        if observer_message:
            exclude = [caller] + (list(target_messages.keys()) if target_messages else [])
            caller.location.msg_contents(observer_message, exclude=exclude)

        # Handle NPC responses
        if targets:
            for target in targets:
                if hasattr(target, 'db') and hasattr(target.db, 'is_npc') and target.db.is_npc:
                    response = target.handle_conversation(caller, message)
                    caller.location.msg_contents(format_sentence(response.strip(), no_period=True))

class CmdInventory(default_cmds.CmdInventory):
    """
    view inventory
    
    Usage:
      inventory
      inv
      i
    
    Shows your inventory and current currency.
    """
    
    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    
    def get_health_color(self, health):
        """Get color code based on health percentage"""
        if health <= 0:
            return "|r"  # Red for empty
        elif health <= 2:
            return "|505"  # Dark red for very low
        elif health <= 5:
            return "|y"  # Yellow for half
        elif health <= 8:
            return "|g"  # Green for good
        else:
            return "|G"  # Bright green for full/nearly full
    
    def func(self):
        """Handle the inventory display"""
        items = self.caller.contents
        if not items:
            string = "You are carrying nothing."
        else:
            table = self.styled_table(border="header")
            for item in items:
                # Get health if it's a consumable item
                health = None
                if hasattr(item, 'db'):
                    health = item.db.health if hasattr(item.db, 'health') else None
                
                if health is not None:
                    # Add health bar for consumable items
                    health_color = self.get_health_color(health)
                    table.add_row(
                        f"{item.name}",
                        f"{health_color}({health}/10)|n",
                        item.db.desc if item.db.desc else ""
                    )
                else:
                    # Regular items without health
                    table.add_row(
                        f"{item.name}",
                        "",
                        item.db.desc if item.db.desc else ""
                    )
            string = f"|wYou are carrying:|n|/{table}"
        
        self.caller.msg(string)
        
        # Add currency information with color coding
        currency = self.caller.get_currency()
        if currency:
            self.caller.msg(
                f"|/|Y|hPurse|h|n|/"
                f"-----------------------------------|/"
                f"|Y|hG|h|n {currency['gold']}    "
                f"|W|hS|h|n {currency['silver']}    "
                f"|r|hC|h|n {currency['copper']}    "
            )

class GiveCommand(default_cmds.MuxCommand):
    """
    Give something to someone
    
    Usage:
      give <item> to <target>
      give <amount> <item/currency> to <target>
      
    Examples:
      give sword to Bob
      give 5 swords to Bob
      give 5 gold to Willow
      give 10 silver to Tom
      give 20 copper to merchant
    
    You can give multiple items or currency.
    """
    
    key = "give"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Handle the giving"""
        caller = self.caller
        
        if not self.args:
            caller.msg("Give what to whom?")
            return
            
        if "to" not in self.args.lower():
            caller.msg("Usage: give <item/amount currency> to <person>")
            return
            
        # Split into gift and target
        gift, target_name = self.args.lower().split(" to ", 1)
        gift = gift.strip()
        target_name = target_name.strip()
        
        # Find the target
        target = caller.search(target_name, location=caller.location)
        if not target:
            return
            
        # Check if this is a quantity transaction
        words = gift.split()
        if len(words) >= 2 and words[0].isdigit():
            amount = int(words[0])
            item_name = " ".join(words[1:])  # Join the rest as item name
            
            # Check if it's currency
            if item_name.rstrip('s') in ['gold', 'silver', 'copper']:
                currency_type = item_name.rstrip('s')
                
                # Convert to copper for comparison
                caller_currency = caller.get_currency()
                total_copper_has = (
                    (caller_currency["gold"] * 100) + 
                    (caller_currency["silver"] * 10) + 
                    caller_currency["copper"]
                )
                
                # Calculate needed copper based on currency type
                copper_multiplier = {"gold": 100, "silver": 10, "copper": 1}
                total_copper_needed = amount * copper_multiplier[currency_type]
                
                if total_copper_has < total_copper_needed:
                    caller.msg(f"You don't have enough {currency_type}.")
                    return
                
                # Transfer the currency
                if caller.remove_currency(**{currency_type: amount}):
                    target.add_currency(**{currency_type: amount})
                    
                    # Notify everyone
                    caller.msg(f"You give {amount} {currency_type} to {target.name}.")
                    
                    # If target is an NPC, handle currency reception
                    if hasattr(target, 'at_receive_currency'):
                        target.at_receive_currency(amount, currency_type, caller)
                    else:
                        target.msg(f"{caller.name} gives you {amount} {currency_type}.")
                        caller.location.msg_contents(
                            f"{caller.name} gives {amount} {currency_type} to {target.name}.",
                            exclude=[caller, target]
                        )
                else:
                    caller.msg("Something went wrong with the transaction.")
                    
            else:
                # Handle multiple items
                # First, try to find the items
                items = []
                base_item_name = item_name.rstrip('s')  # Remove potential plural
                for obj in caller.contents:
                    if obj.key.lower() == base_item_name:
                        items.append(obj)
                        if len(items) == amount:
                            break
                
                if not items:
                    caller.msg(f"You don't have any {base_item_name}.")
                    return
                    
                if len(items) < amount:
                    caller.msg(f"You only have {len(items)} {base_item_name}{'s' if len(items) != 1 else ''}.")
                    return
                
                # Give the items
                for obj in items[:amount]:
                    obj.move_to(target, quiet=True)
                
                # Notify everyone
                s = 's' if amount != 1 else ''
                caller.msg(f"You give {amount} {base_item_name}{s} to {target.name}.")
                target.msg(f"{caller.name} gives you {amount} {base_item_name}{s}.")
                caller.location.msg_contents(
                    f"{caller.name} gives {amount} {base_item_name}{s} to {target.name}.",
                    exclude=[caller, target]
                )
                
        else:
            # Handle single item giving
            obj = caller.search(gift, location=caller)
            if not obj:
                return
                
            if obj.location != caller:
                caller.msg("You don't have that.")
                return
                
            # Give the item
            obj.move_to(target, quiet=True)
            caller.msg(f"You give {obj.name} to {target.name}.")
            target.msg(f"{caller.name} gives you {obj.name}.")
            caller.location.msg_contents(
                f"{caller.name} gives {obj.name} to {target.name}.",
                exclude=[caller, target]
            )

class CmdEat(default_cmds.MuxCommand):
    """
    Eat some food
    
    Usage:
      eat <food>
    """
    
    key = "eat"
    locks = "cmd:all()"
    
    def func(self):
        """Handle eating"""
        caller = self.caller
        
        if not self.args:
            caller.msg("Eat what?")
            return
            
        obj = caller.search(self.args.strip(), location=caller)
        if not obj:
            return
            
        if not hasattr(obj, 'db') or not obj.db.is_food:
            caller.msg("You can't eat that!")
            return
            
        success, msg = obj.eat(caller)
        caller.msg(msg)
        
        # Show room message only if we pass the rate limit
        if success and caller.can_show_consume_message():
            # Get random eating message
            messages = [
                f"{caller.name} takes a bite of {obj.name}.",
                f"{caller.name} munches on {obj.name}.",
                f"{caller.name} enjoys some {obj.name}.",
                f"{caller.name} eats some {obj.name}."
            ]
            room_msg = random.choice(messages)
            caller.location.msg_contents(room_msg, exclude=[caller])

class CmdDrink(default_cmds.MuxCommand):
    """
    Drink something
    
    Usage:
      drink <beverage>
    """
    
    key = "drink"
    locks = "cmd:all()"
    
    def func(self):
        """Handle drinking"""
        caller = self.caller
        
        if not self.args:
            caller.msg("Drink what?")
            return
            
        obj = caller.search(self.args.strip(), location=caller)
        if not obj:
            return
            
        if not hasattr(obj, 'db') or not obj.db.is_drink:
            caller.msg("You can't drink that!")
            return
            
        success, msg = obj.drink(caller)
        caller.msg(msg)
        
        # Show room message only if we pass the rate limit
        if success and caller.can_show_consume_message():
            # Get random drinking message
            messages = [
                f"{caller.name} takes a drink from {obj.name}.",
                f"{caller.name} sips from {obj.name}.",
                f"{caller.name} drinks from {obj.name}.",
                f"{caller.name} enjoys a drink of {obj.name}."
            ]
            room_msg = random.choice(messages)
            caller.location.msg_contents(room_msg, exclude=[caller])

class CmdChug(default_cmds.MuxCommand):
    """
    Quickly drink the entire contents of a drink container

    Usage:
        chug <drink>

    Rapidly consumes the entire drink in one go. This might have 
    stronger effects than sipping it slowly!
    """

    key = "chug"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("What do you want to chug?")
            return

        drink = self.caller.search(self.args, location=self.caller)
        if not drink:
            return

        # Check if it's actually a drink
        if not hasattr(drink, 'db') or not drink.db.is_drink:
            self.caller.msg(f"You can't chug {drink.name} - it's not a drink!")
            return

        if not hasattr(drink.db, 'health') or drink.db.health <= 0:
            self.caller.msg(f"The {drink.name} is empty!")
            return

        # Consume all remaining charges at once
        health = drink.db.health
        alcohol_content = drink.db.alcohol_content if hasattr(drink.db, 'alcohol_content') else 0
        
        # Apply effects (multiply by charges for "chugging" effect)
        if alcohol_content:
            # Drinking quickly hits harder - multiply effect by 1.5
            total_alcohol = (alcohol_content * health) * 1.5
            self.caller.db.intoxication = (self.caller.db.intoxication or 0) + total_alcohol

        # Empty the container
        drink.db.health = 0

        # Messages - always show chug messages regardless of rate limit
        # since chugging is a more significant action
        self.caller.msg(f"You chug the entire {drink.name} in one go!")
        
        messages = [
            f"{self.caller.name} chugs an entire {drink.name}!",
            f"{self.caller.name} downs {drink.name} in one go!",
            f"{self.caller.name} rapidly drinks the entire {drink.name}!",
            f"{self.caller.name} gulps down the whole {drink.name}!"
        ]
        room_msg = random.choice(messages)
        self.caller.location.msg_contents(room_msg, exclude=self.caller)

        # If they're getting drunk, add some flavor
        if alcohol_content:
            if total_alcohol > 10:
                self.caller.msg("Woah! That hits you like a truck!")
            elif total_alcohol > 5:
                self.caller.msg("You feel quite a strong buzz from that!")

class SmellCommand(default_cmds.MuxCommand):
    """
    Smell your surroundings or a specific object/person

    Usage:
      smell [<obj>]

    If no object is specified, smells the current room.
    """
    key = "smell"
    aliases = ["sniff"]
    locks = "cmd:all()"

    def func(self):
        if not self.args:
            # Smell the room
            location = self.caller.location
            if not location:
                self.caller.msg("You have no location to smell!")
                return
            
            smell_desc = location.get_smell_desc() if hasattr(location, 'get_smell_desc') else None
            if smell_desc:
                self.caller.msg(smell_desc)
            else:
                self.caller.msg(f"You smell nothing special about {location.name}.")
            return

        # Smell a specific object
        obj = self.caller.search(self.args.strip())
        if not obj:
            return

        smell_desc = obj.get_smell_desc() if hasattr(obj, 'get_smell_desc') else None
        if smell_desc:
            self.caller.msg(smell_desc)
        else:
            self.caller.msg(f"You smell nothing special about {obj.name}.")

class TasteCommand(default_cmds.MuxCommand):
    """
    Taste an object

    Usage:
      taste <obj>

    Attempts to taste the specified object.
    """
    key = "taste"
    aliases = ["lick"]
    locks = "cmd:all()"

    def func(self):
        if not self.args:
            self.caller.msg("What do you want to taste?")
            return

        obj = self.caller.search(self.args.strip())
        if not obj:
            return

        taste_desc = obj.get_taste_desc() if hasattr(obj, 'get_taste_desc') else None
        if taste_desc:
            self.caller.msg(taste_desc)
        else:
            self.caller.msg(f"You can't taste {obj.name}.")

class CmdIdentify(Command):
    """
    Scan the room to identify objects.
    
    Usage:
      identify
      id
    
    This command will list all visible objects in your current location.
    """
    key = "identify"
    aliases = ["id"]
    locks = "cmd:all()"
    
    def func(self):
        """Execute the identify command."""
        location = self.caller.location
        if not location:
            self.caller.msg("You have no location to scan!")
            return
            
        # Get all objects in the room
        contents = [obj for obj in location.contents if obj != self.caller]
        if not contents:
            self.caller.msg("You don't see any distinct objects here.")
            return
            
        # Group objects by their key
        objects_by_type = {}
        for obj in contents:
            if not obj.destination:  # Skip exits
                key = obj.key
                if key in objects_by_type:
                    objects_by_type[key].append(obj)
                else:
                    objects_by_type[key] = [obj]
        
        if not objects_by_type:
            self.caller.msg("You don't see any distinct objects here.")
            return
            
        # Format the output
        self.caller.msg("You scan the room and identify the following:")
        for key, objs in objects_by_type.items():
            count = len(objs)
            if count > 1:
                self.caller.msg(f"- {key} (x{count})")
            else:
                self.caller.msg(f"- {key}")

class CmdWho(Command):
    """
    List who is currently online.
    """
    key = "who"
    locks = "cmd:all()"

    def func(self):
        # Get all connected accounts using the correct field name
        connected_accounts = AccountDB.objects.filter(db_is_connected=True)
        
        # Get their characters
        characters = ObjectDB.objects.filter(
            db_account__in=connected_accounts
        ).exclude(db_account__isnull=True)

        if not characters:
            self.caller.msg("No one is connected.")
            return

        # Create the who list
        who_list = []
        # Sort characters alphabetically, putting self first
        sorted_chars = sorted(
            [c for c in characters if c != self.caller],
            key=lambda x: x.name.lower()
        )
        if self.caller in characters:
            sorted_chars.insert(0, self.caller)
            
        for char in sorted_chars:
            # Get name and brief description
            if self.caller == char:
                # Looking at self - use full name
                char_name = f"|c{char.name}|n, {get_brief_description(char, include_height=False)}"
            else:
                # For others, show name and brief description
                char_name = f"{char.name}, {get_brief_description(char, include_height=False)}"
                
            who_list.append(char_name)

        # Format and send the message
        if len(who_list) == 1:
            msg = "One character is connected:\n"
        else:
            msg = f"{len(who_list)} characters are connected:\n"
            
        msg += "\n".join(f"  {name}" for name in who_list)
        self.caller.msg(msg)

class CmdLook(default_cmds.CmdLook):
    """
    look at location or object

    Usage:
      look
      look <obj>
      look *<account>
      l
    """
    def func(self):
        """Handle the looking."""
        caller = self.caller
        
        logger.log_info(f"Look command executed by {caller.name}")
        
        # Handle basic cases
        if not self.args:
            super().func()
            return
            
        search_term = self.args.lower().strip()
        
        # Handle special terms first
        if search_term in ['here', 'room']:
            super().func()
            return
            
        if search_term in ['self', 'me']:
            self.msg(caller.at_look(caller))
            return
        
        # Handle looking at exits
        if search_term in ['exits', 'exit', 'out']:
            exits = [obj for obj in caller.location.contents if obj.destination]
            if not exits:
                self.msg("You don't see any obvious exits.")
                return
                
            # Display exits
            self.msg("Available exits:")
            for exit in exits:
                self.msg(f"- {exit.name} leads to {exit.destination.name}")
            return
            
        # Don't try to look at exit directions - they're for movement
        exits = caller.location.exits
        exit_aliases = []
        for exit in exits:
            exit_aliases.extend([alias.lower() for alias in exit.aliases.all()])
            
        if search_term in exit_aliases or any(search_term == exit.key.lower() for exit in exits):
            self.msg("That's a direction you can move in, not something you can look at.")
            return

        # Get candidates for looking (including self but excluding exits)
        candidates = [obj for obj in caller.location.contents if not obj.destination]
        
        # Get descriptions for matching
        matches = []
        for obj in candidates:
            if hasattr(obj, 'get_display_name'):
                full_desc = obj.get_display_name(caller).lower()
            else:
                full_desc = obj.name.lower()
            
            # Direct substring match gets highest priority
            if search_term in full_desc or search_term in obj.key.lower():
                matches.append((obj, 1.0))
            else:
                # Try fuzzy matching without spaces for abbreviations
                desc_no_spaces = full_desc.replace(" ", "")
                key_no_spaces = obj.key.lower().replace(" ", "")
                search_no_spaces = search_term.replace(" ", "")
                
                # Try matching against both description and key
                desc_ratio = SequenceMatcher(None, search_no_spaces, desc_no_spaces).ratio()
                key_ratio = SequenceMatcher(None, search_no_spaces, key_no_spaces).ratio()
                
                # Use the better match
                ratio = max(desc_ratio, key_ratio)
                if ratio > 0.6:  # Threshold for fuzzy matches
                    matches.append((obj, ratio))
            
        logger.log_info(f"Matches for '{search_term}': {[obj.name for obj, ratio in matches]}")
        
        # Sort matches by ratio and extract just the objects
        matches.sort(key=lambda x: x[1], reverse=True)
        matches = [obj for obj, ratio in matches]
        
        if len(matches) == 1:
            # If we have exactly one match, use it
            self.args = matches[0].key
            super().func()
            return
        elif len(matches) > 1:
            # If we have multiple matches, list them
            self.msg("Multiple matches found:")
            for obj in matches:
                if hasattr(obj, 'get_display_name'):
                    self.msg(f"- {obj.get_display_name(caller)}")
                else:
                    self.msg(f"- {obj.name}")
            return
                
        self.msg(f"You don't see anything matching '{search_term}' here.")
        
class CmdWhisper(default_cmds.MuxCommand):
    """
    Whisper a message to a person.

    Usage:
      whisper <person> <message>
      whisper to <person> <message>

    Examples:
      whisper gad ya like jazz
      You whisper to gad, "ya like jazz?"

      whisper to gad ya like jazz?
      You whisper to gad, "Ya like jazz?"
    
    Whispering is different from the say command 
    in that others in the room won't be able to hear 
    you. It is different than the tell command because 
    the person you whisper to must be in the same room 
    as you.
    """
    key = "whisper"
    locks = "cmd:all()"
    help_category = "Communication"

    def find_target(self, caller, search_term):
        """
        Find target based on name or description using fuzzy matching.
        Returns a list of potential matches.
        """
        matches = []
        search_term = search_term.lower()
        
        # Get all characters in the room
        for obj in caller.location.contents:
            if not hasattr(obj, 'is_typeclass') or not obj.is_typeclass('typeclasses.characters.Character'):
                continue
                
            # Skip self as a target
            if obj == caller:
                continue
                
            # If caller knows the character, check their name with fuzzy matching
            if hasattr(caller, 'knows_character') and caller.knows_character(obj):
                name = obj.name.lower()
                # Direct substring match gets highest priority
                if search_term in name:
                    matches.append((obj, 1.0))
                else:
                    # Try fuzzy matching without spaces for abbreviations
                    name_no_spaces = name.replace(" ", "")
                    search_no_spaces = search_term.replace(" ", "")
                    ratio = SequenceMatcher(None, search_no_spaces, name_no_spaces).ratio()
                    if ratio > 0.6:  # Threshold for fuzzy matches
                        matches.append((obj, ratio))
            # If caller doesn't know them, check their description with fuzzy matching
            else:
                brief_desc = get_brief_description(obj).lower()
                # Direct substring match gets highest priority
                if search_term in brief_desc:
                    matches.append((obj, 1.0))
                else:
                    # Try fuzzy matching without spaces
                    desc_no_spaces = brief_desc.replace(" ", "")
                    search_no_spaces = search_term.replace(" ", "")
                    ratio = SequenceMatcher(None, search_no_spaces, desc_no_spaces).ratio()
                    if ratio > 0.6:  # Threshold for fuzzy matches
                        matches.append((obj, ratio))
        
        # Sort matches by ratio (highest first) and return just the objects
        return [obj for obj, ratio in sorted(matches, key=lambda x: x[1], reverse=True)]

    def func(self):
        """Handle whispering"""
        caller = self.caller

        if not self.args:
            caller.msg("Usage: whisper <person> <message> OR whisper to <person> <message>")
            return

        # Parse the input to get target and message
        args = self.args.strip()
        if args.lower().startswith("to "):
            args = args[3:]  # Remove "to " prefix

        try:
            target_name, message = args.split(" ", 1)
        except ValueError:
            caller.msg("Usage: whisper <person> <message> OR whisper to <person> <message>")
            return

        # Check if trying to whisper to self
        if target_name.lower() in ["me", "self", "myself"] or (
            hasattr(caller, 'name') and target_name.lower() == caller.name.lower()
        ):
            caller.msg("You can't whisper to yourself!")
            return

        # Find potential targets
        matches = self.find_target(caller, target_name)
        
        if not matches:
            caller.msg(f"Could not find anyone matching '{target_name}' here.")
            return
            
        if len(matches) > 1:
            # List the matches with appropriate descriptions
            caller.msg("Multiple matches found. Please be more specific:")
            for match in matches:
                if hasattr(caller, 'knows_character') and caller.knows_character(match):
                    caller.msg(f"- {match.name}")
                else:
                    caller.msg(f"- {get_brief_description(match)}")
            return

        target = matches[0]

        # Get knowledge levels between characters
        caller_knows_target = hasattr(caller, 'knows_character') and caller.knows_character(target)
        target_knows_caller = hasattr(target, 'knows_character') and target.knows_character(caller)

        # Get appropriate display names based on knowledge
        target_display = target.name if caller_knows_target else get_brief_description(target)
        caller_display = caller.name if target_knows_caller else get_brief_description(caller)

        # Format and send messages
        caller.msg(f'You whisper to {target_display}, "{message}"')
        target.msg(f'{caller_display} whispers to you, "{message}"')

        # Show a message to others in the room that whispering is happening
        # but they can't hear what's being said
        for obj in caller.location.contents:
            if obj != caller and obj != target and hasattr(obj, 'msg') and hasattr(obj, 'is_typeclass') and obj.is_typeclass('typeclasses.characters.Character'):
                observer_sees_caller = hasattr(obj, 'knows_character') and obj.knows_character(caller)
                observer_sees_target = hasattr(obj, 'knows_character') and obj.knows_character(target)
                
                # Get appropriate names/descriptions based on observer's knowledge
                caller_name = caller.name if observer_sees_caller else get_brief_description(caller)
                target_name = target.name if observer_sees_target else get_brief_description(target)
                
                # Randomly choose a message format for variety
                import random
                messages = [
                    f"{caller_name} whispers something to {target_name}.",
                    f"{caller_name} leans in close to whisper to {target_name}.",
                    f"You notice {caller_name} whispering to {target_name}.",
                    f"{caller_name} quietly whispers something to {target_name}."
                ]
                obj.msg(random.choice(messages))

class CmdHeight(Command):
    """
    Shows height ranges for all races.

    Usage:
      height

    This command displays a table of height ranges for all races,
    showing the minimum and maximum heights for each gender and subrace.
    
    Height descriptions are relative to each race's range:
    - Very Short: Bottom 25% of race's height range
    - Short: 25-40% of race's height range  
    - Average: 40-60% of race's height range
    - Tall: 60-75% of race's height range
    - Very Tall: Top 25% of race's height range
    """
    key = "height"
    locks = "cmd:all()"

    def func(self):
        """Execute the height command."""
        from evennia.utils.evtable import EvTable
        from django.conf import settings

        # Create table headers
        table = EvTable(
            "|wRace/Subrace|n",
            "|wHeight Range (Male/Female)|n",
            table=None,
            border="table",
            pad_width=1
        )

        # Process each race and store entries
        entries = []
        for race, height_data in sorted(settings.RACE_HEIGHT_RANGES.items()):
            # Handle races with subraces
            if isinstance(height_data, dict) and any(subrace in ["normal", "hill", "wood", "high"] for subrace in height_data):
                for subrace, gender_data in sorted(height_data.items()):
                    race_name = f"{race} ({subrace.capitalize()})"
                    if 'male' in gender_data and 'female' in gender_data:
                        male = gender_data['male']
                        female = gender_data['female']
                        male_min = f"{male['min'] // 12}'{male['min'] % 12}"
                        male_max = f"{male['max'] // 12}'{male['max'] % 12}"
                        female_min = f"{female['min'] // 12}'{female['min'] % 12}"
                        female_max = f"{female['max'] // 12}'{female['max'] % 12}"
                        height_range = f"{male_min} ({female_min}) - {male_max} ({female_max})"
                        entries.append((race_name, height_range))
            else:
                # Handle races without subraces
                if 'male' in height_data and 'female' in height_data:
                    male = height_data['male']
                    female = height_data['female']
                    male_min = f"{male['min'] // 12}'{male['min'] % 12}"
                    male_max = f"{male['max'] // 12}'{male['max'] % 12}"
                    female_min = f"{female['min'] // 12}'{female['min'] % 12}"
                    female_max = f"{female['max'] // 12}'{female['max'] % 12}"
                    height_range = f"{male_min} ({female_min}) - {male_max} ({female_max})"
                    entries.append((race, height_range))

        # Add entries to table one per row
        for entry in sorted(entries):
            table.add_row(*entry)

        # Display the table
        self.msg("|c=== Race Height Ranges ===|n")
        self.msg("|w(Heights shown as: Male (Female))|n")
        self.msg(table)
        
        # Show height category ranges
        self.msg("\n|wHeight Categories:|n")
        self.msg("Very Short: Bottom 25% of race's height range")
        self.msg("Short: 25-40% of race's height range")
        self.msg("Average: 40-60% of race's height range")
        self.msg("Tall: 60-75% of race's height range")
        self.msg("Very Tall: Top 25% of race's height range")

class CmdAge(Command):
    """
    Shows age ranges for all races.

    Usage:
      age

    This command displays a table of age ranges for all races,
    showing the minimum and maximum ages for each race and subrace.
    
    Age categories are relative to each race's range:
    - Very Young: Bottom 25% of race's age range
    - Young: 25-40% of race's age range  
    - Adult: 40-60% of race's age range
    - Mature: 60-75% of race's age range
    - Elder: Top 25% of race's age range
    """
    key = "age"
    locks = "cmd:all()"

    def func(self):
        """Execute the age command."""
        from evennia.utils.evtable import EvTable
        from django.conf import settings
        import os
        from pathlib import Path

        try:
            # Try to get age ranges from settings
            age_ranges = settings.RACE_AGE_RANGES
        except AttributeError:
            # If not in settings, try to load directly from file
            try:
                game_dir = settings.GAME_DIR
                data_path = Path(game_dir) / "data" / "descriptions" / "race_ages.json"
                with open(data_path, 'r') as f:
                    import json
                    age_ranges = json.load(f)
            except Exception as e:
                self.msg("Error: Could not load race age ranges. Please notify an admin.")
                self.msg(f"Technical details: {str(e)}")
                return

        # Create table headers
        table = EvTable(
            "|wRace/Subrace|n",
            "|wAge Range|n",
            "|wLife Expectancy|n",
            table=None,
            border="table",
            pad_width=1
        )

        # Process each race and store entries
        entries = []
        for race, age_data in sorted(age_ranges.items()):
            # Handle races with subraces
            if isinstance(age_data, dict) and any(subrace in ["normal", "halfling", "hill", "wood", "high", "mountain", "half"] for subrace in age_data):
                for subrace, subrace_data in sorted(age_data.items()):
                    race_name = f"{race} ({subrace.capitalize()})"
                    min_age = subrace_data.get('min', 'Unknown')
                    max_age = subrace_data.get('max', 'Unknown')
                    life_expectancy = subrace_data.get('life_expectancy', 'Unknown')
                    entries.append((race_name, f"{min_age}-{max_age}", str(life_expectancy)))
            else:
                # Handle races without subraces
                min_age = age_data.get('min', 'Unknown')
                max_age = age_data.get('max', 'Unknown')
                life_expectancy = age_data.get('life_expectancy', 'Unknown')
                entries.append((race, f"{min_age}-{max_age}", str(life_expectancy)))

        # Add entries to table one per row
        for entry in sorted(entries):
            table.add_row(*entry)

        # Display the table
        self.msg("|c=== Race Age Ranges ===|n")
        self.msg("|wNote: Life expectancy indicates natural lifespan under normal conditions.|n")
        self.msg(table)


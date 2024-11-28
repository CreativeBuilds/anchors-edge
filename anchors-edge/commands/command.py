"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia.commands.command import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.mirror import Mirror
from evennia.commands.default.general import CmdLook
from evennia import default_cmds
import random
import os
import requests
from time import time

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

class SayCommand(default_cmds.MuxCommand):
    """
    Speak in the room or to a specific person

    Usage:
      say <message>
      say to <character> <message>

    Examples:
      say Hello everyone!
      say to Willow Can I get a drink?
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
                        f"Convert exactly: '{message}'\n"
                        f"To drunk speech. {instructions}\n"
                        "Rules:\n"
                        "1. Keep exactly the same length and meaning\n"
                        "2. Don't add any new words or context\n"
                        "3. Only modify pronunciation and spelling\n"
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

    def get_drunk_action_text(self, intoxication_level, is_self=False):
        """Get appropriate action text based on intoxication level"""
        if intoxication_level <= 1:
            return "say" if is_self else "says"
        elif intoxication_level == 2:
            return "slur" if is_self else "slurs"
        elif intoxication_level == 3:
            return "drunkenly say" if is_self else "drunkenly says"
        else:
            return "very drunkenly slur" if is_self else "very drunkenly slurs"

    def func(self):
        """Implements the command"""
        caller = self.caller

        if not self.args:
            caller.msg("Say what?")
            return

        # Get intoxication level
        intoxication_level = caller.get_intoxication_level() if hasattr(caller, 'get_intoxication_level') else 0
        action_text_others = self.get_drunk_action_text(intoxication_level, is_self=False)
        action_text_self = self.get_drunk_action_text(intoxication_level, is_self=True)

        # Check if this is a targeted message
        if self.args.lower().startswith("to "):
            # Remove the "to " prefix and split into target and message
            remaining = self.args[3:].strip()
            try:
                target_name, message = remaining.split(" ", 1)
            except ValueError:
                caller.msg("What do you want to say to them?")
                return

            # Look for target in the same location
            target = caller.search(target_name, location=caller.location)
            if not target:
                return

            # Modify speech if drunk
            if intoxication_level > 1:
                message = self.modify_drunk_speech(message, intoxication_level)

            # Send the targeted message with drunk action text
            room_message = f'{caller.name} {action_text_others} to {target.name}, "{message}"'
            caller.location.msg_contents(room_message, exclude=[caller])
            caller.msg(f'You {action_text_self} to {target.name}, "{message}"')
            
            # If target is an NPC, handle conversation
            if hasattr(target, 'db') and hasattr(target.db, 'is_npc') and target.db.is_npc:
                response = target.handle_conversation(caller, message)
                # Send response to everyone in the room
                caller.location.msg_contents(response.strip())

        else:
            # Regular say command
            message = self.args
            
            # Modify speech if drunk
            if intoxication_level > 1:
                message = self.modify_drunk_speech(message, intoxication_level)

            # Use drunk action text in both messages
            room_message = f'{caller.name} {action_text_others}, "{message}"'
            caller.location.msg_contents(room_message, exclude=[caller])
            caller.msg(f'You {action_text_self}, "{message}"')

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
            string = f"|wYou are carrying:|n\n{table}"
        
        self.caller.msg(string)
        
        # Add currency information with color coding
        currency = self.caller.get_currency()
        if currency:
            self.caller.msg(
                f"\n|Y|hPurse|h|n\n"
                f"-----------------------------------\n"
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
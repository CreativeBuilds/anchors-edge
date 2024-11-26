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
        return "\n|yThey appear slightly tipsy.|n"
    elif intoxication <= INTOX_DRUNK:
        return "\n|yThey are noticeably drunk.|n"
    elif intoxication <= INTOX_VERY_DRUNK:
        return "\n|rThey are very drunk and unsteady on their feet.|n"
    else:
        return "\n|RThey are completely intoxicated and can barely stand.|n"

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
        
        # Initialize intoxication system
        self.db.intoxication = 0    # Current intoxication level
        self.db.max_intoxication = INTOX_PASS_OUT  # Pass out at this level
        
        # Start the sobriety ticker (checks every minute)
        from evennia import TICKER_HANDLER
        TICKER_HANDLER.add(60, self.process_sobriety)
        
        # Add rate limiting attributes
        self.db.last_consume_message = 0  # Timestamp of last consume message
        self.db.consume_cooldown = 5  # Seconds between consume messages
        
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

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        Args:
            looker (Object): Object doing the looking.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not looker:
            return ""
        
        # Get the base description
        string = f"{self.key}(#{self.id})\n"
        if self.db.desc:
            string += self.db.desc
        
        # Add intoxication level to the description if the character is drunk
        if hasattr(self, 'db'):
            intoxication = self.db.intoxication if hasattr(self.db, 'intoxication') else 0
            if intoxication:
                string += get_intoxication_description(intoxication)
        
        # Get room context
        room = self.location
        if room and hasattr(room, 'get_time_period') and hasattr(room, 'get_weather'):
            time_period = room.get_time_period()
            weather_data = room.db.weather_data if hasattr(room.db, 'weather_data') else {}
            
            # Extract weather conditions
            conditions = []
            if weather_data.get('weather_code') in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                conditions.append("rain")
            if weather_data.get('wind_speed_10m', 0) > 15:
                conditions.append("windy")
            if weather_data.get('weather_code') in [95, 96, 99]:
                conditions.append("thunderstorm")
            if weather_data.get('cloud_cover', 0) > 80:
                conditions.append("overcast")
            elif weather_data.get('cloud_cover', 0) > 40:
                conditions.append("partly cloudy")
            
            weather_str = " and ".join(conditions) if conditions else "clear"
            
            # Use OpenRouter to get dynamic description
            if OPENROUTER_API_KEY:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:4001",
                    "X-Title": f"A.E. {looker.key} Character Look"
                }
                
                data = {
                    "model": "x-ai/grok-vision-beta",
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"Character description: {string}\n\n"
                                f"Current conditions:\n"
                                f"Time: {time_period}\n"
                                f"Weather: {weather_str}\n"
                                f"Temperature: {weather_data.get('apparent_temperature', 'unknown')}°F\n"
                                f"Wind Speed: {weather_data.get('wind_speed_10m', 'unknown')} mph\n\n"
                                "Add a single, poetic sentence describing how these conditions affect "
                                "the character's appearance. Focus on lighting, shadows, and atmospheric effects. "
                                "Consider how the weather and time of day interact with their features.\n\n"
                                "Examples based on conditions:\n"
                                "- Rain: |cRaindrops glisten in her hair like tiny crystals.|n\n"
                                "- Night + Clear: |wMoonlight catches her elven features, giving them an ethereal glow.|n\n"
                                "- Dawn + Windy: |yThe morning breeze gently lifts her hair as dawn's first light touches her face.|n\n"
                                "Keep it short, atmospheric, and focused on the current conditions."
                            )
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 60
                }
                
                try:
                    response = requests.post(url, headers=headers, json=data)
                    if response.status_code == 200:
                        ai_description = response.json()['choices'][0]['message']['content'].strip()
                        string += f"\n{ai_description}"
                except Exception as e:
                    print(f"Error getting dynamic appearance description: {e}")
        
        return string

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
        print(f"\nConversation history between {self.name} and {speaker.key}:")
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
        """
        Parse only the most recent response for pending transactions.
        Returns list of tuples (type, name, cost, intoxication) or None if no transaction pending.
        """
        player_memory = self.db.conversation_memory["per_player"].get(speaker.key)
        if not player_memory or not player_memory["recent_interactions"]:
            return None
            
        # Only check the most recent interaction
        last_interaction = player_memory["recent_interactions"][-1]
        response = last_interaction["response"].lower()
        
        # If this response is about giving items, it's not an offer
        if "accepts the payment and hands you" in response:
            return None
        
        # Look for transaction tags
        import re
        
        # Find all item offers in the response
        offers = []
        drink_matches = re.findall(r"<drink name='([^']+)' cp='(\d+)' intoxication='(\d+)'/>", response)
        food_matches = re.findall(r"<food name='([^']+)' cp='(\d+)'/>", response)
        
        for name, cost, intoxication in drink_matches:
            offers.append(("drink", name, int(cost), int(intoxication)))
        for name, cost in food_matches:
            offers.append(("food", name, int(cost)))
            
        # Also check for plain text mentions of prices
        if not offers:
            # Look for total price mention
            price_matches = re.findall(r"that'll be (\d+) copper", response)
            if price_matches:
                total_price = int(price_matches[0])
                
                # Look for quantity + item mentions
                quantity_item_matches = [
                    (int(m.group(1)), m.group(2))
                    for m in re.finditer(r"(\d+)\s+(ale|beer|wine|mead|bread|meat|stew)s?", response)
                ]
                
                # Also look for single items without quantities
                single_item_matches = [
                    (1, item) for item in ["ale", "beer", "wine", "mead", "bread", "meat", "stew"]
                    if f" {item}" in response and not any(item == m[1] for m in quantity_item_matches)
                ]
                
                # Combine all found items
                all_items = quantity_item_matches + single_item_matches
                
                # Create offers for each item
                for quantity, item in all_items:
                    if item in ["ale", "beer", "wine", "mead"]:
                        # Set appropriate costs and intoxication levels
                        costs = {"ale": 5, "beer": 4, "wine": 10, "mead": 15}
                        intox = {"ale": 3, "beer": 2, "wine": 5, "mead": 7}
                        for _ in range(quantity):
                            offers.append(("drink", item, costs[item], intox[item]))
                    else:
                        # Handle food items
                        costs = {"bread": 1, "meat": 5, "stew": 8}
                        for _ in range(quantity):
                            offers.append(("food", item, costs[item]))
        
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
            f"Recent conversation between {source.name} and {self.name}:\n\n"
        )
        
        for interaction in recent_interactions:
            context += f"{source.name}: {interaction['message']}\n"
            context += f"{self.name}: {interaction['response']}\n"

        context += f"\n{source.name} just gave {amount} {currency_type} to {self.name}.\n"

        # Prepare the prompt
        prompt = (
            f"{context}\n\n"
            "Based on this conversation and payment, what is the customer trying to purchase?\n"
            "Respond using ONLY these formats for items:\n"
            "<drink name='ale' cp='5' intoxication='3'/>\n"
            "<drink name='beer' cp='4' intoxication='2'/>\n"
            "<drink name='wine' cp='10' intoxication='5'/>\n"
            "<drink name='mead' cp='15' intoxication='7'/>\n"
            "<food name='bread' cp='1'/>\n"
            "<food name='meat' cp='5'/>\n"
            "<food name='stew' cp='8'/>\n"
            "\nIf multiple items could match, choose the most likely based on:\n"
            "1. Recent conversation context\n"
            "2. Amount of money given\n"
            "3. Common tavern orders\n"
            "\nRespond with ONLY the item tag, nothing else."
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
        
        # Initialize response variable
        response = None
        
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
                    
                    if len(item_descriptions) == 1:
                        response = f"{self.name} accepts the payment and hands you {item_descriptions[0]}."
                    else:
                        items_list = ", ".join(item_descriptions[:-1]) + f" and {item_descriptions[-1]}"
                        response = f"{self.name} accepts the payment and hands you {items_list}."
                else:
                    # Something went wrong, return the money
                    source.add_currency(**{currency_type: amount})
                    response = f"{self.name} frowns, 'I'm sorry, something seems to be wrong with that order.'"
            else:
                # Wrong amount, return the money
                source.add_currency(**{currency_type: amount})
                response = f"{self.name} hands the coins back, 'For those items I'll need {total_cost} copper pieces.'"
        else:
            # Try to determine what they want to buy from conversation
            purchase_intent = self.parse_conversation_for_purchase(source, amount, currency_type)
            
            if purchase_intent:
                # Calculate total cost of all items
                total_cost = sum(item[2] for item in purchase_intent)  # item[2] is the cost
                
                if total_copper == total_cost:
                    # Create and give all items
                    items_given = []
                    for purchase in purchase_intent:
                        if len(purchase) == 4:  # Drink
                            item_type, item_name, item_cost, intoxication = purchase
                        else:  # Food
                            item_type, item_name, item_cost = purchase
                            intoxication = None
                            
                        item = self.create_ordered_item(item_type, item_name, intoxication)
                        if item:
                            item.move_to(source, quiet=True)
                            items_given.append(item_name)
                    
                    if items_given:
                        if len(items_given) == 1:
                            response = f"{self.name} accepts the payment and hands you a fresh {items_given[0]}."
                        else:
                            items_list = ", ".join(items_given[:-1]) + f" and {items_given[-1]}"
                            response = f"{self.name} accepts the payment and hands you fresh {items_list}."
                    else:
                        # Something went wrong, return the money
                        source.add_currency(**{currency_type: amount})
                        response = f"{self.name} frowns, 'I'm sorry, something seems to be wrong with that order.'"
                else:
                    # Wrong amount, return the money
                    source.add_currency(**{currency_type: amount})
                    response = f"{self.name} hands the coins back, 'For those items I'll need {total_cost} copper pieces.'"
            else:
                # No pending offers or purchase intent found
                source.add_currency(**{currency_type: amount})
                response = f"{self.name} hands the coins back, 'I'm sorry, what would you like to order?'"
        
        # Send the response and remember the interaction
        if response:  # Only send if we have a response
            self.location.msg_contents(response)
            if hasattr(source, 'has_account') and source.has_account:
                self.remember_interaction(
                    source,
                    f"*gives {amount} {currency_type} to {self.key}*",
                    response
                )

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
            
        # Build conversation context
        context = (
            f"You are roleplaying as {self.key}, {self.db.personality}\n"
            f"Conversation style: {self.db.conversation_style}\n"
            f"Knowledge: {self.db.knowledge}\n\n"
            f"Time of day: {time_period}\n"
            f"The room's current state: {room_desc}\n\n"
            "Example responses for specific topics:\n"
        )
        
        # Add example responses
        for triggers, responses in self.db.responses.items():
            trigger_words = [t.strip() for t in triggers.split(',')]
            example_responses = list(responses)  # Convert _SaverList to list
            context += f"When someone mentions {' or '.join(trigger_words)}, you might say:\n"
            for response in example_responses:
                context += f"- {response}\n"
            context += "\n"
            
        context += f"\nIn a conversation with {speaker.key}:\n"
        
        # Add recent conversation history
        for interaction in conversation_history[-3:]:
            context += (
                f"{speaker.key}: {interaction['message']}\n"
                f"{self.key}: {interaction['response']}\n"
            )
            
        # Add current message
        context += f"\n{speaker.key}: {message}\n{self.key}:"
        
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
                        f"{context}\n\n"
                        f"{self.append_to_context()}"
                        "Respond in character with a single short response (max 100 tokens). "
                        "Include basic emotes or actions that fit the current room's state. "
                        "Stay consistent with the character's personality and knowledge. "
                        "Consider the time of day and current room conditions in your response. "
                        "Use the example responses as a guide for tone and style, but create "
                        "a natural response that fits the current conversation flow. "
                        "Make your responses interesting and engaging but short and concise."
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
        """Append additional context to the AI prompt"""
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
        
        weather_descriptions = {
            "rain": [
                "Raindrops glisten in their hair like tiny crystals.",
                "They are slightly damp from the falling rain.",
                "Water droplets trace paths down their form."
            ],
            "windy": [
                "Their hair and clothes flutter in the breeze.",
                "The wind plays with the edges of their garments.",
                "A gusty breeze tousles their appearance."
            ],
            "thunderstorm": [
                "Lightning flashes occasionally illuminate their form.",
                "Thunder and rain create a dramatic backdrop around them.",
                "They stand resolute against the stormy conditions."
            ],
            "overcast": [
                "Diffused light from the cloudy sky softens their features.",
                "The grey light casts them in muted tones.",
                "Overcast conditions blur their edges slightly."
            ],
            "partly cloudy": [
                "Shifting clouds create changing patterns of light around them.",
                "Occasional sunbeams highlight their presence.",
                "They move between patches of sun and shade."
            ],
            "clear": [
                "Clear conditions show them in pristine detail.",
                "Nothing obscures their clear appearance.",
                "They stand in perfect clarity."
            ]
        }
        
        # Extract weather conditions
        conditions = []
        if weather_data.get('weather_code') in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            conditions.append("rain")
        if weather_data.get('wind_speed_10m', 0) > 15:
            conditions.append("windy")
        if weather_data.get('weather_code') in [95, 96, 99]:
            conditions.append("thunderstorm")
        if weather_data.get('cloud_cover', 0) > 80:
            conditions.append("overcast")
        elif weather_data.get('cloud_cover', 0) > 40:
            conditions.append("partly cloudy")
        if not conditions:
            conditions.append("clear")
        
        # Select atmospheric descriptions
        atmospheric_desc = []
        
        # Add time-based description
        if time_period and time_period in time_descriptions:
            atmospheric_desc.append(random.choice(time_descriptions[time_period]))
        
        # Add weather-based description (pick one random weather condition if multiple exist)
        if conditions:
            weather_condition = random.choice(conditions)
            if weather_condition in weather_descriptions:
                atmospheric_desc.append(random.choice(weather_descriptions[weather_condition]))
        
        # Combine descriptions
        final_desc = self.db.base_desc
        if atmospheric_desc:
            final_desc += "\n\n" + " ".join(atmospheric_desc)
        
        self.db.desc = final_desc

class Willow(OpenrouterCharacter):
    """
    The half-elven barmaid NPC with AI-enhanced conversation.
    """
    def at_object_creation(self):
        """Set up Willow's specific attributes and responses"""
        super().at_object_creation()
        
        # Set Willow to get 2 responses from OpenRouter
        self.db.n = 2
        
        # Set description
        self.db.base_desc = (
            "Willow is a graceful half-elven woman with long, slightly curled brunette hair "
            "that cascades down her back. Her elven heritage is evident in her delicately "
            "pointed ears and ethereal features, though her warm human nature shines through "
            "in her expressions. She moves through the tavern with an innate elvish grace, "
            "serving drinks and maintaining a welcoming atmosphere. Her gentle smile and "
            "quick wit make her a favorite among the regular patrons."
        )
        
        # get the room they're in
        room = self.location
        if room:
            self.db.room_desc = room.db.desc
        else:
            self.db.room_desc = "unknown location"
        
        # Set personality for AI context
        self.db.personality = (
            "a friendly and attentive half-elven barmaid. You are warm and welcoming, "
            "with a quick wit and gentle demeanor. Your elven heritage gives you an air of grace, "
            "while your human side makes you approachable and understanding."
        )
        
        self.db.conversation_style = (
            "Speaks warmly and politely, often with a gentle smile. Uses proper grammar but "
            "not overly formal. Sometimes includes small gestures or actions while speaking."
        )
        
        self.db.knowledge = (
            "Expert knowledge of drinks, local gossip, and tavern operations. Familiar with "
            "both human and elven customs. Knows about the local area and its regular visitors."
        )
        
        # Set up default responses (used if AI fails)
        self.db.default_responses = [
            "Willow smiles warmly, 'Welcome to the tavern! Can I get you something to drink?'",
            "Willow nods politely, 'Let me know if you need anything.'",
            "Willow's eyes sparkle with interest, 'Oh? Do tell me more!'",
            "Willow laughs softly, 'That's quite a tale!'",
            "Willow listens attentively while wiping down the bar."
        ]
        
        # Set up example responses with comma-separated trigger words
        self.db.responses = {
            "drink, drinks, thirsty, beverage": [
                "Willow nods, 'We have ale, mead, and wine. What's your pleasure?'",
                "Willow gestures to the bottles behind the bar, 'What can I get you?'"
            ],
            "food, hungry, eat, meal": [
                "Willow smiles, 'Our cook makes an excellent stew, and the bread is fresh.'",
                "Willow nods, 'Hungry? The kitchen's still open.'"
            ],
            "hello, hi, greetings, welcome": [
                "Willow gives a warm smile, 'Hello! Welcome to our humble tavern.'",
                "Willow looks up from wiping the bar, 'Welcome! Make yourself comfortable.'"
            ]
        }
        
        # Add responses for receiving items
        self.db.item_responses = {
            "default": [
                "Willow looks at the item curiously, 'Oh? What's this for?'",
                "Willow accepts the item with a gentle smile, 'How thoughtful of you.'"
            ],
            "coin": [
                "Willow nods appreciatively, 'Thank you for your patronage.'",
                "Willow tucks the coins away behind the bar, 'Much appreciated.'"
            ],
            "food": [
                "Willow accepts the food with a surprised smile, 'How kind! Though I should be the one serving you.'",
                "Willow places the food carefully on the bar, 'That's very thoughtful, thank you.'"
            ],
            "drink": [
                "Willow chuckles softly, 'Usually I'm the one doing the serving!'",
                "Willow accepts the drink with a graceful nod, 'How kind of you to think of me.'"
            ]
        }
        
        # Add responses for receiving currency
        self.db.currency_responses = {
            "copper": [
                "Willow accepts the copper pieces with a nod, 'Thank you. Will you be having a drink?'",
                "Willow tucks the copper away, 'Much appreciated. Can I get you something?'"
            ],
            "silver": [
                "Willow carefully counts the silver, 'Thank you kindly. What can I get for you?'",
                "Willow smiles as she stores the silver, 'Much appreciated. What's your pleasure?'"
            ],
            "gold": [
                "Willow's eyes widen slightly at the gold, 'Most generous! Let me know what you'd like.'",
                "Willow carefully handles the gold pieces, 'Thank you indeed! What can I get for you?'"
            ]
        }
        
        # call the update_desc function to set the initial description
        self.update_desc()
        
    def append_to_context(self):
        """Append additional context to the AI's context of the world"""
        return (
            "Willow is a half-elven barmaid who serves drinks and food to the customers. "
            "The tavern is called the Wyld Boar. "
            "The menu is the following: "
            "Beer (4cp), Wine (10cp), Ale (5cp), Cider (6cp), "
            "Food is available all day, including bread (1cp), meat (5cp), stew (8cp), fruit (2cp), "
            "cheese (3cp), and pie (7cp)."
        )
        
    def append_to_prompt(self):
        """Append additional context to the AI prompt"""
        return (
            "\n\nHOW TO HANDLE PURCHASES\nWhen someone asks for items respond like this with the following example:\n"
            "<drink name='ale' cp='5' intoxication='3'/>\n"
            "<drink name='beer' cp='4' intoxication='2'/>\n"
            "<drink name='wine' cp='10' intoxication='5'/>\n"
            "<drink name='mead' cp='15' intoxication='7'/>\n"
            "<food name='bread' cp='1'/>\n"
            "<food name='meat' cp='5'/>\n"
            "<food name='stew' cp='8'/>\n"
            "<message>Your out loud response to the user here</message>\n\n"
            "This will give a prompt to the user about the purchase that they can then accept or decline."
        )

    def create_ordered_item(self, item_type, item_name, intoxication=None):
        """Create an item based on type and name"""
        from evennia import create_object
        
        if item_type == "drink":
            # Clean up item name
            clean_name = item_name.replace(",", "").strip()
            obj = create_object(
                "typeclasses.items.Drink",
                key=clean_name,
                location=self.location
            )
            # Set drink type which also sets default alcohol content
            obj.set_type(clean_name)
            # Override with specific intoxication if provided
            if intoxication is not None:
                obj.db.alcohol_content = intoxication
            obj.db.desc = f"A fresh {clean_name} from the tavern."
            return obj
            
        elif item_type == "food":
            obj = create_object(
                "typeclasses.items.Food",
                key=item_name,
                location=self.location
            )
            obj.db.food_type = item_name
            obj.db.desc = f"Some fresh {item_name} from the tavern."
            return obj
            
        return None

    def update_desc(self):
        """
        Updates Willow's description based on current room conditions.
        Only adds atmospheric effects at dawn and dusk when weather permits.
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
        
        # Check weather conditions
        cloud_cover = weather_data.get('cloud_cover', 0)
        is_overcast = cloud_cover > 80
        is_raining = weather_data.get('weather_code') in [51, 53, 55, 61, 63, 65, 80, 81, 82]
        is_stormy = weather_data.get('weather_code') in [95, 96, 99]
        
        # Only add atmospheric descriptions if conditions are right
        atmospheric_desc = ""
        if not (is_overcast or is_raining or is_stormy):
            if time_period == "dawn":
                atmospheric_desc = (
                    "\n\nThe soft morning light streams through the windows, "
                    "highlighting her delicate elven features and making her hair shimmer "
                    "with hints of copper and gold."
                )
            elif time_period == "dusk":
                atmospheric_desc = (
                    "\n\nThe last rays of sunset filter through the tavern, "
                    "casting a warm glow that illuminates her graceful form and makes "
                    "her eyes sparkle with ethereal light."
                )
            
        # Combine descriptions
        self.db.desc = self.db.base_desc + (atmospheric_desc if atmospheric_desc else "")


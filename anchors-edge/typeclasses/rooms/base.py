"""
Base room types and templates.
"""

from evennia import DefaultRoom
from django.conf import settings
from datetime import datetime
import pytz
from evennia.scripts.models import ScriptDB
from textwrap import fill, TextWrapper
from utils.text_formatting import format_sentence

class WeatherAwareRoom(DefaultRoom):
    """Base class for rooms that are affected by weather."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.weather_enabled = True
        self.db.weather_modifiers = {
            "sheltered": False,
            "indoor": False,
            "magical": False
        }
        # Tag the room as weather-aware for efficient searching
        self.tags.add("weather_aware", category="room")
        
    def get_current_hour(self):
        """Get the current hour (0-23) in Austin timezone."""
        austin_tz = pytz.timezone('America/Chicago')
        austin_time = datetime.now(austin_tz)
        return austin_time.hour
        
    def get_current_weather(self):
        """Get current weather condition."""
        # Get the global weather script using ScriptDB
        weather_script = ScriptDB.objects.filter(db_key='weather_controller').first()
        if weather_script:
            return weather_script.db.current_weather
        return 'clear'  # Default to clear if no weather system
        
    def get_weather_data(self):
        """Get complete weather data."""
        # Get the global weather script using ScriptDB
        weather_script = ScriptDB.objects.filter(db_key='weather_controller').first()
        if weather_script:
            return {
                'weathercode': weather_script.db.current_weather,
                'time_period': self.get_time_period(),
                'apparent_temperature': weather_script.db.temperature
            }
        return None
        
    def get_time_period(self):
        """Get the current time period of day."""
        hour = self.get_current_hour()
        
        if 5 <= hour < 7:
            return "dawn"
        elif 7 <= hour < 10:
            return "morning"
        elif 10 <= hour < 14:
            return "noon"
        elif 14 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 19:
            return "early_evening"
        elif 19 <= hour < 22:
            return "evening"
        elif 22 <= hour < 24:
            return "late_night"
        else:  # 0-5
            return "witching_hour"
            
    def wrap_text(self, text):
        """
        Wraps text to the configured width.
        
        Args:
            text (str): Text to wrap
            
        Returns:
            str: Wrapped text
        """
        width = getattr(settings, 'ROOM_DESCRIPTION_WIDTH', 78)
        wrapper = TextWrapper(width=width, expand_tabs=True, 
                            replace_whitespace=False,
                            break_long_words=False,
                            break_on_hyphens=False)
        return wrapper.fill(text)
        
    def return_appearance(self, looker, **kwargs):
        """
        This is called when someone looks at this room.
        Only show other characters in the 'You see:' section.
        """
        # Get room title with proper spacing (two lines before, one after)
        title = f"|/|/|c{self.get_display_name(looker)}|n|/|/"
        
        # Get the room description and wrap it
        description = self.wrap_text(self.get_display_desc(looker, **kwargs))
        
        # Combine title and description
        full_text = f"{title}{description}"
        
        # Get exits without the "Exits:" prefix
        exits = self.get_display_exits(looker, **kwargs)
        if exits:
            # Remove any existing "Exits:" prefix that might be in the string
            exits = exits.replace("Exits:", "").strip()
            # Wrap the exits text and add spacing (one line before)
            exits = self.wrap_text(f"Exits: {exits}")
            full_text += f"|/|/{exits}"
        
        # Get all characters
        characters = [obj for obj in self.contents 
                     if obj.is_typeclass('typeclasses.characters.Character') 
                     and obj.access(looker, "view")]
        
        # Only add the "You see:" section if there are characters present
        if characters:
            full_text += f"|/|/|wYou see:|n"
            # Add each character on a new line with their status
            for char in characters:
                # If this is the looker, show their name
                if char == looker:
                    display_name = char.name
                    # Get roleplay status if available
                    rp_status = ""
                    if hasattr(char.db, 'rstatus') and char.db.rstatus:
                        rp_status = f" ({char.db.rstatus})"
                    char_line = f"{display_name}{rp_status}"
                else:
                    # For other characters, use get_display_name which already includes status
                    char_line = char.get_display_name(looker, include_rstatus=True)
                    
                full_text += f"|/  |c{char_line}|n"
        
        return full_text
        
    def notify_weather_change(self, old_weather, new_weather):
        """Notify all characters in the room about weather changes."""
        if old_weather == new_weather:
            return
            
        # Get all characters in the room
        characters = [obj for obj in self.contents 
                     if obj.is_typeclass('typeclasses.characters.Character')]
                     
        # Generate transition message
        message = self.get_weather_transition(old_weather, new_weather)
        
        # Send to all characters
        for char in characters:
            char.msg(f"|w{message}|n")
            
    def notify_temperature_change(self, old_temp, new_temp):
        """Notify all characters in the room about temperature changes."""
        if old_temp == new_temp:
            return
            
        # Get all characters in the room
        characters = [obj for obj in self.contents 
                     if obj.is_typeclass('typeclasses.characters.Character')]
                     
        # Generate transition message
        message = self.get_temperature_transition(old_temp, new_temp)
        
        # Send to all characters
        for char in characters:
            char.msg(f"|w{message}|n")
            
    def notify_wind_change(self, old_wind, new_wind):
        """Notify all characters in the room about wind speed changes."""
        if old_wind == new_wind:
            return
            
        # Get all characters in the room
        characters = [obj for obj in self.contents 
                     if obj.is_typeclass('typeclasses.characters.Character')]
                     
        # Generate transition message
        message = self.get_wind_transition(old_wind, new_wind)
        
        # Send to all characters
        for char in characters:
            char.msg(f"|w{message}|n")

    def get_temperature_transition(self, old_temp, new_temp):
        """Get temperature transition message. Override in subclasses."""
        if new_temp > old_temp:
            return f"The temperature rises noticeably, becoming warmer."
        else:
            return f"The temperature drops noticeably, becoming cooler."
            
    def get_wind_transition(self, old_wind, new_wind):
        """Get wind speed transition message. Override in subclasses."""
        if new_wind > old_wind:
            return f"The wind picks up strength, blowing with increased intensity."
        else:
            return f"The wind dies down, becoming more gentle."

    def get_weather_transition(self, old_weather, new_weather):
        """Get weather transition message. Override in subclasses."""
        return f"The weather changes from {old_weather} to {new_weather}."
        
    def get_time_transition(self, old_period, new_period):
        """Get time transition message. Override in subclasses."""
        return f"Time shifts from {old_period} to {new_period}."

RESPAWN_MESSAGE = """
The crushing darkness of death gives way to a gentle, phosphorescent glow. Your consciousness drifts through familiar waters - the same waters that lap at the shores of Anchors Edge. Ancient mariners spoke of the Tide Mother's mercy, how she claims no soul that still has purpose in her realm.

The salt spray carries whispers of forgotten tales: of sailors lost at sea, of promises to loved ones left unfulfilled, of adventures yet to be had. The very essence of the harbor town seems to pull at you, refusing to let you drift into the great beyond.

Gradually, the ethereal currents guide you back to shore. You feel your form solidifying as the waves gently deposit you on the sandy beach where the harbor meets the sea. The taste of salt lingers on your lips as consciousness fully returns, your body whole once more.

The familiar creaking of ship timbers and calls of seabirds welcome you back to the world of the living. The weathered steps leading up to the harbor docks await nearby - another soul returned by the Tide Mother's grace to continue their tale in Anchors Edge.
"""
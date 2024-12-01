"""
Base room types and templates.
"""

from evennia import DefaultRoom
from django.conf import settings
from datetime import datetime
import pytz
from evennia.scripts.models import ScriptDB
from textwrap import fill, TextWrapper

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
        Wrap the description text before returning.
        """
        # Get the base appearance
        appearance = super().return_appearance(looker, **kwargs)
        
        # Split into lines, wrap each line separately to preserve formatting
        lines = appearance.split('\n')
        wrapped_lines = []
        
        for line in lines:
            if line.strip():  # Only wrap non-empty lines
                wrapped_lines.append(self.wrap_text(line))
            else:
                wrapped_lines.append(line)
                
        # Rejoin the lines
        return '\n'.join(wrapped_lines)
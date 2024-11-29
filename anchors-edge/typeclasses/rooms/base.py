"""
Base room types and weather-aware functionality.
"""

from evennia.objects.objects import DefaultRoom
from evennia import GLOBAL_SCRIPTS
import logging
from textwrap import fill
from django.conf import settings

# Configure logging
logging.basicConfig(level=logging.ERROR)

class WeatherAwareRoom(DefaultRoom):
    """Base class for rooms that respond to weather and time."""
    
    # Override the default appearance template with explicit newlines and spacing
    appearance_template = """
|/|/|w{name}|n|/
{desc}|/
{exits}
{things}
{footer}"""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.weather_enabled = True  # Default to enabled
        self.db.weather_data = {}
        self.db.weather_modifiers = {
            "sheltered": False,  # Is this area protected from rain/wind?
            "indoor": False,     # Is this an indoor area?
            "magical": False     # Does this area have magical weather effects?
        }
    
    def ensure_weather_modifiers(self):
        """Ensure weather modifiers exist."""
        if not hasattr(self.db, "weather_modifiers") or self.db.weather_modifiers is None:
            self.db.weather_modifiers = {
                "sheltered": False,
                "indoor": False,
                "magical": False
            }
    
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        # Ensure weather modifiers exist
        self.ensure_weather_modifiers()
        
        desc = self.db.desc
        desc = desc.strip()
        
        # Add weather description if applicable
        if self.db.weather_enabled and not self.db.weather_modifiers.get("indoor", False):
            weather_data = self.get_weather_data()
            if weather_data:
                weather_desc = self._get_weather_description(weather_data)
                if weather_desc:
                    desc = f"{desc}|/|/{weather_desc}"
        
        # Add debug info for admins/builders
        if looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            weather_data = self.get_weather_data()
            debug_info = ["|/|r[Weather Debug Info]|n"]
            if weather_data:
                debug_info.extend([
                    f"Temperature: {weather_data.get('apparent_temperature')}°F",
                    f"Wind Speed: {weather_data.get('wind_speed_10m')} mph",
                    f"Wind Direction: {weather_data.get('wind_direction_10m')}°",
                    f"Cloud Cover: {weather_data.get('cloud_cover')}%",
                    f"Weather Code: {weather_data.get('weathercode')}"
                ])
            else:
                debug_info.append("No weather data available")
                
            debug_info.extend([
                f"Room Modifiers: {self.db.weather_modifiers}",
                f"Weather Enabled: {self.db.weather_enabled}"
            ])
            
            desc = f"{desc}|/|/{'|/'.join(debug_info)}"
        
        return desc
        
    def get_display_exits(self, looker, **kwargs):
        """Get the exits of the room."""
        # Get raw exits without the "Exits:" prefix
        exits = super().get_display_exits(looker, **kwargs)
            
        # Remove any existing "Exits:" prefix and clean up
        exits = exits.replace("Exits:", "").strip()
        return f"|/|wExits|n:{exits}"
        
    def get_display_things(self, looker, **kwargs):
        """Hide objects by default."""
        return ""
        
    def get_weather_data(self):
        """Fetch weather data from the global weather script."""
        try:
            weather = GLOBAL_SCRIPTS.weather_controller
            if weather:
                data = weather.get_weather_data("main_island")
                if data:
                    # Ensure time_period exists and is valid
                    if 'time_period' not in data or not data['time_period']:
                        current_time = weather.get_current_time_period()
                        data['time_period'] = current_time if current_time else 'day'
                return data
            else:
                from evennia.utils import logger
                logger.log_err("Weather controller not found in GLOBAL_SCRIPTS")
                return {}
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error getting weather data: {e}")
            return {'time_period': 'day'}  # Provide a default fallback

    def update_weather(self):
        """Update the room's weather data."""
        weather_data = self.get_weather_data()
        if weather_data:
            self.db.weather_data = weather_data 
    
    def wrap_text(self, text):
        """
        Wraps text to the configured width.
        
        Args:
            text (str): Text to wrap
            
        Returns:
            str: Wrapped text
        """
        width = getattr(settings, 'ROOM_DESCRIPTION_WIDTH', 78)
        return fill(text, width=width, expand_tabs=True, replace_whitespace=False)
    
    def return_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        """
        if not looker:
            return ""
            
        # Get the base appearance
        appearance = super().return_appearance(looker)
        
        # Only add weather debug info if enabled and viewer is an admin
        if (getattr(settings, 'SHOW_WEATHER_DEBUG', False) and 
            looker.permissions.check("Admin")):
            weather_data = self.get_weather_data()
            debug_info = "\n\n[Weather Debug Info]"
            if weather_data:
                debug_info += f"\nTemperature: {weather_data.get('apparent_temperature')}°F"
                debug_info += f"\nWind Speed: {weather_data.get('wind_speed_10m')} mph"
                debug_info += f"\nWind Direction: {weather_data.get('wind_direction_10m')}°"
                debug_info += f"\nCloud Cover: {weather_data.get('cloud_cover')}%"
                debug_info += f"\nWeather Code: {weather_data.get('weathercode')}"
            debug_info += f"\nRoom Modifiers: {self.db.weather_modifiers}"
            debug_info += f"\nWeather Enabled: {self.db.weather_enabled}"
            appearance += debug_info
            
        return appearance
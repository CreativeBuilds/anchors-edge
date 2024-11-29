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
        self.db.weather_enabled = False
        self.db.weather_modifiers = {
            "sheltered": False,
            "indoor": False,
            "magical": False
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
            if settings.SHOW_WEATHER_DEBUG:
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
            else:
                debug_info.append("Weather debug info disabled")
                
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
        """Get current weather data."""
        if not self.db.weather_enabled:
            return None
            
        # Get the weather script using the correct search method
        from evennia.utils.search import search_script
        weather_script = search_script('weather_controller')
        if not weather_script:
            return None
            
        # Get weather data for main island
        return weather_script[0].get_weather_data('main_island')
    
    def _get_weather_description(self, weather_data):
        """Get weather description based on current conditions."""
        if not weather_data or not self.db.weather_enabled:
            return ""
            
        weather_code = weather_data.get('weathercode')
        temp = weather_data.get('apparent_temperature', 70)
        wind_speed = weather_data.get('wind_speed_10m', 0)
        
        descriptions = []
        
        # Add temperature description if outdoors
        if not self.db.weather_modifiers.get("indoor", False):
            if temp > 85:
                descriptions.append("The air is hot and humid")
            elif temp > 75:
                descriptions.append("The weather is pleasantly warm")
            elif temp > 60:
                descriptions.append("The temperature is mild")
            elif temp > 45:
                descriptions.append("There's a noticeable chill in the air")
            else:
                descriptions.append("The air is quite cold")
            
        # Add wind description for outdoor or partially sheltered areas
        if not (self.db.weather_modifiers.get("indoor", False) or 
                self.db.weather_modifiers.get("sheltered", False)):
            if wind_speed > 20:
                descriptions.append("strong winds whip through the area")
            elif wind_speed > 10:
                descriptions.append("a steady breeze blows")
            elif wind_speed > 5:
                descriptions.append("a gentle breeze stirs the air")
            
        # Add weather condition description
        if weather_code in [95, 96, 99]:  # Thunderstorm
            if self.db.weather_modifiers.get("indoor", False):
                descriptions.append("thunder rumbles in the distance")
            else:
                descriptions.append("thunder rumbles overhead as lightning flashes across the sky")
        elif weather_code in [61, 63, 65]:  # Rain
            if self.db.weather_modifiers.get("indoor", False):
                descriptions.append("rain can be heard pattering outside")
            else:
                descriptions.append("rain falls steadily")
        elif weather_code in [45, 48]:  # Foggy/cloudy
            if not self.db.weather_modifiers.get("indoor", False):
                descriptions.append("clouds fill the sky")
            
        # Combine descriptions
        if descriptions:
            weather_desc = ", ".join(descriptions)
            return f"\nThe weather: {weather_desc}."
        return ""
    
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
        
        # Debug info is now handled in get_display_desc
        return appearance
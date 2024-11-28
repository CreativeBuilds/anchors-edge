"""
Room typeclasses for weather-aware and dynamic environments.
"""

from evennia.objects.objects import DefaultRoom
from evennia import GLOBAL_SCRIPTS
import logging


# Configure logging
logging.basicConfig(level=logging.ERROR)

# Time constants
DESCRIPTION_UPDATE_INTERVAL = 5 * 60  # 5 minutes in seconds
CACHE_EXPIRY = 900  # 15 minutes in seconds

# Weather codes mapping
WEATHER_CODES = {
    "light_rain": [51, 53, 55],
    "rain": [61, 63, 65],
    "showers": [80, 81, 82],
    "thunderstorm": [95, 96, 99]
}

class WeatherAwareRoom(DefaultRoom):
    """A room that is aware of weather conditions."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.weather_enabled = False  # Default to weather disabled
        self.db.weather_data = {}
        
    def return_appearance(self, looker, **kwargs):
        """
        This is called when someone looks at the room.
        """
        # Get the base appearance
        appearance = super().return_appearance(looker, **kwargs)
        
        # Only show room ID to admins/builders
        if not looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            # Remove the room ID from the appearance
            # The ID is typically shown as (#1234) at the end of the first line
            lines = appearance.split('\n')
            if lines:
                lines[0] = lines[0].split(' (#')[0]  # Remove the ID part
            appearance = '\n'.join(lines)
        
        # Only add weather if enabled and we're not indoors
        if self.db.weather_enabled and not self.db.weather_modifiers.get("indoor", False):
            weather_data = self.get_weather_data()
            if weather_data:
                # Add weather information to the room description
                weather_desc = self._get_weather_description(weather_data)
                if weather_desc:
                    appearance += f"\r\n\r\n{weather_desc}"
        
        return appearance
        
    def _get_weather_description(self, weather_data):
        """Generate a weather description based on current conditions."""
        desc_parts = []
        
        # Temperature
        temp = weather_data.get('apparent_temperature')
        if temp is not None:
            if temp < 40:
                desc_parts.append("The air is bitingly cold")
            elif temp < 60:
                desc_parts.append("The air is cool and crisp")
            elif temp < 80:
                desc_parts.append("The temperature is pleasantly warm")
            else:
                desc_parts.append("The air is hot and humid")
        
        # Wind
        wind = weather_data.get('wind_speed_10m')
        if wind is not None:
            if wind > 25:
                desc_parts.append("strong winds whip through the area")
            elif wind > 15:
                desc_parts.append("a steady breeze blows")
            elif wind > 5:
                desc_parts.append("a gentle breeze stirs the air")
        
        # Cloud cover and precipitation
        clouds = weather_data.get('cloud_cover')
        if clouds is not None:
            if clouds > 80:
                desc_parts.append("the sky is heavily overcast")
            elif clouds > 50:
                desc_parts.append("scattered clouds drift overhead")
            else:
                desc_parts.append("the sky is mostly clear")
        
        if desc_parts:
            return ". ".join(desc_parts) + "."
        return ""
        
    def get_weather_data(self):
        """
        Fetch weather data from the global weather script.
        
        Returns:
            dict: Current weather data for this room's location
        """
        try:
            weather = GLOBAL_SCRIPTS.weather_controller
            if weather:
                return weather.get_weather_data("main_island")
            else:
                from evennia.utils import logger
                logger.log_err("Weather controller not found in GLOBAL_SCRIPTS")
                return {}
        except Exception as e:
            from evennia.utils import logger
            logger.log_err(f"Error getting weather data: {e}")
            return {}

class IslandRoom(WeatherAwareRoom):
    """
    A room that updates its description based on weather and time of day.
    This room type should be used for outdoor areas on islands that need
    to reflect current weather conditions.
    """
    
    def at_object_creation(self):
        """Initialize the island room."""
        super().at_object_creation()
        
        # Set default weather modification flags
        self.db.weather_modifiers = {
            "sheltered": False,  # Is this area protected from rain/wind?
            "indoor": False,     # Is this an indoor area?
            "magical": False     # Does this area have magical weather effects?
        }

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
        
    def get_display_name(self, looker, **kwargs):
        """Get the name of the room."""
        if not looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            return f"{self.key}"
        return f"{self.key} (#{self.id})"
        
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        desc = self.db.desc
        # Ensure description has proper spacing
        desc = desc.strip()  # Remove any leading/trailing whitespace
        
        # Add weather description if applicable
        if self.db.weather_enabled and not self.db.weather_modifiers.get("indoor", False):
            weather_data = self.get_weather_data()
            if weather_data:
                weather_desc = self._get_weather_description(weather_data)
                if weather_desc:
                    desc = f"{desc}|/|/{weather_desc}|/"
        
        # Add debug info only for admins/builders
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
            
            # Get time period if available
            if hasattr(self, 'get_time_period'):
                debug_info.append(f"Time Period: {self.get_time_period()}")
            
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
        
    def return_appearance(self, looker, **kwargs):
        """
        This is called when someone looks at the room.
        """
        # Get the base appearance
        appearance = super().return_appearance(looker, **kwargs)
        
        # Only show room ID to admins/builders
        if not looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            # Remove the room ID from the appearance
            lines = appearance.split('|/')
            if lines:
                lines[0] = lines[0].split(' (#')[0]  # Remove the ID part
                appearance = '|/'.join(lines)
        
        # Only add weather if enabled and we're not indoors
        if self.db.weather_enabled and not self.db.weather_modifiers.get("indoor", False):
            weather_data = self.get_weather_data()
            if weather_data:
                weather_desc = self._get_weather_description(weather_data)
                if weather_desc:
                    appearance += f"{weather_desc}"
        
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

    def update_weather(self):
        """Update the room's weather data."""
        weather_data = self.get_weather_data()
        if weather_data:
            self.db.weather_data = weather_data

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

class TavernRoom(WeatherAwareRoom):
    """A special room type for taverns with dynamic descriptions."""
    
    def at_object_creation(self):
        """Called when room is first created."""
        super().at_object_creation()
        self.db.base_desc = self.db.desc
        self.db.is_tavern = True
        self.db.weather_enabled = True
        self.db.weather_modifiers = {
            "sheltered": True,
            "indoor": True,
            "magical": False
        }
    
    def update_weather(self):
        """Update the room's weather data."""
        super().update_weather()
        self._update_dynamic_description()
        
    def get_display_name(self, looker, **kwargs):
        """Return the magenta-colored name of the room."""
        return f"|m{super().get_display_name(looker, **kwargs)}|n"
        
    def return_appearance(self, looker, **kwargs):
        """
        Custom appearance handler for tavern rooms.
        Adds time and weather-based description elements.
        """
        # Store the current description
        current_desc = self.db.desc
        
        # Update description based on time and weather
        self._update_dynamic_description()
        
        # Get the appearance with cleaned articles (from parent class)
        appearance = super().return_appearance(looker, **kwargs)
        
        # Restore the base description
        self.db.desc = current_desc
        
        return appearance
        
    def _update_dynamic_description(self):
        """Update the room's description based on current conditions."""
        if not hasattr(self.db, "base_desc"):
            self.db.base_desc = self.db.desc
            
        desc_parts = [self.db.base_desc.strip()]  # Start with base description
        
        time_period = self.get_time_period() if hasattr(self, 'get_time_period') else "day"
        weather_data = self.get_weather_data()
        temp = weather_data.get('apparent_temperature') if weather_data else None
        
        # Handle hearth based on temperature and time
        if temp is not None and time_period:
            if temp < 70 or time_period == "night":
                if time_period == "night":
                    desc_parts.append("A crackling fire burns brightly in the hearth, casting dancing shadows across the room.")
                elif time_period == "dawn":
                    desc_parts.append("Warm coals glow softly in the hearth, awaiting the morning's fresh wood.")
                else:
                    desc_parts.append("A modest fire burns in the hearth, taking the chill from the air.")
            else:
                desc_parts.append("The hearth stands cold and empty in the warm weather.")
        
        # Add indoor weather effects
        if weather_data:
            weather_code = weather_data.get('weathercode')
            
            # Window state based on weather and temperature
            windows_open = temp and temp >= 70 and not (
                weather_code in WEATHER_CODES["rain"] + 
                WEATHER_CODES["light_rain"] + 
                WEATHER_CODES["thunderstorm"]
            )
            
            if windows_open:
                desc_parts.append("The windows are open to let in the warm breeze.")
            else:
                if weather_code in WEATHER_CODES["rain"] + WEATHER_CODES["light_rain"]:
                    desc_parts.append("The closed windows are streaked with raindrops, their patter creating a cozy atmosphere inside.")
                elif weather_code in WEATHER_CODES["thunderstorm"]:
                    desc_parts.append("The wooden shutters are closed tight against the storm, while the wall sconces provide warm illumination within.")
            
            # Add temperature-based indoor descriptions
            if temp is not None:
                if temp < 40:
                    if time_period in ["night", "dawn"]:
                        desc_parts.append("The hearth's warmth is especially welcome given the bitter cold outside.")
                    else:
                        desc_parts.append("The tavern provides welcome shelter from the bitter cold outside.")
                elif temp > 85:
                    if windows_open:
                        desc_parts.append("Despite the open windows, the air inside remains warm and stuffy.")
                    else:
                        desc_parts.append("The closed windows trap the heat, making the air inside warm and stuffy.")
        
        # Join all parts with double newlines
        self.db.desc = "|/|/".join(desc_parts)

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

# Add these constants at the top with the other constants
TIME_PERIODS = {
    "dawn": (5, 7),      # 5:00 AM - 7:00 AM
    "morning": (7, 12),  # 7:00 AM - 12:00 PM
    "noon": (12, 14),    # 12:00 PM - 2:00 PM
    "afternoon": (14, 17),# 2:00 PM - 5:00 PM
    "dusk": (17, 19),    # 5:00 PM - 7:00 PM
    "twilight": (19, 21),# 7:00 PM - 9:00 PM
    "night": (21, 5)     # 9:00 PM - 5:00 AM
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
    
    def ensure_weather_modifiers(self):
        """Ensure weather modifiers exist."""
        if not hasattr(self.db, "weather_modifiers") or self.db.weather_modifiers is None:
            self.db.weather_modifiers = {
                "sheltered": False,
                "indoor": False,
                "magical": False
            }
    
    def get_display_name(self, looker, **kwargs):
        """Get the name of the room."""
        if not looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            return f"{self.key}"
        return f"{self.key} (#{self.id})"
        
    def get_display_desc(self, looker, **kwargs):
        """Get the description of the room."""
        # Ensure weather modifiers exist
        self.ensure_weather_modifiers()
        
        desc = self.db.desc
        desc = desc.strip()
        
        # Add time description
        time_desc = self.get_time_description()
        if time_desc:
            desc = f"{desc}|/|/{time_desc}"
        
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
                f"Weather Enabled: {self.db.weather_enabled}",
                f"Time Period: {self.get_time_period()}"
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

    def get_time_period(self):
        """Get the current time period based on server time."""
        from datetime import datetime
        current_hour = datetime.now().hour
        
        for period, (start, end) in TIME_PERIODS.items():
            if period == "night":
                # Handle night crossing midnight
                if current_hour >= start or current_hour < end:
                    return period
            else:
                if start <= current_hour < end:
                    return period
        
        return "day"  # Default fallback
    
    def get_time_description(self):
        """Get description based on time of day."""
        # Ensure weather modifiers exist
        self.ensure_weather_modifiers()
        
        time_period = self.get_time_period()
        
        if self.db.weather_modifiers.get("indoor", False):
            # Indoor time descriptions
            descriptions = {
                "dawn": "Early morning light filters softly through the windows.",
                "morning": "Morning sunlight streams through the windows.",
                "noon": "Bright daylight fills the room.",
                "afternoon": "The warm afternoon light angles through the windows.",
                "dusk": "The fading light of dusk softens the room's features.",
                "twilight": "The last rays of twilight give way to evening shadows.",
                "night": "Night has fallen outside the windows."
            }
        else:
            # Outdoor time descriptions
            descriptions = {
                "dawn": "The sky is painted in soft hues as dawn breaks.",
                "morning": "The morning sun climbs in the eastern sky.",
                "noon": "The sun hangs high overhead.",
                "afternoon": "The sun drifts westward in the afternoon sky.",
                "dusk": "The sun sinks toward the horizon, painting the sky in warm colors.",
                "twilight": "The last light of day fades from the darkening sky.",
                "night": "Stars twinkle in the night sky above."
            }
            
        return descriptions.get(time_period, "")

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
    
    # Base template for the main tavern room
    MAIN_TAVERN_TEMPLATE = """
A warm and inviting tavern that serves as a haven for sailors and locals alike. The main room stretches before you, with a well-worn bar running along the left wall. Three private booths line the back wall, offering more intimate spaces for quiet conversations. A large stone hearth dominates the western wall, while sturdy wooden stairs in the northwest corner lead up to the second floor.

{lighting_desc}

{hearth_desc}

{window_desc}

{atmosphere_desc}"""

    # Templates for different aspects
    LIGHTING_TEMPLATES = {
        "dawn": "Early morning light filters softly through the windows, mixing with the warm glow of the wall sconces.",
        "morning": "Morning sunlight streams through the windows, illuminating the polished wooden beams that cross the ceiling.",
        "noon": "Bright daylight fills the tavern through the tall windows.",
        "afternoon": "The warm afternoon light angles through the windows, casting long shadows across the floor.",
        "dusk": "The fading light of dusk mingles with the growing warmth of the lit sconces.",
        "twilight": "The wall sconces provide most of the illumination now, their flames casting a warm glow throughout the room.",
        "night": "The tavern is illuminated by the warm glow of wall sconces and {hearth_light}."
    }

    HEARTH_TEMPLATES = {
        "cold": "The hearth stands cold and empty in the warm weather.",
        "dead_coals": "The hearth contains only cold ashes.",
        "warm_coals": "Warm coals glow softly in the hearth, awaiting fresh wood.",
        "modest_fire": "A modest fire burns in the hearth, taking the chill from the air.",
        "bright_fire": "A crackling fire burns brightly in the hearth, casting dancing shadows across the room.",
        "roaring_fire": "A roaring fire blazes in the hearth, its warmth reaching every corner of the room."
    }

    WINDOW_TEMPLATES = {
        "open": "The windows are open to let in the {breeze_desc}.",
        "closed": "The windows are closed against the {weather_desc}.",
        "shuttered": "The wooden shutters are closed tight against {weather_desc}.",
        "rain_streaked": "Raindrops streak down the windowpanes, creating patterns in the {light_desc}."
    }

    ATMOSPHERE_TEMPLATES = {
        "cozy": "The overall atmosphere is cozy and inviting.",
        "warm": "The air is warm and comfortable.",
        "hot": "The air inside is warm and slightly stuffy.",
        "cold": "A noticeable chill permeates the air.",
        "stormy": "The tavern provides a welcome haven from the storm outside."
    }

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

        weather_data = self.get_weather_data()
        if not weather_data:
            self.db.desc = self.db.base_desc
            return

        # Get time period with fallback
        time_period = weather_data.get('time_period')
        if time_period not in self.LIGHTING_TEMPLATES:
            time_period = "day"  # Default to day if we get an invalid time period
        
        temp = weather_data.get('apparent_temperature', 70)  # Default to 70°F if no temperature
        weather_code = weather_data.get('weathercode')
        wind_speed = weather_data.get('wind_speed_10m', 0)  # Default to no wind

        # Determine hearth state
        hearth_desc = self._get_hearth_desc(temp, time_period)
        hearth_light = "firelight" if "fire" in hearth_desc else "sconces alone"

        try:
            # Determine lighting with error handling
            lighting_desc = self.LIGHTING_TEMPLATES[time_period].format(hearth_light=hearth_light)

            # Determine window state and description
            window_desc = self._get_window_desc(temp, weather_code, time_period, wind_speed)

            # Determine atmosphere
            atmosphere_desc = self._get_atmosphere_desc(temp, weather_code, time_period)

            # Format the complete description
            self.db.desc = self.MAIN_TAVERN_TEMPLATE.format(
                lighting_desc=lighting_desc,
                hearth_desc=hearth_desc,
                window_desc=window_desc,
                atmosphere_desc=atmosphere_desc
            )
        except Exception as e:
            # If anything goes wrong, fall back to base description
            from evennia.utils import logger
            logger.log_err(f"Error updating tavern description: {e}")
            self.db.desc = self.db.base_desc

    def _get_hearth_desc(self, temp, time_period):
        """Get the appropriate hearth description."""
        if temp > 75:
            return self.HEARTH_TEMPLATES["cold"]
        elif time_period == "night":
            return self.HEARTH_TEMPLATES["bright_fire"]
        elif time_period == "dawn":
            return self.HEARTH_TEMPLATES["warm_coals"]
        elif temp < 50:
            return self.HEARTH_TEMPLATES["roaring_fire"]
        elif temp < 65:
            return self.HEARTH_TEMPLATES["modest_fire"]
        else:
            return self.HEARTH_TEMPLATES["dead_coals"]

    def _get_window_desc(self, temp, weather_code, time_period, wind_speed):
        """Get the appropriate window description."""
        if weather_code in WEATHER_CODES["thunderstorm"]:
            return self.WINDOW_TEMPLATES["shuttered"].format(
                weather_desc="the raging storm"
            )
        elif weather_code in WEATHER_CODES["rain"] + WEATHER_CODES["light_rain"]:
            return self.WINDOW_TEMPLATES["rain_streaked"].format(
                light_desc="dim light" if time_period in ["dusk", "night"] else "daylight"
            )
        elif temp >= 70 and wind_speed > 0:
            breeze = "cool" if temp < 75 else "warm"
            return self.WINDOW_TEMPLATES["open"].format(
                breeze_desc=f"the {breeze} breeze"
            )
        else:
            return self.WINDOW_TEMPLATES["closed"].format(
                weather_desc="the cold" if temp < 60 else "the heat"
            )

    def _get_atmosphere_desc(self, temp, weather_code, time_period):
        """Get the appropriate atmosphere description."""
        if weather_code in WEATHER_CODES["thunderstorm"]:
            return self.ATMOSPHERE_TEMPLATES["stormy"]
        elif temp > 85:
            return self.ATMOSPHERE_TEMPLATES["hot"]
        elif temp < 60:
            return self.ATMOSPHERE_TEMPLATES["cold"]
        elif time_period in ["night", "twilight", "dawn"]:
            return self.ATMOSPHERE_TEMPLATES["cozy"]
        else:
            return self.ATMOSPHERE_TEMPLATES["warm"]

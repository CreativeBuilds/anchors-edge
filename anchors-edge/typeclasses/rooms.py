"""
Room typeclasses for weather-aware and dynamic environments.
Provides dynamic room descriptions based on real-time weather data and time of day.
"""

from evennia.objects.objects import DefaultRoom
from datetime import datetime
import time
from evennia import TICKER_HANDLER
import pytz
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Time constants
WEATHER_UPDATE_INTERVAL = 15 * 60  # 15 minutes in seconds
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
    """
    A room that updates its description based on weather and time of day.
    
    This class fetches real-time weather data and adjusts room descriptions
    accordingly. It handles time periods (dawn, day, dusk, night) and various
    weather conditions (rain, wind, clouds, etc.).
    """
    
    def at_object_creation(self):
        """
        Initialize room attributes and start update tickers.
        Sets up base descriptions, weather data, and periodic update handlers.
        """
        super().at_object_creation()
        self.initialize_descriptions()
        self.initialize_weather_data()
        self.initialize_time_handlers()
        
        # Initial description update
        self.update_description()

    def initialize_descriptions(self):
        """
        Set up base descriptions and caching.
        Initializes different descriptions for various times of day.
        """
        self.db.cached_descriptions = {}
        self.db.cache_timestamps = {}
        self.db.desc_base = {
            "dawn": "You find yourself in a room as dawn breaks.",
            "day": "You find yourself in a room bathed in daylight.",
            "dusk": "You find yourself in a room as dusk settles.",
            "night": "You find yourself in a room under the cover of night."
        }

    def initialize_weather_data(self):
        """
        Set up weather-related attributes.
        Initializes weather effects, location coordinates, and timezone.
        """
        self.db.weather_data = {}
        self.db.last_weather_update = 0
        self.db.weather_effects = {
            "rain": "\r\n\r\nThe sound of rain can be heard.",
            "wind": "\r\n\r\nThe wind howls outside.",
            "thunder": "\r\n\r\nThunder rumbles in the distance.",
            "cloudy_light": "dim",
            "cloudy_sun": "daylight"
        }
        # Turks and Caicos coordinates
        self.db.latitude = 21.4655745
        self.db.longitude = -71.1390341
        
        # Cache timezone object
        self.db.timezone = pytz.timezone('America/Chicago')

    def initialize_time_handlers(self):
        """
        Set up periodic update handlers.
        Configures tickers for weather and description updates.
        """
        TICKER_HANDLER.add(WEATHER_UPDATE_INTERVAL, self.update_weather)
        TICKER_HANDLER.add(DESCRIPTION_UPDATE_INTERVAL, self.update_description)

    def get_weather_data(self):
        """
        Fetch current weather data from Open-Meteo API.
        
        Returns:
            dict: Weather data if successful, None if failed
            
        The API returns various weather parameters including:
        - apparent_temperature: Feel-like temperature in Fahrenheit
        - weather_code: Numeric code representing weather condition
        - cloud_cover: Percentage of sky covered by clouds
        - wind_speed_10m: Wind speed in mph
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.db.latitude,
            "longitude": self.db.longitude,
            "current": "apparent_temperature,precipitation,rain,showers,"
                      "weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,"
                      "wind_gusts_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "America/Chicago"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()['current']
        except Exception as e:
            logging.error(f"Weather API error: {e}")
        return None

    def update_weather(self, *args, **kwargs):
        """
        Update weather data and trigger description update if needed.
        Checks for significant weather changes before updating description.
        """
        weather_data = self.get_weather_data()
        if weather_data:
            old_weather = self.db.weather_data
            self.db.weather_data = weather_data
            self.db.last_weather_update = datetime.now().timestamp()
            
            if self.should_update_description(old_weather, weather_data):
                self.update_description()

    def should_update_description(self, old_weather, new_weather):
        """
        Check if weather changes warrant a description update.
        
        Args:
            old_weather (dict): Previous weather data
            new_weather (dict): Current weather data
            
        Returns:
            bool: True if description should be updated
            
        Significant changes are:
        - Wind speed change > 5 mph
        - Cloud cover change > 20%
        - Any change in weather code
        """
        if not old_weather:
            return True
            
        significant_changes = [
            abs(new_weather.get('wind_speed_10m', 0) - old_weather.get('wind_speed_10m', 0)) > 5,
            abs(new_weather.get('cloud_cover', 0) - old_weather.get('cloud_cover', 0)) > 20,
            new_weather.get('weather_code', 0) != old_weather.get('weather_code', 0)
        ]
        
        return any(significant_changes)

    def update_description(self):
        """
        Update room description based on current time and weather.
        Caches the new description and updates timestamps.
        """
        current_period = self.get_time_period()
        base_desc = self.db.desc_base.get(current_period, "You see nothing special.")
        
        weather_desc = self.apply_weather_effects(
            base_desc,
            self.db.weather_data.get('weather_code', 0),
            self.db.weather_data.get('wind_speed_10m', 0),
            self.db.weather_data.get('cloud_cover', 0)
        )
        
        self.db.cached_descriptions[current_period] = weather_desc
        self.db.cache_timestamps[current_period] = time.time()
        self.db.desc = weather_desc

    def apply_weather_effects(self, desc, weather_code, wind_speed, cloud_cover):
        """
        Apply weather effects to the room description.
        
        Args:
            desc (str): Base description
            weather_code (int): Current weather code
            wind_speed (float): Wind speed in mph
            cloud_cover (int): Cloud cover percentage
            
        Returns:
            str: Modified description with weather effects
        """
        # Apply rain effects
        if weather_code in WEATHER_CODES["light_rain"] + WEATHER_CODES["rain"] + WEATHER_CODES["showers"]:
            desc += self.db.weather_effects["rain"]
        
        # Apply wind effects
        if wind_speed > 15:
            desc += self.db.weather_effects["wind"]
        
        # Apply thunder effects
        if weather_code in WEATHER_CODES["thunderstorm"]:
            desc += self.db.weather_effects["thunder"]
        
        # Modify lighting for cloudy conditions during day
        if cloud_cover > 80 and self.get_time_period() == "day":
            desc = desc.replace("bright", self.db.weather_effects["cloudy_light"])
            desc = desc.replace("sunlight", self.db.weather_effects["cloudy_sun"])
        
        return desc

    def get_time_period(self):
        """
        Determine current time period based on hour.
        
        Returns:
            str: Current time period (dawn, day, dusk, or night)
        """
        hour = self.get_time_of_day()
        if 5 <= hour < 7: return "dawn"
        elif 7 <= hour < 17: return "day"
        elif 17 <= hour < 20: return "dusk"
        else: return "night"

    def get_time_of_day(self):
        """
        Get current hour in configured timezone.
        
        Returns:
            int: Current hour (0-23)
        """
        return datetime.now(self.db.timezone).hour

    def return_appearance(self, looker, **kwargs):
        """
        Display the room's appearance with weather effects.
        
        Args:
            looker: The object looking at this room
            **kwargs: Additional arguments
            
        Returns:
            str: Formatted room description
        """
        if not looker:
            return ""
            
        current_period = self.get_time_period()
        
        # Update description if needed
        if not self.db.cached_descriptions.get(current_period):
            self.update_description()
        elif time.time() - self.db.cache_timestamps.get(current_period, 0) > CACHE_EXPIRY:
            self.update_description()
            
        appearance = super().return_appearance(looker, **kwargs)
        if not appearance:
            return ""
            
        return f"\r\n\r\n{appearance}"
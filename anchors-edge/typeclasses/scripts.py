"""
Scripts for weather and time systems.
"""
from evennia import DefaultScript
from evennia.utils import logger
from datetime import datetime
import pytz
import requests
import time
from typing import Dict, Optional

class IslandWeatherScript(DefaultScript):
    """
    A global script that manages weather and time systems.
    """
    
    def at_script_creation(self):
        """Set up the script."""
        super().at_script_creation()
        self.key = "weather_controller"
        self.desc = "Manages weather and time systems"
        self.persistent = True
        self.interval = 900  # 15 minutes between updates
        self.start_delay = False  # Start immediately
        
        # Initialize basic weather data
        self.db.temperature = 70
        self.db.current_weather = 'clear'
        self.db.wind_speed = 5
        self.db.apparent_temperature = 70
        
        # Initialize data storage
        self.db.weather_systems = {}
        self.db.last_updates = {}
        self.db.coordinates = {
            "main_island": (21.4655745, -71.1390341),  # Turks and Caicos
        }
        
        # Time period definitions
        self.db.time_periods = {
            "dawn": (5, 7),          # 5:00 AM - 7:00 AM
            "morning": (7, 11),      # 7:00 AM - 11:00 AM
            "noon": (11, 14),        # 11:00 AM - 2:00 PM
            "afternoon": (14, 17),    # 2:00 PM - 5:00 PM
            "early_evening": (17, 19),# 5:00 PM - 7:00 PM
            "evening": (19, 23),      # 7:00 PM - 11:00 PM
            "late_night": (23, 2),    # 11:00 PM - 2:00 AM
            "witching_hour": (2, 5)   # 2:00 AM - 5:00 AM
        }
        
        # Current time period
        self.db.current_time_period = self.get_current_time_period()
        
        # Force first update
        self.update_weather()
        
    def get_current_time_period(self) -> str:
        """Get the current time period based on Austin time."""
        austin_tz = pytz.timezone('America/Chicago')
        current_time = datetime.now(austin_tz)
        current_hour = current_time.hour
        
        # Handle periods that cross midnight
        if current_hour >= 23 or current_hour < 2:
            return "late_night"
        elif 2 <= current_hour < 5:
            return "witching_hour"
        elif 5 <= current_hour < 7:
            return "dawn"
        elif 7 <= current_hour < 11:
            return "morning"
        elif 11 <= current_hour < 14:
            return "noon"
        elif 14 <= current_hour < 17:
            return "afternoon"
        elif 17 <= current_hour < 19:
            return "early_evening"
        elif 19 <= current_hour < 23:
            return "evening"
        
        return "day"  # Default fallback
        
    def at_repeat(self):
        """Called every self.interval seconds."""
        # Update time period
        new_time_period = self.get_current_time_period()
        if new_time_period != self.db.current_time_period:
            self.db.current_time_period = new_time_period
            logger.log_info(f"Time period changed to: {new_time_period} (Austin time)")
        
        # Update weather
        self.update_weather()
        
    def update_weather(self):
        """Update weather for all islands."""
        try:
            # Default values in case API fails
            default_weather = {
                'apparent_temperature': self.db.temperature,
                'weathercode': 0,  # Clear sky
                'wind_speed_10m': self.db.wind_speed,
                'time_period': self.db.current_time_period
            }
            
            for island, coords in self.db.coordinates.items():
                try:
                    lat, lon = coords
                    url = (f"https://api.open-meteo.com/v1/forecast?"
                          f"latitude={lat}&longitude={lon}"
                          f"&current=apparent_temperature,precipitation,rain,showers,"
                          f"weathercode,cloud_cover,wind_speed_10m,wind_direction_10m,"
                          f"wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"
                          f"&precipitation_unit=inch&timezone=America%2FChicago")
                    
                    response = requests.get(url)
                    if response.status_code == 200:
                        weather_data = response.json()['current']
                        # Store main values separately for easy access
                        self.db.temperature = weather_data.get('apparent_temperature', 70)
                        self.db.wind_speed = weather_data.get('wind_speed_10m', 5)
                        self.db.current_weather = self._get_weather_type(weather_data.get('weathercode', 0))
                        
                        # Add time period to weather data
                        weather_data['time_period'] = self.db.current_time_period
                        self.db.weather_systems[island] = weather_data
                        self.db.last_updates[island] = time.time()
                        logger.log_info(f"Updated weather for {island}: {weather_data}")
                    else:
                        self.db.weather_systems[island] = default_weather
                        logger.log_err(f"Failed to get weather data for {island}: {response.status_code}")
                except Exception as e:
                    self.db.weather_systems[island] = default_weather
                    logger.log_err(f"Error updating weather for {island}: {e}")
        except Exception as e:
            logger.log_err(f"Critical error in weather update: {e}")
    
    def _get_weather_type(self, code: int) -> str:
        """Convert weather code to simple weather type."""
        if code in [0, 1]:
            return 'clear'
        elif code in [2, 3]:
            return 'cloudy'
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            return 'rain'
        elif code in [95, 96, 99]:
            return 'storm'
        return 'clear'
    
    def get_weather_data(self, island: str = "main_island") -> Optional[Dict]:
        """Get current weather data for an island."""
        data = self.db.weather_systems.get(island, {})
        if not data:
            # Return default data if no data exists
            return {
                'apparent_temperature': self.db.temperature,
                'weathercode': 0,
                'wind_speed_10m': self.db.wind_speed,
                'time_period': self.db.current_time_period
            }
        return data
        
    def at_server_reload(self):
        """Update weather when server reloads."""
        self.db.current_time_period = self.get_current_time_period()
        self.update_weather()
        
    def at_server_shutdown(self):
        """Clean up before shutdown."""
        pass

class GlobalSettingsScript(DefaultScript):
    """
    Script for handling global game settings and periodic tasks.
    This script runs persistently.
    """
    
    def at_script_creation(self):
        """
        Setup the script
        """
        self.key = "global_settings_script"
        self.desc = "Handles global game settings and periodic tasks"
        self.persistent = True
        self.interval = 300  # 5 minutes between checks
        
    def at_repeat(self):
        """
        Called every self.interval seconds.
        """
        # Add any periodic tasks here
        pass

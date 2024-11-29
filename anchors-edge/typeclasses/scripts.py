"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems.
"""

from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger
from typing import Optional, Dict
import time
from datetime import datetime
import requests
import pytz  # Make sure to add pytz to your requirements.txt

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
        
        # Initialize data storage
        self.db.weather_systems = {}
        self.db.last_updates = {}
        self.db.coordinates = {
            "main_island": (21.4655745, -71.1390341),  # Turks and Caicos
        }
        
        # Time period definitions
        self.db.time_periods = {
            "dawn": (5, 7),          # 5:00 AM - 7:00 AM
            "morning": (7, 12),      # 7:00 AM - 12:00 PM
            "noon": (12, 14),        # 12:00 PM - 2:00 PM
            "afternoon": (14, 17),    # 2:00 PM - 5:00 PM
            "early_evening": (17, 20),# 5:00 PM - 8:00 PM
            "evening": (20, 24),      # 8:00 PM - 12:00 AM
            "late_night": (0, 3),     # 12:00 AM - 3:00 AM
            "witching_hour": (3, 5)   # 3:00 AM - 5:00 AM
        }
        
        # Current time period
        self.db.current_time_period = self.get_current_time_period()
        
        # Force first update
        self.update_weather()
        
    def get_current_time_period(self) -> str:
        """Get the current time period based on Austin time."""
        # Get current time in Austin
        austin_tz = pytz.timezone('America/Chicago')
        current_time = datetime.now(austin_tz)
        current_hour = current_time.hour
        
        for period, (start, end) in self.db.time_periods.items():
            if start <= current_hour < end:
                return period
            # Special handling for evening which crosses midnight
            elif period == "evening" and (current_hour >= start or current_hour < end):
                return period
        
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
        for island, coords in self.db.coordinates.items():
            try:
                lat, lon = coords
                url = (f"https://api.open-meteo.com/v1/forecast?"
                      f"latitude={lat}&longitude={lon}"
                      f"&current=apparent_temperature,precipitation,rain,showers,"
                      f"weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,"
                      f"wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"
                      f"&precipitation_unit=inch&timezone=America%2FChicago")  # Set timezone to Austin
                
                response = requests.get(url)
                if response.status_code == 200:
                    weather_data = response.json()['current']
                    # Add time period to weather data
                    weather_data['time_period'] = self.db.current_time_period
                    self.db.weather_systems[island] = weather_data
                    self.db.last_updates[island] = time.time()
                    logger.log_info(f"Updated weather for {island}: {weather_data}")
                else:
                    logger.log_err(f"Failed to get weather data for {island}: {response.status_code}")
            except Exception as e:
                logger.log_err(f"Error updating weather for {island}: {e}")
    
    def get_weather_data(self, island: str) -> Optional[Dict]:
        """Get current weather data for an island."""
        data = self.db.weather_systems.get(island, {})
        if data and 'time_period' not in data:
            data['time_period'] = self.db.current_time_period
        return data
        
    def at_server_reload(self):
        """Update weather when server reloads."""
        self.db.current_time_period = self.get_current_time_period()
        self.update_weather()
        
    def at_server_shutdown(self):
        """Clean up before shutdown."""
        pass

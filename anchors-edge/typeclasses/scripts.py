"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems.
"""

from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger
from typing import Optional, Dict
import time
import requests

class IslandWeatherScript(DefaultScript):
    """
    A global script that manages weather for different island regions.
    """
    
    def at_script_creation(self):
        """Set up the script."""
        super().at_script_creation()
        self.key = "weather_controller"
        self.desc = "Manages weather systems for different islands"
        self.persistent = True
        self.interval = 900  # 15 minutes between updates
        self.start_delay = False  # Start immediately
        
        # Initialize weather data storage
        self.db.weather_systems = {}
        self.db.last_updates = {}
        self.db.coordinates = {
            "main_island": (21.4655745, -71.1390341),  # Turks and Caicos
        }
        
        # Force first update
        self.update_weather()
        
    def at_repeat(self):
        """Called every self.interval seconds."""
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
                      f"&precipitation_unit=inch&timezone=America%2FChicago")
                
                response = requests.get(url)
                if response.status_code == 200:
                    weather_data = response.json()['current']
                    self.db.weather_systems[island] = weather_data
                    self.db.last_updates[island] = time.time()
                    logger.log_info(f"Updated weather for {island}: {weather_data}")
                else:
                    logger.log_err(f"Failed to get weather data for {island}: {response.status_code}")
            except Exception as e:
                logger.log_err(f"Error updating weather for {island}: {e}")
    
    def get_weather_data(self, island: str) -> Optional[Dict]:
        """Get current weather data for an island."""
        return self.db.weather_systems.get(island, {})
        
    def at_server_reload(self):
        """Update weather when server reloads."""
        self.update_weather()
        
    def at_server_shutdown(self):
        """Clean up before shutdown."""
        pass

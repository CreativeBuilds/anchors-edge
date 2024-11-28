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
        self.key = "weather_controller"
        self.desc = "Manages weather systems for different islands"
        self.persistent = True
        
        # Initialize weather data storage
        self.db.weather_systems = {}
        self.db.last_updates = {}
        self.db.coordinates = {
            "main_island": (21.4655745, -71.1390341),  # Turks and Caicos
        }

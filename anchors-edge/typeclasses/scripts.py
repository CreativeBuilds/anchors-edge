"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger
from typing import Optional, Dict
import time
import requests

# Time constants
WEATHER_UPDATE_INTERVAL = 15 * 60  # 15 minutes in seconds

class Script(DefaultScript):
    """
    This is the base TypeClass for all Scripts. Scripts describe
    all entities/systems without a physical existence in the game world
    that require database storage (like an economic system or
    combat tracker). They
    can also have a timer/ticker component.

    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties (check docs for full listing, this could be
      outdated).

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     create(key, **kwargs)
     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_pause()
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_script_delete()
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.
      at_server_start()

    """

    pass

class IslandWeatherScript(DefaultScript):
    """
    A global script that manages weather for different island regions.
    This is a more appropriate solution than using a room, as it:
    - Persists with the server
    - Can be accessed globally
    - Doesn't tie weather data to a physical location
    - Can manage multiple weather systems
    
    Usage:
        from evennia import GLOBAL_SCRIPTS
        weather = GLOBAL_SCRIPTS.weather
        current_weather = weather.get_weather_data("main_island")
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
            # Add other islands as needed
        }
    
    def get_weather_data(self, island_key: str) -> Optional[Dict]:
        """
        Get weather data for a specific island.
        
        Args:
            island_key (str): Identifier for the island
            
        Returns:
            dict: Weather data if available, None if island_key is invalid
        """
        # First check if island exists
        if island_key not in self.db.coordinates:
            logger.log_err(f"Invalid island key: {island_key}. Available islands: {list(self.db.coordinates.keys())}")
            return None
            
        now = time.time()
        
        # Check if we need to update
        if (island_key not in self.db.last_updates or 
            now - self.db.last_updates.get(island_key, 0) > WEATHER_UPDATE_INTERVAL):
            self._update_weather(island_key)
            
        return self.db.weather_systems.get(island_key)
    
    def _update_weather(self, island_key: str) -> None:
        """Update weather data for an island."""
        if island_key not in self.db.coordinates:
            logger.log_err(f"No coordinates found for island {island_key}")
            return
            
        lat, lon = self.db.coordinates[island_key]
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
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
                self.db.weather_systems[island_key] = response.json()['current']
                self.db.last_updates[island_key] = time.time()
        except Exception as e:
            logger.log_err(f"Weather API error for {island_key}: {e}")

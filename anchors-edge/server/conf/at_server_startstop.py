"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence.
"""

from evennia.utils import logger, create
import os
from pathlib import Path

def at_server_start():
    """
    This is called every time the server starts up.
    """
    try:
        # Create last_wipe.py if it doesn't exist
        last_wipe_path = Path("server/conf/last_wipe.py")
        if not last_wipe_path.exists():
            from datetime import datetime
            timestamp = int(datetime.now().timestamp() * 1000)
            with open(last_wipe_path, 'w') as f:
                f.write(f"LAST_WIPE = {timestamp}  # Timestamp in milliseconds\n")
            logger.log_info("Created new last_wipe.py file.")
            
        # Initialize global settings script
        from evennia.utils import search
        from typeclasses.scripts import GlobalSettingsScript, IslandWeatherScript
        
        # Initialize global settings script
        settings_script = search.search_script("global_settings")
        if not settings_script:
            logger.log_info("Creating global settings script...")
            settings_script = create.create_script(GlobalSettingsScript)
            if settings_script:
                logger.log_info("Global settings script initialized successfully.")
            else:
                logger.log_err("Failed to create global settings script!")
        else:
            logger.log_info("Global settings script already exists.")
            
        # Initialize weather system script
        weather_script = search.search_script("weather_controller")
        if not weather_script:
            logger.log_info("Creating weather system script...")
            script = create.create_script(IslandWeatherScript)
            if script:
                logger.log_info("Weather system initialized successfully.")
            else:
                logger.log_err("Failed to create weather system script!")
        else:
            logger.log_info("Weather system script already exists.")
            
    except Exception as e:
        logger.log_err(f"Error during server startup initialization: {e}")

def at_server_stop():
    """
    This is called just before the server is shut down fully.
    """
    try:
        from evennia.utils import search
        # Properly save weather data before shutdown
        weather_script = search.search_script("weather_controller")
        if weather_script:
            weather_script[0].at_server_shutdown()
    except Exception as e:
        logger.log_err(f"Error during weather system shutdown: {e}")

def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass

def at_server_reload_stop():
    """
    This is called only time the server stops during a reload.
    """
    pass

def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass

def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass

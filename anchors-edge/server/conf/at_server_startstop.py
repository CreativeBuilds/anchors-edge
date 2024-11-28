"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence.
"""

from evennia.utils import logger

def at_server_start():
    """
    This is called every time the server starts up.
    """
    try:
        from evennia import create_script
        from evennia.utils import search
        
        # Check if weather script exists
        weather_script = search.search_script("weather_controller")
        if not weather_script:
            logger.log_info("Creating weather system script...")
            # Use string path instead of direct class reference
            script = create_script(
                "typeclasses.scripts.IslandWeatherScript",
                key="weather_controller",
                persistent=True,
                autostart=True
            )
            if script:
                logger.log_info("Weather system initialized successfully.")
            else:
                logger.log_err("Failed to create weather system script!")
        else:
            logger.log_info("Weather system script already exists.")
            
    except Exception as e:
        logger.log_err(f"Error initializing weather system: {e}")

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

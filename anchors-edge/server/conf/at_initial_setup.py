"""
At_initial_setup module template

Custom at_initial_setup method. This allows you to hook special
modifications to the initial server startup process. Note that this
will only be run once - when the server starts up for the very first
time! It is called last in the startup process and can thus be used to
overload things that happened before it.

The module must contain a global function at_initial_setup().  This
will be called without arguments. Note that tracebacks in this module
will be QUIETLY ignored, so make sure to check it well to make sure it
does what you expect it to.

"""

from evennia.utils import logger, create
from evennia.objects.models import ObjectDB

def at_initial_setup():
    """
    This is called only once, when the server starts up for the very first time.
    """
    try:
        # Create weather system
        from typeclasses.scripts import IslandWeatherScript
        weather_script = create.create_script(IslandWeatherScript)
        if weather_script:
            logger.log_info("Weather system initialized successfully.")
        else:
            logger.log_err("Failed to create weather system!")
            
        # Set up Limbo as default spawn until buildworld command changes it
        limbo = ObjectDB.objects.get_id(2)  # Limbo is always #2
        if limbo:
            # Update settings.py directly
            settings_path = "server/conf/settings.py"
            with open(settings_path, 'r') as f:
                lines = f.readlines()
            
            with open(settings_path, 'w') as f:
                for line in lines:
                    if line.startswith('DEFAULT_HOME'):
                        f.write('DEFAULT_HOME = "#2"\n')
                    elif line.startswith('START_LOCATION'):
                        f.write('START_LOCATION = "#2"\n')
                    else:
                        f.write(line)
                        
            logger.log_info("Set Limbo as initial spawn point.")
            
    except Exception as e:
        logger.log_err(f"Error during initial setup: {e}")

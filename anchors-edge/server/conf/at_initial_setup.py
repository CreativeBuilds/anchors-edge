"""
At_initial_setup module that creates essential rooms and objects.
"""

from evennia import create_object, settings, search_object
from evennia.utils import logger
from typeclasses.rooms.base import WeatherAwareRoom
from typeclasses.rooms.character_select import CharacterSelectRoom
from typeclasses.rooms.tavern import TavernRoom
from typeclasses.exits import Exit
from django.conf import settings as django_settings
from evennia.commands.default.batchprocess import CmdBatchCommands

def at_initial_setup():
    """
    Custom at_initial_setup hook.
    """
    try:
        # Get the existing Limbo room
        default_home = search_object("Limbo")[0]
        
        # Update the DEFAULT_HOME setting
        settings.DEFAULT_HOME = f"#{default_home.id}"
        django_settings.DEFAULT_HOME = f"#{default_home.id}"
        
        # Create character selection room
        character_select = create_object(
            typeclass=CharacterSelectRoom,
            key="Character Selection",
            home=default_home,
            report_to=None
        )
        character_select.db.desc = "Welcome to Anchors Edge! Here you can create or select your character."

        
    except Exception as e:
        logger.log_err(f"Error in at_initial_setup: {e}")
        logger.log_trace()
        raise

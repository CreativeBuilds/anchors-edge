"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia.commands.command import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.mirror import Mirror

class CmdDescribeSelf(MuxCommand):
    """
    Describe yourself while looking in the mirror
    
    Usage:
      describe <description>
      desc <description>
    
    Sets your character's description that others see when looking at you.
    This command only works when looking in a mirror.
    """
    key = "describe"
    aliases = ["desc"]
    locks = "cmd:all()"
    
    def func(self):
        """Handle the description setting"""
        caller = self.caller
        
        # First check if there's a mirror in the room
        mirror = caller.location.search("mirror", typeclass=Mirror)
        if not mirror:
            caller.msg("You need to be near a mirror to describe yourself.")
            return
            
        if not self.args:
            caller.msg("Usage: describe <description>")
            return
            
        # Set the description
        desc = self.args.strip()
        caller.db.desc = desc
        caller.msg(f"You look in the mirror and see: {desc}")

class BriefCommand(MuxCommand):
    """
    Toggle brief room descriptions
    
    Usage:
      brief
    
    Switches between normal and brief room descriptions.
    Brief descriptions show only essential information about the room.
    """
    key = "brief"
    aliases = ["br"]
    locks = "cmd:all()"
    
    def func(self):
        """Toggle brief mode"""
        caller = self.caller
        
        # Initialize brief_mode if it doesn't exist
        if not hasattr(caller.db, "brief_mode"):
            caller.db.brief_mode = False
            
        # Toggle brief mode
        if caller.db.brief_mode:
            caller.db.brief_mode = False
            caller.msg("|GBrief mode disabled.|n Room descriptions will now show full details.")
        else:
            caller.db.brief_mode = True
            caller.msg("|GBrief mode enabled.|n Room descriptions will now be shortened.")

class CmdRegenRoom(MuxCommand):
    """
    Force regenerate a room's descriptions
    
    Usage:
      regen [room]
    
    Forces a weather-aware room to regenerate all its descriptions
    and clear its caches. If no room is specified, regenerates the
    current room.
    
    Admin only command.
    """
    key = "regen"
    aliases = ["regenerate"]
    locks = "cmd:perm(Admin)"
    
    def func(self):
        """Handle the regeneration"""
        caller = self.caller
        
        # Get the target room
        if self.args:
            target = caller.search(self.args.strip())
            if not target:
                return
        else:
            target = caller.location
            
        # Check if it's a weather-aware room
        if not hasattr(target, 'update_weather'):
            caller.msg("This room is not weather-aware.")
            return
            
        # Clear all caches and force update
        target.db.cached_descriptions = {
            "dawn": None,
            "day": None,
            "dusk": None,
            "night": None
        }
        target.db.cache_timestamps = {
            "dawn": 0,
            "day": 0,
            "dusk": 0,
            "night": 0
        }
        target.db.brief_desc = None
        target.db.weather_data = {}
        
        # Force an update
        target.update_description()
        
        caller.msg(f"|GForced regeneration of descriptions for {target.key}.|n")

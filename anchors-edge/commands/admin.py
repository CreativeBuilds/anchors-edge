"""
Admin commands for managing players and characters.
"""

from evennia import Command
from evennia.utils import search
from evennia.objects.models import ObjectDB

class CmdRespawn(Command):
    """
    Respawn a player at the world spawn point.
    
    Usage:
        @respawn <player>
    
    Examples:
        @respawn Bob
        @respawn #123
    """
    
    key = "@respawn"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.msg("Usage: @respawn <player>")
            return
            
        # Try to find the target player
        target = self.caller.search(self.args)
        if not target:
            return
            
        try:
            # Get spawn location from settings.py
            from server.conf.settings import START_LOCATION
            from evennia.utils import search
            
            # Convert dbref string to actual object
            spawn_dbref = START_LOCATION.strip('#')
            spawn_location = search.search_object(f"#{spawn_dbref}", exact=True)
            
            if not spawn_location:
                self.msg("|rError: Spawn location not found.|n")
                return
            
            spawn_location = spawn_location[0]
            
            # Store old location for message
            old_location = target.location
            
            # Move player to spawn
            target.location = spawn_location
            
            # Notify everyone involved
            self.msg(f"|gMoved {target.name} to spawn location ({spawn_location.name}).|n")
            target.msg(f"|yYou have been moved to {spawn_location.name} by {self.caller.name}.|n")
            if old_location:
                old_location.msg_contents(f"{target.name} vanishes in a flash of light.", exclude=[target])
            spawn_location.msg_contents(f"{target.name} appears in a flash of light.", exclude=[target])
            
        except Exception as e:
            self.msg(f"|rError respawning player: {e}|n") 
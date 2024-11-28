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
            # Get the world spawn location
            GLOBAL_SCRIPTS = ObjectDB.objects.get_id(1)
            spawn_location = GLOBAL_SCRIPTS.db.default_spawn_location
            
            if not spawn_location:
                self.msg("|rError: World spawn location not set.|n")
                return
                
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
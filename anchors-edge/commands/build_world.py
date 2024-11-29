"""
Command module for building the game world.
This has been replaced by batch commands in world/batch_cmds.ev
"""

from evennia import Command

class CmdBuildWorld(Command):
    """
    Build the game world using batch commands.
    
    Usage:
        buildworld
        
    This command has been replaced by batch commands.
    Please use @batchcommand world.batch_cmds instead.
    """
    
    key = "buildworld"
    locks = "cmd:perm(Admin)"
    help_category = "Building"
    
    def func(self):
        """Execute command."""
        self.caller.msg("This command has been deprecated. Please use '@batchcommand world.batch_cmds' instead.") 
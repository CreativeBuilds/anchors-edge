"""
Unloggedin commands for Anchors Edge.
These commands are available before a player logs in.
"""

from evennia.commands.command import Command
from evennia.commands.cmdhandler import CMD_LOGINSTART
from server.conf.connection_screens import get_connection_screen

class CmdUnloggedinLook(Command):
    """
    Look command for unloggedin state.
    This is called by the server when the player first connects.
    """
    key = CMD_LOGINSTART
    aliases = ["look", "l"]
    locks = "cmd:all()"
    
    def func(self):
        """Show the dynamic connection screen."""
        connection_screen = get_connection_screen()
        if connection_screen:
            self.msg(connection_screen) 
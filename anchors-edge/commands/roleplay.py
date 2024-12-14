"""
This module contains commands related to roleplay status management.
"""

from evennia.commands.default.muxcommand import MuxCommand

class CmdRoleplayStatus(MuxCommand):
    """
    Set your character's roleplay status.

    Usage:
      rstatus
      rstatus off
      rstatus <status description>

    This command allows you to set a status for your character that will show up
    in the room description of what your character is doing. The status will
    automatically clear when you move.

    Maximum length: 50 characters

    Examples:
      rstatus sitting in a chair
      rstatus leaning against the wall
      rstatus off

    Note: Your roleplay status will automatically turn off if you move.
          Also, if you are drunk, your rstatus will be modified to show that.
    """
    key = "rstatus"
    aliases = ["rs"]
    locks = "cmd:all()"
    help_category = "Roleplay"

    def func(self):
        """Execute command."""
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            # Show current status
            current_status = caller.get_rstatus()
            if current_status:
                caller.msg(f"Your current roleplay status: {current_status}")
            else:
                caller.msg("You have no roleplay status set.")
            return

        if args.lower() == "off":
            # Clear status
            success, msg = caller.set_rstatus(None)
            caller.msg(msg)
            return

        # Set new status
        success, msg = caller.set_rstatus(args)
        caller.msg(msg)


class CmdOptionalStatus(MuxCommand):
    """
    Set your character's optional status.

    Usage:
      ostatus
      ostatus off
      ostatus <status description>

    This command allows you to set an optional current moving description of your
    character that people will see when they look at you. This description is
    only for short periods and is NOT to replace your description, tattoos,
    hair color, eye color, piercings, and the like.

    Maximum length: 180 characters

    Examples:
      ostatus His hair is wild and windblown from a day at the ocean.
      ostatus He has a long cut from his neck to his forearm.
      ostatus off

    Note: This is for temporary descriptive elements only.
    """
    key = "ostatus"
    aliases = ["os"]
    locks = "cmd:all()"
    help_category = "Roleplay"

    def func(self):
        """Execute command."""
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            # Show current status
            current_status = caller.get_ostatus()
            if current_status:
                caller.msg(f"Your current optional status: {current_status}")
            else:
                caller.msg("You have no optional status set.")
            return

        if args.lower() == "off":
            # Clear status
            success, msg = caller.set_ostatus(None)
            caller.msg(msg)
            return

        # Set new status
        success, msg = caller.set_ostatus(args)
        caller.msg(msg) 
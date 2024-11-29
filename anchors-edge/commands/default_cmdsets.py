"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds
from commands.command import (
    CmdDescribeSelf, BriefCommand, CmdRegenRoom, 
    SayCommand, CmdInventory, GiveCommand,
    CmdEat, CmdDrink, CmdChug, CmdIdentify  # Add CmdIdentify
)
from commands.build_world import CmdBuildWorld, CmdListObjects
from commands.admin import CmdRespawn
from evennia import CmdSet
from evennia import Command


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdDescribeSelf())
        self.add(BriefCommand())
        self.add(CmdRegenRoom())
        self.add(SayCommand())
        self.add(CmdInventory())
        self.add(GiveCommand())
        self.add(CmdEat())      # Add eat command
        self.add(CmdDrink())    # Add drink command
        self.add(CmdChug())     # Add chug command
        self.add(CmdBuildWorld())
        self.add(CmdListObjects())
        self.add(CmdRespawn())
        self.add(CmdIdentify())  # Add the new identify command
        

class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class CmdSmell(Command):
    """
    Smell the flowers
    
    Usage:
      smell flowers
    """
    key = "smell"
    aliases = ["sniff"]
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("What do you want to smell?")
            return
            
        target = self.caller.search(self.args.strip())
        if not target:
            return
            
        if hasattr(target.db, "smell_desc"):
            self.caller.msg(target.db.smell_desc)
        else:
            self.caller.msg(f"You smell {target.name}, but notice nothing special.")

class FlowerCmdSet(CmdSet):
    """
    Cmdset for flower objects.
    """
    key = "flower_cmdset"
    
    def at_cmdset_creation(self):
        """Called when cmdset is first created."""
        self.add(CmdSmell())

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
    CmdSay, CmdLsay, CmdInventory, GiveCommand,
    CmdEat, CmdDrink, CmdChug, SmellCommand,
    TasteCommand, CmdIdentify, CmdWho, CmdLook,
    EmoteCommand
)

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
        self.add(CmdSay())
        self.add(CmdLsay())
        self.add(CmdInventory())
        self.add(GiveCommand())
        self.add(CmdEat())
        self.add(CmdDrink())
        self.add(CmdChug())
        self.add(SmellCommand())
        self.add(TasteCommand())
        self.add(CmdIdentify())
        self.add(CmdWho())
        self.add(CmdLook())
        # Replace the default emote command with our custom one
        self.remove("emote")  # Remove by command key
        self.add(EmoteCommand())


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
        
        # Character selection commands
        self.add(CmdCharList())
        self.add(CmdCharSelect())
        self.add(CmdCreateCharacter())
        self.add(CmdSignout())
        self.add(CmdChangelog())
        self.add(CmdQuit())
        self.add(CmdWho())
        
        
        # Admin commands
        self.add(CmdCleanupAccounts())
        self.add(CmdResetAccount())
        self.add(CmdDebugCharacter())
        self.add(CmdLastWipe())
        self.add(CmdResetWorld())


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
        # Add our custom unloggedin look command
        self.add(CmdUnloggedinLook())


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
        """
        super().at_cmdset_creation()

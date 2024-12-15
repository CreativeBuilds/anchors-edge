"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.
"""

from evennia.commands.default.cmdset_character import CharacterCmdSet as DefaultCharacterCmdSet
from evennia.commands.default.cmdset_account import AccountCmdSet as DefaultAccountCmdSet
from evennia.commands.default.cmdset_session import SessionCmdSet as DefaultSessionCmdSet
from evennia.commands.default.cmdset_unloggedin import UnloggedinCmdSet as DefaultUnloggedinCmdSet

from commands.build_world import CmdBuildWorld
from commands.character import (
    CmdCharList, CmdCharSelect, CmdSignout,
    CmdIntro, CmdLongIntro, CmdQuit
)
from commands.chargen import CmdCreateCharacter
from commands.admin import (
    CmdCleanupAccounts, CmdResetAccount, CmdDebugCharacter,
    CmdLastWipe, CmdChangelog, CmdResetWorld
)
from commands.command import CmdWho, CmdLook, CmdSay, CmdLsay
from commands.emote import CmdEmote, CmdPmote, CmdOmote, CmdTmote, CmdEmoteList
from commands.unloggedin import CmdUnloggedinLook
from commands.social import add_social_commands
from commands.roleplay import CmdRoleplayStatus, CmdOptionalStatus


class CharacterCmdSet(DefaultCharacterCmdSet):
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
        self.add(CmdBuildWorld())
        # Add intro commands
        self.add(CmdIntro())
        self.add(CmdLongIntro())
        self.add(CmdQuit())
        self.add(CmdWho())
        # Add the emote commands
        self.add(CmdEmote())
        self.add(CmdPmote())
        self.add(CmdOmote())
        self.add(CmdTmote())
        self.add(CmdEmoteList())
        self.add(CmdLook())
        self.add(CmdSay())
        self.add(CmdLsay())
        # Add roleplay status commands
        self.add(CmdRoleplayStatus())
        self.add(CmdOptionalStatus())
        add_social_commands(self)


class AccountCmdSet(DefaultAccountCmdSet):
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


class UnloggedinCmdSet(DefaultUnloggedinCmdSet):
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


class SessionCmdSet(DefaultSessionCmdSet):
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

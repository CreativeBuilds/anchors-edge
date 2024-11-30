"""
Admin commands for managing players and characters.
"""

from evennia import Command
from evennia.utils import search
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB

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

class CmdCleanupAccounts(Command):
    """
    Admin command to clean up account character lists
    
    Usage:
        @cleanupaccounts
    """
    key = "@cleanupaccounts"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """Execute command."""
        count = 0
        for account in AccountDB.objects.all():
            if hasattr(account.db, '_playable_characters'):
                valid_characters = []
                for char in account.db._playable_characters:
                    if char and hasattr(char, 'is_typeclass') and char.is_typeclass('typeclasses.characters.Character'):
                        valid_characters.append(char)
                if len(valid_characters) != len(account.db._playable_characters):
                    count += 1
                    account.db._playable_characters = valid_characters
                    
        self.caller.msg(f"Cleaned up {count} accounts.") 

class CmdResetAccount(Command):
    """
    Admin command to reset an account's character list
    
    Usage:
        @resetaccount <account>
    """
    key = "@resetaccount"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("Usage: @resetaccount <account>")
            return
            
        # Find the account
        from evennia.accounts.models import AccountDB
        account = AccountDB.objects.filter(username__iexact=self.args.strip()).first()
        
        if not account:
            self.caller.msg(f"Account '{self.args}' not found.")
            return
            
        # Reset their character list
        account.db._playable_characters = []
        self.caller.msg(f"Reset character list for account {account.username}") 
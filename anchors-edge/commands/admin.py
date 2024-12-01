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

class CmdDebugCharacter(Command):
    """
    Debug character links and permissions
    
    Usage:
        @debugchar <character name>
    """
    key = "@debugchar"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """Execute command."""
        if not self.args:
            self.caller.msg("Usage: @debugchar <character name>")
            return
            
        # Search for character
        char = search.search_object(self.args.strip())
        if not char:
            self.caller.msg("Character not found.")
            return
            
        char = char[0]
        self.msg(f"Debug info for character: {char.key}")
        self.msg(f"Object ID: {char.id}")
        self.msg(f"Typeclass: {char.typeclass_path}")
        self.msg(f"Location: {char.location}")
        self.msg(f"Home: {char.home}")
        self.msg(f"Permissions: {char.permissions.all()}")
        self.msg(f"Locks: {char.locks}")
        
        if hasattr(char.db, 'account'):
            self.msg(f"Linked account: {char.db.account}")
        else:
            self.msg("No account link found in char.db.account")
            
        # Check which accounts have this character in their playable_characters
        for account in AccountDB.objects.all():
            if hasattr(account.db, '_playable_characters'):
                if char in account.db._playable_characters:
                    self.msg(f"Found in account's playable_characters: {account}") 

class CmdLastWipe(Command):
    """
    Check when the last server wipe occurred.
    
    Usage:
        @lastwipe
    """
    key = "@lastwipe"
    locks = "cmd:all()"  # Everyone can check this
    help_category = "Info"
    
    def func(self):
        """Execute command."""
        try:
            from server.conf.last_wipe import LAST_WIPE
            from datetime import datetime
            
            now = int(datetime.now().timestamp() * 1000)
            diff = now - LAST_WIPE
            
            # Convert to seconds
            seconds = int(diff / 1000)
            
            if seconds < 60:
                time_str = f"{seconds} seconds"
            elif seconds < 3600:
                minutes = seconds // 60
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif seconds < 86400:
                hours = seconds // 3600
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            elif seconds < 604800:
                days = seconds // 86400
                time_str = f"{days} day{'s' if days != 1 else ''}"
            else:
                weeks = seconds // 604800
                time_str = f"{weeks} week{'s' if weeks != 1 else ''}"
                
            self.caller.msg(f"Time since last server wipe: {time_str}")
            
        except Exception as e:
            self.caller.msg("Unable to determine last wipe time.") 

class CmdChangelog(Command):
    """
    View the game's changelog.
    Shows what's new and what has changed in the game.
    
    Usage:
        changelog [version]
        
    Examples:
        changelog        - Show full changelog
        changelog 0.0.1  - Show changes for version 0.0.1
    """
    key = "changelog"
    aliases = ["changes", "updates"]
    locks = "cmd:all()"  # Everyone can view changelog
    help_category = "General"  # Changed from Info to General
    
    def func(self):
        """Execute command."""
        try:
            with open("CHANGELOG", 'r') as f:
                changelog = f.read()
            
            if self.args:
                # Show specific version
                version = self.args.strip()
                sections = changelog.split('v')
                for section in sections:
                    if section.startswith(version):
                        # Color the version number blue
                        section = section.replace(version, f"|c{version}|n", 1)
                        self.caller.msg(f"v{section}")
                        return
                self.caller.msg(f"Version v{version} not found in changelog.")
            else:
                # Show full changelog with colored version numbers
                self.caller.msg("|wAnchors Edge Changelog|n")
                self.caller.msg("|y(Newest to Oldest)|n")
                self.caller.msg("-" * 50)
                
                # Show full changelog with colored version numbers
                colored_log = changelog.replace('v', '|cv')
                colored_log = colored_log.replace('\n-', '|n\n-')
                self.caller.msg(colored_log)
                
                self.caller.msg("-" * 50)
                self.caller.msg("Use |wchangelog <version>|n to see a specific version.")
                
        except FileNotFoundError:
            self.caller.msg("Changelog file not found.")
        except Exception as e:
            self.caller.msg(f"Error reading changelog: {e}") 
"""
Cleanup script for resetting the game world while preserving accounts.
"""

from django.conf import settings
from evennia import DefaultScript
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB
from evennia.utils import search

class WorldCleanupScript(DefaultScript):
    """Script to clean up the world while preserving accounts."""
    
    def at_script_creation(self):
        """Set up the script."""
        self.key = "world_cleanup"
        self.desc = "Cleans up world while preserving accounts"
        self.persistent = True
        
    def clean_world(self):
        """
        Clean up the world, preserving accounts but moving their characters to Limbo.
        """
        limbo = search.search_object('#2')[0]  # Limbo is always #2
        
        # Get all accounts to preserve them
        accounts = AccountDB.objects.all()
        
        # Store account-character links before cleanup
        char_map = {}
        for account in accounts:
            if account.db._last_puppet:
                char_map[account.id] = account.db._last_puppet
        
        # Delete all objects except accounts and Limbo
        for obj in ObjectDB.objects.all():
            # Skip accounts and Limbo
            if obj.id == 2 or hasattr(obj, 'is_account'):
                continue
            obj.delete()
            
        # Recreate characters for accounts and place them in Limbo
        for account in accounts:
            if account.id in char_map:
                from evennia import create_object
                char = create_object(
                    typeclass=settings.BASE_CHARACTER_TYPECLASS,
                    key=char_map[account.id].key,
                    location=limbo,
                    home=limbo,
                    permissions=["Player"],
                    locks="call:false();control:pid({account_id}) or perm(Admin);delete:pid({account_id}) or perm(Admin)".format(
                        account_id=account.id
                    ),
                )
                # Link character to account
                char.db.desc = char_map[account.id].db.desc
                account.db._last_puppet = char 
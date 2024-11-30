"""
Cleanup script for resetting the game world while preserving accounts.
"""

from django.conf import settings
from evennia import DefaultScript, create_object
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB
from evennia.utils import search
from evennia.commands.default.cmdset_character import CharacterCmdSet

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
        
        # Store account-character links and data before cleanup
        char_map = {}
        for account in accounts:
            if account.db._last_puppet:
                char = account.db._last_puppet
                char_map[account.id] = {
                    'key': char.key,
                    'desc': char.db.desc,
                    'cmdsets': [cmdset.path for cmdset in char.cmdset.all()],
                    'permissions': char.permissions.all()
                }
        
        # Delete all objects except accounts and Limbo
        for obj in ObjectDB.objects.all():
            # Skip accounts and Limbo
            if obj.id == 2 or hasattr(obj, 'is_account'):
                continue
            obj.delete()
            
        # Recreate characters for accounts and place them in Limbo
        for account in accounts:
            if account.id in char_map:
                char_data = char_map[account.id]
                char = create_object(
                    typeclass=settings.BASE_CHARACTER_TYPECLASS,
                    key=char_data['key'],
                    location=limbo,
                    home=limbo,
                    permissions=["Player"] + list(char_data['permissions']),
                    locks="call:false();control:pid({account_id}) or perm(Admin);delete:pid({account_id}) or perm(Admin)".format(
                        account_id=account.id
                    ),
                )
                
                # Restore character data
                char.db.desc = char_data['desc']
                
                # Ensure default character cmdset is added
                char.cmdset.add(CharacterCmdSet, permanent=True)
                
                # Add any additional stored cmdsets
                for cmdset_path in char_data['cmdsets']:
                    if cmdset_path != CharacterCmdSet.path:
                        try:
                            char.cmdset.add(cmdset_path, permanent=True)
                        except Exception as e:
                            print(f"Error adding cmdset {cmdset_path}: {e}")
                
                # Link character to account
                account.db._last_puppet = char
                
                # Make sure character is properly initialized
                char.at_object_creation()
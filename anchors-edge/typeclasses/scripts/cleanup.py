"""
Cleanup script for resetting the game world
"""
from evennia import DefaultScript
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB
from django.conf import settings
from evennia import create_object
from evennia.commands.default.cmdset_character import CharacterCmdSet

class WorldCleanupScript(DefaultScript):
    """Script for cleaning up and resetting the game world"""
    
    def clean_world(self):
        """Clean up the game world"""
        # Get limbo
        limbo = ObjectDB.objects.get_id(2)
        if not limbo:
            print("Error: Could not find Limbo (#2)")
            return
            
        # Store character data before deletion
        accounts = AccountDB.objects.all()
        char_map = {}
        
        for account in accounts:
            if hasattr(account.db, '_playable_characters'):
                for char in account.db._playable_characters:
                    if char:
                        char_map[account.id] = {
                            'key': char.key,
                            'desc': char.db.desc if hasattr(char.db, 'desc') else '',
                            'permissions': char.permissions.all(),
                            'cmdsets': [cmdset.path for cmdset in char.cmdset.all()]
                        }
        
        # Delete all objects except system rooms (limbo etc)
        for obj in ObjectDB.objects.all():
            if obj.id > 2:  # Keep #1 (void) and #2 (limbo)
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
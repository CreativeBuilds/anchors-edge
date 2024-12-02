"""
Character Selection Room
"""
from evennia import DefaultRoom

class CharacterSelectRoom(DefaultRoom):
    """
    This room represents the out-of-character character selection space.
    Players will be placed here when they log in until they select a character.
    """
    
    def at_object_creation(self):
        """Called when room is first created"""
        super().at_object_creation()
        self.db.desc = """
|c== Character Selection ==|n

You are in a formless void between realities. This is where you must choose 
your vessel in the world - your character through which you will experience 
the game.

|wAvailable Commands:|n
  |ycharlist|n  - List your available characters
  |ycharcreate|n - Create a new character
  |ycharselect|n - Select a character to play

You must either select an existing character or create a new one to enter 
the game world.
"""
        
        # Lock down most commands in this room with proper lock syntax
        self.locks.add("call:false();puppet:perm(Admin)")
        
    def return_appearance(self, looker, **kwargs):
        """
        This is called when someone looks at this room.
        """
        # For sessions without a puppet (accounts in character selection)
        if hasattr(looker, 'account') and looker.account:
            # Let the account's at_look handle the display
            return ""
            
        # For normal characters (shouldn't be here anyway)
        return "|rYou shouldn't be here.|n"
        
    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """
        Called when an object enters this room.
        """
        # Prevent characters from entering this room
        if hasattr(moved_obj, 'account') and moved_obj.account:
            if moved_obj.location:
                moved_obj.location = moved_obj.home or '#2'
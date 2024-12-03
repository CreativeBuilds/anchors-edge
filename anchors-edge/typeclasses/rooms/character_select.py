"""
Character Selection Room
"""
from evennia import DefaultRoom
from evennia.utils import evtable

class CharacterSelectRoom(DefaultRoom):
    """
    This room represents the character selection screen.
    """
    
    def at_object_creation(self):
        """Called when room is first created"""
        super().at_object_creation()
        # Lock down most commands in this room
        self.locks.add("call:false();puppet:false()")
    
    def return_appearance(self, looker, **kwargs):
        """
        This is called when someone looks at the room.
        """
        # Ensure we're working with the account
        if hasattr(looker, 'account') and looker.account:
            account = looker.account
        else:
            account = looker

        text = "|c== Character Selection ==|n\n"
        
        if not account.db._playable_characters:
            text += "\nYou have no characters yet. Use |wcharcreate|n to make one."
            return text
            
        # Create table of characters
        table = evtable.EvTable(
            "|wName|n",
            "|wRace|n", 
            "|wGender|n",
            "|wBackground|n",
            border="header"
        )
        
        for char in account.db._playable_characters:
            table.add_row(
                char.key,
                char.db.race + (f" ({char.db.subrace})" if char.db.subrace else ""),
                char.db.gender or "Unknown",
                char.db.background or "Unknown"
            )
            
        text += "\n" + str(table)
        text += "\n\nAvailable commands:"
        text += "\n  |wcharselect <name>|n - Play as a character"
        text += "\n  |wcharcreate|n - Create a new character"
        text += "\n  |wchardelete <name>|n - Delete a character"
        
        return text

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """When an object enters the room"""
        if moved_obj.has_account:
            # Get the account
            account = moved_obj.account
            
            # Make sure we're in OOC mode
            account.execute_cmd('@ooc')
            
            # Show the character selection screen
            account.execute_cmd("look")
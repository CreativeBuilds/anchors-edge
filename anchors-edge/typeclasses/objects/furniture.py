"""
Furniture objects for the game.
"""

from evennia.objects.objects import DefaultObject
from textwrap import fill
from django.conf import settings

class Furniture(DefaultObject):
    """Base class for furniture items."""
    
    def at_object_creation(self):
        """Called when furniture is first created."""
        super().at_object_creation()
        self.locks.add("get:false()")  # Furniture can't be picked up
        # Set the description from base_desc if it exists
        if hasattr(self, 'db') and hasattr(self.db, 'base_desc'):
            self.db.desc = self.db.base_desc
        
    def get_display_name(self, looker, **kwargs):
        """Get the display name of the furniture."""
        if looker.locks.check_lockstring(looker, "perm(Admin) or perm(Builder)"):
            return f"|w|hthe {self.key}(#{self.id})|n"
        return f"|w|hthe {self.key}|n"
        
    def return_appearance(self, looker):
        """Format the description with proper spacing."""
        name = self.get_display_name(looker)
        desc = self.db.desc if self.db.desc else "You see nothing special."
        
        # Format with proper spacing - only one newline before title
        # and one after, then wrap the description
        width = getattr(settings, 'ROOM_DESCRIPTION_WIDTH', 78)
        formatted_desc = fill(desc, width=width, expand_tabs=True, replace_whitespace=False)
        
        return f"|/{name}|/{formatted_desc}|/"

class Bed(Furniture):
    """A bed for sleeping."""
    
    def at_object_creation(self):
        """Set up the bed."""
        self.db.base_desc = (
            "A well-made bed with crisp linen sheets and plump pillows invites rest. The sturdy "
            "wooden frame is polished to a warm glow, and a soft woolen blanket is folded neatly "
            "at the foot."
        )
        super().at_object_creation()
        self.db.smell_desc = "The bed linens smell fresh and clean, with a hint of lavender."

class Desk(Furniture):
    """A desk that responds to lighting conditions."""
    
    def at_object_creation(self):
        """Set up the desk."""
        self.db.base_desc = (
            "A sturdy wooden desk sits beneath the window, its surface well-maintained and ready "
            "for use. Several drawers offer storage, while its position provides an excellent "
            "view while working or writing."
        )
        super().at_object_creation()
        self.db.smell_desc = "The wood has a pleasant, polished scent with hints of beeswax."

class Chair(Furniture):
    """A chair for sitting."""
    
    def at_object_creation(self):
        """Set up the chair."""
        self.db.base_desc = (
            "A comfortable wooden chair with a cushioned seat accompanies the desk. Its design "
            "offers good support while remaining pleasant for extended use. The woodwork shows "
            "signs of expert craftsmanship."
        )
        super().at_object_creation()
        self.db.smell_desc = "The chair has a faint woody scent with traces of polish." 
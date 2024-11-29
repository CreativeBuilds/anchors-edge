"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from random import choice

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    pass


class LockedDoor(Exit):
    """A locked door that can't be opened yet"""
    def at_traverse(self, traversing_object, target_location, **kwargs):
        """Called when someone tries to traverse this object."""
        if self.location.db.door_locked:
            traversing_object.msg("The door is locked tight. No amount of pushing seems to budge it.")
            return
        super().at_traverse(traversing_object, target_location, **kwargs)


class StaffExit(DefaultExit):
    """An exit that only staff can see and use."""
    
    def at_object_creation(self):
        """Called when exit is created."""
        super().at_object_creation()
        # Allow kitchen staff or admins to traverse
        self.locks.add("traverse: tag(kitchen_staff) or perm(Admin)")
        
    def return_appearance(self, looker):
        """Only show exit to staff or admins."""
        if looker.tags.has("kitchen_staff") or looker.permissions.check("Admin"):
            return super().return_appearance(looker)
        return ""
        
    def at_failed_traverse(self, traversing_object):
        """
        Called when someone who can't use the exit tries to use it.
        """
        # List of possible responses when non-staff try to enter
        responses = [
            "A busy server emerges just as you reach for the door, politely but firmly blocking the way.",
            "The kitchen door swings open as a cook exits, giving you a questioning look that makes you reconsider entering.",
            "A stern-looking woman in an apron steps out, shaking her head. 'Patrons aren't allowed in the kitchen, dear.'",
            "The sounds of busy kitchen work drift out as someone exits, making it clear this is a staff-only area.",
            "A harried-looking server deftly steps between you and the door. 'Can I help you find something?'",
        ]
        traversing_object.msg(choice(responses))

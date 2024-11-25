"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

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

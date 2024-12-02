"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit


class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets up default exit locks
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed
     at_pre_traverse(**kwargs) - called just before traversing
     at_post_traverse(**kwargs) - called just after traversing
     at_after_traverse(**kwargs) - called after traversing
     at_failed_traverse(**kwargs) - called if traversal fails
     at_msg_receive(**kwargs) - called if someone tries to communicate through exit
     at_desc(**kwargs) - called when exit is looked at
    """

    pass

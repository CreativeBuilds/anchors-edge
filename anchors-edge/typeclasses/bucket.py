from evennia import DefaultObject

class WaterBucket(DefaultObject):
    """
    A bucket of water that can be used as a reflection surface
    """
    def at_object_creation(self):
        """Called when object is first created"""
        self.locks.add("get:false()")
        self.db.desc = (
            "A simple wooden bucket filled with water. Despite the ship's gentle "
            "swaying, the water's surface is calm enough to see your reflection."
        ) 
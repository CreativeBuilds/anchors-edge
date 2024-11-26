"""
Items module for creating various game items.
"""

from evennia.objects.objects import DefaultObject

class Item(DefaultObject):
    """Base item class"""
    def at_object_creation(self):
        """Called when item is first created"""
        super().at_object_creation()
        self.db.desc = ""
        self.locks.add("get:all();drop:all()")

class Drink(Item):
    """Class for drink items"""
    def at_object_creation(self):
        """Set up drink-specific attributes"""
        super().at_object_creation()
        self.db.drink_type = ""  # ale, wine, etc.
        self.db.health = 10      # how many drinks left
        self.db.is_drink = True
        self.db.alcohol_content = 0  # Amount of alcohol per sip
        
        # Default alcohol content for different drinks
        self.db.alcohol_levels = {
            "water": 0,
            "juice": 0,
            "ale": 1,
            "beer": 1,
            "wine": 2,
            "mead": 3,
            "strong spirits": 4
        }
        
    def set_type(self, drink_type):
        """Set drink type and appropriate alcohol content"""
        self.db.drink_type = drink_type
        self.db.alcohol_content = self.db.alcohol_levels.get(drink_type.lower(), 0)
        
    def get_drink_desc(self):
        """Get description based on remaining health"""
        base_desc = f"A container of {self.db.drink_type}"
        
        if self.db.health <= 0:
            return f"{base_desc}, completely empty."
        elif self.db.health <= 2:
            return f"{base_desc}, with just a few drops left."
        elif self.db.health <= 5:
            return f"{base_desc}, less than half full."
        elif self.db.health <= 8:
            return f"{base_desc}, more than half full."
        else:
            return f"{base_desc}, nearly full."
            
    def return_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        """
        text = self.get_drink_desc()
        return text
        
    def drink(self, drinker):
        """
        Take a drink and reduce health by 1
        
        Args:
            drinker (Object): The one drinking
            
        Returns:
            tuple: (success, message)
        """
        if self.db.health <= 0:
            return (False, "It's empty.")
            
        self.db.health -= 1
        self.db.desc = self.get_drink_desc()
        
        # Apply alcohol effect if drinker can get drunk
        if hasattr(drinker, 'add_intoxication'):
            drinker.add_intoxication(self.db.alcohol_content)
        
        if self.db.health <= 0:
            msg = f"You finish the last of the {self.db.drink_type}."
        else:
            msg = f"You take a drink of the {self.db.drink_type}."
            
        return (True, msg)

class Food(Item):
    """Class for food items"""
    def at_object_creation(self):
        """Set up food-specific attributes"""
        super().at_object_creation()
        self.db.food_type = ""   # bread, meat, etc.
        self.db.health = 10      # how many bites left
        self.db.is_food = True
        
    def get_food_desc(self):
        """Get description based on remaining health"""
        base_desc = f"Some {self.db.food_type}"
        
        if self.db.health <= 0:
            return f"The remains of {self.db.food_type}, nothing edible left."
        elif self.db.health <= 2:
            return f"{base_desc}, just a few crumbs remain."
        elif self.db.health <= 5:
            return f"{base_desc}, about half eaten."
        elif self.db.health <= 8:
            return f"{base_desc}, with a few bites taken."
        else:
            return f"{base_desc}, fresh and untouched."
            
    def return_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        """
        text = self.get_food_desc()
        return text
        
    def eat(self, eater):
        """
        Take a bite and reduce health by 1
        
        Args:
            eater (Object): The one eating
            
        Returns:
            tuple: (success, message)
        """
        if self.db.health <= 0:
            return (False, "There's nothing left to eat.")
            
        self.db.health -= 1
        
        self.db.desc = self.get_food_desc()
        
        if self.db.health <= 0:
            msg = f"You finish the last of the {self.db.food_type}."
        else:
            msg = f"You take a bite of the {self.db.food_type}."
            
        return (True, msg)
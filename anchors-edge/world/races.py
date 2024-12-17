from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel

class RaceAttribute(SharedMemoryModel):
    """
    Stores physical attributes for different races.
    Heights are stored in centimeters.
    """
    race = models.OneToOneField('objects.ObjectDB', related_name='race_attributes', 
                               on_delete=models.CASCADE)
    min_height = models.IntegerField(help_text="Minimum height in cm")
    max_height = models.IntegerField(help_text="Maximum height in cm")
    
    # You might want to add more attributes later like:
    # average_lifespan = models.IntegerField()
    # average_weight = models.IntegerField()
    
    def get_height_category(self, height):
        """
        Returns the height category for a given height.
        """
        if not (self.min_height <= height <= self.max_height):
            return "Invalid"
            
        range_size = self.max_height - self.min_height
        percentile = (height - self.min_height) / range_size * 100
        
        if percentile < 25:
            return "Very Short"
        elif percentile < 40:
            return "Short"
        elif percentile < 60:
            return "Average"
        elif percentile < 75:
            return "Tall"
        else:
            return "Very Tall" 
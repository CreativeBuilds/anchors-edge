def notify_weather_changes(self, old_weather, new_weather):
    """Notify all weather-aware rooms about weather changes."""
    # Get all weather-aware rooms
    from typeclasses.rooms.base import WeatherAwareRoom
    for room in WeatherAwareRoom.objects.all():
        room.notify_weather_change(old_weather, new_weather)
        
def notify_time_changes(self, old_period, new_period):
    """Notify all weather-aware rooms about time period changes."""
    from typeclasses.rooms.base import WeatherAwareRoom
    for room in WeatherAwareRoom.objects.all():
        room.notify_time_change(old_period, new_period) 
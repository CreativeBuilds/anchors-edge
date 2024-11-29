"""
Weather code definitions and mappings.
"""

WEATHER_CODES = {
    "clear": [0],  # Clear sky
    "partly_cloudy": [1, 2, 3],  # Partly cloudy
    "cloudy": [45, 48],  # Foggy/cloudy
    "rain": [51, 53, 55, 61, 63, 65, 80, 81, 82],  # Various intensities of rain
    "snow": [71, 73, 75, 77, 85, 86],  # Various intensities of snow
    "thunderstorm": [95, 96, 99],  # Thunderstorm
    "drizzle": [51, 53, 55],  # Drizzle
    "heavy_rain": [65, 82],  # Heavy rain
    "light_rain": [61, 80],  # Light rain
    "moderate_rain": [63, 81],  # Moderate rain
    "freezing_rain": [66, 67],  # Freezing rain
    "sleet": [68, 69, 83, 84],  # Sleet
    "light_snow": [71, 85],  # Light snow
    "moderate_snow": [73, 86],  # Moderate snow
    "heavy_snow": [75, 77],  # Heavy snow
} 
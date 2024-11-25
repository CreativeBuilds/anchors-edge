import requests

# Austin's latitude and longitude
lat = 21.4655745
lon = -71.1390341

# API endpoint for current weather
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=apparent_temperature,precipitation,rain,showers,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FChicago"

response = requests.get(url)

if response.status_code == 200:
    weather_data = response.json()
    print(weather_data['current'])
else:
    print("Failed to retrieve weather data")
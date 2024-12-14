import os
import sys
import requests
import datetime
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("API_KEY")

# Get the location and units from command-line arguments
if len(sys.argv) != 3:
    print("Usage: python weather_forecast.py <location> <units>")
    sys.exit(1)

location = sys.argv[1]
units = sys.argv[2]

# OpenWeatherMap API endpoint and parameters
api_endpoint = "http://api.openweathermap.org/data/2.5/forecast/daily"
params = {
    "q": location,
    "cnt": 7,
    "appid": api_key,
    "units": units
}

try:
    # Make the API request
    response = requests.get(api_endpoint, params=params)
    response.raise_for_status()

    data = response.json()["list"]

    # Print the header row
    print("Date         | Temperature | Weather")
    print("-------------|-------------|------------------")

    # Iterate over the forecasts
    for forecast in data:
        date = datetime.datetime.fromtimestamp(forecast["dt"]).strftime("%Y-%m-%d")
        temperature = forecast["temp"]["day"]
        main_weather = forecast["weather"][0]["main"]
        description = forecast["weather"][0]["description"]

        print(f"{date} | {temperature:>11} | {main_weather} ({description})")

except: requests
#!/usr/bin/env python3
"""
Main controller for the SMHI weather forecast application.

Flow:
1. User provides a location name
2. Convert location to coordinates using Mistral AI
3. Fetch weather data from SMHI API
4. Generate interesting forecast using Mistral AI
"""

import json
import sys
import time
import threading
from prompts import location_to_coordinates, forecast
from fetch_weather import get_weather_data_as_json

# Loading animation
class LoadingIndicator:
    def __init__(self, message=""):
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        # Print a sleeping emoji if it took a while
        print(f"  😴 {self.message}... done!")

    def _animate(self):
        symbols = ["🌤️", "🌥️", "🌦️", "⛅", "☁️", "🌧️"]
        i = 0
        start_time = time.time()

        while not self.stop_event.wait(0.3):
            # Only show animation if it's taking more than 2 seconds
            if time.time() - start_time > 2:
                sys.stdout.write(f"\r  {symbols[i % len(symbols)]} {self.message}... ")
                sys.stdout.flush()
            i += 1

        # Clear the line
        sys.stdout.write("\r")
        sys.stdout.flush()

def main():
    """Main application flow."""
    print("🌤️ SMHI Weather Forecast Application")
    print("=" * 50)

    # Step 1: Get location from user
    location = input("Enter a location in Sweden (e.g., Stockholm, Gothenburg): ").strip()

    if not location:
        print("Error: Location cannot be empty.")
        return

    print(f"\n🔍 Looking up coordinates for: {location}")

    # Step 2: Convert location to coordinates
    try:
        print(f"\n🔍 Looking up coordinates for: {location}")
        loader = LoadingIndicator("Getting coordinates")
        loader.start()

        coordinates_result = location_to_coordinates(location)

        # Parse coordinates - handle markdown code blocks and extract JSON
        try:
            # Remove markdown code blocks if present
            if coordinates_result.startswith('```'):
                # Extract JSON from markdown code block
                json_start = coordinates_result.find('{')
                json_end = coordinates_result.rfind('}') + 1
                if json_start > 0 and json_end > json_start:
                    json_str = coordinates_result[json_start:json_end]
                else:
                    json_str = coordinates_result
            else:
                json_str = coordinates_result

            coords = json.loads(json_str)
            lat = float(coords.get("latitude"))
            lon = float(coords.get("longitude"))
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            loader.stop()
            print(f"Error parsing coordinates: {e}. They are not in correct format, should be like this: ```{{\"latitude\": 59.33, \"longitude\": 18.08}}```")
            print(f"Raw response: {coordinates_result}")
            return

    except Exception as e:
        if 'loader' in locals():
            loader.stop()
        print(f"Error getting coordinates: {e}")
        return

    loader.stop()

    print(f"📍 Found coordinates: Latitude {lat}, Longitude {lon}")

    # Step 3: Fetch weather data
    print(f"\n🌡️ Fetching weather data for {location}...")
    try:
        loader = LoadingIndicator("Fetching weather data")
        loader.start()

        weather_json = get_weather_data_as_json(lat, lon)

        loader.stop()
        print("Weather data retrieved successfully!")
    except Exception as e:
        if 'loader' in locals():
            loader.stop()
        print(f"Error fetching weather data: {e}")
        return

    # Step 4: Generate interesting forecast
    print(f"\n🤖 Generating interesting forecast...")
    try:
        loader = LoadingIndicator("Generating forecast")
        loader.start()

        forecast_result = forecast(weather_json)

        loader.stop()
        print("\n" + "=" * 50)
        print("📢 INTERESTING WEATHER FORECAST:")
        print("=" * 50)
        print(forecast_result)
        print("=" * 50)
    except Exception as e:
        if 'loader' in locals():
            loader.stop()
        print(f"Error generating forecast: {e}")
        return

if __name__ == "__main__":
    main()

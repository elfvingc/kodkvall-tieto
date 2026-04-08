# fetch_weather.py
import json
from smhi_open_data import SMHIOpenDataClient, Parameter

def get_weather_data(lat: float, lon: float) -> dict:
    """
    Fetches weather data for the given latitude and longitude from SMHI's API
    and returns structured weather information.

    Args:
        lat (float): Latitude (e.g., 59.33 for Stockholm)
        lon (float): Longitude (e.g., 18.08 for Stockholm)

    Returns:
        dict: Weather data containing station info, parameters, and observations
    """
    client = SMHIOpenDataClient()

    # Get the closest weather station to the given coordinates
    closest_station = client.get_closest_station(latitude=lat, longitude=lon)

    # Get available parameters at the station
    parameters = client.get_station_parameters(station_id=closest_station["id"])

    # Get latest observations for available parameters
    # Try to get temperature data if available
    temperature_obs = []
    if Parameter.TemperaturePast1h in parameters:
        temperature_obs = client.get_latest_observations(parameter=Parameter.TemperaturePast1h)
    elif Parameter.TemperatureDew in parameters:
        temperature_obs = client.get_latest_observations(parameter=Parameter.TemperatureDew)

    # Get humidity if available
    humidity_obs = []
    if Parameter.Humidity in parameters:
        humidity_obs = client.get_latest_observations(parameter=Parameter.Humidity)

    # Get wind speed if available
    wind_obs = []
    if Parameter.WindSpeed in parameters:
        wind_obs = client.get_latest_observations(parameter=Parameter.WindSpeed)

    # Get pressure if available
    pressure_obs = []
    if Parameter.Pressure in parameters:
        pressure_obs = client.get_latest_observations(parameter=Parameter.Pressure)

    return {
        "station": closest_station,
        "available_parameters": [p.name for p in parameters],
        "observations": {
            "temperature": temperature_obs,
            "humidity": humidity_obs,
            "wind_speed": wind_obs,
            "pressure": pressure_obs
        }
    }

def get_weather_data_as_json(lat: float, lon: float) -> str:
    """
    Fetches weather data and returns it as a JSON string.

    Args:
        lat (float): Latitude
        lon (float): Longitude

    Returns:
        str: JSON string containing weather data
    """
    weather_data = get_weather_data(lat, lon)
    return json.dumps(weather_data, indent=2, default=str)

# Example usage
if __name__ == "__main__":
    print("Fetching weather data for Stockholm:")
    weather_json = get_weather_data_as_json(lat=59.33, lon=18.08)  # Stockholm coordinates
    print(weather_json)

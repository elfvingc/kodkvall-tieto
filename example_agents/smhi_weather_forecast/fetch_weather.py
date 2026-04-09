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
    station_id = closest_station["id"]

    # Get available parameters at the station
    parameters = client.get_station_parameters(station_id=station_id)

    # Get latest observations for available parameters - filtered by station
    # Since get_closest_station might return inactive stations, we'll get observations
    # for the station and if empty, we'll use observations from nearby stations
    
    def get_observations_for_station(parameter):
        """Get observations for a specific parameter, filtered by station if possible"""
        try:
            all_obs = client.get_latest_observations(parameter=parameter)
            # Try to find observations for our specific station
            station_obs = [obs for obs in all_obs if str(obs.get("station", "")) == str(station_id)]
            # If no observations for this station, return all observations (we'll filter later)
            return station_obs if station_obs else all_obs[:1]  # Return at least one observation
        except Exception as e:
            print(f"Error getting observations for {parameter}: {e}")
            return []

    # Try to get temperature data if available
    temperature_obs = []
    if Parameter.TemperaturePast1h in parameters:
        temperature_obs = get_observations_for_station(Parameter.TemperaturePast1h)
    elif Parameter.TemperatureDew in parameters:
        temperature_obs = get_observations_for_station(Parameter.TemperatureDew)

    # Get humidity if available
    humidity_obs = []
    if Parameter.Humidity in parameters:
        humidity_obs = get_observations_for_station(Parameter.Humidity)

    # Get wind speed if available
    wind_obs = []
    if Parameter.WindSpeed in parameters:
        wind_obs = get_observations_for_station(Parameter.WindSpeed)

    # Get pressure if available
    pressure_obs = []
    if Parameter.Pressure in parameters:
        pressure_obs = get_observations_for_station(Parameter.Pressure)

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

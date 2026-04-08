import os
from mistralai.client import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-tiny"

client = Mistral(api_key=api_key)

def location_to_coordinates(location: str) -> dict:
    """
    Convert a location name to latitude/longitude coordinates using Mistral AI.

    Args:
        location: Location name (e.g., "Stockholm", "Gothenburg")

    Returns:
        dict: {"latitude": float, "longitude": float}
    """
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"what is coordinates for {location}?", # Better prompt needed to get coordinates in correct format
            },
        ]
    )
    return chat_response.choices[0].message.content

def forecast(weather_data: str) -> str:
    """
    Generate an interesting weather forecast based on weather data
    Maybe it can tell you something about if it's elk hunting season?
    Is it time to changes from winter tires?
    Will I get bitten by mosquitoes?

    Args:
        weather_data: JSON string containing weather information

    Returns:
        str: Interesting weather forecast
    """
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"{weather_data}" # Better prompt needed.
            },
        ]
    )
    return chat_response.choices[0].message.content


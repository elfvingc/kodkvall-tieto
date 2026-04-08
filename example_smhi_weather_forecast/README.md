# SMHI Weather Forecast with Mistral AI

A Python application that combines SMHI weather data with Mistral AI for location lookup and weather analysis.

## What This Program Should Do

1. **Location to Coordinates**: Convert location names (e.g., "Stockholm") to latitude/longitude using Mistral AI
2. **Fetch Weather Data**: Get real-time weather data from SMHI's API
3. **Generate Forecast**: Use Mistral AI to create interesting weather insights

## Setup

### Install dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Or just install requirements
pip install -r requirements.txt
```

### Set your Mistral API key

```bash
export MISTRAL_API_KEY=your_api_key_here
```

Or create `.env` file:
```bash
echo "MISTRAL_API_KEY=your_api_key_here" > .env
```

## Usage

```bash
# Run the application
python3 main.py

# Example session:
Enter a location in Sweden (e.g., Stockholm, Gothenburg): Stockholm
# ... application runs and shows weather forecast ...
```

## Files

- `main.py`: Main application controller with loading animations
- `fetch_weather.py`: SMHI API client for fetching weather data
- `prompts.py`: Mistral AI prompts (needs fixing!)
- `requirements.txt`: Python dependencies

## Expected Output Format

The `location_to_coordinates()` function should return JSON like:
```json
{"latitude": 59.33, "longitude": 18.08}
```

Not the current format with bullet points and text.

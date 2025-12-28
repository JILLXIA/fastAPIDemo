import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

@tool
def get_weather_by_prompt(prompt: str) -> dict:
    """
    Gets weather data for a given prompt using the OpenWeatherMap assistant API.

    Args:
        prompt: A string describing the weather request, 
                e.g., "What’s weather like in San Jose, CA next weekend?"

    Returns:
        A dictionary containing the weather data.
    """
    load_dotenv()
    WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    # For local development, you can set the OPENWEATHERMAP_API_KEY environment variable.
    # You can get a key from https://home.openweathermap.org/api_keys
    # The user provided this key: 40ca2d6e6d33ca1556009a741586bb1a
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", WEATHER_API_KEY)
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY not found in environment variables.")

    url = "https://api.openweathermap.org/assistant/session"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    data = {
        "prompt": prompt
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        response_data = response.json()
        return response_data.get("answer", "No answer found.")
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
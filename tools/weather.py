import os
import requests
from typing import List, Optional, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime

def kelvin_to_c(k: float) -> float:
    return round(k - 273.15, 1)


def kelvin_to_f(k: float) -> float:
    return round((k - 273.15) * 9 / 5 + 32, 1)

def convert_temp(temp_k: float | None, units: str) -> float | None:
    if temp_k is None:
        return None
    return kelvin_to_c(temp_k) if units == "celsius" else kelvin_to_f(temp_k)

def convert_unix_timestamp_to_human_readable(timestamp: int) -> str:
    """
    Converts a Unix timestamp to a human-readable date string (YYYY-MM-DD HH:MM:SS).
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

class OneCallInput(BaseModel):
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit for output"
    )
    days: int = Field(
        default=7,
        description="Number of daily forecasts to return (max 8)"
    )


@tool(
    "get_weather_onecall",
    description="Get current weather and daily forecast using OpenWeather One Call 3.0",
    args_schema=OneCallInput
)
def get_weather_onecall(
    lat: float,
    lon: float,
    units: str = "celsius",
    days: int = 7
) -> dict:
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return {"error": "OPENWEATHERMAP_API_KEY not configured"}

    url = "https://api.openweathermap.org/data/3.0/onecall"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "exclude": "minutely,hourly,alerts",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        daily = data.get("daily", [])[:days]

        return {
            "location": {
                "lat": lat,
                "lon": lon,
                "timezone": data.get("timezone"),
            },
            "current": {
                "temperature": convert_temp(current.get("temp"), units),
                "feels_like": convert_temp(current.get("feels_like"), units),
                "humidity": current.get("humidity"),
                "uvi": current.get("uvi"),
                "wind_speed": current.get("wind_speed"),
                "condition": current.get("weather", [{}])[0].get("description"),
            },
            "daily_forecast": [
                {
                    "date": convert_unix_timestamp_to_human_readable(day.get("dt")),
                    "summary": day.get("summary"),
                    "temp_min": convert_temp(day.get("temp", {}).get("min"), units),
                    "temp_max": convert_temp(day.get("temp", {}).get("max"), units),
                    "humidity": day.get("humidity"),
                    "uvi": day.get("uvi"),
                    "wind_speed": day.get("wind_speed"),
                    "rain_probability": day.get("pop"),
                    "rain_amount": day.get("rain", 0),
                    "condition": day.get("weather", [{}])[0].get("main"),
                    "description": day.get("weather", [{}])[0].get("description"),
                }
                for day in daily
            ],
        }

    except requests.exceptions.HTTPError:
        return {
            "error": "OpenWeather One Call API error",
            "status": response.status_code,
            "details": response.text,
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

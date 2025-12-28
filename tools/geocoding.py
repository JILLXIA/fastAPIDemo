from typing import Optional
import requests
from pydantic import BaseModel, Field
from langchain.tools import tool

# =========================
# Models
# =========================

class GeoInput(BaseModel):
    city: str = Field(
        ...,
        description="City name with optional country, e.g., 'Huangshi, China' or 'San Jose CA'"
    )

class GeoResult(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    display_name: str = Field(..., description="Resolved location name from OpenStreetMap")


# =========================
# LangChain Tool
# =========================

@tool(
    "geocode_city_tool",
    description="Resolve the latitude and longitude of a city using OpenStreetMap Nominatim. "
                "Returns a dictionary containing 'lat', 'lon', and 'display_name'. "
                "Useful for geocoding city names for weather, POI, or mapping purposes.",
    args_schema=GeoInput
)
def geocode_city_tool(city: str) -> dict:
    """
    Convert a city name into latitude and longitude using OpenStreetMap Nominatim.
    Returns a dict with 'lat', 'lon', 'display_name', or empty dict if not found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "weekend-planner-agent/1.0",
        "Accept-Language": "en",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return {}

        result = GeoResult(
            lat=data[0]["lat"],
            lon=data[0]["lon"],
            display_name=data[0].get("display_name", ""),
        )
        return result.model_dump()

    except requests.exceptions.Timeout:
        return {}
    except requests.exceptions.RequestException as e:
        print(f"Geocoding failed for '{city}': {e}")
        return {}

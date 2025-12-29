import os
import requests
import pygeohash as pgh
from typing import Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class EventDiscoveryInput(BaseModel):
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    radius: int = Field(default=20, description="Radius for search")
    unit: str = Field(default="km", description="Unit for radius (km or miles)")
    size: int = Field(default=5, description="Number of events to return")
    segment_name: str = Field(default="music", description="Segment name (e.g., music, sports)")

@tool("discover_events", args_schema=EventDiscoveryInput)
def discover_events(
    lat: float,
    lon: float,
    radius: int = 20,
    unit: str = "km",
    size: int = 5,
    segment_name: str = "music"
) -> dict:
    """
    Discover events using Ticketmaster API based on location (latitude and longitude).
    """
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        return {"error": "TICKETMASTER_API_KEY not configured"}

    # Convert lat/lon to geohash
    geo_point = pgh.encode(lat, lon, precision=9)

    url = "https://app.ticketmaster.com/discovery/v2/events"
    params = {
        "apikey": api_key,
        "geoPoint": geo_point,
        "radius": radius,
        "unit": unit,
        "size": size,
        "sort": "date,asc",
        "segmentName": segment_name
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        events = []
        if "_embedded" in data and "events" in data["_embedded"]:
            for event in data["_embedded"]["events"]:
                event_info = {
                    "name": event.get("name"),
                    "url": event.get("url"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate"),
                    "time": event.get("dates", {}).get("start", {}).get("localTime"),
                }

                # Try to get venue info
                if "_embedded" in event and "venues" in event["_embedded"]:
                    venues = event["_embedded"]["venues"]
                    if venues:
                        event_info["venue"] = venues[0].get("name")
                        event_info["city"] = venues[0].get("city", {}).get("name")

                events.append(event_info)

        return {"events": events}

    except Exception as e:
        return {"error": str(e)}


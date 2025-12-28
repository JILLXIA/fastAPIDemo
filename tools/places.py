import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class PlaceInput(BaseModel):
    lat: float = Field(..., description="Latitude of the center point")
    lon: float = Field(..., description="Longitude of the center point")
    radius: int = Field(25000, description="Search radius in meters")
    amenity: str = Field(..., description="Type of amenity to search for (e.g., restaurant, cafe, bar, fast_food, cinema, parking, fuel, bank, pharmacy, hospital)")
    cuisine: Optional[str] = Field(None, description="Cuisine type (e.g., chinese, italian, mexican, indian, japanese, burger, pizza). Only applicable for food-related amenities.")
    limit: int = Field(10, description="Maximum number of results to return")

@tool("get_places_osm", args_schema=PlaceInput)
def get_places_osm(lat: float, lon: float, amenity: str, radius: int = 25000, cuisine: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Find places of interest using OpenStreetMap (Overpass API).

    Common amenities:
    - Sustenance: bar, bbq, biergarten, cafe, fast_food, food_court, ice_cream, pub, restaurant
    - Entertainment: arts_centre, casino, cinema, community_centre, gambling, nightclub, planetarium, theatre
    - Others: bank, atm, pharmacy, hospital, clinic, doctors, dentist, veterinary, police, post_office, library, university, school, kindergarten, place_of_worship, parking, fuel, taxi, bus_station, train_station

    Common cuisines (for restaurants/fast_food):
    - american, asian, bagel, bbq, breakfast, burger, cake, chicken, chinese, coffee_shop, donut, fish_and_chips, french, german, greek, ice_cream, indian, italian, japanese, kebab, korean, mexican, noodle, pizza, ramen, sandwich, seafood, spanish, steak_house, sushi, thai, turkish, vietnamese
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Construct the query
    # Example: [out:json]; node ["amenity"="restaurant"] ["cuisine"~"chinese"] (around:25000,37.33,-121.89); out 10;

    query_parts = ["[out:json];", "node"]
    query_parts.append(f'["amenity"="{amenity}"]')

    if cuisine:
        # Using regex match ~ as per user example
        query_parts.append(f'["cuisine"~"{cuisine}"]')

    query_parts.append(f'(around:{radius},{lat},{lon});')
    query_parts.append(f'out {limit};')

    query = " ".join(query_parts)

    try:
        response = requests.post(overpass_url, data=query, headers={'Content-Type': 'text/plain'})
        response.raise_for_status()
        data = response.json()

        elements = data.get("elements", [])
        results = []
        for el in elements:
            tags = el.get("tags", {})

            # Format address
            addr_parts = []
            if tags.get('addr:housenumber'):
                addr_parts.append(tags.get('addr:housenumber'))
            if tags.get('addr:street'):
                addr_parts.append(tags.get('addr:street'))
            if tags.get('addr:city'):
                addr_parts.append(tags.get('addr:city'))

            address = " ".join(addr_parts) if addr_parts else "Address not available"

            results.append({
                "name": tags.get("name", "Unknown"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "amenity": tags.get("amenity"),
                "cuisine": tags.get("cuisine"),
                "address": address,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "opening_hours": tags.get("opening_hours")
            })
        return results

    except Exception as e:
        return [{"error": str(e)}]

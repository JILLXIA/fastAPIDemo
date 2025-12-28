import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

try:
    from langchain.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    StructuredTool = None

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def search_cuisine(
    lat: float,
    lon: float,
    cuisine: str,
    preferences: List[str] = None,
    radius: int = 2000,
) -> List[dict]:
    """
    Generic cuisine search using OSM + heuristics.
    Returns a list of raw OSM elements.
    """
    preferences = preferences or []
    
    # User-Agent is required by Overpass API policy
    headers = {
        "User-Agent": "weekend-planner-agent/1.0"
    }

    cuisine_pattern = cuisine.lower() if cuisine else ""

    # Preference keywords → name-based matching
    pref_keywords = {
        "spicy": "spicy|sichuan|szechuan|chongqing|hot",
        "hotpot": "hotpot|hot pot|火锅",
        "noodles": "noodle|ramen|lamian|拉面",
        "dumplings": "dumpling|jiaozi|包子|dim sum"
    }

    name_pattern = "|".join(
        pref_keywords[p] for p in preferences if p in pref_keywords
    )
    
    # Construct the query parts
    # Part 1: Cuisine match (if cuisine provided)
    query_part_cuisine = ""
    if cuisine_pattern:
        query_part_cuisine = f"""
        node
            ["amenity"~"restaurant|fast_food"]
            ["cuisine"~"{cuisine_pattern}"]
            (around:{radius},{lat},{lon});
        """
    
    # Part 2: Name match (only if we have a pattern from preferences)
    query_part_name = ""
    if name_pattern:
        query_part_name = f"""
        node
            ["amenity"~"restaurant|fast_food"]
            ["name"~"{name_pattern}", i]
            (around:{radius},{lat},{lon});
        """

    # If neither, just search for restaurants (fallback, though usually cuisine is provided)
    if not query_part_cuisine and not query_part_name:
        query_part_cuisine = f"""
        node
            ["amenity"~"restaurant|fast_food"]
            (around:{radius},{lat},{lon});
        """

    query = f"""
    [out:json];
    (
      {query_part_cuisine}
      {query_part_name}
    );
    out tags;
    """

    try:
        resp = requests.post(OVERPASS_URL, data=query, headers=headers)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except requests.exceptions.RequestException as e:
        print(f"Error searching cuisine: {e}")
        return []

def score_place(tags: dict, preferences: List[str]) -> float:
    score = 0.0

    name = tags.get("name", "").lower()
    cuisine = tags.get("cuisine", "").lower()

    # Base score if named (unnamed places are often lower quality)
    if "name" in tags:
        score += 1.0

    # Cuisine specificity
    if ";" in cuisine or "," in cuisine:
        score += 0.5

    # Preference matching
    keyword_map = {
        "spicy": ["sichuan", "szechuan", "chongqing", "spicy"],
        "hotpot": ["hotpot", "hot pot", "火锅"],
        "noodles": ["noodle", "lamian", "ramen"],
        "dumplings": ["dumpling", "jiaozi", "包子", "dim sum"]
    }

    for pref in preferences:
        for kw in keyword_map.get(pref, []):
            if kw in name or kw in cuisine:
                score += 1.5

    # Brand heuristic (often consistent quality)
    brands = ["din tai fung", "haidilao"]
    if any(b in name for b in brands):
        score += 2.0

    return score

def find_best_restaurants(
    latitude: float,
    longitude: float,
    cuisine: Optional[str] = "restaurant",
    preferences: Optional[List[str]] = None,
    radius: int = 2000
) -> List[Dict[str, Any]]:
    """
    Finds and ranks restaurants based on cuisine and preferences.
    Returns a list of dictionaries with restaurant details.
    """
    prefs = preferences or []
    places = search_cuisine(latitude, longitude, cuisine, prefs, radius)

    scored = []
    for p in places:
        tags = p.get("tags", {})
        if not "name" in tags:
            continue
            
        score = score_place(tags, prefs)
        
        # Extract useful info
        place_info = {
            "name": tags.get("name"),
            "cuisine": tags.get("cuisine", "unknown"),
            "score": score,
            "address": f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip(),
            "opening_hours": tags.get("opening_hours"),
            "website": tags.get("website") or tags.get("contact:website"),
            "lat": p.get("lat"),
            "lon": p.get("lon")
        }
        scored.append(place_info)

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    # Deduplicate by name
    seen = set()
    top_results = []
    for place in scored:
        if place["name"] not in seen:
            top_results.append(place)
            seen.add(place["name"])
        if len(top_results) >= 10:
            break

    return top_results

# --- LangChain Integration ---

class PlaceSearchInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    cuisine: Optional[str] = Field("restaurant", description="Type of cuisine (e.g., 'chinese', 'italian', 'pizza')")
    preferences: Optional[List[str]] = Field(default_factory=list, description="List of preferences (e.g., ['spicy', 'hotpot', 'cheap'])")
    radius: Optional[int] = Field(2000, description="Search radius in meters")

if LANGCHAIN_AVAILABLE and StructuredTool:
    places_tool = StructuredTool.from_function(
        func=find_best_restaurants,
        name="find_restaurants",
        description="Find nearby restaurants by cuisine and preferences. Returns a list of matches with details.",
        args_schema=PlaceSearchInput
    )
else:
    places_tool = None


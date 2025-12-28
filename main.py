from fastapi import FastAPI
from tools.weather import get_weather_by_prompt
from tools.geocoding import get_lat_lon
from tools.places import find_best_restaurants
from typing import Optional

app = FastAPI()

@app.get("/restaurants")
async def get_restaurants(
    city_name: str = "San Jose, CA",
    cuisine: str = "chinese",
    preferences: Optional[str] = None
):
    """
    Finds restaurants based on city, cuisine and preferences.
    """
    lat_lon_data = get_lat_lon(city_name)
    if not lat_lon_data:
        return {"error": "Could not find location for the given city."}
    
    prefs_list = [p.strip() for p in preferences.split(",")] if preferences else []
    
    result = find_best_restaurants(
        lat_lon_data["lat"], 
        lat_lon_data["lon"], 
        cuisine, 
        prefs_list
    )
    
    return {"result": result}

@app.get("/plan")
async def get_plan(
    prompt: str = "What’s weather like in San Jose, CA next weekend?",
    city_name: str = "San Jose, CA"
):
    """
    Creates a weekend plan.
    It gets the weather for the given prompt and latitude/longitude for the city.
    """
    weather_data = get_weather_by_prompt(prompt)
    lat_lon_data = get_lat_lon(city_name)
    
    response_content = {
        "plan": "Here is the information for your trip:",
        "weather": weather_data
    }
    
    if lat_lon_data:
        response_content["location"] = lat_lon_data
    else:
        response_content["location"] = "Could not retrieve latitude and longitude for the given city."

    return response_content

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Weekend Planner Agent!"}

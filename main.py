from fastapi import FastAPI
from tools.weather import get_weather_by_prompt
from tools.geocoding import get_lat_lon

app = FastAPI()

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

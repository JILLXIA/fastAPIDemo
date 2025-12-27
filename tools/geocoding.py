import requests

def get_lat_lon(city_name: str) -> dict | None:
    """
    Gets the latitude and longitude for a given city name using Nominatim OpenStreetMap API.

    Args:
        city_name: The name of the city (e.g., "Huangshi, China").

    Returns:
        A dictionary with 'lat' and 'lon' if successful, None otherwise.
    """
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {
        "User-Agent": "weekend-planner-agent/1.0"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data and len(data) > 0:
            first_result = data[0]
            return {
                "lat": first_result.get("lat"),
                "lon": first_result.get("lon")
            }
        else:
            print(f"No results found for city: {city_name}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching geocoding data for {city_name}: {e}")
        return None

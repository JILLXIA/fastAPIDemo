from tools.events import discover_events
import sys

def test_tool():
    print("Starting test...", flush=True)
    # Seattle coordinates
    lat = 47.6062
    lon = -122.3321

    print(f"Testing discover_events for Seattle ({lat}, {lon})...", flush=True)
    try:
        result = discover_events.invoke({
            "lat": lat,
            "lon": lon,
            "radius": 20,
            "unit": "km",
            "size": 5,
            "segment_name": "music"
        })
        print("Result:", result, flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    test_tool()


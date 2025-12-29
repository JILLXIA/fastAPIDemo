"""Manual tool smoke test.

NOTE: This is NOT a pytest test file. It is a manual script.
The unit tests live in files named test_*.py and containing proper pytest tests.
"""

from tools.events import discover_events


def main():
    print("Starting manual test...", flush=True)
    # Seattle coordinates
    lat = 47.6062
    lon = -122.3321

    print(f"Testing discover_events for Seattle ({lat}, {lon})...", flush=True)
    result = discover_events.invoke({
        "lat": lat,
        "lon": lon,
        "radius": 20,
        "unit": "km",
        "size": 5,
        "segment_name": "music",
    })
    print("Result:", result, flush=True)


if __name__ == "__main__":
    main()

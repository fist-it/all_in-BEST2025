import json
import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

geolocator = Nominatim(user_agent="event_map_processor_v1")

INPUT_FILE = 'data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668.json'
OUTPUT_FILE = 'data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json'

def process_events():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"File not found {INPUT_FILE}")
        return

    processed_events = []
    
    print(f"Processing {len(events)} events...")

    for i, event in enumerate(events):
        address = event.get("location.name")

        if not address or address.lower() in ["polska", "poland", "gdansk", "gdańsk", "gdańsk, polska", "gdansk, polska", "gdansk, poland", "gdańsk, poland"]:
            print(f"[{i+1}] No address, skip: {event.get('name')}")
            continue

        if not any(cityname in address.lower() for cityname in ["gdansk", "gdańsk"]):
            address += ", Gdańsk"
        
        try:
            location = geolocator.geocode(address, timeout=10)

            if location:
                if not event["location.city"]: 
                    event["location.city"] = "Gdańsk"
                if not event["location.countryCode"]: 
                    event["location.countryCode"] = "PL"
                event["latitude"] = location.latitude
                event["longitude"] = location.longitude
                
                processed_events.append(event)
                print(f"[{i+1}] Success: {address} -> {location.latitude}, {location.longitude}")
            else:
                print(f"[{i+1}] Not found, skip: {address}")

        except (GeocoderTimedOut, GeocoderUnavailable):
            print(f"[{i+1}] Connection error, skip: {address}")
        
        # time.sleep(1)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_events, f, ensure_ascii=False, indent=2)

    print("-" * 30)
    print(f"Finished processing. Successfully processed {len(processed_events)} of {len(events)} events.")
    print(f"Outputs stored in: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_events()
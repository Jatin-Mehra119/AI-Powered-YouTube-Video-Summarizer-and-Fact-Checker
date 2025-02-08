"""
load_cc.py
-----------
This module fetches the captions JSON from a provided URL,
parses out the timestamped captions, and saves them to a CSV file.
"""

import requests
import csv

def fetch_captions_json(captions_url: str) -> dict:
    """
    Fetches captions JSON data from the given URL.
    
    Args:
        captions_url (str): URL to fetch the captions JSON.
        
    Returns:
        dict: The JSON data if successful; otherwise, None.
    """
    try:
        response = requests.get(captions_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching captions JSON: {e}")
        return None

def save_captions_to_csv(captions_json: dict, output_csv: str = "captions.csv") -> None:
    """
    Parses the captions JSON, extracts timestamps and caption text,
    and saves the results into a CSV file.
    
    Args:
        captions_json (dict): JSON data containing captions events.
        output_csv (str): Path to output CSV file.
    """
    if not captions_json or "events" not in captions_json:
        print("Invalid captions JSON format.")
        return

    data = []
    for event in captions_json["events"]:
        if "segs" in event:
            timestamp = event.get("tStartMs", 0) / 1000.0
            caption_text = " ".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if caption_text and caption_text != "\\n":
                data.append([timestamp, caption_text])

    if not data:
        print("No valid captions data found.")
        return

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp (s)", "Caption"])
        writer.writerows(data)
    print(f"Captions saved to {output_csv}")
    
"""
# For testing from the command line
if __name__ == "__main__":
    url = input("Enter Captions URL: ")
    json_data = fetch_captions_json(url)
    if json_data:
        save_captions_to_csv(json_data)
"""
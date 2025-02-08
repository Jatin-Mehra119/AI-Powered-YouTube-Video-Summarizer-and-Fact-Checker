"""
load_cc.py
-----------
Fetches the captions JSON from a given URL, cleans it, and saves it as a CSV.
Timestamps are converted into hh:mm:ss format.
"""

import requests
import csv

def fetch_captions_json(captions_url: str) -> dict:
    """
    Fetches and returns the JSON data from the captions URL.
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
    Parses the captions JSON, converts timestamps to hh:mm:ss format, and writes to CSV.
    """
    if not captions_json or "events" not in captions_json:
        print("Invalid captions JSON format.")
        return

    data = []
    for event in captions_json["events"]:
        if "segs" in event:
            # Convert milliseconds to seconds
            start_time = event.get("tStartMs", 0) / 1000.0
            # Convert to hh:mm:ss format
            hours = int(start_time // 3600)
            minutes = int((start_time % 3600) // 60)
            seconds = int(start_time % 60)
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            caption_text = " ".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if caption_text and caption_text != "\\n":
                data.append([timestamp, caption_text])
    
    if not data:
        print("No valid captions found.")
        return

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Caption"])
        writer.writerows(data)
    print(f"Captions saved to {output_csv}")

if __name__ == "__main__":
    url = input("Enter Captions URL: ")
    json_data = fetch_captions_json(url)
    if json_data:
        save_captions_to_csv(json_data)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import dotenv
import re
import asyncio
import json
import pandas as pd
from src.CC_capture import CC, load_cc
from src.Database import faiss_search
from src.pipelines.fact_checker import FactChecker
import groq

# Load environment variables
dotenv.load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI-Powered Podcast Search & Fact-Checker API")

# Initialize Groq Client
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
fact_checker = FactChecker(groq_client)

# -------------------------------
# 📌 Utility Functions
# -------------------------------

def extract_video_id(url: str):
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def get_context_around_timestamp(target_seconds: int, context_window: int = 10):
    """Fetches context around a given timestamp from captions.csv."""
    df = pd.read_csv("captions.csv")
    context_rows = []

    for ts_str, caption in zip(df["Timestamp"], df["Caption"]):
        try:
            hh, mm, ss = map(int, ts_str.split(":"))
            t_sec = hh * 3600 + mm * 60 + ss
            if abs(t_sec - target_seconds) <= context_window:
                context_rows.append(caption)
        except Exception:
            continue

    return " ".join(context_rows)


# -------------------------------
# 📌 Request Models
# -------------------------------

class VideoURLRequest(BaseModel):
    video_url: str


class SearchRequest(BaseModel):
    search_query: str
    context_window: int = 10  # Default to 10 seconds


class FactCheckRequest(BaseModel):
    context_text: str


# -------------------------------
# 🚀 1️⃣ Fetch Captions API
# -------------------------------

@app.get("/")
def read_root():
    return {"message": "AI-Powered Podcast Search & Fact-Checker API is running!"}


@app.post("/fetch-captions/")
async def fetch_captions(request: VideoURLRequest):
    video_url = request.video_url
    video_id = extract_video_id(video_url)

    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        caps_url = CC.fetch_captions(video_url)
        if not caps_url:
            raise HTTPException(status_code=500, detail="Failed to fetch captions")

        # Load and save captions
        caps_json = load_cc.fetch_captions_json(caps_url)
        load_cc.save_captions_to_csv(caps_json)

        # Create FAISS index
        faiss_search.create_faiss_index()

        return {"message": "Captions fetched and indexed successfully", "video_id": video_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# 🚀 2️⃣ Search Captions API
# -------------------------------

@app.post("/search/")
async def search_captions(request: SearchRequest):
    search_query = request.search_query
    context_window = request.context_window

    try:
        search_result = faiss_search.search_faiss(search_query)
        if not search_result:
            raise HTTPException(status_code=404, detail="No captions found")

        timestamp = search_result["timestamp"]
        caption = search_result["caption"]

        # Convert timestamp to seconds
        try:
            h, m, s = map(int, timestamp.split(":"))
            target_seconds = h * 3600 + m * 60 + s
        except ValueError:
            target_seconds = 0

        # Get context around timestamp
        full_context = get_context_around_timestamp(target_seconds, context_window)

        return {
            "message": "Captions searched successfully",
            "timestamp": timestamp,
            "caption": caption,
            "full_context": full_context
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# 🚀 3️⃣ Summarize Video API
# -------------------------------

@app.get("/summarize/")
async def summarize_video():
    try:
        df = pd.read_csv("captions.csv")
        full_transcript = " ".join(df["Caption"].tolist())

        summary = await fact_checker.summarize_text(full_transcript)

        return {"message": "Video summarized successfully", "summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# 🚀 4️⃣ Fact-Check Context API
# -------------------------------

@app.post("/fact-check/")
async def fact_check_context(request: FactCheckRequest):
    context_text = request.context_text

    if not context_text:
        raise HTTPException(status_code=400, detail="Context text cannot be empty")

    try:
        fc_results = await fact_checker.fact_check(context_text)

        return {"message": "Fact-check completed", "results": fc_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main:app --reload
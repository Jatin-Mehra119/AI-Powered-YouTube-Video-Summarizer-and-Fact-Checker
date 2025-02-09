from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import dotenv
import re
from src.CC_capture import CC, load_cc
from src.Database import faiss_search
from src.pipelines.fact_checker import FactChecker
import asyncio
import json
import groq

# Load environment variables
dotenv.load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Video Summarizer & Fact-Checker API")

# Function to extract video ID from YouTube URL
def extract_video_id(url: str):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# Request model
class VideoURLRequest(BaseModel):
    video_url: str

# -------------------------------
# 🚀 1️⃣ Fetch Captions API
# -------------------------------

@app.get("/")
def read_root():
    return {"message": "AI-Powered YouTube Video Summarizer & Fact-Checker API is running!"}


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

# Run with: uvicorn main:app --reload
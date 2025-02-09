"""
app.py
------
Streamlit UI for the AI-Powered Podcast Search & Fact-Checker.
"""

import streamlit as st
import os
import pandas as pd
import asyncio
import json
import dotenv
import groq
import re

# Load environment variables
dotenv.load_dotenv()

# Import custom modules
from src.CC_capture import CC, load_cc
from src.Database import faiss_search
from src.pipelines.fact_checker import FactChecker

# Streamlit UI settings
st.set_page_config(page_title="AI Video Search & Fact-Checker",
                   page_icon=":mag:",
                   layout="wide")
st.title("AI Video Search & Fact-Checker")

# Initialize session state variables if not already set
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "full_context" not in st.session_state:
    st.session_state.full_context = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "fc_results" not in st.session_state:
    st.session_state.fc_results = None

# -------------------------------
# Section 1: Fetch Captions & Video Preview
# -------------------------------
st.header("📌 1. Fetch Captions & Preview Video")
video_url = st.text_input("🎥 Enter YouTube Video URL:")

# Function to extract video ID from URL
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

video_id = extract_video_id(video_url) if video_url else None

if video_id:
    st.video(f"https://www.youtube.com/embed/{video_id}")  # Embed YouTube video

if st.button("Fetch Captions") and video_url:
    st.write("Fetching captions...")
    caps_url = CC.fetch_captions(video_url)
    if caps_url:
        st.success("Captions fetched! Generating FAISS index...")
        caps_json = load_cc.fetch_captions_json(caps_url)
        if caps_json:
            load_cc.save_captions_to_csv(caps_json)
            faiss_search.create_faiss_index()
            st.success("Captions indexed successfully.")
    else:
        st.error("Failed to fetch captions. Check your URL and cookies.")

# -------------------------------
# Section 2: Search Captions
# -------------------------------
st.header("🔍 2. Search Captions")
search_query = st.text_input("Enter search query:")
context_window = st.number_input("⏳ Context window (seconds)", min_value=5, max_value=60, value=10, step=5)

if st.button("Search") and search_query:
    st.write("Searching...")
    result = faiss_search.search_faiss(search_query)

    if result:
        timestamp = result["timestamp"]
        caption = result["caption"]

        # Convert timestamp to seconds
        try:
            h, m, s = map(int, timestamp.split(":"))
            target_seconds = h * 3600 + m * 60 + s
        except ValueError:
            st.error("Error parsing timestamp.")
            target_seconds = 0

        # Generate YouTube URL with timestamp
        video_link = f"https://www.youtube.com/watch?v={video_id}&t={target_seconds}s" if video_id else None
        st.session_state.search_result = {"timestamp": timestamp, "caption": caption, "video_link": video_link}

        # Store context in session state
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
        
        st.session_state.full_context = " ".join(context_rows)

# Display Search Results Persistently
if st.session_state.search_result:
    st.subheader("🔍 Search Results")
    result = st.session_state.search_result
    if result["video_link"]:
        st.markdown(f"🎯 **Closest Match at [{result['timestamp']}]({result['video_link']})**")
    st.write(f"📌 `{result['caption']}`")

    st.subheader("📖 Extracted Context")
    st.write(st.session_state.full_context)

# -------------------------------
# Section 3: Summarize Video
# -------------------------------
st.header("📝 3. Summarize Video")

if st.button("Summarize Video"):
    try:
        st.write("Generating summary... Please wait.")

        # Load full captions
        df = pd.read_csv("captions.csv")
        full_transcript = " ".join(df["Caption"].tolist())

        # Send the transcript to the summarization function
        fact_checker = FactChecker(groq.Client(api_key=os.getenv("GROQ_API_KEY")))
        st.session_state.summary = asyncio.run(fact_checker.summarize_text(full_transcript))

    except Exception as e:
        st.error(f"Summarization failed: {str(e)}")

# Display Summary Persistently
if st.session_state.summary:
    st.subheader("📌 Video Summary")
    st.write(st.session_state.summary)

# -------------------------------
# Section 4: Fact-Check Context
# -------------------------------
st.header("✅ 4. Fact-Check Context")

if st.button("🔍 Refine & Fact-Check"):
    if not st.session_state.full_context:
        st.error("Please perform a search first.")
    else:
        try:
            with st.spinner("Running fact-checking pipeline..."):
                groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
                fact_checker = FactChecker(groq_client)
                st.session_state.fc_results = asyncio.run(
                    fact_checker.fact_check(st.session_state.full_context)
                )
        except Exception as e:
            st.error(f"Fact-checking failed: {str(e)}")
            st.session_state.fc_results = {"error": str(e)}

# Display Fact-Check Results Persistently
if st.session_state.fc_results:
    fc_results = st.session_state.fc_results
    if "error" in fc_results:
        st.error(fc_results["error"])
    else:
        st.subheader("📌 Refined Context")
        refined_context = fc_results.get("refined_context", {})
        st.write(refined_context.get("context", "No refined context available."))

        st.subheader("🧐 Fact-Check Results")
        verification_result = fc_results.get("verification_result", {})
        if isinstance(verification_result, str):
            try:
                verification_result = json.loads(verification_result)
            except json.JSONDecodeError:
                st.write(verification_result)
        if isinstance(verification_result, dict):
            st.write(f"✅ **Factually Correct:** {verification_result.get('factually_correct', 'Unknown')}")
            st.write(f"📊 **Confidence:** {verification_result.get('confidence', 'N/A')}")
            st.write(f"💡 **Explanation:** {verification_result.get('explanation', 'No explanation provided.')}")
        else:
            st.write(verification_result)

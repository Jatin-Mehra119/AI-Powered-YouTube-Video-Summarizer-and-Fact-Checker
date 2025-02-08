"""
app.py
------
Streamlit UI for the AI-Powered Podcast Search & Fact-Checker.
The UI performs the following:
  1. Accepts a YouTube URL, fetches captions, cleans and saves them.
  2. Generates embeddings and creates a FAISS index.
  3. Allows the user to enter a search query.
  4. Retrieves the closest matching caption and its timestamp.
  5. Optionally, uses a user-specified context window (e.g., ± seconds) to extract a context snippet.
  6. Refines and fact-checks the context using Groq and crawl4ai.
"""

import streamlit as st
import os
import pandas as pd
import asyncio
import json
import dotenv
import groq

# Load environment variables
dotenv.load_dotenv()

# Import your custom modules
from src.CC_capture import CC, load_cc
from src.Database import faiss_search
from src.pipelines.fact_checker import FactChecker

# Set the page title and configuration
st.set_page_config(page_title="AI-Powered Podcast Search & Fact-Checker",
                   page_icon=":mag:",
                   layout="wide")

st.title("AI-Powered Podcast Search & Fact-Checker")

# -------------------------------
# Section 1: Fetch Captions
# -------------------------------
st.header("1. Fetch Captions")
video_url = st.text_input("Enter YouTube Video URL:")

if st.button("Fetch Captions") and video_url:
    st.write("Fetching captions...")
    caps_url = CC.fetch_captions(video_url)
    if caps_url:
        st.success("Captions URL fetched!")
        caps_json = load_cc.fetch_captions_json(caps_url)
        if caps_json:
            load_cc.save_captions_to_csv(caps_json)
            st.success("Captions saved to CSV.")
            st.write("Creating FAISS index...")
            faiss_search.create_faiss_index()
            st.success("FAISS index created.")
    else:
        st.error("Failed to fetch captions. Please check your URL and cookies.")

# -------------------------------
# Section 2: Search Captions
# -------------------------------
st.header("2. Search Captions")
search_query = st.text_input("Enter search query:")

# Allow user to specify a context window in seconds (before and after the result)
context_window = st.number_input("Context window (seconds)", min_value=5, max_value=60, value=10, step=5)

if st.button("Search") and search_query:
    st.write("Searching...")
    result = faiss_search.search_faiss(search_query)
    if result:
        st.markdown(f"**Closest Match at {result['timestamp']}**")
        st.write(result["caption"])
        
        # Load the full captions CSV to extract context.
        df = pd.read_csv("captions.csv")
        # Assuming timestamp is in hh:mm:ss format, convert it to seconds.
        try:
            h, m, s = map(int, result["timestamp"].split(":"))
            target_seconds = h * 3600 + m * 60 + s
        except Exception as e:
            st.error("Error parsing timestamp.")
            target_seconds = 0

        # Extract rows within the context window.
        context_rows = []
        for ts_str, caption in zip(df["Timestamp"], df["Caption"]):
            try:
                hh, mm, ss = map(int, ts_str.split(":"))
                t_sec = hh * 3600 + mm * 60 + ss
                if abs(t_sec - target_seconds) <= context_window:
                    context_rows.append(caption)
            except Exception as e:
                continue
        full_context = " ".join(context_rows)
        st.subheader("Extracted Context")
        st.write(full_context)
        
        # Store context in session state
        st.session_state.full_context = full_context

# -------------------------------
# Section 3: Fact-Check Context
# -------------------------------
st.header("3. Fact-Check Context")
if "fc_results" not in st.session_state:
    st.session_state.fc_results = None

if st.button("Refine and Fact-Check"):
    if "full_context" not in st.session_state:
        st.error("Please perform a search first to get context.")
    else:
        try:
            with st.spinner("Running fact-check pipeline..."):
                groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
                fact_checker = FactChecker(groq_client)
                st.session_state.fc_results = asyncio.run(
                    fact_checker.fact_check(st.session_state.full_context)
                )
        except Exception as e:
            st.error(f"Fact-checking failed: {str(e)}")
            st.session_state.fc_results = {"error": str(e)}

if st.session_state.fc_results:
    if "error" in st.session_state.fc_results:
        st.error(st.session_state.fc_results["error"])
    else:
        st.subheader("Refined Context")
        refined_context = st.session_state.fc_results.get("refined_context", {})
        st.write(refined_context.get("context", "No refined context available."))
        
        st.subheader("Fact-Check Results")
        verification_result = st.session_state.fc_results.get("verification_result", {})
        if isinstance(verification_result, str):
            try:
                verification_result = json.loads(verification_result)
            except json.JSONDecodeError:
                st.write(verification_result)
        if isinstance(verification_result, dict):
            st.write(f"**Factually Correct:** {verification_result.get('factually_correct', 'Unknown')}")
            st.write(f"**Confidence:** {verification_result.get('confidence', 'N/A')}")
            st.write(f"**Explanation:** {verification_result.get('explanation', 'No explanation provided.')}")
        else:
            st.write(verification_result)
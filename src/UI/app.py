"""
app.py
------
Streamlit UI for the AI-Powered Podcast Search & Fact-Checker.
This interface allows the user to:
  1. Enter a YouTube URL to fetch captions.
  2. Process and index the captions.
  3. Enter a search query to find relevant moments.
  
All pipeline steps run sequentially from this UI.
"""

import streamlit as st
from src.CC_capture import CC, load_cc
from src.Database import faiss_search

def main():
    st.title("AI-Powered Podcast Search & Fact-Checker")
    
    st.header("1. Fetch and Process Captions")
    video_url = st.text_input("Enter YouTube Video URL:")
    if st.button("Fetch Captions") and video_url:
        st.write("Fetching captions...")
        captions_url = CC.fetch_captions(video_url)
        if captions_url:
            st.success("Captions URL fetched!")
            captions_json = load_cc.fetch_captions_json(captions_url)
            if captions_json:
                load_cc.save_captions_to_csv(captions_json)
                st.success("Captions saved to CSV!")
                st.write("Creating FAISS index...")
                faiss_search.create_faiss_index()
                st.success("FAISS index created.")
            else:
                st.error("Failed to fetch captions JSON.")
        else:
            st.error("Failed to fetch captions URL. Check your video URL or cookies.")
    
    st.header("2. Search Captions")
    search_query = st.text_input("Enter your search query:")
    if st.button("Search") and search_query:
        results = faiss_search.search_faiss(search_query)
        if results is not None and not results.empty:
            st.write("### Search Results:")
            for _, row in results.iterrows():
                st.write(f"[{row['Timestamp (s)']} s] {row['Caption']}")
        else:
            st.write("No results found.")

if __name__ == "__main__":
    main()

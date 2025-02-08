```
📂 AI_Podcast_Search
│── LICENSE
│── README.md
│── requirements.txt
│── captions.csv
│── faiss_index.bin
│── captions_with_metadata.csv
│── captions.index
│── .gitignore
│── src/
│   │── __init__.py
│   │── UI/
│   │   │── app.py  # Streamlit UI
│   │
│   │── CC_capture/
│   │   │── __init__.py
│   │   │── CC.py  # Extract captions from YouTube
│   │   │── load_cc.py  # Fetch, clean, and store captions
│   │   │── cookies.txt  # Cookies for authentication
│   │
│   │── Database/
│   │   │── faiss_search.py  # FAISS search with refined timestamp format
│   │
│   │── pipelines/
│   │   │── __init__.py
│   │   │── captions_pipeline.py  # Fetch captions & store in DB
│   │   │── embedding_pipeline.py  # Convert captions to embeddings
│   │   │── search_pipeline.py  # Search captions and fetch surrounding context
│   │   │── fact_checker.py  # Validate claims using Groq & Crawl4AI
```
**Phase 1: Podcast Transcription & Search**

-   Fetch CC from YouTube Videos using `YouTube-transcript-API`. 
-   Store & index text using **FAISS / ChromaDB** for **fast retrieval**
-   Build a **basic search interface** (Streamlit / FastAPI)

 **Phase 2: Fact-Checking System**

-   Extract **claims/statements** using NLP
-   Use **Crawl4AI** to fetch relevant sources
-   Rank sources & flag misinformation using **similarity checks**

 **Phase 3: Full Web/App Deployment**

-   UI for **searching, highlighting timestamps, & fact-checking results**
-   Optimize for **real-time processing** & scale-up

### **Tech Stack & Tools**

| Component         | Tech Stack                          |
|-------------------|-------------------------------------|
| Fetch CC    		| youtube-transcript-api              |
| Search Indexing   | FAISS / ChromaDB                   |
| Fact-Checking     | Crawl4AI + LLMs (Groq API)         |
| Backend           | FastAPI / Flask                    |
| Frontend          | Streamlit (MVP) → React/Flutter (Full App) |
| Storage           | SQLite / Postgres (Metadata)       |


#### **First Task: Get Transcription & Search Working**

- **Goal:** Take a podcast audio file → **Convert to text** → **Make it searchable**  
- **Deliverable:** A simple **Streamlit app** that lets users upload audio & search within it.


# First Task: Fetch & Search YouTube Captions

#### **Step 1: Get YouTube Captions (CC) Programmatically**

We’ll use the **`youtube-transcript-api`** Python package to:  
✅ Fetch **captions from a given YouTube video**  
✅ Store **timestamps & text in a structured format**  
✅ Convert to **FAISS/ChromaDB embeddings** for searching

#### **Step 2: Search & Retrieve Key Parts of the Podcast**

✅ Build a **search function** so users can **enter a query & find relevant timestamps**  
✅ Output the **relevant text snippet + clickable timestamp**
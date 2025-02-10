# API Endpoints Plan

| Endpoint        | Method | Description                                               |
|-----------------|--------|-----------------------------------------------------------|
| /fetch-captions | POST   | Fetch YouTube captions and store them as a CSV & Generate a FAISS index from captions for efficient search.          |
| /search         | GET    | Search captions and return matching results.              |
| /summarize      | POST   | Summarize the full video transcript for quick insights.   |
| /fact-check     | POST   | Verify extracted context using AI and WebCrawler.         |

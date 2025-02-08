import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

CSV_FILE = "captions.csv"
FAISS_INDEX_FILE = "faiss_index.bin"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def search_faiss(query, context_window=30):
    """Searches FAISS for relevant captions & fetches context."""
    df = pd.read_csv(CSV_FILE)
    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode([query], convert_to_numpy=True)

    index = faiss.read_index(FAISS_INDEX_FILE)
    distances, indices = index.search(query_embedding, 1)
    
    result_idx = indices[0][0]
    if result_idx == -1:
        return None

    start_time = df.iloc[result_idx]["Timestamp"]
    
    return {"timestamp": start_time, "caption": df.iloc[result_idx]["Caption"]}

if __name__ == "__main__":
    query = input("Enter search query: ")
    results = search_faiss(query)
    print(results)

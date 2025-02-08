"""
faiss_search.py
----------------
Generates embeddings for captions using SentenceTransformers,
builds a FAISS index, and provides search functionality.
"""

import faiss
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_FILE = "faiss_index.bin"
CSV_FILE = "captions.csv"

# Initialize the embedding model once
model = SentenceTransformer(MODEL_NAME)

def get_embedding(text: str) -> np.ndarray:
    """
    Returns the embedding for the given text.
    """
    return model.encode(text, convert_to_numpy=True)

def create_faiss_index():
    """
    Loads captions from CSV, generates embeddings, and saves a FAISS index along with metadata.
    """
    df = pd.read_csv(CSV_FILE)
    captions = df["Caption"].tolist()
    embeddings = np.array([get_embedding(c) for c in captions]).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    # Save both index and DataFrame together for later retrieval.
    with open(FAISS_INDEX_FILE, "wb") as f:
        pickle.dump((index, df), f)
    print("FAISS index created and saved.")

def search_faiss(query: str, top_k: int = 1):
    """
    Searches for the caption most similar to the query.
    Returns the corresponding row from the DataFrame.
    """
    with open(FAISS_INDEX_FILE, "rb") as f:
        index, df = pickle.load(f)
    query_embedding = get_embedding(query).astype("float32").reshape(1, -1)
    distances, indices = index.search(query_embedding, top_k)
    if indices[0][0] == -1:
        return None
    # Return the best matching result along with its distance.
    row = df.iloc[indices[0][0]]
    return {"timestamp": row["Timestamp"], "caption": row["Caption"], "distance": distances[0][0]}

if __name__ == "__main__":
    create_faiss_index()
    q = input("Enter search query: ")
    res = search_faiss(q)
    print(res)

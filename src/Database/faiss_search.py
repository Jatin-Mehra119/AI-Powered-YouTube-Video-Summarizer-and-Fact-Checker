"""
faiss_search.py
----------------
This module handles the creation and querying of a FAISS index.
It loads the captions from a CSV file, generates embeddings using a
Hugging Face SentenceTransformer, and stores/queries them via FAISS.
"""

import faiss
import pandas as pd
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_FILE = "faiss_index.pkl"
CSV_FILE = "captions.csv"

# Initialize the embedding model (this may take a few seconds)
model = SentenceTransformer(MODEL_NAME)

def get_embedding(text: str) -> np.ndarray:
    """
    Generates an embedding for the given text.
    
    Args:
        text (str): Input text.
        
    Returns:
        np.ndarray: Embedding vector.
    """
    return model.encode(text, convert_to_numpy=True)

def create_faiss_index():
    """
    Loads captions from the CSV file, generates embeddings, and builds a FAISS index.
    The index and corresponding DataFrame are saved to disk.
    """
    df = pd.read_csv(CSV_FILE)
    captions = df["Caption"].tolist()
    embeddings = np.array([get_embedding(c) for c in captions]).astype("float32")
    
    # Create a flat L2 index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    # Save index and DataFrame together
    with open(FAISS_INDEX_FILE, "wb") as f:
        pickle.dump((index, df), f)
    print("FAISS index created and saved.")

def search_faiss(query: str, top_k: int = 5):
    """
    Searches the FAISS index for captions similar to the query.
    
    Args:
        query (str): The search query.
        top_k (int): Number of top results to return.
        
    Returns:
        pd.DataFrame: A subset of the captions DataFrame with the top matching entries.
    """
    try:
        with open(FAISS_INDEX_FILE, "rb") as f:
            index, df = pickle.load(f)
    except Exception as e:
        print("Error loading FAISS index. Run create_faiss_index() first.")
        return None

    query_embedding = get_embedding(query).astype("float32").reshape(1, -1)
    distances, indices = index.search(query_embedding, top_k)
    return df.iloc[indices[0]]
    
if __name__ == "__main__":
    # Test the indexing and search functionality.
    create_faiss_index()
    q = input("Enter search query: ")
    results = search_faiss(q)
    print(results)

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import os

CSV_FILE = "captions.csv"
FAISS_INDEX_FILE = "faiss_index.pkl"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def create_faiss_index():
    """Converts captions to embeddings and stores them in FAISS."""
    if not os.path.exists(CSV_FILE):
        print("CSV file not found.")
        return

    df = pd.read_csv(CSV_FILE)
    captions = df["Caption"].tolist()
    
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(captions, convert_to_numpy=True)

    d = embeddings.shape[1]  
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)

    faiss.write_index(index, FAISS_INDEX_FILE)
    print("FAISS index saved.")

if __name__ == "__main__":
    create_faiss_index()

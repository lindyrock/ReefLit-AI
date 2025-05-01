#!/usr/bin/env python
"""
search_index.py
Example:
    python src/search_index.py "ocean acidification carbonate"
"""

from pathlib import Path
import pickle, argparse
import faiss
from sentence_transformers import SentenceTransformer

IDX  = Path("index/reeflit.faiss")
META = Path("index/metadata.pkl")

model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index(str(IDX))
metadata = pickle.load(META.open("rb"))

def query(q, k=5):
    qvec = model.encode(q, normalize_embeddings=True).reshape(1,-1)
    D,I  = index.search(qvec, k)
    for rank,(dist,idx) in enumerate(zip(D[0], I[0]),1):
        m = metadata[idx]
        print(f"{rank:>2}. ({dist:.3f})  {m['title']}")
        print(f"    DOI: {m['doi']}  |  Tags: {m['stressors']}\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+", help="Free-text query")
    ap.add_argument("-k", type=int, default=5, help="Top-K")
    args = ap.parse_args()
    query(" ".join(args.query), k=args.k)

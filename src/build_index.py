#!/usr/bin/env python
"""
build_index.py  ▸ ReefLit AI
Transforms title+abstract into Sentence-Transformer embeddings
and saves a FAISS index + metadata pickle.

Run:
    python src/build_index.py                      # default paths
"""

from pathlib import Path
import json, pickle, argparse, logging

import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s",
                    force=True)

def get_text(rec):
    return (rec.get("title") or "") + " " + (rec.get("abstract") or "")

def main(args):
    in_path  = Path(args.input)
    idx_path = Path(args.index)
    meta_path= Path(args.meta)
    idx_path.parent.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    dim   = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatIP(dim)          # cosine via inner-product on normalised vecs

    metadata = []                           # keep DOI + title etc.

    logging.info("Embedding corpus …")
    with in_path.open() as fh:
        for rec in tqdm(map(json.loads, fh)):
            vec = model.encode(get_text(rec), normalize_embeddings=True)
            index.add(vec.reshape(1,-1))
            metadata.append({
                "doi"   : rec.get("doi"),
                "title" : rec.get("title","")[:300],
                "stressors": rec.get("stressors", [])
            })

    logging.info("Records indexed: %d", index.ntotal)
    faiss.write_index(index, str(idx_path))
    pickle.dump(metadata, meta_path.open("wb"))
    logging.info("Saved FAISS ➜ %s  |  meta ➜ %s", idx_path, meta_path)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/corpus_labeled.jsonl")
    p.add_argument("--index", default="index/reeflit.faiss")
    p.add_argument("--meta",  default="index/metadata.pkl")
    main(p.parse_args())

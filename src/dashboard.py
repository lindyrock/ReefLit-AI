#!/usr/bin/env python
"""
dashboard.py ▸ ReefLit AI
---------------------------------------
Run:
    streamlit run src/dashboard.py
"""

from pathlib import Path
import pickle, json, collections

import streamlit as st
import plotly.express as px
from sentence_transformers import SentenceTransformer
import faiss

# --------- Config paths --------- #
INDEX_PATH = Path("index/reeflit.faiss")
META_PATH  = Path("index/metadata.pkl")
LABELED_PATH = Path("data/corpus_labeled.jsonl")

@st.cache_resource
def load_search_engine():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index(str(INDEX_PATH))
    metadata = pickle.load(META_PATH.open("rb"))
    return model, index, metadata

@st.cache_data
def load_counts():
    counts = collections.Counter()
    with LABELED_PATH.open() as fh:
        for line in fh:
            rec = json.loads(line)
            for s in rec.get("stressors", []):
                counts[s] += 1
    return counts

def search(query, k=5):
    model, index, metadata = load_search_engine()
    qvec = model.encode(query, normalize_embeddings=True).reshape(1, -1)
    D, I = index.search(qvec, k)
    results = []
    for dist, idx in zip(D[0], I[0]):
        m = metadata[idx]
        results.append({"score": float(dist), **m})
    return results

# --------------- UI --------------- #
st.set_page_config(page_title="ReefLit AI – Demo", layout="wide")
st.title("📚 ReefLit AI – Literature Dashboard (stub)")

# -- Bar chart
counts = load_counts()
chart = px.bar(
    x=list(counts.keys()),
    y=list(counts.values()),
    labels={"x": "Stressor", "y": "Paper count"},
    title="Papers per stressor (weak-labels)"
)
st.plotly_chart(chart, use_container_width=True)

# -- Search
st.header("🔎 Semantic search")
query = st.text_input("Enter search phrase", "")
k = st.slider("Top-K", 1, 10, 5, 1)
if query:
    with st.spinner("Searching…"):
        results = search(query, k)
    for r in results:
        st.markdown(f"**{r['title']}**")
        st.write(f"DOI: {r['doi']}   |  Tags: {r['stressors']}   |  Score: {r['score']:.3f}")
        st.markdown("---")

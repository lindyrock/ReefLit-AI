# ReefLit AI Pipeline

> **Goal:** Continuously transform the fire‑hose of coral‑reef literature into queryable, up‑to‑date evidence graphs and dashboards— with end‑to‑end reproducibility.

---

## 🗺️ High‑Level Flow

```mermaid
flowchart TD
    subgraph Ingest
        A1[CrossRef API]
        A2[PubMed API]
        A3[bioRxiv RSS]
        A4[NOAA CoRIS CSV]
        A5[Springer RSS]
        A1 --> B[Raw JSONL]
        A2 --> B
        A3 --> B
        A4 --> B
        A5 --> B
    end

    subgraph Screening
        B --> C[Weak‑Supervision Rule‑Matcher <br> (stressors.yml)]
        C --> D[Labelled JSONL]
    end

    subgraph Enrichment
        D --> E[PDF Fetcher  ➜  Text Extractor]
        E --> F[spaCy / scispaCy NER]
        D --> F
        F --> G[Embeddings (Sentence‑Transformers)]
    end

    subgraph Storage
        G --> H[FAISS Vector DB]
        F --> I[Postgres / DuckDB]
    end

    subgraph Synthesis
        H --> J[RAG Q&A API]
        I --> K[Plots & KPIs]
        I --> L[Neo4j Knowledge Graph]
    end

    subgraph Serve
        J --> M[Dash/Streamlit Dashboard]
        K --> M
        L --> M
    end

    click stressors.yml "../stressors.yml" "Taxonomy"
```

---

## 1️⃣ Ingest
| Component | Purpose | Notes |
|-----------|---------|-------|
| **`fetch.py`** | Harvest metadata (title, abstract, DOI, journal, year) from each source. | Rate‑limited; retries with exponential back‑off. |
| **Storage** | Append to `data/raw/YYYY-MM-DD.jsonl`. | Raw dump kept for provenance; never overwritten. |

### Data Sources
* CrossRef query: `coral reef` OR `scleractinia`
* PubMed E‑Utils search: mesh terms `coral reefs` + `2010:` current
* bioRxiv RSS filter: keyword `coral`
* NOAA CoRIS publications CSV (monthly)
* Springer **Coral Reefs** journal RSS

## 2️⃣ Screening (Weak Supervision)
* **Rule‑Matcher**: spaCy pipeline loads `stressors.yml` to assign provisional multi‑label tags (`warming`, `acidification`, etc.).
* **Confidence score** = (# matched keywords) ÷ (keywords per stressor).
* **Output** saved to `data/processed/screened.jsonl`.

> **Why weak supervision?**  Bootstraps a usable corpus without hundreds of manual annotations; iterative active‑learning cycles will refine.

## 3️⃣ Enrichment
| Step | Tooling | Output |
|------|---------|--------|
| **PDF Fetch** | Unpaywall + Publisher URLs; fallback to ScienceHub. | `pdfs/DOI.pdf` |
| **Text Extraction** | `PyMuPDF` to plaintext; fallback `GROBID` TEI. | `txt/DOI.txt` |
| **NER** | spaCy (`en_core_sci_lg`) + custom entities (`LOCATION`, `METHOD`, `INTERVENTION`). | token spans + JSONL |
| **Embeddings** | `sentence-transformers/all-mpnet-base-v2` on title+abstract. | `faiss/index.bin` |

## 4️⃣ Storage
* **Postgres/DuckDB** stores metadata + NER output (easy SQL joins).
* **FAISS** provides fast vector similarity for RAG queries.
* **Neo4j** (optional) builds graph of `Reef ↔ Stressor ↔ Intervention`.

## 5️⃣ Synthesis
* **KPIs**: count papers per stressor, per region, yearly trends.
* **Forest plots**: meta‑analysis of effect sizes where extractable.
* **RAG Q&A**: Haystack pipeline pulls top‑k similar embeddings + abstracts, feeds to OpenAI (or local LLM) to craft answer citations.

## 6️⃣ Serve
* **Dashboard**: Dash/Plotly app shows KPIs, lets users ask our API, and downloads CSV.
* **API**: `/query?q="heat stress Western Pacific"&top_n=10` returns JSON with citations, scores.

---

## 🔄 Automation
* **GitHub Actions** nightly workflow (`.github/workflows/pipeline.yml`):
  1. `fetch.py` → commit raw JSONL artefact.
  2. `screen.py` → commit processed JSONL.
  3. `enrich.py` → push updated FAISS & DB dumps to cloud‑storage.
  4. Trigger Render deploy webhook to refresh dashboard.

## 🛠️ Local Development
```bash
conda env create -f environment.yml
conda activate reeflit
# Run pipeline end‑to‑end on a sample day
python pipeline/run_local.py --date 2025-04-29 --sample 500
# Launch dashboard
streamlit run app.py
```

## 🔒 Data & Ethics
* **Licenses:** store DOIs only; PDFs fetched are for text‑mining under fair use, never re‑distributed.
* **Attribution:** Every dashboard claim links back to source DOI.
* **Transparency:** All weak‑supervision rules & evaluation notebooks are public.

## 📈 Future Enhancements
1. Active‑learning UI for manual validation.
2. Fine‑tuned SciBERT classifier to replace rules.
3. Automatic PRISMA diagram rendering per stressor.
4. Webhooks for email/Slack alerts when new high‑impact papers appear.

---

_Questions?  Open an issue or reach us on X/Twitter [@ReefLitAI](https://twitter.com/reeflitai)._
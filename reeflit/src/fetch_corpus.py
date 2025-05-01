"""fetch_corpus.py  ▸ ReefLit AI
-------------------------------------------------
Fetch ≥ N recent coral-reef papers from CrossRef **and** PubMed, then write a
deduplicated newline-delimited JSON corpus so downstream pipelines can run
locally or in CI.

Run (default 5,000 records):
    python src/fetch_corpus.py              # → data/coral_corpus.jsonl
    python src/fetch_corpus.py --max 10000  # custom

The script is idempotent: if the output file already exists it will overwrite
**only** when `--force` flag is passed.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Iterable

import requests
from retrying import retry  # lightweight retry lib (<10 KB)
from tqdm.auto import tqdm

############################################################
# Logging setup                                            #
############################################################
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("reeflit.fetch")

############################################################
# Constants                                                #
############################################################
DEFAULT_MAX = 5_000
DEFAULT_YEARS_BACK = 20
DATA_DIR = Path("data")
OUTPUT_PATH = DATA_DIR / "coral_corpus.jsonl"
HEADERS = {
    "User-Agent": "ReefLitAI/0.1 (mailto:contact@reeflit.ai)",
}
CROSSREF_URL = "https://api.crossref.org/works"
PUBMED_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=json&id="
)

############################################################
# Helpers                                                  #
############################################################

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch coral-reef literature corpus")
    p.add_argument("--max", type=int, default=DEFAULT_MAX, help="records to fetch (≥)")
    p.add_argument("--force", action="store_true", help="overwrite existing file")
    return p.parse_args()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)


############################################################
# CrossRef                                                 #
############################################################
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1_000)
def _get_crossref_cursor(cursor: str | None = None, rows: int = 1000):
    params = {
        "query": "coral reef",
        "filter": f"from-pub-date:{datetime.utcnow().year - DEFAULT_YEARS_BACK}-01-01",
        "rows": rows,
        "cursor": cursor or "*",
    }
    r = requests.get(CROSSREF_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def iter_crossref(max_records: int) -> Iterable[dict]:
    """Yield CrossRef items until max_records reached."""
    fetched = 0
    cursor = None
    pbar = tqdm(total=max_records, desc="CrossRef")
    while fetched < max_records:
        data = _get_crossref_cursor(cursor)
        cursor = data["message"].get("next-cursor")
        for item in data["message"]["items"]:
            if "title" not in item or not item["title"]:
                continue
            yield {
                "title": item["title"][0],
                "abstract": item.get("abstract", ""),
                "doi": item.get("DOI", ""),
                "year": item.get("issued", {}).get("date-parts", [[None]])[0][0],
                "source": "crossref",
            }
            fetched += 1
            pbar.update(1)
            if fetched >= max_records:
                break
        if cursor is None:
            break
    pbar.close()


############################################################
# PubMed                                                   #
############################################################
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1_000)
def _search_pubmed(retmax: int, retstart: int = 0) -> list[str]:
    params = {
        "db": "pubmed",
        "term": "coral reef",
        "retmode": "json",
        "retmax": retmax,
        "retstart": retstart,
        "datetype": "pdat",
        "mindate": datetime.utcnow().year - DEFAULT_YEARS_BACK,
    }
    r = requests.get(PUBMED_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    return ids

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1_000)
def _fetch_pubmed_details(ids: list[str]) -> list[dict]:
    ids_str = ",".join(ids)
    r = requests.get(PUBMED_FETCH_URL + ids_str, headers=HEADERS, timeout=30)
    r.raise_for_status()
    docs = r.json()["result"]
    results = []
    for key, itm in docs.items():
        if key == "uids":
            continue
        if not itm.get("title"):
            continue
        results.append(
            {
                "title": itm.get("title"),
                "abstract": itm.get("abstract", ""),
                "doi": itm.get("elocationid", ""),
                "year": itm.get("pubdate", "").split(" ")[0],
                "source": "pubmed",
            }
        )
    return results


def iter_pubmed(max_records: int, batch: int = 200) -> Iterable[dict]:
    fetched = 0
    start = 0
    pbar = tqdm(total=max_records, desc="PubMed")
    while fetched < max_records:
        ids = _search_pubmed(retmax=batch, retstart=start)
        if not ids:
            break
        papers = _fetch_pubmed_details(ids)
        for p in papers:
            yield p
            fetched += 1
            pbar.update(1)
            if fetched >= max_records:
                break
        start += batch
    pbar.close()


############################################################
# Main                                                     #
############################################################

def fetch_corpus(max_records: int = DEFAULT_MAX) -> list[dict]:
    logger.info("Fetching %s records (target)", max_records)
    records = {}
    for paper in iter_crossref(max_records):
        records[paper["doi"] or paper["title"]] = paper
        if len(records) >= max_records:
            break
    if len(records) < max_records:
        for paper in iter_pubmed(max_records * 2):  # extra to cover dups
            records[paper["doi"] or paper["title"]] = paper
            if len(records) >= max_records:
                break
    logger.info("Collected %s deduplicated records", len(records))
    return list(records.values())


def save_jsonl(corpus: list[dict], path: Path):
    ensure_data_dir()
    with path.open("w", encoding="utf-8") as f:
        for rec in corpus:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")
    logger.info("Saved corpus → %s", path)


def main():
    args = parse_args()
    if OUTPUT_PATH.exists() and not args.force:
        logger.warning("%s already exists. Use --force to overwrite.", OUTPUT_PATH)
        return
    corpus = fetch_corpus(max_records=args.max)
    save_jsonl(corpus, OUTPUT_PATH)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
weak_label.py  ▸ ReefLit AI
---------------------------------
Weak-supervision tagger that scans each
paper's title/abstract and assigns one
or more stressor labels using spaCy's
phrase-matcher.

Run:
    python src/weak_label.py                            # default paths
    python src/weak_label.py --in data/coral*.jsonl \
                             --out data/corpus_labeled.jsonl
"""

from pathlib import Path
import json
import yaml
import argparse
import logging
from collections import Counter

import spacy
from spacy.matcher import PhraseMatcher
from tqdm import tqdm

# --------------------------------------------------------------------------- #
#  Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,  # works in scripts & notebooks
)
logger = logging.getLogger("weak_label")

# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def load_taxonomy(path: Path) -> dict:
    """Read YAML taxonomy → {stressor: [keywords]}"""
    with path.open() as fh:
        tax = yaml.safe_load(fh)
    return {k: [s.lower() for s in v] for k, v in tax.items()}


def build_matcher(nlp, taxonomy: dict) -> PhraseMatcher:
    """Compile spaCy PhraseMatcher with all keywords."""
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for stressor, phrases in taxonomy.items():
        patterns = [nlp.make_doc(p) for p in phrases]
        matcher.add(stressor, patterns)
    return matcher


def tag_text(matcher: PhraseMatcher, doc) -> list[str]:
    """Return list of stressors matched in doc (deduped)."""
    matches = matcher(doc)
    return sorted({doc.vocab.strings[match_id] for match_id, _, _ in matches})


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main(args):
    nlp = spacy.blank("en")  # tokenizer-only; lightweight
    taxonomy = load_taxonomy(Path(args.taxonomy))
    matcher = build_matcher(nlp, taxonomy)

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    label_counts = Counter()
    total, with_any = 0, 0

    logger.info("Reading %s …", in_path.name)
    with in_path.open() as fin, out_path.open("w") as fout:
        for line in tqdm(fin, desc="Tagging"):
            total += 1
            record = json.loads(line)

            # Combine title + abstract (if present)
            text_parts = [record.get("title", "")]
            if record.get("abstract"):
                text_parts.append(record["abstract"])
            text = " ".join(text_parts).lower()

            doc = nlp(text)
            labels = tag_text(matcher, doc)
            record["stressors"] = labels

            if labels:
                with_any += 1
                label_counts.update(labels)

            fout.write(json.dumps(record) + "\n")

    # ---------------- Summary ---------------- #
    logger.info("Finished tagging %s records", total)
    logger.info("Records with ≥1 label: %s (%.1f%%)",
                with_any, 100 * with_any / total)
    logger.info("Label distribution:")
    for lbl, cnt in label_counts.most_common():
        logger.info("  %-20s %4d", lbl, cnt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--taxonomy",
        default="config/stressors.yml",
        help="Path to stressor keyword YAML.",
    )
    parser.add_argument(
        "--input",
        default="data/coral_corpus.jsonl",
        help="Input JSONL file from fetch_corpus.",
    )
    parser.add_argument(
        "--output",
        default="data/corpus_labeled.jsonl",
        help="Output JSONL with stressors field.",
    )
    args = parser.parse_args()
    main(args)

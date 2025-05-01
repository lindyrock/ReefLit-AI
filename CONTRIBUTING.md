# Contributing to **ReefLit AI**

> We love pull‑requests!  This guide explains the dev setup, coding style, and review process so your contribution lands smoothly.

---

## 📋 Table of Contents
1. [Getting Started](#getting-started)
2. [How to Propose Changes](#how-to-propose-changes)
3. [Coding & Style Guide](#coding--style-guide)
4. [Running Tests](#running-tests)
5. [Pipeline Data Tips](#pipeline-data-tips)
6. [Issue & PR Etiquette](#issue--pr-etiquette)
7. [Code of Conduct](#code-of-conduct)

---

## Getting Started

```bash
# fork + clone
$ git clone https://github.com/lindyrock/ReefLit-AI.git
$ cd ReefLit-AI

# conda env (preferred)
$ conda env create -f environment.yml
$ conda activate reeflit

# install editable package
$ pip install -e .
```

The **environment.yml** locks core libraries (`spaCy`, `sentence-transformers`, `FAISS`, `Dash`, etc.).  Feel free to use **mamba** for faster solves.

### Pre‑commit hooks *(optional but encouraged)*
```bash
$ pre-commit install  # auto‑formats on commit
```

---

## How to Propose Changes
1. **Open an Issue** — describe the bug or feature; maintainers will triage.  
2. **Create a Branch**: `git checkout -b feat/<short-slug>`  
3. **Commit Atomically**: one logical change per commit; follow Conventional Commits (`fix:`, `feat:`, `docs:` …).  
4. **Push & PR**: `git push origin feat/<slug>` then open a Pull Request; link the issue.

> **First‑timers:** look for ⭐︎`good-first-issue` labels.

---

## Coding & Style Guide
* **Python ≥3.10**  
* PEP‑8 via **black** (⩽88 char line) and **isort** for imports.  
* Type hints required for new functions; run **mypy** locally.  
* Docstrings: Google style.

##### Directory Overview
```
ReefLit-AI/
├── pipelines/        # ETL + weak‑label scripts
├── app/              # Dash / FastAPI code
├── reeflit/          # lib code (models, utils)
├── tests/            # pytest suite
└── docs/             # md + images (architecture, how‑tos)
```

---

## Running Tests
```bash
$ pytest -q   # unit + integration
```
Coverage must stay ≥90 % for core modules.

GitHub Actions runs the same suite on every PR.

---

## Pipeline Data Tips
* **Taxonomy edits** → edit `config/stressors.yml` + update tests.  
* **Large files** (>100 MB) → avoid committing; use links to Zenodo or `reefdata/` S3 bucket.  
* **Secrets** → never commit keys; use `dotenv` and GitHub repo secrets for CI.

---

## Issue & PR Etiquette
* Be respectful, stay on topic, and provide reproduction steps.  
* Small PRs merge faster than mega‑PRs.  
* Tag reviewers when ready (`@lindyrock`, etc.).

---

## Code of Conduct
This project adheres to the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).  By participating, you agree to uphold these guidelines.

---

Happy hacking & thank you for helping advance coral‑reef science! 🌊🪸


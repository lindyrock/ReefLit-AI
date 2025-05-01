#!/usr/bin/env python
"""
Download the newest 'reeflit-data' artifact from GitHub Actions
and extract it to data/ and index/ folders.

Render sets GITHUB_TOKEN env-var so this script runs unauthenticated locally
and authenticated in production.
"""
from pathlib import Path
import os, sys, requests, zipfile, io, logging

REPO   = "lindyrock/ReefLit-AI"     
WORKFLOW_NAME = "nightly-pipeline"         # job name in ci.yml
ARTIFACT_NAME = "reeflit-data"

logging.basicConfig(level=logging.INFO, format="%(message)s")

def get_latest_artifact_url():
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN','')}"}
    runs_url = f"https://api.github.com/repos/{REPO}/actions/workflows/ci.yml/runs?status=success&branch=main"
    runs = requests.get(runs_url, headers=headers).json().get("workflow_runs", [])
    if not runs:
        logging.error("No successful runs found.")
        sys.exit(1)
    run_id = runs[0]["id"]
    artifacts_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts"
    artifacts = requests.get(artifacts_url, headers=headers).json().get("artifacts", [])
    for art in artifacts:
        if art["name"] == ARTIFACT_NAME:
            return art["archive_download_url"]
    logging.error("Artifact not found.")
    sys.exit(1)

def download_and_extract(url):
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN','')}"}
    logging.info("Downloading artifact …")
    r = requests.get(url, headers=headers)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(".")
    logging.info("✓ Extracted files: %s", z.namelist())
    logging.info("✅ Fetched latest artifact from %s", run_id)


if __name__ == "__main__":
    url = get_latest_artifact_url()
    download_and_extract(url)

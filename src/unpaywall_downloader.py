import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import Optional, List, Set
from urllib.parse import urlparse
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_download.log'),
        logging.StreamHandler()
    ]
)

def get_unpaywall_data(doi: str, email: str) -> Optional[dict]:
    """
    Query Unpaywall API for a given DOI.
    
    Args:
        doi: The DOI to query
        email: Your email address (required by Unpaywall API)
    
    Returns:
        dict: Unpaywall data if successful, None if failed
    """
    base_url = "https://api.unpaywall.org/v2"
    url = f"{base_url}/{doi}?email={email}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data for DOI {doi}: {e}")
        return None

def get_pdf_urls(data: dict) -> List[str]:
    """
    Extract all possible PDF URLs from Unpaywall data.
    Prioritizes publisher URLs over repository URLs.
    
    Args:
        data: Unpaywall API response data
    
    Returns:
        List[str]: List of PDF URLs to try
    """
    urls = []
    
    # First try the best OA location
    if data.get('best_oa_location'):
        best_loc = data['best_oa_location']
        if best_loc.get('url_for_pdf'):
            urls.append(best_loc['url_for_pdf'])
        elif best_loc.get('url'):
            urls.append(best_loc['url'])
    
    # Then try other OA locations
    for location in data.get('oa_locations', []):
        if location.get('url_for_pdf'):
            urls.append(location['url_for_pdf'])
        elif location.get('url'):
            urls.append(location['url'])
    
    return list(dict.fromkeys(urls))  # Remove duplicates while preserving order

def download_pdf(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """
    Download a PDF from a given URL with retries.
    
    Args:
        url: URL of the PDF to download
        output_path: Path where to save the PDF
        max_retries: Maximum number of retry attempts
    
    Returns:
        bool: True if download successful, False otherwise
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if we got a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'application/pdf' not in content_type and not url.endswith('.pdf'):
                logging.warning(f"Response from {url} doesn't appear to be a PDF (content-type: {content_type})")
                return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify the file is not empty
            if output_path.stat().st_size == 0:
                logging.warning(f"Downloaded file is empty from {url}")
                return False
                
            return True
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
    
    return False

def process_doi(doi: str, email: str, output_dir: Path) -> bool:
    """
    Process a single DOI: query Unpaywall and download PDF if available.
    
    Args:
        doi: The DOI to process
        email: Your email address for Unpaywall API
        output_dir: Directory to save PDFs
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Query Unpaywall
    data = get_unpaywall_data(doi, email)
    if not data:
        return False
    
    # Check if OA PDF is available
    if not data.get('is_oa'):
        logging.info(f"No OA version available for DOI: {doi}")
        return False
    
    # Get all possible PDF URLs
    pdf_urls = get_pdf_urls(data)
    if not pdf_urls:
        logging.info(f"No PDF URLs found for DOI: {doi}")
        return False
    
    # Create filename from DOI
    filename = f"{doi.replace('/', '_')}.pdf"
    output_path = output_dir / filename
    
    # Try each URL until one works
    for url in pdf_urls:
        logging.info(f"Trying to download from: {url}")
        if download_pdf(url, output_path):
            logging.info(f"Successfully downloaded PDF for DOI: {doi}")
            return True
    
    logging.warning(f"Failed to download PDF for DOI: {doi} after trying all URLs")
    return False

def get_existing_pdfs(output_dir: Path) -> Set[str]:
    """Get set of DOIs that have already been downloaded."""
    return {f.stem.replace('_', '/') for f in output_dir.glob('*.pdf')}

def process_corpus(corpus_path: str, email: str, output_dir: Path, batch_size: int = 100):
    """
    Process DOIs from a JSONL corpus file.
    
    Args:
        corpus_path: Path to the JSONL file
        email: Your email address for Unpaywall API
        output_dir: Directory to save PDFs
        batch_size: Number of DOIs to process before saving progress
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Get already downloaded PDFs
    existing_dois = get_existing_pdfs(output_dir)
    logging.info(f"Found {len(existing_dois)} existing PDFs")
    
    # Process DOIs from corpus
    processed_count = 0
    success_count = 0
    
    with open(corpus_path, 'r') as f:
        # Use tqdm for progress bar
        for line in tqdm(f, desc="Processing DOIs"):
            try:
                data = json.loads(line)
                doi = data.get('doi')
                
                if not doi:
                    continue
                
                # Skip if already downloaded
                if doi in existing_dois:
                    continue
                
                # Process DOI
                if process_doi(doi, email, output_dir):
                    success_count += 1
                
                processed_count += 1
                
                # Add delay between requests
                time.sleep(1)
                
                # Log progress periodically
                if processed_count % batch_size == 0:
                    logging.info(f"Processed {processed_count} DOIs, {success_count} successful downloads")
                
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON line: {e}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error processing DOI: {e}")
                continue
    
    logging.info(f"Finished processing {processed_count} DOIs")
    logging.info(f"Successfully downloaded {success_count} PDFs")

def main():
    # Your email for Unpaywall API
    email = "rauchstar23@yahoo.com"
    
    # Process corpus
    corpus_path = "data/coral_corpus.jsonl"
    output_dir = Path("pdfs")
    
    process_corpus(corpus_path, email, output_dir)

if __name__ == "__main__":
    main() 
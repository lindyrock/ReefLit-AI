import json
from pathlib import Path
import logging
from tqdm import tqdm
from effect_size_ner import EffectSizeNER
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_doi_from_filename(filename: str) -> str:
    """Extract DOI from filename.
    
    Args:
        filename: Name of the text file (e.g., '10.3755_jcrs.20.89.txt')
        
    Returns:
        DOI string (e.g., '10.3755/jcrs.20.89')
    """
    # Remove .txt extension
    doi = filename[:-4]
    
    # Split into prefix and suffix
    parts = doi.split('_', 1)
    if len(parts) != 2:
        logger.warning(f"Unexpected filename format: {filename}")
        return doi
    
    prefix, suffix = parts
    
    # Handle special cases
    if 'galaxea.g' in suffix:
        # For galaxea.g2020_s3r format
        return f"{prefix}/{suffix}"
    elif 'galaxea.' in suffix and '_' in suffix:
        # For galaxea.21.1_27 format
        return f"{prefix}/{suffix}"
    elif 'journal.' in suffix:
        # For journal.pone.0234567 format
        return f"{prefix}/{suffix}"
    elif 'fmars.' in suffix:
        # For fmars.2020.00001 format
        return f"{prefix}/{suffix}"
    elif 's41598-' in suffix:
        # For s41598-020-63625-0 format
        return f"{prefix}/{suffix}"
    elif 'pnas.' in suffix:
        # For pnas.091092998 format
        return f"{prefix}/{suffix}"
    else:
        # For standard format, replace remaining underscores with forward slashes
        return f"{prefix}/{suffix.replace('_', '/')}"

def process_corpus(jsonl_file: str, txt_dir: str, output_file: str):
    """Process corpus and add effect size information.
    
    Args:
        jsonl_file: Path to input JSONL file with metadata
        txt_dir: Directory containing text files
        output_file: Path to output JSONL file
    """
    try:
        # Initialize NER
        ner = EffectSizeNER()
        
        # Verify patterns are loaded
        if not ner.verify_patterns():
            logger.error("Failed to load patterns properly")
            return
        
        # Load all JSONL records into memory for quick lookup
        logger.info("Loading JSONL records...")
        records = {}
        records_without_doi = 0
        with open(jsonl_file, 'r') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doi = doc.get('doi')
                    if doi:
                        records[doi] = doc
                    else:
                        records_without_doi += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {str(e)}")
                    continue
        
        logger.info(f"Loaded {len(records)} records with DOIs")
        if records_without_doi > 0:
            logger.warning(f"Found {records_without_doi} records without DOIs")
        
        # Get list of text files
        txt_path = Path(txt_dir)
        txt_files = list(txt_path.glob('*.txt'))
        
        logger.info(f"Found {len(txt_files)} text files")
        
        # Track statistics
        processed = 0
        skipped_no_record = 0
        skipped_empty = 0
        skipped_errors = 0
        
        # Process each text file
        with open(output_file, 'w') as f_out:
            for txt_file in tqdm(txt_files):
                try:
                    # Get DOI from filename
                    doi = get_doi_from_filename(txt_file.name)
                    
                    # Look up record
                    doc = records.get(doi)
                    if not doc:
                        logger.warning(f"No record found for DOI: {doi} (file: {txt_file.name})")
                        skipped_no_record += 1
                        continue
                    
                    # Read text content
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    if not text.strip():
                        logger.warning(f"Empty text in file: {txt_file}")
                        skipped_empty += 1
                        continue
                    
                    # Extract effects
                    effects = []
                    entities = ner.get_entities(text)
                    
                    for entity in entities:
                        effects.append({
                            'type': entity['label'],
                            'value': entity['text'],
                            'description': entity['description'],
                            'start': entity['start'],
                            'end': entity['end']
                        })
                    
                    # Add effects to document
                    doc['effects'] = effects
                    
                    # Write enriched document
                    f_out.write(json.dumps(doc) + '\n')
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {txt_file}: {str(e)}")
                    skipped_errors += 1
                    continue
        
        # Log final statistics
        logger.info("Processing complete. Statistics:")
        logger.info(f"- Total text files: {len(txt_files)}")
        logger.info(f"- Successfully processed: {processed}")
        logger.info(f"- Skipped (no matching record): {skipped_no_record}")
        logger.info(f"- Skipped (empty text): {skipped_empty}")
        logger.info(f"- Skipped (errors): {skipped_errors}")
        logger.info(f"Output written to {output_file}")
        
    except Exception as e:
        logger.error(f"Error in process_corpus: {str(e)}")
        raise

def main():
    """Main function to process corpus."""
    jsonl_file = "data/corpus_labeled.jsonl"
    txt_dir = "txt"
    output_file = "data/corpus_effects.jsonl"
    
    process_corpus(jsonl_file, txt_dir, output_file)

if __name__ == "__main__":
    main() 
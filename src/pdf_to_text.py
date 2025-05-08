import os
import logging
import warnings
from pathlib import Path
from typing import Optional, Tuple
from io import StringIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_extraction.log'),
        logging.StreamHandler()
    ]
)

# Suppress PDFMiner color space warnings
warnings.filterwarnings('ignore', message='.*Cannot set gray non-stroke color.*')

def extract_text_from_pdf(pdf_path: Path, output_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Extract text from a PDF file and save it to a text file.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path where to save the extracted text
    
    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    try:
        # Configure PDFMiner parameters for better text extraction
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
            detect_vertical=True
        )
        
        # Extract text
        text = extract_text(pdf_path, laparams=laparams)
        
        # Basic text cleaning
        text = text.replace('\x0c', '')  # Remove form feed characters
        text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        
        # Save to file
        output_path.write_text(text, encoding='utf-8')
        
        return True, None
        
    except Exception as e:
        error_msg = f"Error extracting text from {pdf_path}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def process_pdfs(pdf_dir: Path, txt_dir: Path, batch_size: int = 100):
    """
    Process all PDFs in a directory and extract their text.
    
    Args:
        pdf_dir: Directory containing PDF files
        txt_dir: Directory where to save extracted text files
        batch_size: Number of files to process before logging progress
    """
    # Create output directory if it doesn't exist
    txt_dir.mkdir(exist_ok=True)
    
    # Get list of PDF files
    pdf_files = list(pdf_dir.glob('*.pdf'))
    total_files = len(pdf_files)
    
    if total_files == 0:
        logging.warning(f"No PDF files found in {pdf_dir}")
        return
    
    logging.info(f"Found {total_files} PDF files to process")
    
    # Process files
    success_count = 0
    error_count = 0
    error_files = []
    
    for pdf_file in tqdm(pdf_files, desc="Extracting text from PDFs"):
        # Create corresponding text file path
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        
        # Skip if text file already exists
        if txt_file.exists():
            logging.info(f"Skipping {pdf_file.name} - text file already exists")
            continue
        
        # Extract text
        success, error = extract_text_from_pdf(pdf_file, txt_file)
        
        if success:
            success_count += 1
        else:
            error_count += 1
            error_files.append((pdf_file.name, error))
        
        # Log progress periodically
        if (success_count + error_count) % batch_size == 0:
            logging.info(f"Processed {success_count + error_count}/{total_files} files")
    
    # Log final statistics
    logging.info(f"\nExtraction complete:")
    logging.info(f"Total files processed: {total_files}")
    logging.info(f"Successful extractions: {success_count}")
    logging.info(f"Failed extractions: {error_count}")
    
    if error_files:
        logging.info("\nFailed files:")
        for filename, error in error_files:
            logging.info(f"- {filename}: {error}")

def main():
    # Set up directories
    pdf_dir = Path("pdfs")
    txt_dir = Path("txt")
    
    # Process PDFs
    process_pdfs(pdf_dir, txt_dir)

if __name__ == "__main__":
    main() 
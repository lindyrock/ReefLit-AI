import json
import random
import pandas as pd
from pathlib import Path
from typing import List, Dict
import logging
from utils import doi_to_filename, filename_to_doi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_effects(jsonl_path: str) -> List[Dict]:
    """Load effects from JSONL file."""
    effects = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            doc = json.loads(line)
            doi = doc.get('doi', '')
            # Get text from the corresponding txt file
            txt_path = Path('txt') / f"{doi_to_filename(doi)}.txt"
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as txt_file:
                    text = txt_file.read()
            else:
                logger.warning(f"Text file not found for DOI: {doi}")
                text = ""
            
            for effect in doc.get('effects', []):
                effect['doi'] = doi
                effect['text'] = text
                effects.append(effect)
    return effects

def get_context(text: str, start: int, end: int, window: int = 100) -> str:
    """Get text context around the effect.
    
    Args:
        text: Full text content
        start: Start position of the effect
        end: End position of the effect
        window: Number of characters to include before and after
        
    Returns:
        Raw text context around the effect
    """
    if not text:
        return ""
    
    # Get context window
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    
    # Return raw text from the context window
    return text[context_start:context_end]

def sample_effects(effects: List[Dict], n: int = 50) -> List[Dict]:
    """Sample diverse effects for evaluation."""
    # Group effects by type
    by_type = {}
    for effect in effects:
        effect_type = effect['type']
        if effect_type not in by_type:
            by_type[effect_type] = []
        by_type[effect_type].append(effect)
    
    # Sample proportionally from each type
    samples = []
    for effect_type, type_effects in by_type.items():
        n_samples = max(1, int(n * len(type_effects) / len(effects)))
        samples.extend(random.sample(type_effects, min(n_samples, len(type_effects))))
    
    # If we don't have enough samples, add more randomly
    if len(samples) < n:
        remaining = random.sample(effects, n - len(samples))
        samples.extend(remaining)
    
    return random.sample(samples, n)

def create_evaluation_df(effects: List[Dict]) -> pd.DataFrame:
    """Create DataFrame for manual evaluation."""
    rows = []
    for effect in effects:
        context = get_context(effect['text'], effect['start'], effect['end'])
        row = {
            'doi': effect['doi'],
            'effect_type': effect['type'],
            'extracted_value': effect['value'],
            'description': effect['description'],
            'context': context,
            'true_label': '',  # To be filled manually
            'predicted_label': effect['type'],  # Current prediction
            'is_correct': '',  # To be filled manually
            'notes': '',  # For any additional observations
            'start': effect['start'],
            'end': effect['end']
        }
        rows.append(row)
    
    return pd.DataFrame(rows)

def main():
    # Load effects
    effects = load_effects('data/corpus_effects.jsonl')
    logger.info(f"Loaded {len(effects)} effects from {len(set(e['doi'] for e in effects))} papers")
    
    # Sample effects
    samples = sample_effects(effects)
    logger.info(f"Sampled {len(samples)} effects for evaluation")
    
    # Create evaluation DataFrame
    df = create_evaluation_df(samples)
    
    # Save to CSV
    output_path = 'data/enrich_corpus_sample.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved evaluation samples to {output_path}")
    
    # Print summary
    print("\nEffect type distribution in sample:")
    print(df['effect_type'].value_counts())

if __name__ == "__main__":
    main() 
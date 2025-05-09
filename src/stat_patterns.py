import spacy
import yaml
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatPatternMatcher:
    """A class to match statistical patterns in text using spaCy's Matcher."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the matcher with a spaCy model and load patterns.
        
        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
            self.matcher = spacy.matcher.Matcher(self.nlp.vocab)
            self.patterns = self._load_patterns()
            self._add_patterns_to_matcher()
            logger.info(f"Initialized StatPatternMatcher with {len(self.patterns)} pattern types")
        except Exception as e:
            logger.error(f"Error initializing StatPatternMatcher: {str(e)}")
            raise

    def _load_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load patterns from YAML file.
        
        Returns:
            Dictionary of pattern types and their patterns
        """
        try:
            config_path = Path(__file__).parent.parent / "config" / "effect_sizes.yaml"
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('patterns', {})
        except Exception as e:
            logger.error(f"Error loading patterns from YAML: {str(e)}")
            raise

    def _add_patterns_to_matcher(self):
        """Add all patterns to the spaCy matcher."""
        try:
            for pattern_type, pattern_list in self.patterns.items():
                for i, pattern_data in enumerate(pattern_list):
                    pattern_id = f"{pattern_type}_{i}"
                    # Convert the pattern string to a list of dicts
                    pattern = yaml.safe_load(pattern_data['pattern'])
                    self.matcher.add(pattern_id, [pattern])
                    logger.debug(f"Added pattern {pattern_id}: {pattern_data['description']}")
        except Exception as e:
            logger.error(f"Error adding patterns to matcher: {str(e)}")
            raise

    def find_matches(self, text: str) -> List[Dict[str, Any]]:
        """Find all statistical patterns in the given text.
        
        Args:
            text: The text to search for patterns
            
        Returns:
            List of dictionaries containing match information
        """
        try:
            doc = self.nlp(text)
            matches = self.matcher(doc)
            results = []
            
            for match_id, start, end in matches:
                pattern_id = self.nlp.vocab.strings[match_id]
                pattern_type = pattern_id.split('_')[0]
                span = doc[start:end]
                
                results.append({
                    'pattern_type': pattern_type,
                    'text': span.text,
                    'start': start,
                    'end': end,
                    'description': self.patterns[pattern_type][int(pattern_id.split('_')[-1])]['description']
                })
            
            return results
        except Exception as e:
            logger.error(f"Error finding matches: {str(e)}")
            raise

    def get_pattern_types(self) -> List[str]:
        """Get list of all pattern types.
        
        Returns:
            List of pattern type names
        """
        return list(self.patterns.keys())

    def get_pattern_descriptions(self) -> Dict[str, List[str]]:
        """Get descriptions for all patterns.
        
        Returns:
            Dictionary mapping pattern types to lists of descriptions
        """
        return {
            pattern_type: [p['description'] for p in pattern_list]
            for pattern_type, pattern_list in self.patterns.items()
        }

def main():
    """Example usage of the StatPatternMatcher."""
    # Example text with various statistical patterns
    text = """
    The study found a significant effect (p < 0.05) with a large effect size (Cohen's d = 0.82).
    The t-test results showed t(23) = 2.45, and the F-test was F(2, 45) = 3.21.
    The correlation was r = 0.45, and the odds ratio was OR = 2.34.
    The 95% confidence interval was (1.23, 3.45).
    """
    
    try:
        # Initialize matcher
        matcher = StatPatternMatcher()
        
        # Find matches
        matches = matcher.find_matches(text)
        
        # Print results
        print("\nFound matches:")
        for match in matches:
            print(f"\nType: {match['pattern_type']}")
            print(f"Text: {match['text']}")
            print(f"Description: {match['description']}")
        
        # Print available pattern types
        print("\nAvailable pattern types:")
        for pattern_type in matcher.get_pattern_types():
            print(f"- {pattern_type}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
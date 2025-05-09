import spacy
from spacy.language import Language
from spacy.pipeline import EntityRuler
from pathlib import Path
import yaml
import logging
import argparse
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EffectSizeNER:
    """A custom Named Entity Recognition pipeline for statistical effect sizes."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the NER pipeline with a spaCy model and custom entity ruler.
        
        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            # Load the base model
            self.nlp = spacy.load(model_name)
            
            # Disable the default NER model
            if "ner" in self.nlp.pipe_names:
                self.nlp.remove_pipe("ner")
            
            # Load patterns first
            self.patterns = self._load_patterns()
            
            # Create ruler patterns
            ruler_patterns = []
            for pattern_type, pattern_list in self.patterns.items():
                for pattern_data in pattern_list:
                    # Convert the pattern string to a list of dicts
                    pattern = yaml.safe_load(pattern_data['pattern'])
                    
                    # Create a ruler pattern with label
                    ruler_pattern = {
                        "label": pattern_type.upper(),  # Convert to uppercase for consistency
                        "pattern": pattern
                    }
                    ruler_patterns.append(ruler_pattern)
            
            # Remove existing entity_ruler if it exists
            if "entity_ruler" in self.nlp.pipe_names:
                self.nlp.remove_pipe("entity_ruler")
            
            # Create and add the entity ruler
            ruler = self.nlp.add_pipe("entity_ruler")
            ruler.add_patterns(ruler_patterns)
            
            # Store the ruler for later use
            self.ruler = ruler
            
            logger.info(f"Initialized EffectSizeNER with {len(ruler_patterns)} patterns")
        except Exception as e:
            logger.error(f"Error initializing EffectSizeNER: {str(e)}")
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

    def process_text(self, text: str) -> spacy.tokens.Doc:
        """Process text and identify effect size entities.
        
        Args:
            text: The text to process
            
        Returns:
            spaCy Doc object with identified entities
        """
        try:
            return self.nlp(text)
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise

    def get_entities(self, text: str) -> List[Dict[str, Any]]:
        """Get all effect size entities from text.
        
        Args:
            text: The text to process
            
        Returns:
            List of dictionaries containing entity information
        """
        try:
            doc = self.process_text(text)
            entities = []
            
            for ent in doc.ents:
                # Only include entities that match our pattern types
                if ent.label_.lower() in self.patterns:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'description': self._get_entity_description(ent.label_, ent.text)
                    })
            
            return entities
        except Exception as e:
            logger.error(f"Error getting entities: {str(e)}")
            raise

    def _get_entity_description(self, label: str, text: str) -> Optional[str]:
        """Get the description for an entity based on its label and text.
        
        Args:
            label: The entity label
            text: The entity text
            
        Returns:
            Description of the entity pattern if found, None otherwise
        """
        try:
            pattern_type = label.lower()
            if pattern_type in self.patterns:
                for pattern_data in self.patterns[pattern_type]:
                    # Here we could add more sophisticated matching if needed
                    return pattern_data['description']
            return None
        except Exception as e:
            logger.error(f"Error getting entity description: {str(e)}")
            return None

    def verify_patterns(self) -> bool:
        """Verify that patterns are properly loaded in the entity ruler.
        
        Returns:
            True if patterns are loaded, False otherwise
        """
        try:
            # Get the entity ruler from the pipeline
            ruler = self.nlp.get_pipe("entity_ruler")
            
            # Check if patterns are loaded
            if not hasattr(ruler, 'patterns') or not ruler.patterns:
                logger.warning("No patterns found in entity ruler")
                return False
                
            logger.info(f"Found {len(ruler.patterns)} patterns in entity ruler")
            return True
        except Exception as e:
            logger.error(f"Error verifying patterns: {str(e)}")
            return False

def main(show_tokenization: bool = False):
    """Example usage of the EffectSizeNER.
    
    Args:
        show_tokenization: Whether to print tokenization details (default: False)
    """
    # Complex example text with various statistical patterns
    text = """
    The study found significant effects across multiple measures. The primary outcome showed a large effect size (Cohen's d = 0.82, 95% CI: 0.45, 1.19) and a significant p-value (p < 0.001). 
    
    Secondary analyses revealed a strong correlation (r = 0.78, p < 0.05) between variables. The t-test results showed t(45) = 3.21, p = 0.002, while the ANOVA yielded F(2, 87) = 4.56, p < 0.01.
    
    The odds ratio was OR = 2.34 (95% CI: 1.23, 3.45), indicating increased risk. Hedges' g was 0.75 (SE = 0.12), and the regression analysis showed β = 0.45 (t = 2.34, p < 0.05).
    
    Sample sizes varied across conditions (n = 100 for control, n = 95 for treatment). The chi-square test was significant (χ2(3) = 8.76, p < 0.05), and the R-squared value was R2 = 0.34.
    
    The effect size was moderate (d = 0.50) with a confidence interval of (0.25, 0.75). The standard error was SE = 0.15, and the F-test for the interaction was F(1, 88) = 5.67, p = 0.02.
    """
    
    try:
        # Initialize NER
        ner = EffectSizeNER()
        
        # Verify patterns are loaded
        if not ner.verify_patterns():
            logger.error("Failed to load patterns properly")
            return
        
        # Print tokenization if requested
        if show_tokenization:
            doc = ner.nlp(text)
            print("\nTokenization:")
            for token in doc:
                print(f"Token: '{token.text}', Lemma: '{token.lemma_}', POS: {token.pos_}")
        
        # Process text and get entities
        entities = ner.get_entities(text)
        
        # Print results
        print("\nFound entities:")
        for entity in entities:
            print(f"\nType: {entity['label']}")
            print(f"Text: {entity['text']}")
            print(f"Description: {entity['description']}")
            print(f"Position: {entity['start']}-{entity['end']}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract statistical entities from text.')
    parser.add_argument('--show-tokenization', action='store_true',
                      help='Show tokenization details for debugging')
    args = parser.parse_args()
    
    main(show_tokenization=args.show_tokenization) 
import re
# pyrefly: ignore [missing-import]
import nltk
# pyrefly: ignore [missing-import]
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

from src.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# NLTK Resource Download
# ---------------------------------------------------------------------------
# Download required NLTK resources on first run. These are small files.
# 'punkt' is for tokenization, 'stopwords' for common word removal,
# 'wordnet' + 'omw-1.4' are for the lemmatizer.
def _download_nltk_resources():
    """Downloads required NLTK data packages if they are not already present."""
    resources = {
        "tokenizers/punkt": "punkt",
        "corpora/stopwords": "stopwords",
        "corpora/wordnet": "wordnet",
        "corpora/omw-1.4": "omw-1.4",
    }
    for path, package in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            logger.info(f"Downloading NLTK resource: '{package}'...")
            nltk.download(package, quiet=True)

# Run the download check when the module is first imported
_download_nltk_resources()

# ---------------------------------------------------------------------------
# Preprocessor Class
# ---------------------------------------------------------------------------

class TextPreprocessor:
    """
    A reusable NLP preprocessing pipeline for text data.

    This pipeline handles:
    - Lowercasing (makes matching case-insensitive)
    - Spell Correction (optional, for user queries)
    - URL and email removal
    - Punctuation and special character removal
    - Tokenization (splitting text into individual words)
    - Stopword removal (removes common, low-signal words like 'the', 'is', 'a')
    - Lemmatization (reduces words to their base form, e.g. 'running' -> 'run')

    This approach provides resilience against minor typos and grammatical variations.
    """

    def __init__(self):
        """Initializes the lemmatizer and loads the English stopwords list."""
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))
        logger.info("TextPreprocessor initialized.")

    def clean(self, text: str, is_query: bool = False) -> str:
        """
        Runs the full NLP preprocessing pipeline on a given text string.

        Args:
            text (str): The raw input text to clean.
            is_query (bool): If True, applies spelling correction.

        Returns:
            str: The fully cleaned and normalized text string.
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        # 1. Lowercase the text
        text = text.lower()

        # 2. Spell Correction (Applied only to user queries to avoid slowing down training)
        if is_query and TextBlob is not None:
            try:
                corrected_text = str(TextBlob(text).correct())
                if corrected_text != text:
                    logger.info(f"Typo corrected: '{text}' -> '{corrected_text}'")
                text = corrected_text
            except Exception as e:
                logger.warning(f"Spellcheck failed: {e}")

        # 3. Remove URLs (e.g., http://example.com)
        text = re.sub(r"http\S+|www\S+", "", text)

        # 4. Remove email addresses (e.g., user@domain.com)
        text = re.sub(r"\S+@\S+", "", text)

        # 5. Remove all punctuation and non-alphabetic characters, keeping spaces
        text = re.sub(r"[^a-z\s]", "", text)

        # 6. Tokenize: split the sentence into a list of words
        try:
            tokens = word_tokenize(text)
        except LookupError:
            tokens = text.split()

        # 7. Remove stopwords and lemmatize each remaining token
        processed_tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 1
        ]

        return " ".join(processed_tokens)

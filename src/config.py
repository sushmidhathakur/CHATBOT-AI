import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Data Files
FAQ_DATA_PATH = DATA_DIR / "faq_dataset.csv"
LOG_FILE_PATH = LOG_DIR / "chatbot.log"

# Engine Configurations
# Minimum cosine similarity score to consider a match valid.
# Adjust this value based on dataset size and variance (0.0 to 1.0)
CONFIDENCE_THRESHOLD = 0.4 

FALLBACK_MESSAGE = "I'm sorry, I don't have an exact answer for that. Could you please rephrase your question or contact our support team?"

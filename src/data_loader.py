import pandas as pd
from pathlib import Path
from src.config import FAQ_DATA_PATH
from src.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)


def load_faq_data(filepath: Path = FAQ_DATA_PATH) -> pd.DataFrame:
    """
    Loads the FAQ dataset from a CSV or JSON file into a pandas DataFrame.

    The CSV must have at least two columns: 'Question' and 'Answer'.
    The function validates the schema and raises clear errors if something is wrong.

    Args:
        filepath (Path): Path to the FAQ data file. Defaults to config path.

    Returns:
        pd.DataFrame: A cleaned DataFrame with 'Question' and 'Answer' columns.

    Raises:
        FileNotFoundError: If the data file does not exist at the given path.
        ValueError: If the required columns are missing from the file.
    """
    filepath = Path(filepath)

    # --- Step 1: Check if file exists ---
    if not filepath.exists():
        logger.error(f"FAQ data file not found at: {filepath}")
        raise FileNotFoundError(f"FAQ data file not found at: {filepath}")

    logger.info(f"Loading FAQ data from: {filepath}")

    # --- Step 2: Load based on file extension ---
    try:
        suffix = filepath.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(filepath)
        elif suffix == ".json":
            df = pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: '{suffix}'. Use .csv or .json.")
    except Exception as e:
        logger.error(f"Failed to read data file: {e}")
        raise

    # --- Step 3: Validate required columns ---
    required_columns = {"Question", "Answer"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"FAQ dataset must contain columns: {required_columns}. Missing: {missing}")

    # --- Step 4: Drop rows with null values in key columns and reset index ---
    initial_count = len(df)
    df = df[["Question", "Answer"]].dropna().reset_index(drop=True)
    dropped = initial_count - len(df)

    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing values.")

    logger.info(f"Successfully loaded {len(df)} FAQ entries.")
    return df

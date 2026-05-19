from typing import Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import CONFIDENCE_THRESHOLD, FALLBACK_MESSAGE
from src.preprocessor import TextPreprocessor
from src.logger import setup_logger

try:
    from thefuzz import process
except ImportError:
    process = None


# Initialize logger for this module
logger = setup_logger(__name__)


class FAQMatchingEngine:
    """
    The core semantic matching engine for the FAQ Chatbot.

    This engine uses TF-IDF (Term Frequency-Inverse Document Frequency) to
    convert all FAQ questions into mathematical vectors, and then uses
    Cosine Similarity to find the most relevant FAQ question for a given
    user query.

    ---
    How It Works:
    1.  `fit(df)`: Preprocesses all FAQ questions and builds a TF-IDF matrix.
        This is done once at startup.

    2.  `get_response(query)`: Preprocesses the user's query, converts it
        to a TF-IDF vector, and computes the cosine similarity against all
        FAQ vectors. The FAQ with the highest similarity score is returned,
        provided it exceeds the CONFIDENCE_THRESHOLD.
    ---
    """

    def __init__(self):
        """Initializes the engine with a TF-IDF vectorizer and the text preprocessor."""
        # TfidfVectorizer configuration:
        # - ngram_range=(1,2): Considers both single words and word pairs for richer context.
        # - min_df=1: Include a term even if it appears in only 1 document (good for small datasets).
        # - max_df=0.95: Ignore terms that appear in more than 95% of documents (very common terms).
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
        self.preprocessor = TextPreprocessor()

        # These will be populated after calling fit()
        self.faq_df = None
        self.tfidf_matrix = None
        self._is_fitted = False

    def fit(self, df: pd.DataFrame) -> None:
        """
        Preprocesses the FAQ dataset and builds the TF-IDF matrix.
        This is the "training" step and must be called before get_response().

        Args:
            df (pd.DataFrame): DataFrame with 'Question' and 'Answer' columns.
        """
        logger.info("Fitting TF-IDF vectorizer on FAQ dataset...")
        self.faq_df = df.copy()

        # Preprocess every FAQ question and store in a new column
        self.faq_df["Processed_Question"] = self.faq_df["Question"].apply(
            self.preprocessor.clean
        )

        # Fit the vectorizer and transform questions into TF-IDF vectors
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.faq_df["Processed_Question"]
        )

        self._is_fitted = True
        logger.info(f"Engine fitted successfully on {len(self.faq_df)} FAQ entries.")

    def get_response(self, user_query: str, threshold: float = None) -> Tuple[str, str, float]:
        """
        Finds the best matching FAQ answer for a given user query.

        Process:
        1. Preprocess the raw user query.
        2. Transform it into a TF-IDF vector using the fitted vectorizer.
        3. Compute cosine similarity against all FAQ TF-IDF vectors.
        4. Return the best match if its score exceeds the confidence threshold.

        Args:
            user_query (str): The raw text query from the user.
            threshold (float, optional): Dynamic threshold override.

        Returns:
            Tuple[str, str, float]: A tuple of (matched_question, answer, confidence_score).
                If confidence is below threshold, returns the fallback message.

        Raises:
            RuntimeError: If the engine has not been fitted with data yet.
        """
        if not self._is_fitted:
            raise RuntimeError("Engine not fitted. Call fit(df) before get_response().")

        # Step 1: Preprocess the user's query with spell correction
        processed_query = self.preprocessor.clean(user_query, is_query=True)
        logger.info(f"User query: '{user_query}' | Processed: '{processed_query}'")

        if not processed_query:
            logger.warning("User query is empty after preprocessing.")
            return "", FALLBACK_MESSAGE, 0.0

        # Step 2: Transform query into a TF-IDF vector
        query_vector = self.vectorizer.transform([processed_query])

        # Step 3: Compute cosine similarity between the query and all FAQs
        # cosine_similarity returns a 2D array; we flatten it to a 1D list
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Step 4: Find the index and value of the highest similarity score
        best_match_idx = similarity_scores.argmax()
        confidence = float(similarity_scores[best_match_idx])

        logger.info(f"Best match index: {best_match_idx} | Confidence: {confidence:.4f}")

        active_threshold = threshold if threshold is not None else CONFIDENCE_THRESHOLD

        # Step 5: Check if confidence meets the threshold
        if confidence < active_threshold:
            logger.warning(
                f"Low TF-IDF confidence ({confidence:.4f}) for query: '{user_query}'."
            )
            # Fuzzy Matching Fallback
            if process is not None:
                # thefuzz process.extractOne returns (match_string, score_out_of_100, index)
                # or (match_string, score_out_of_100) depending on input type.
                questions_list = self.faq_df["Question"].tolist()
                fuzzy_match = process.extractOne(user_query, questions_list)
                
                if fuzzy_match:
                    fuzzy_q, fuzzy_score = fuzzy_match[0], fuzzy_match[1]
                    if fuzzy_score >= 80:  # 80/100 threshold for fuzzy match
                        logger.info(f"Fuzzy fallback successful: '{fuzzy_q}' with score {fuzzy_score}")
                        # Find the answer for this fuzzy matched question
                        answer = self.faq_df[self.faq_df["Question"] == fuzzy_q].iloc[0]["Answer"]
                        # Return the fuzzy match with a normalized confidence score
                        return fuzzy_q, answer, fuzzy_score / 100.0

            # If fuzzy fallback also fails or isn't available
            matched_question = self.faq_df.iloc[best_match_idx]["Question"]
            return matched_question, FALLBACK_MESSAGE, confidence

        # Step 6: Return the matched question, its answer, and the confidence score
        matched_question = self.faq_df.iloc[best_match_idx]["Question"]
        answer = self.faq_df.iloc[best_match_idx]["Answer"]

        return matched_question, answer, confidence

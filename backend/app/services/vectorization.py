# Embeddings (optional)
import numpy as np
from typing import List
from sklearn.feature_extraction.text import HashingVectorizer


# Stateless vectorizer (no fitting required)
_vectorizer = HashingVectorizer(
    n_features=512,
    alternate_sign=False,
    norm="l2"
)


def generate_embeddings(text: str) -> np.ndarray:
    """
    Generate embeddings for text data (offline, stateless)
    """
    if not text or not isinstance(text, str):
        return np.zeros(512)

    try:
        vector = _vectorizer.transform([text])
        return vector.toarray()[0]

    except Exception:
        return np.zeros(512)


def batch_generate_embeddings(texts: List[str]) -> List[np.ndarray]:
    """
    Generate embeddings for multiple texts
    """
    if not texts:
        return []

    try:
        texts = [t if isinstance(t, str) else "" for t in texts]
        vectors = _vectorizer.transform(texts)
        return vectors.toarray().tolist()

    except Exception:
        return [np.zeros(512) for _ in texts]

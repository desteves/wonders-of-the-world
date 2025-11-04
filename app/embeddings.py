"""
embeddings.py: Voyage AI embedding utilities used by the application.
"""

import os
from typing import Optional

import numpy as np
import requests
from dotenv import load_dotenv

# Load environment variables for embedding configuration.
load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("Missing VOYAGE_API_KEY in the .env file")

VOYAGE_API_BASE = os.getenv("VOYAGE_API_BASE", "https://api.voyageai.com/v1").rstrip("/")
VOYAGE_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3-large")
VOYAGE_INPUT_TYPE = (os.getenv("VOYAGE_INPUT_TYPE", "document") or "").strip() or None
VOYAGE_TIMEOUT_SECONDS = float(os.getenv("VOYAGE_TIMEOUT_SECONDS", "30"))

_embedding_dim_override_raw = os.getenv("VOYAGE_EMBED_DIMENSION")
if _embedding_dim_override_raw:
    try:
        EMBEDDING_DIMENSION_OVERRIDE: Optional[int] = int(_embedding_dim_override_raw)
    except ValueError as exc:
        raise ValueError("VOYAGE_EMBED_DIMENSION must be an integer") from exc
else:
    EMBEDDING_DIMENSION_OVERRIDE = None

VOYAGE_EMBEDDINGS_ENDPOINT = f"{VOYAGE_API_BASE}/embeddings"
_voyage_session = requests.Session()
_voyage_session.headers.update(
    {
        "Authorization": f"Bearer {VOYAGE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "wonders-of-the-world/embedding-service",
    }
)
_model_dimension_cache: Optional[int] = None


def _request_voyage_embedding(text: str) -> list[float]:
    """Call the Voyage embeddings endpoint and return the raw embedding vector."""
    payload = {
        "input": [text],
        "model": VOYAGE_MODEL,
        "truncation": True,
    }
    if VOYAGE_INPUT_TYPE:
        payload["input_type"] = VOYAGE_INPUT_TYPE

    try:
        response = _voyage_session.post(
            VOYAGE_EMBEDDINGS_ENDPOINT,
            json=payload,
            timeout=VOYAGE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Voyage embedding request failed: {exc}") from exc

    try:
        body = response.json()
        embedding = body["data"][0]["embedding"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Voyage embedding response was not in the expected format") from exc

    return embedding


def get_embedding(data: str) -> np.ndarray:
    """
    Generate a Voyage embedding for the given text.

    Args:
        data (str): Input text to embed.

    Returns:
        numpy.ndarray: Float32 embedding vector.
    """
    embedding = np.asarray(_request_voyage_embedding(data), dtype=np.float32)

    global _model_dimension_cache
    if _model_dimension_cache is None:
        _model_dimension_cache = embedding.size

    if EMBEDDING_DIMENSION_OVERRIDE and embedding.size != EMBEDDING_DIMENSION_OVERRIDE:
        raise ValueError(
            f"Voyage embedding dimension mismatch. Expected {EMBEDDING_DIMENSION_OVERRIDE}, got {embedding.size}."
        )

    return embedding


def get_embedding_dimension() -> int:
    """
    Resolve the embedding dimensionality for the configured Voyage model.

    Returns:
        int: Embedding dimensionality.
    """
    if EMBEDDING_DIMENSION_OVERRIDE:
        return EMBEDDING_DIMENSION_OVERRIDE

    if _model_dimension_cache:
        return _model_dimension_cache

    probe_vector = get_embedding("voyage dimension probe")
    return probe_vector.size


def get_embedding_model_info() -> dict[str, object]:
    """
    Return metadata describing the configured Voyage embedding model.

    Returns:
        dict[str, object]: Model metadata including name, provider, and dimension.
    """
    return {
        "name": VOYAGE_MODEL,
        "provider": "voyage-ai",
        "embedding_dimension": get_embedding_dimension(),
    }


__all__ = [
    "get_embedding",
    "get_embedding_dimension",
    "get_embedding_model_info",
]

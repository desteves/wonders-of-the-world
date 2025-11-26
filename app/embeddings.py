"""
embeddings.py: Voyage AI embedding utilities used by the application.
"""

import os

import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

_voyage_session = requests.Session()
_voyage_session.headers.update(
    {
        "Authorization": f"Bearer {VOYAGE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "wonders-of-the-world/embedding-service",
    }
)


def get_embedding(data: str) -> np.ndarray:
    """
    Generate a Voyage embedding for the given text.

    Args:
        data (str): Input text to embed.

    Returns:
        numpy.ndarray: Float32 embedding vector.
    """
    payload = {
        "input": [data],
        "model": "voyage-3-large",
        "truncation": True,
        "input_type": "document",
    }

    try:
        response = _voyage_session.post("https://api.voyageai.com/v1/embeddings", json=payload, timeout=30.0)
        response.raise_for_status()
        body = response.json()
        embedding = body["data"][0]["embedding"]
    except Exception as exc:
        raise RuntimeError("Voyage embedding request failed") from exc

    return np.asarray(embedding, dtype=np.float32)


__all__ = [
    "get_embedding",
]

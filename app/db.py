"""
db.py: Handles MongoDB connection, embedding generation, and setup for vector search functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import certifi
from bson.binary import Binary, BinaryVectorDtype
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.operations import SearchIndexModel

from .embeddings import get_embedding

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

EMBEDDING_DIMENSION = 1024
IS_CLOUD = os.getenv("IS_CLOUD") == "1"
MONGO_CLIENT = MongoClient(MONGODB_URI)
COLLECTION = MONGO_CLIENT["ww"]["facts"]
VECTOR_INDEX_NAME = "vector-index"

def _create_vector_search_index():
    """Create or update the vector search index to match the embedding configuration."""
    num_dimensions = EMBEDDING_DIMENSION

    search_index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": num_dimensions,
                    "similarity": "dotProduct",
                    "quantization": "scalar",
                }
            ]
        },
        name="vector-index",
        type="vectorSearch",
    )

    try:
        COLLECTION.create_search_index(model=search_index_model)
    except PyMongoError:
        pass


def _load_sample_data():
    """
    Ingest sample documents with Voyage embeddings into MongoDB.

    Returns:
        int: Count of documents successfully inserted.
    """
    data_path = Path(__file__).resolve().parent / "data.json"
    print(f"Loading sample data from {data_path}")

    try:
        with open(data_path, encoding="utf-8") as file:
            data_entries = json.load(file)
    except (OSError, json.JSONDecodeError):
        return 0

    inserted_doc_count = 0
    model_info = {
        "model_name": "voyage-3-large",
        "provider": "voyage-ai",
        "embedding_dimension": EMBEDDING_DIMENSION,
        "created_timestamp": datetime.now().isoformat(),
    }
    print(f"Using model info: {model_info}")

    for entry in data_entries:
        if "text" not in entry:
            continue

        text = entry["text"]
        _id = entry["_id"]
        embedding = get_embedding(text)

        document = {
            "_id": _id,
            "text": text,
            "embedding": Binary.from_vector(embedding.tolist(), BinaryVectorDtype.FLOAT32),
            "model_info": model_info,
        }
        try:
            COLLECTION.insert_one(document)
            inserted_doc_count += 1
        except PyMongoError:
            pass

    print(f"Inserted {inserted_doc_count} documents into the collection.")
    return inserted_doc_count


def setup_vector_search():
    """
    Configure MongoDB Atlas for vector search by creating a search index and ingesting sample data.

    1. Creates a vector search index on the specified collection (sans IaC).
    2. Loads sample data with vector embeddings into the collection.

    Returns:
        int: Number of documents successfully inserted into the collection.
    """
    try:
        _create_vector_search_index()
        return _load_sample_data()
    except Exception:
        return 0


if __name__ == "__main__":
    print(_load_sample_data())

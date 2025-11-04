"""
db.py: Handles MongoDB connection, embedding generation, and setup for vector search functionality.
"""

from pathlib import Path

import json
import logging
import os
from datetime import datetime

from bson.binary import Binary, BinaryVectorDtype
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.operations import SearchIndexModel

from .embeddings import (
    get_embedding,
    get_embedding_dimension,
    get_embedding_model_info,
)

# Load environment variables from .env file
load_dotenv()

# MongoDB connection setup
MONGODB_URI = os.getenv("MONGODB_URI")  # Fetch the MongoDB URI from the .env file
if not MONGODB_URI:
    raise ValueError("Missing MONGODB_URI in the .env file")

LOGGER = logging.getLogger(__name__)

MONGO_CLIENT = MongoClient(MONGODB_URI)
COLLECTION = MONGO_CLIENT["ww"]["facts"]  # Update database and collection names as needed



def _search_not_enabled(exc: Exception) -> bool:
    """Detect whether a PyMongo error indicates Atlas Search is unavailable."""
    details = getattr(exc, "details", None)
    if isinstance(details, dict):
        code = details.get("code")
        code_name = details.get("codeName")
        message = details.get("errmsg") or str(exc)
    else:
        code = None
        code_name = None
        message = str(exc)
    if code == 31082 or code_name == "SearchNotEnabled":
        return True
    return "SearchNotEnabled" in message or "requires additional configuration" in message


def _create_vector_search_index():
    """Create or update the vector search index to match the embedding configuration."""
    num_dimensions = get_embedding_dimension()

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
        existing_index = next(COLLECTION.list_search_indexes(name="vector-index"), None)
    except PyMongoError as exc:
        if _search_not_enabled(exc):
            LOGGER.warning("Vector search commands unavailable; skipping index setup (%s)", exc)
            return
        LOGGER.error("Error checking search index state: %s", exc)
        existing_index = None

    if existing_index:
        latest_definition = existing_index.get("latestDefinition") or existing_index.get("definition") or {}
        fields = latest_definition.get("fields", [])
        existing_dimensions = next(
            (field.get("numDimensions") for field in fields if field.get("path") == "embedding"),
            None,
        )

        if existing_dimensions == num_dimensions:
            LOGGER.info("Search index 'vector-index' already matches the expected definition.")
            return

        LOGGER.info("Updating search index 'vector-index' to match Voyage embedding dimensions...")
        try:
            COLLECTION.update_search_index(
                "vector-index",
                search_index_model.document["definition"],
            )
            LOGGER.info("Search index 'vector-index' updated successfully.")
        except PyMongoError as exc:
            if _search_not_enabled(exc):
                LOGGER.warning("Vector search update unsupported; skipping (%s)", exc)
                return
            LOGGER.error("Error updating search index: %s", exc)
        return

    try:
        COLLECTION.create_search_index(model=search_index_model)
        LOGGER.info("Search index 'vector-index' created successfully.")
    except PyMongoError as exc:
        if _search_not_enabled(exc):
            LOGGER.warning("Vector search creation unsupported; skipping (%s)", exc)
            return
        LOGGER.error("Error creating search index: %s", exc)


def _load_sample_data():
    """
    Ingest sample documents with Voyage embeddings into MongoDB.

    Returns:
        int: Count of documents successfully inserted.
    """

    data_path = Path(__file__).resolve().parent / "data.json"
    # Read data from data.json
    try:
        with open(data_path, encoding="utf-8") as file:
            data_entries = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.error("Error reading data.json: %s", exc)
        return 0

    bulk_size = 100
    buffer = []
    inserted_doc_count = 0
    model_info = {
        **get_embedding_model_info(),
        "created_timestamp": datetime.now().isoformat(),
    }
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
        buffer.append(document)

        if len(buffer) == bulk_size:
            try:
                COLLECTION.insert_many(buffer, ordered=False)
                inserted_doc_count += len(buffer)
            except PyMongoError as exc:
                LOGGER.error("Error inserting documents: %s", exc)
            finally:
                buffer.clear()

    if buffer:
        try:
            COLLECTION.insert_many(buffer, ordered=False)
            inserted_doc_count += len(buffer)
        except PyMongoError as exc:
            LOGGER.error("Error inserting remaining documents: %s", exc)

    LOGGER.info("Inserted %s documents.", inserted_doc_count)
    return inserted_doc_count


def setup_vector_search():
    """
    Configure MongoDB Atlas for vector search by creating a search index and ingesting sample data.

    1. Creates a vector search index on the specified collection (sans IaC).
    2. Loads sample data with vector embeddings into the collection.

    Returns:
        int: Number of documents successfully inserted into the collection.
    """
    LOGGER.info("Ensuring vector search index...")
    _create_vector_search_index()
    LOGGER.info("Loading sample data...")
    return _load_sample_data()

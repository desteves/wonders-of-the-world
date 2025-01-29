"""
db.py: Handles MongoDB connection, embedding generation, and setup for vector search functionality.
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI")  # Fetch the MongoDB URI from the .env file
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI in the .env file")

client = MongoClient(MONGO_URI)
db = client["ww"]  # Update this with your database name
collection = db["test"]  # Update this with your collection name

# Load the embedding model
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

def get_embedding(data):
    """
    Generates vector embeddings for the given data using the SentenceTransformer model.

    Args:
        data (str): Input data to generate embeddings for.

    Returns:
        List[float]: Vector embeddings as a list of floats.
    """
    embedding = model.encode(data)
    return embedding.tolist()


def _create_vector_search_index():
    # Create vector search index definition
    search_index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",       # Field for vector embeddings
                    "numDimensions": 768,     # Adjust this to match your embedding dimensions
                    "similarity": "dotProduct",  # Similarity metric (e.g., cosine, dotProduct)
                    "quantization": "scalar"     # Quantization type
                }
            ]
        },
        name="vector_index",  # Name for the index in MongoDB Atlas
        type="vectorSearch",  # Specifies this as a vector search index
    )

    # Create the search index (if not already created)
    try:
        collection.create_search_index(model=search_index_model)
        print("Search index 'vector_index' created successfully.")
    except Exception as e:
        print(f"Error creating search index: {str(e)}")

def _load_sample_data():

    # Read data from data.json
    try:
        with open("data.json", encoding="utf-8") as file:
            data_entries = json.load(file)
    except Exception as e:
        print(f"Error reading data.json: {str(e)}")
        return 0

    bulk_size = 20
    buffer = []
    inserted_doc_count = 0
    model_info = {
        "name": model.model_name_or_path,
        "created_timestamp": datetime.now().isoformat(),
    }
    for entry in data_entries:
        if 'text' in entry:
            text = entry['text']
            _id = entry['_id']
            embedding = get_embedding(text)  # Generate embedding for each text

            # Prepare the document
            document = {
                "_id": _id,
                "text": text,
                "embedding": embedding,
                "model_info": model_info
            }
            buffer.append(document)

            # If buffer reaches the bulk_size, perform batch insert
            if len(buffer) == bulk_size:
                try:
                    collection.insert_many(buffer)
                    inserted_doc_count += len(buffer)
                    buffer.clear()  # Clear buffer after insert
                except Exception as e:
                    print(f"Error inserting documents: {str(e)}")
    # Insert any remaining documents in the buffer
    if buffer:
        try:
            collection.insert_many(buffer)
            inserted_doc_count += len(buffer)
        except Exception as e:
            print(f"Error inserting remaining documents: {str(e)}")
    print(f"Inserted {inserted_doc_count} documents.")
    return inserted_doc_count


def setup_vector_search():
    """
    Configures MongoDB Atlas for vector search by creating a search index and ingesting sample data.

    1. Creates a vector search index on the specified collection.
    2. Loads sample data with vector embeddings into the collection.

    Returns:
        int: Number of documents successfully inserted into the collection.
    """
    # _create_vector_search_index()
    return _load_sample_data()

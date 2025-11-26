"""Minimal Flask app exposing a single vector search endpoint."""

import os

from flask import Flask, jsonify, request

from .db import COLLECTION, VECTOR_INDEX_NAME, setup_vector_search
from .embeddings import get_embedding

app = Flask(__name__)


@app.route("/vectorsearch", methods=["GET"])
def vector_search():
    prompt = request.args.get("prompt")
    if not prompt:
        return jsonify({"error": "missing prompt"}), 400

    try:
        query_vector = get_embedding(prompt).tolist()
        results = list(
            COLLECTION.aggregate(
                [
                    {
                        "$vectorSearch": {
                            "index": VECTOR_INDEX_NAME,
                            "queryVector": query_vector,
                            "path": "embedding",
                            "numCandidates": 200,
                            "limit": 5,
                        }
                    },
                    {
                        "$project": {
                            "text": 1,
                            "score": {"$meta": "vectorSearchScore"},
                        }
                    },
                ]
            )
        )
    except Exception:
        return jsonify({"error": "query failed"}), 500

    return jsonify({"query": prompt, "results": results})


if __name__ == "__main__":
    setup_vector_search()
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

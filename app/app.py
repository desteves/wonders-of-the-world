"""
app.py: Flask application that provides a /vectorsearch endpoint and optionally sets up the database.
"""

from flask import Flask, request, jsonify
from db import collection, get_embedding, setup_vector_search  # Import necessary utilities

app = Flask(__name__)

@app.route('/vectorsearch', methods=['GET'])
def vector_search():
    """
    Endpoint to perform a vector search on the MongoDB collection.

    This endpoint expects a 'prompt' query parameter and searches the collection
    using vector embeddings to find similar documents.

    Returns:
        JSON response containing the query and the search results.
    """
    # Get the "prompt" query parameter
    prompt = request.args.get('prompt')

    if not prompt:
        return jsonify({
            "error": "Missing required query parameter 'prompt'"
        }), 400

    # Generate the embedding for the user's input
    query_embedding = get_embedding(prompt)

    # Vector search pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",  # Update this to match your vector search index name
                "queryVector": query_embedding,
                "path": "embedding",  # The field in the collection where embeddings are stored
                "exact": True,
                "limit": 5  # Limit the number of results returned
            }
        },
        {
            "$project": {
                "text": 1,  # Include the field storing document text
                "score": {  # Include the similarity score
                    "$meta": "vectorSearchScore"
                }
            }
        },
        {
            "$sort": {
                "score": -1  # Sort results by descending similarity score
            }
        }
    ]

    # Fetch results using the aggregation pipeline
    data = []
    try:
        results = collection.aggregate(pipeline)
        for doc in results:
            data.append(doc)
    except Exception as e:
        return jsonify({"error": f"An error occurred with the search"}), 500

    return jsonify({
        "query": prompt,
        "results": data
    })


if __name__ == '__main__':
    # Uncomment the line below to initialize the database and run the Flask server
    # setup_vector_search()
    app.run(port=8080, debug=True, host='0.0.0.0')

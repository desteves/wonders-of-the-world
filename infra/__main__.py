"""A Python Pulumi program"""
import json
import os
import pulumi
from dotenv import load_dotenv
import pulumi_mongodbatlas as mongodbatlas

# Load environment variables from .env file
load_dotenv()

# MongoDB connection setup
MONGODB_PROJECT_ID = os.getenv("MONGODB_PROJECT_ID")  # Fetch the MongoDB URI from the .env file
if not MONGODB_PROJECT_ID:
    raise ValueError("Missing MONGODB_PROJECT_ID in the .env file")

# Create a *free* MongoDB Atlas Cluster running on Google Cloud
database = mongodbatlas.Cluster("vector-database",
    project_id=MONGODB_PROJECT_ID,
    name="vector-database",
    provider_name="TENANT",
    backing_provider_name="GCP",
    provider_region_name="CENTRAL_US",
    provider_instance_size_name="M0",
)


# Create a database user for the cluster with specific privileges
user = mongodbatlas.DatabaseUser(
    "vector-user",
    project_id=MONGODB_PROJECT_ID,
    username="vector-user",
    password="v3ct0rp4ssw0rd", # clearly this is strictly for demo purposes
    auth_database_name="admin",
    roles=[
      mongodbatlas.DatabaseUserRoleArgs(
            role_name="readWrite",
            database_name="ww",
            collection_name="facts"
)],

    scopes=[
        mongodbatlas.DatabaseUserScopeArgs(
            name=database.name,
            type="CLUSTER")
    ]
)

# Define the search index fields
search_index_fields = [
                {
                    "type": "vector",
                    "path": "embedding",       # Field for vector embeddings
                    "numDimensions": 768,     # Adjust this to match your embedding dimensions
                    "similarity": "dotProduct",  # Similarity metric (e.g., cosine, dotProduct)
                    "quantization": "scalar"     # Quantization type
                }
            ]

# Create a MongoDB Atlas Search Index
search_index = mongodbatlas.SearchIndex("vector-index",
    project_id=MONGODB_PROJECT_ID,
    name="vector-index",
    cluster_name=database.name,
    database="ww",
    collection_name="facts",
    type="vectorSearch",
    fields=json.dumps(search_index_fields),
    wait_for_index_build_completion=True,
)



pulumi.export("user", user.username)
pulumi.export("conn_string", database.connection_strings[0].standard_srv)
pulumi.export("search_index_name", search_index.name)

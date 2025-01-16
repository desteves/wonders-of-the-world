"""A Python Pulumi program"""
import json
import os
import requests
import urllib.parse

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

import pulumi
from pulumi import ResourceOptions, Output
import pulumi_mongodbatlas as mongodbatlas

# Load environment variables from .env file
load_dotenv()

# MongoDB connection setup
MONGODB_PROJECT_ID = os.getenv("MONGODB_PROJECT_ID")  # Fetch the MongoDB URI from the .env file
if not MONGODB_PROJECT_ID:
    raise ValueError("Missing MONGODB_PROJECT_ID in the .env file")

# Fetch DB_NAME and COLLECTION_NAME from environment variables
DB_NAME = os.getenv("DB_NAME", "ww")  # Default to "ww" if not found
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "facts")  # Default to "facts" if not found

def get_public_ip():
    """
    Retrieves the public IP address of the machine using an external service.
    Returns the IP address as a string or None if there's an error.
    """
    try:
        # Use ipify API to get the public IP address
        response = requests.get("https://api.ipify.org?format=json")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data["ip"]
    except requests.RequestException as e:
        print(f"Error retrieving public IP: {e}")
        return None

# Try to get the public IP address from the environment variable or fetch it if not available
IP_ADDRESS = os.getenv("IP_ADDRESS", get_public_ip())

# if IP_ADDRESS:
#     print(f"Using IP Address: {IP_ADDRESS}")
# else:
#     print("Could not retrieve an IP address.")


# Create a *free* MongoDB Atlas Cluster running on Google Cloud
vector_database = mongodbatlas.Cluster("vector-database",
    project_id=MONGODB_PROJECT_ID,
    name="vector-database",
    provider_name="TENANT",
    backing_provider_name="GCP",
    provider_region_name="CENTRAL_US",
    provider_instance_size_name="M0",
)


# Create a database user for the cluster with specific privileges
vector_user = mongodbatlas.DatabaseUser(
    "vector-user",
    project_id=MONGODB_PROJECT_ID,
    username="vector-user",
    password="v3ct0rp4ssw0rd", # clearly this is strictly for demo purposes
    auth_database_name="admin",
    roles=[
      mongodbatlas.DatabaseUserRoleArgs(
            role_name="readWrite",
            database_name=DB_NAME,
            collection_name=COLLECTION_NAME
)],

    scopes=[
        mongodbatlas.DatabaseUserScopeArgs(
            name=vector_database.name,
            type="CLUSTER"),

    ],
    opts=ResourceOptions(depends_on=[vector_database])
)

# Adds the current IP to the access list of the project
# to be able to then create the collection within the database cluster
my_current_ip = mongodbatlas.ProjectIpAccessList("my-current-ip",
    project_id=MONGODB_PROJECT_ID,
    ip_address=IP_ADDRESS,
    comment = "ip for vector index creation",
    opts=ResourceOptions(additional_secret_outputs=['ip_address'])
)


def create_mongodb_collection(user: str, pwd: str, uri: str) -> pulumi.Output[bool]:
    """
    Connects to MongoDB Atlas, creates a collection, and checks if it was created successfully.

    :param uri: MongoDB connection string.
    :return: Pulumi Output wrapping True if the collection was created or already exists, False if there was an error.
    """
    try:
        # Establish connection to MongoDB Atlas
        MongoClient(uri,
                    username=user,
                    password=pwd,
                    maxPoolSize=1,  # Limits the connection pool to a single connection
                    minPoolSize=1,  # Ensures at least one connection is maintained
                    connect=True     # Establishes connection immediately
                    )[DB_NAME].command("create", COLLECTION_NAME)
        return pulumi.Output.from_input(True)

    except OperationFailure as e:
        # Handle error if collection already exists
        if "already exists" in str(e):
            return pulumi.Output.from_input(True)
        return pulumi.Output.from_input(False)

# Ensure that the IP whitelist is created before the collection creation
is_collection_created = pulumi.Output.all(
    vector_user.username,
    vector_user.password,
    vector_database.connection_strings,
    my_current_ip.id).apply(
        lambda args: create_mongodb_collection(
            user=urllib.parse.quote_plus(args[0]),
            pwd=urllib.parse.quote_plus(args[1]),
            uri=args[2][0]['standard_srv']))

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

# Ensure collection is created before proceeding
search_index = is_collection_created.apply(lambda created: mongodbatlas.SearchIndex(
    "vector-index",
    project_id=MONGODB_PROJECT_ID,
    name="vector-index",
    cluster_name=vector_database.name,
    database=DB_NAME,
    collection_name=COLLECTION_NAME,
    type="vectorSearch",
    fields=json.dumps(search_index_fields),
    wait_for_index_build_completion=True,
    opts=ResourceOptions(depends_on=[my_current_ip])  # Use a real Pulumi resource here
) if created else None)



pulumi.Output.all(search_index.status, search_index.name).apply(
    lambda args: print(
        f"🎉 Your Vector Search Index '{args[1]}' is ready! 🚀\n"
        f"Start running vector searches now: 👉 "
        f"https://www.mongodb.com/docs/atlas/atlas-vector-search/tutorials/vector-search-quick-start/#run-a-vector-search-query"
    ) if args[0] == "STEADY" else None
)

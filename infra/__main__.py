"""A Python Pulumi program to provision a MongoDB Atlas cluster with vector search capabilities."""

# Standard library imports
import json

# Third-party imports
import pulumi  # Pulumi SDK for infrastructure as code
from pulumi import ResourceOptions
import pulumi_mongodbatlas as mongodbatlas  # Pulumi MongoDB Atlas provider

# Local application imports
from mongodb_collection import MongoDBCollection  # Custom Pulumi resource
from config import MONGODB_PROJECT_ID, IP_ADDRESS, VECTOR_DATABASE, VECTOR_COLLECTION, VECTOR_USER, VECTOR_PASSWORD

# Create a *free* MongoDB Atlas cluster running on Google Cloud
vector_cluster = mongodbatlas.AdvancedCluster(
    "vector-cluster",
    project_id=MONGODB_PROJECT_ID,
    name="vector-cluster",
    cluster_type="REPLICASET",
    replication_specs=[{
        "zone_name": "iac managed",
        "region_configs": [{
            "electable_specs": {
                "instance_size" : "M0",  # Free tier instance size
                "node_count": 3
            },
            "provider_name":"TENANT",
            "backing_provider_name":"GCP",
            "region_name":"CENTRAL_US",
            "priority": 7,
        }],
    }],
    opts=ResourceOptions(
        ignore_changes=["replication_specs"]
    ))

# Extract the connection string for use in the collection
vector_uri = vector_cluster.connection_strings.apply(lambda c: c[0].standard_srv )

# Create a database user for the cluster with specific privileges
vector_user = mongodbatlas.DatabaseUser(
    "vector-user",
    project_id=MONGODB_PROJECT_ID,
    username=VECTOR_USER,
    password=VECTOR_PASSWORD,
    auth_database_name="admin",
    roles=[{
            "role_name" : "readWrite",
            "database_name" : VECTOR_DATABASE,
            "collection_name" : VECTOR_COLLECTION
    }],
    scopes=[{
            "name" : vector_cluster.name,
            "type" : "CLUSTER"}
    ],
    opts=ResourceOptions(depends_on=[vector_cluster])
)

# Adds the current IP to the access list of the project
my_current_ip = mongodbatlas.ProjectIpAccessList(
    "my-current-ip",
    project_id=MONGODB_PROJECT_ID,
    ip_address=IP_ADDRESS,
    comment = "Enable local cluster access.",
    opts=ResourceOptions(additional_secret_outputs=['ip_address'])
)

# Creates a MongoDB collection for the Vector Search Index
vector_username = vector_user.username.apply(lambda u: u)
vector_password = vector_user.password.apply(lambda p: p)
vector_collection = MongoDBCollection(
    "vector-collection",
    props={
        "user": vector_username,
        "pwd": vector_password,
        "uri": vector_uri,
        "db": VECTOR_DATABASE,
        "coll": VECTOR_COLLECTION
    },
    opts=ResourceOptions(depends_on=[vector_user, my_current_ip])
    )

# Define the search index fields
vector_search_index_fields = [
    {
        "type": "vector",
        "path": "embedding",        # Field for vector embeddings
        "numDimensions": 768,       # Adjust this to match your embedding dimensions
        "similarity": "dotProduct", # Similarity metric (e.g., cosine, dotProduct)
        "quantization": "scalar"    # Quantization type
    }
]

# Ensure collection is created before proceeding
vector_search_index = mongodbatlas.SearchIndex(
    "vector-index",
    project_id=MONGODB_PROJECT_ID,
    name="vector-index",
    cluster_name=vector_cluster.name,
    database=VECTOR_DATABASE,
    collection_name=VECTOR_COLLECTION,
    type="vectorSearch",
    fields=json.dumps(vector_search_index_fields),
    wait_for_index_build_completion=True,
    opts=ResourceOptions(depends_on=[vector_collection])
)

def _notify_when_ready(args):
    name, status = args
    if status == "STEADY":
        print(f"🎉 Your Vector Search Index '{name}' is ready! 🚀\n"
              f"Start running vector searches now: 👉\n"
              f"https://tinyurl.com/vector-search")

pulumi.Output.all(vector_search_index.name, vector_search_index.status).apply(_notify_when_ready)

pulumi.export("MONGODB_URI", vector_uri)

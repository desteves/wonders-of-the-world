"""A Python Pulumi program to provision a MongoDB Atlas cluster with vector search capabilities."""

# Standard library imports
import json
from pathlib import Path
from typing import Any, Mapping

# Third-party imports
import pulumi  # Pulumi SDK for infrastructure as code
from pulumi import ResourceOptions, log
import pulumi_mongodbatlas as mongodbatlas  # Pulumi MongoDB Atlas provider

# Local application imports
from mongodb_collection import MongoDBCollection  # Custom Pulumi resource
from config import (
    GCP_FUNCTION_IP,
    MONGODB_ATLAS_PROJECT_ID,
    IP_ADDRESS,
    VECTOR_DATABASE,
    VECTOR_COLLECTION,
    VECTOR_USER,
    VECTOR_PASSWORD,
)

VECTOR_INDEX_SPEC_PATH = Path(__file__).resolve().parents[2] / "app" / "vector_index.json"


def _load_vector_index_spec() -> Mapping[str, Any]:
    """Load the vector index spec shared with the application to keep definitions in sync."""
    try:
        return json.loads(VECTOR_INDEX_SPEC_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Vector index spec not found at {VECTOR_INDEX_SPEC_PATH}. "
            "Ensure the application assets are available before running Pulumi."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Vector index spec at {VECTOR_INDEX_SPEC_PATH} is not valid JSON."
        ) from exc


def _extract_standard_srv(conn: Any) -> str:
    """tolerantly extract the standard SRV string from the provider output."""
    if isinstance(conn, dict):
        value = (
            conn.get("standard_srv")
            or conn.get("standardSrv")
            or conn.get("STANDARD_SRV")
        )
        if value:
            return value
    if isinstance(conn, list) and conn:
        entry = conn[0]
        if isinstance(entry, dict):
            value = (
                entry.get("standard_srv")
                or entry.get("standardSrv")
                or entry.get("STANDARD_SRV")
            )
            if value:
                return value
    raise ValueError("Unable to extract standard SRV connection string from cluster output.")


VECTOR_INDEX_SPEC = _load_vector_index_spec()
VECTOR_INDEX_NAME = VECTOR_INDEX_SPEC.get("name", "vector-index")
_VECTOR_INDEX_DEFINITION = VECTOR_INDEX_SPEC.get("definition") or {}
VECTOR_SEARCH_INDEX_FIELDS = _VECTOR_INDEX_DEFINITION.get("fields") or []
if not VECTOR_SEARCH_INDEX_FIELDS:
    raise RuntimeError("Vector index specification is missing field definitions.")

# Validate that the Pulumi config matches the application defaults.
spec_database = VECTOR_INDEX_SPEC.get("database")
if spec_database and spec_database != VECTOR_DATABASE:
    log.warn(
        f"Vector index spec database '{spec_database}' differs from Pulumi config '{VECTOR_DATABASE}'. "
        "Pulumi will use the config value."
    )
spec_collection = VECTOR_INDEX_SPEC.get("collectionName") or VECTOR_INDEX_SPEC.get("collection_name")
if spec_collection and spec_collection != VECTOR_COLLECTION:
    log.warn(
        f"Vector index spec collection '{spec_collection}' differs from Pulumi config '{VECTOR_COLLECTION}'. "
        "Pulumi will use the config value."
    )

# Create a *free* MongoDB Atlas cluster running on Google Cloud
vector_cluster = mongodbatlas.AdvancedCluster(
    "vector-cluster",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    name="vector-cluster",
    cluster_type="REPLICASET",
    replication_specs=[{
        "zone_name": "iac managed",
        "region_configs": [{
            "electable_specs": {
                "instance_size" : "M0",  # Free tier instance size
            },
            "provider_name":"TENANT",
            "backing_provider_name":"GCP",
            "region_name":"CENTRAL_US",
            "priority": 7,
        }],
    }],
)

# Extract the connection string for use in the collection
vector_uri = vector_cluster.connection_strings.apply(_extract_standard_srv)

# Create a database user for the cluster with specific privileges
vector_user = mongodbatlas.DatabaseUser(
    "vector-user",
    project_id=MONGODB_ATLAS_PROJECT_ID,
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
    project_id=MONGODB_ATLAS_PROJECT_ID,
    ip_address=IP_ADDRESS,
    comment = "Enable local cluster access.",
    opts=ResourceOptions(additional_secret_outputs=['ip_address'])
)

if GCP_FUNCTION_IP:
    mongodbatlas.ProjectIpAccessList(
        "gcp-function-ip",
        project_id=MONGODB_ATLAS_PROJECT_ID,
        ip_address=GCP_FUNCTION_IP,
        comment="Allow Google Cloud Function egress.",
        opts=ResourceOptions(additional_secret_outputs=["ip_address"]),
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
# Ensure collection is created before proceeding
vector_search_index = mongodbatlas.SearchIndex(
    "vector-index",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    name=VECTOR_INDEX_NAME,
    cluster_name=vector_cluster.name,
    database=VECTOR_DATABASE,
    collection_name=VECTOR_COLLECTION,
    type="vectorSearch",
    fields=json.dumps(VECTOR_SEARCH_INDEX_FIELDS),
    wait_for_index_build_completion=True,
    opts=ResourceOptions(depends_on=[vector_collection])
)

# Export a full MongoDB URI with credentials and database
full_mongodb_uri = pulumi.Output.all(VECTOR_USER, VECTOR_PASSWORD, vector_uri, VECTOR_DATABASE).apply(
    lambda args: f"mongodb+srv://{args[0]}:{args[1]}@{args[2].split('://')[1]}/{args[3]}?retryWrites=true&w=majority"
)
pulumi.export("MONGODB_URI", pulumi.Output.secret(full_mongodb_uri))

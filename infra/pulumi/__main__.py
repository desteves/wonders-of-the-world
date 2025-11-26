"""Pulumi program to provision MongoDB Atlas and deploy the Wonders API to Cloud Run."""

import json
from pathlib import Path

import pulumi
import pulumi_gcp as gcp
import pulumi_command as command
import pulumi_mongodbatlas as mongodbatlas
from pulumi import ResourceOptions
from pulumi_docker import DockerBuildArgs, Image

from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    MONGODB_ATLAS_PROJECT_ID,
    VECTOR_COLLECTION,
    VECTOR_DATABASE,
    VECTOR_PASSWORD,
    VECTOR_USER,
    VOYAGE_API_KEY,
)
from mongodb_collection import MongoDBCollection
from utils import (
    extract_standard_srv,
    get_public_ip,
    load_vector_index_spec,
    resolve_ip_from_url,
)

APP_DIR = Path(__file__).resolve().parents[2] / "app"
APP_DOCKERFILE = APP_DIR / "Dockerfile"
VECTOR_INDEX_SPEC =  APP_DIR / "vector_index.json"


vector_index_spec = load_vector_index_spec(VECTOR_INDEX_SPEC)
vector_index_name = vector_index_spec["name"]
vector_search_index_fields = vector_index_spec["definition"]["fields"]

# Atlas cluster (free tier)
vector_cluster = mongodbatlas.AdvancedCluster(
    "vector-cluster",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    name="vector-cluster",
    cluster_type="REPLICASET",
    replication_specs=[
        {
            "zone_name": "iac managed",
            "region_configs": [
                {
                    "electable_specs": {
                        "instance_size": "M0",
                    },
                    "provider_name": "TENANT",
                    "backing_provider_name": "GCP",
                    "region_name": "CENTRAL_US",
                    "priority": 7,
                }
            ],
        }
    ],
)

vector_uri = vector_cluster.connection_strings.apply(extract_standard_srv)

vector_user = mongodbatlas.DatabaseUser(
    "vector-user",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    username=VECTOR_USER,
    password=VECTOR_PASSWORD,
    auth_database_name="admin",
    roles=[
        {
            "role_name": "readWrite",
            "database_name": VECTOR_DATABASE,
            "collection_name": VECTOR_COLLECTION,
        }
    ],
    scopes=[
        {
            "name": vector_cluster.name,
            "type": "CLUSTER",
        }
    ],
    opts=ResourceOptions(
        depends_on=[vector_cluster],
    ),
)

workstation_ip = get_public_ip()

access_workstation_ip = mongodbatlas.ProjectIpAccessList(
        "workstation-ip-access",
        project_id=MONGODB_ATLAS_PROJECT_ID,
        ip_address=workstation_ip,
        comment="Allow current workstation.",
    )

vector_collection = MongoDBCollection(
    "vector-collection",
    props={
        "user": vector_user.username,
        "pwd": vector_user.password,
        "uri": vector_uri,
        "db": VECTOR_DATABASE,
        "coll": VECTOR_COLLECTION,
    },
    opts=ResourceOptions(depends_on=[vector_user, access_workstation_ip]),
)

full_mongodb_uri = pulumi.Output.all(
    VECTOR_USER,
    VECTOR_PASSWORD,
    vector_uri,
    VECTOR_DATABASE,
).apply(
    lambda args: (
        f"mongodb+srv://{args[0]}:{args[1]}"
        f"@{args[2].split('://')[1]}/{args[3]}"
        "?retryWrites=true&w=majority"
    )
)

vector_data = command.local.Command(
    "vector-data",
    create=f"python {APP_DIR}/db.py",
    environment={
        "MONGODB_URI": full_mongodb_uri,
        "VOYAGE_API_KEY": VOYAGE_API_KEY,
    },
    opts=ResourceOptions(depends_on=[vector_collection]),
)



vector_search_index = mongodbatlas.SearchIndex(
    "vector-index",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    name=vector_index_name,
    cluster_name=vector_cluster.name,
    database=VECTOR_DATABASE,
    collection_name=VECTOR_COLLECTION,
    type="vectorSearch",
    fields=json.dumps(vector_search_index_fields),
    wait_for_index_build_completion=True,
    opts=ResourceOptions(depends_on=[vector_collection]),
)

pulumi.export("MONGODB_URI", pulumi.Output.secret(full_mongodb_uri))

image = Image(
    "api-image",
    image_name=f"gcr.io/{GCP_PROJECT_ID}/wonders-api:latest",
    build=DockerBuildArgs(
        context=str(APP_DIR),
        dockerfile=str(APP_DOCKERFILE),
        platform="linux/amd64",
    ),
    skip_push=False,
)

service = gcp.cloudrunv2.Service(
    "api-service",
    location=GCP_REGION,
    project=GCP_PROJECT_ID,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=image.image_name,
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="MONGODB_URI",
                        value=full_mongodb_uri,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="IS_CLOUD",
                        value="1",
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="VOYAGE_API_KEY",
                        value=VOYAGE_API_KEY,
                    ),
                ],
                ports=[
                    gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                        name="http1",
                        container_port=8080,
                    )
                ],
            )
        ],
    ),
    traffics=[
        gcp.cloudrunv2.ServiceTrafficArgs(
            type="TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
            percent=100,
        )
    ],
)
gcp.cloudrun.IamMember(
    "api-run-access",
    project=GCP_PROJECT_ID,
    location=GCP_REGION,
    service=service.name,
    role="roles/run.invoker",
    member="allUsers",
    opts=ResourceOptions(depends_on=[service]),
)

cloud_run_ip = service.uri.apply(resolve_ip_from_url)

access_cloud_run_ip = mongodbatlas.ProjectIpAccessList(
    "api-ip-access",
    project_id=MONGODB_ATLAS_PROJECT_ID,
    ip_address=cloud_run_ip,
    comment="Allow Cloud Run egress.",
)

pulumi.export("CLOUD_RUN_URL", service.uri)

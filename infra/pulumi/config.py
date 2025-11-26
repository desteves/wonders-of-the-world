"""
Configuration loader for Pulumi that relies solely on environment variables.

Expected variables (see .envSAMPLE):
- MONGODB_ATLAS_PROJECT_ID
- MONGODB_ATLAS_PUBLIC_KEY
- MONGODB_ATLAS_PRIVATE_KEY
- VECTOR_DATABASE (default: ww)
- VECTOR_COLLECTION (default: facts)
- VECTOR_USER (default: vector-user)
- VECTOR_PASSWORD (default: v3ct0rp4ssw0rd)
- GCP_PROJECT_ID
- GCP_REGION (default: us-central1)
- GOOGLE_APPLICATION_CREDENTIALS
- APP_IMAGE (optional; overrides auto-build to gcr.io/<project>/wonders-api:latest)
"""

import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_ATLAS_PROJECT_ID = os.getenv("MONGODB_ATLAS_PROJECT_ID") or ""
MONGODB_ATLAS_PUBLIC_KEY = os.getenv("MONGODB_ATLAS_PUBLIC_KEY") or ""
MONGODB_ATLAS_PRIVATE_KEY = os.getenv("MONGODB_ATLAS_PRIVATE_KEY") or ""

VECTOR_DATABASE = os.getenv("VECTOR_DATABASE", "ww")
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "facts")
VECTOR_USER = os.getenv("VECTOR_USER", "vector-user")
VECTOR_PASSWORD = os.getenv("VECTOR_PASSWORD", "v3ct0rp4ssw0rd")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") or ""
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS = (
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    or os.getenv("GOOGLE_CREDENTIALS")
    or ""
)
APP_IMAGE = (
    os.getenv("APP_IMAGE")
    or (f"gcr.io/{GCP_PROJECT_ID}/wonders-api:latest" if GCP_PROJECT_ID else "")
)

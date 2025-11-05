# Pulumi Infrastructure for Wonders of the World

This package provisions the MongoDB Atlas resources required by the application.
It consumes the same `app/vector_index.json` definition that the Flask service loads at runtime, ensuring a consistent vector index schema across environments.

## Prerequisites

- Python 3.11+
- Pulumi CLI 3.100.0 or newer
- MongoDB Atlas API keys with project admin permissions
- Google Cloud SDK (`gcloud`) 464+ if you plan to deploy the app on Cloud Functions
- A Python virtual environment (recommended)

Install the Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Initialize the state backend + stack

```bash
pulumi login --local
pulumi stack init dev
```

## Configure Atlas secrets and project settings

```bash
pulumi config set vector_database ww
pulumi config set vector_collection facts
pulumi config set vector_user vector-user
pulumi config set --secret vector_password v3ct0rp4ssw0rd
pulumi config set mongodbatlas_projectId <PROJECT_ID>
pulumi config set mongodbatlas:publicKey <PUBLIC_KEY>
pulumi config set --secret mongodbatlas:privateKey <PRIVATE_KEY>

pulumi config set gcp:project <GCP_PROJECT_ID>
pulumi config set gcp:region <GCP_REGION>

# gcloud auth application-default login OR:
pulumi config set --secret gcp:credentials @path/to/key.json

pulumi config set mongodbatlas_ip_address <YOUR_IP>   # optional, auto-detected if omitted
```

    > **Deploying to Google Cloud Functions?**
    > Capture the function’s static egress IP (from Cloud NAT or another static source) so Pulumi can whitelist it in MongoDB Atlas:
    > `pulumi config set gcp_function_ip <FUNCTION_STATIC_IP>`

4. **Preview and deploy**

    ```bash
    pulumi preview
    pulumi up
    ```

    Pulumi creates the Atlas cluster, database user, access list entries, collection, and vector search index.

5. **Retrieve outputs**

    ```bash
    pulumi stack output MONGODB_URI --show-secrets
    ```

## Cleaning Up

Remove managed resources and local state:

```bash
pulumi destroy
pulumi stack rm dev
```

Adjust the stack name if you used one other than `dev`.

## Optional: Deploy the API to Google Cloud Functions

You can host the Flask application as a Cloud Functions (Gen 2) service using the existing Dockerfile. When you provide the function’s static egress IP via `gcp_function_ip`, Pulumi automatically adds it to the MongoDB Atlas access list.

### Additional prerequisites

- Google Cloud project with the following APIs enabled:
  - Cloud Functions
  - Cloud Build
  - Artifact Registry
  - VPC Access
  - Cloud NAT (if you need a fixed egress IP)
- `gcloud` authenticated as a service account with roles:
  - Cloud Functions Admin
  - Artifact Registry Administrator
  - Cloud Build Editor
  - Compute Network Admin (for Serverless VPC/NAT)
- Service account JSON key file (keep it safe!)

### Configure GCP credentials for Pulumi

```bash
pulumi config set gcp:project <GCP_PROJECT_ID>
pulumi config set gcp:region <GCP_REGION>          # e.g. us-central1
pulumi config set --secret gcp:credentials @path/to/service-account.json
pulumi config set gcp_function_ip <FUNCTION_STATIC_IP>
```

Alternatively, export `GOOGLE_APPLICATION_CREDENTIALS` before running Pulumi instead of storing the credentials in Pulumi config.

### Build and deploy the Cloud Function

1. **Build and push the container**

```bash
export GCP_PROJECT_ID=<your-project>
export GCP_REGION=<your-region>
gcloud builds submit app \
  --tag "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/wonders/functions-api"
```

2. **Deploy the Cloud Function (Gen 2)**

  ```bash
  export SERVICE_ACCOUNT_EMAIL=<service-account@${GCP_PROJECT_ID}.iam.gserviceaccount.com>
  gcloud functions deploy wonders-api \
    --gen2 \
    --runtime=python312 \
    --region="${GCP_REGION}" \
    --entry-point=app \
    --trigger-http \
    --allow-unauthenticated \
    --service-account="${SERVICE_ACCOUNT_EMAIL}" \
    --set-env-vars="MONGODB_URI=$(pulumi stack output MONGODB_URI)" \
    --env-vars-file=app/.env
  ```

    Ensure the function uses a Serverless VPC Access connector with Cloud NAT (or another static egress solution) so outbound traffic originates from the IP you added to Atlas. Refer to the [Google Cloud networking guide](https://cloud.google.com/functions/docs/networking/connecting-vpc) for step-by-step instructions.

3. **Re-run Pulumi (if needed)**

    After confirming the static egress IP, run `pulumi up` again so the access list entry is definitely present.

### Test the deployed function

```bash
curl "https://<REGION>-<PROJECT_ID>.cloudfunctions.net/wonders-api/vectorsearch?prompt=Eiffel%20Tower"
```

You should receive JSON results once the Atlas vector index reaches the `QUERYABLE` state.

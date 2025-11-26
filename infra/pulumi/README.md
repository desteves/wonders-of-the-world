# IaC with Pulumi + Python

This package provisions the MongoDB Atlas resources required by the application.
It consumes the same `app/vector_index.json` definition that the Flask service loads at runtime, ensuring a consistent vector index schema across environments.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- [MongoDB Atlas API keys](https://www.mongodb.com/docs/atlas/configure-api-access/) with project admin permissions

## Quickstart

0. Setup (install deps and auth):

```bash
# Python deps
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Google Cloud credentials
gcloud auth application-default login
# THEN UPDATE YOUR GOOGLE_APPLICATION_CREDENTIALS in the env file!!!
```

> [!WARNING]
> **Update all required .env settings** See the [`.envSAMPLE` file](.envSAMPLE) for reference.

```bash
source .env
```

1.  Initialize local state and stack

```sh
pulumi login --local
# Logged in to M-ABC123 as d (file://~)
pulumi stack init dev
# Created stack 'dev'
```

2. Deploy

```bash
pulumi up
# Previewing update (dev):
# Select 'Yes'
```

Pulumi creates the **free forver** Atlas cluster, database user, access list entries, collection, and vector search index. It also deploys the API as a Google Cloud Run function.

3. Clean up

```bash
pulumi destroy
pulumi stack rm dev
```

## What's next?

- Use a durable backend to mange the IaC state via Pulumi Cloud (free tier available)
- Add additional cloud security best practices such as VPC peering or a Private Link to establish a secure, private connection between the database and the applicaiton.
- Limit access to the Cloud function via required key, cors, or only allow internal Google project traffic.

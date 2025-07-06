# Wonders of the World: A Vector Search Demo App


Search fun facts about the Wonders of the World based on semantic similarity to a given prompt.

This application demonstrates a vector search functionality using MongoDB Atlas (local and in the cloud) and Sentence Transformers.


## Prereqs

- **Docker**
- **Python**
- **[MongoDB Atlas CLI](https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/#install-the-atlas-cli)**

## Running everything locally (offline)

```sh
# Setup local environment and run application
make setup-local
make run

# (optional) Test the endpoint
make test
```

## Running the vector db in the cloud with IaC

Launch the application's cloud resources (the vector search database) using Pulumi Python.

### Prerequisites

1. Install the **[Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)**
2. Set up your **[MongoDB Atlas Environment Variables](https://www.mongodb.com/cloud/atlas/register)
    - `MONGODB_PROJECT_ID`: The MongoDB Atlas project ID where resources will be created.
    - `MONGODB_ATLAS_PUBLIC_KEY`: The public key for MongoDB Atlas API authentication.
    - `MONGODB_ATLAS_PRIVATE_KEY`: The private key for MongoDB Atlas API authentication.

### Deploy and Run

```sh
# Setup cloud environment (deploys infrastructure and configures app)
make setup-cloud
make run

# Test the endpoint
make test
```

## Docker Usage

```sh
# Build Docker image
make build
make docker-run

# Stop Docker container
make docker-stop

# Clean up
make clean
```

## Available Make Commands

Run `make help` to see all available commands


## License

This project is licensed under the MIT License.

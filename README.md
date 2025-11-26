# Wonders of the World

Search fun facts about the Wonders of the World using semantic similarity. Locally it runs MongoDB 8.2 Community vector search with Voyage AI’s `voyage-3-large` embeddings behind a small Flask API. IaC samples show how to spin up the same stack on MongoDB Atlas and Google Cloud.

## Requirements

- [Voyage AI](https://www.voyageai.com/) API key
- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/)
- For IaC:
  - Either [Pulumi](https://www.pulumi.com/) or [Terraform](https://www.terraform.io/)
  - [MongoDB Atlas API keys](https://www.mongodb.com/docs/atlas/configure-api-access/) + [Google Cloud credentials](https://cloud.google.com/iam/docs/keys-create) (for the cloud deploy path)

## Quick start (local)

```sh
export VOYAGE_API_KEY=your_key
docker compose up --build -d
curl "http://127.0.0.1:8080/vectorsearch?prompt=religion"
```

Notes:
- The app seeds `ww.facts` and builds a vector index at startup
- If curl says “connection reset by peer,” wait for the Flask reloader to finish and retry.

## Deploy to the cloud (via Infrastructure as Code)

See:
- Pulumi guide: `infra/pulumi/README.md`
- Terraform skeleton: `infra/terraform` (TODO: docs)

You’ll need: MongoDB Atlas project ID + API keys, Google Cloud project/region, and your Voyage API key.

## License

MIT License.

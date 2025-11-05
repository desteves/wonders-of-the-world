# Wonders of the World

Search fun facts about the Wonders of the World using semantic similarity.
This project combines MongoDB 8.2 Community’s native vector search with Voyage AI’s `voyage-3-large` embeddings, served through a Flask API.

## Requirements

- Python 3.11+
- MongoDB 8.2+
- [Voyage AI](https://www.voyageai.com/) account + [API key](https://dashboard.voyageai.com/organization/api-keys)
- Docker + Docker Compose (Make sho' it's running!!!)

## Run

```sh
VOYAGE_API_KEY=your_key docker compose up --build -d
```

```sh
# test the flask api
curl -f http://localhost:8080/vectorsearch?prompt=religion
```

Stop and remove containers/volumes when finished:

```sh
docker compose down -v
```

## License

MIT License.

# Wonders of the World – Vector Search Demo

Search fun facts about the Wonders of the World using semantic similarity.
This project combines MongoDB 8.2 Community’s native vector search with Voyage AI’s `voyage-3-large` embeddings, served through a Flask API.

## Requirements

- Python 3.11+ (tested with 3.13)
- MongoDB 8.2+ with vector search enabled (local binary or Atlas cluster)
- Voyage AI account + API key
- Docker + Docker Compose (Make sho' it's running!!!)

## Run
```sh
VOYAGE_API_KEY=your_key docker compose up --build
```

The compose stack starts two services:
- `mongo`: MongoDB 8.2 listening on localhost:27777
- `app`: Flask API at http://localhost:8080/vectorsearch

Connect locally using `mongodb://root:example@localhost:27777/ww?authSource=admin`.


```bash
#test the flask api
curl -f http://localhost:8080/vectorsearch?prompt=test
```

Stop and remove containers/volumes when finished:

```sh
docker compose down -v
```

## License

MIT License.
# arch-day-root

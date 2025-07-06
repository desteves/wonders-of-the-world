.PHONY: help build run clean test docker-build docker-run docker-stop setup-local setup-cloud

# Default target
help:
	@echo "Available commands:"
	@echo "  setup-local    - Setup local environment (venv + vector db)"
	@echo "  setup-cloud    - Setup cloud environment (venv + cloud db)"
	@echo "  build          - Build Docker image"
	@echo "  run            - Run application locally"
	@echo "  docker-run     - Run application in Docker"
	@echo "  docker-stop    - Stop Docker container"
	@echo "  clean          - Clean up generated files"
	@echo "  test           - Test vector search endpoint"

# Setup local environment
setup-local:
	@echo "Setting up local environment..."
	cd app && bash setup_venv.sh
	cd app && bash setup_vector.sh
	@echo "Local environment setup complete!"

# Setup cloud environment
setup-cloud:
	@echo "Setting up cloud environment..."
	cd app && bash setup_venv.sh
	@echo "Setting up infrastructure with Pulumi..."
	cd infra && bash setup_venv.sh
	pulumi up
	@echo "Getting MongoDB URI from Pulumi output..."
	@echo "MONGODB_URI=$(shell pulumi stack output MONGODB_URI)" >> app/.env
	@echo "Cloud environment setup complete!"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t wonders-of-the-world:latest app/
	@echo "Docker image built successfully!"

# Run application locally
run:
	@echo "Running application locally..."
	cd app && source venv/bin/activate && python app.py

# Run application in Docker
docker-run:
	@echo "Running application in Docker..."
	docker run -d --name wonders-app -p 8080:8080 --env-file app/.env wonders-of-the-world:latest
	@echo "Application running on http://localhost:8080"

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	docker stop wonders-app || true
	docker rm wonders-app || true
	@echo "Docker container stopped and removed"

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf app/venv
	rm -f app/app.log
	docker rmi wonders-of-the-world:latest || true
	@echo "Cleanup complete!"

# Test vector search endpoint
test:
	@echo "Testing vector search endpoint..."
	@echo "Testing with prompt: 'Brazil'"
	curl -s "http://localhost:8080/vectorsearch?prompt=Brazil" | jq . || echo "Endpoint not responding or jq not installed"
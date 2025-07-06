# Variables
DOCKER_IMAGE := wonders-of-the-world:latest
DOCKER_CONTAINER := wonders-app
APP_DIR := app
INFRA_DIR := infra
MONGODB_URI_LOCAL := mongodb://localhost:27007/?directConnection=true

.PHONY: help build run clean clean-docker clean-local test docker-run docker-stop setup-local setup-cloud setup-venv

# Default target
help:
	@echo "Available commands:"
	@echo "  setup-local    - Setup local environment (venv + vector db)"
	@echo "  setup-cloud    - Setup cloud environment (venv + cloud db)"
	@echo "  build          - Build Docker image"
	@echo "  run            - Run application locally"
	@echo "  docker-run     - Run application in Docker"
	@echo "  docker-stop    - Stop Docker container"
	@echo "  clean          - Clean up generated files and Docker"
	@echo "  clean-docker   - Clean up Docker resources"
	@echo "  clean-local    - Clean up local Atlas deployment and venvs"
	@echo "  test           - Test vector search endpoint"

# Check if command exists
check-command = @if ! command -v $(1) &> /dev/null; then \
	echo "Error: $(1) is not installed or not in PATH"; \
	exit 1; \
fi

# Setup virtual environment in specified directory
setup-venv:
	@echo "Setting up Python virtual environment in $(DIR)..."
	$(call check-command,python3)
	@cd $(DIR) && if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	else \
		echo "Virtual environment already exists"; \
	fi
	@cd $(DIR) && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Virtual environment setup complete for $(DIR)!"

# Setup local environment
setup-local:
	@echo "Setting up local environment..."
	$(MAKE) setup-venv DIR=$(APP_DIR)
	@echo "Setting up local MongoDB deployment..."
	$(call check-command,atlas)
	@cd $(APP_DIR) && if ! grep -q "127.0.0.1 MDB" /etc/hosts; then \
		echo "Adding MDB entry to /etc/hosts (requires sudo)..."; \
		echo "127.0.0.1 MDB" | sudo tee -a /etc/hosts > /dev/null; \
	else \
		echo "MDB entry already exists in /etc/hosts"; \
	fi
	@cd $(APP_DIR) && atlas deployments setup MDB --type LOCAL --port 27007 --force
	@cd $(APP_DIR) && atlas deployments search indexes create --file vector_index.json
	@cd $(APP_DIR) && echo "MONGODB_URI=$(MONGODB_URI_LOCAL)" > .env
	@echo "Local environment setup complete!"

# Setup cloud environment
setup-cloud:
	@echo "Setting up cloud environment..."
	$(MAKE) setup-venv DIR=$(APP_DIR)
	@echo "Setting up infrastructure with Pulumi..."
	$(MAKE) setup-venv DIR=$(INFRA_DIR)
	@cd $(INFRA_DIR) && source venv/bin/activate && pulumi up
	@echo "Getting MongoDB URI from Pulumi output..."
	@cd $(INFRA_DIR) && source venv/bin/activate && echo "MONGODB_URI=$$(pulumi stack output MONGODB_URI)" >> ../$(APP_DIR)/.env
	@echo "Cloud environment setup complete!"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) $(APP_DIR)/
	@echo "Docker image built successfully!"

# Run application locally
run:
	@echo "Running application locally..."
	cd $(APP_DIR) && source venv/bin/activate && python app.py > app.log 2>&1 &

# Run application in Docker
docker-run:
	@echo "Running application in Docker..."
	docker run -d --name $(DOCKER_CONTAINER) -p 8080:8080 --env-file $(APP_DIR)/.env $(DOCKER_IMAGE)
	@echo "Application running on http://localhost:8080"

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	docker stop $(DOCKER_CONTAINER) || true
	docker rm $(DOCKER_CONTAINER) || true
	@echo "Docker container stopped and removed"

# Clean up Docker resources
clean-docker:
	@echo "Cleaning up Docker resources..."
	docker stop $(DOCKER_CONTAINER) || true
	docker rm $(DOCKER_CONTAINER) || true
	docker rmi $(DOCKER_IMAGE) || true
	@echo "Docker cleanup complete!"

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	rm -rf $(APP_DIR)/venv $(INFRA_DIR)/venv
	rm -f $(APP_DIR)/app.log $(APP_DIR)/.env
	$(MAKE) clean-docker
	@echo "Cleanup complete!"

# Clean up local Atlas deployment and deactivate venvs
clean-local:
	@echo "Cleaning up local Atlas deployment..."
	@if command -v atlas &> /dev/null; then \
		atlas deployments delete MDB --force || echo "No local deployment found or already deleted"; \
	else \
		echo "Atlas CLI not found. Skipping deployment cleanup."; \
	fi
	@echo "Removing MDB entry from /etc/hosts..."
	@if grep -q "127.0.0.1 MDB" /etc/hosts; then \
		sudo sed -i '' '/127\.0\.0\.1 MDB/d' /etc/hosts; \
		echo "MDB entry removed from /etc/hosts"; \
	else \
		echo "MDB entry not found in /etc/hosts"; \
	fi
	@echo "Deactivating virtual environments..."
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Deactivating current virtual environment: $$VIRTUAL_ENV"; \
		deactivate || true; \
	fi
	@echo "Removing virtual environments..."
	rm -rf $(APP_DIR)/venv $(INFRA_DIR)/venv
	@echo "Local Atlas deployment and venv cleanup complete!"

# Test vector search endpoint
test:
	@echo "Testing vector search endpoint..."
	@echo "Testing with prompt: 'Brazil'"
	curl -s "http://localhost:8080/vectorsearch?prompt=Brazil"
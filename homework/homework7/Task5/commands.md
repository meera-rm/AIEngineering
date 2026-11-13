# Task 5 - Docker Compose commands

Run from `Task5/`. The compose file builds the router, retrieval, and workflow images
from `../Task1/router`, `../Task2`, and `../Task4`, and starts the Ollama image.

Before the first run, stop and remove the standalone containers from Tasks 1 to 4,
since they hold the host ports Compose needs. The volumes are kept.

    docker rm -f hw7-router hw7-retrieval hw7-workflow homework7-ollama

## 1. Validate the configuration

    docker compose config --quiet

## 2. Build and start all four services

    docker compose up --build -d

## 3. Check health

    docker compose ps

All four services should show `healthy` once their start periods have passed.
Retrieval can take about a minute.

    curl http://localhost:8000/health

## 4. Stop the deployment

    docker compose down

`down` removes the containers and network but keeps the `homework7_ollama` model volume and
the `homework7_workflow_logs` trace volume.

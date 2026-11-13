# Task 4 - Workflow container commands

Run from `Task4/`. The router (host 8001), retrieval (host 8002), and Ollama (host 8003)
containers must already be running.

## Build

    docker build -t hw7-workflow:1 .

## Create the log volume

    docker volume create homework7_workflow_logs

## Run (host 8000 -> container 8000)

Inside the container `localhost` is the container itself, so the service addresses use
`host.docker.internal` (Docker Desktop on macOS). Task 5 replaces these with Compose service names.

    docker run -d --name hw7-workflow -p 8000:8000 \
      -e ROUTING_URL=http://host.docker.internal:8001 \
      -e RETRIEVAL_URL=http://host.docker.internal:8002 \
      -e OLLAMA_URL=http://host.docker.internal:8003 \
      -v homework7_workflow_logs:/app/logs \
      hw7-workflow:1

## Health check (checks routing, retrieval, and Ollama)

    curl http://localhost:8000/health

Expected: `{"status":"ok"}`. A 503 lists the services that failed.

## Process a ticket

    curl -X POST http://localhost:8000/tickets/process \
      -H "Content-Type: application/json" \
      -d '{"ticket_id": 1, "Body": "I was charged twice for my subscription this month"}'

Expected: `terminal_status` of `summary_ready_for_review`, with the review package fields filled in.

## Logs

    docker exec hw7-workflow cat /app/logs/workflow_trace.jsonl

The log file persists in the `homework7_workflow_logs` volume after the container is removed.

## Stop and remove

    docker stop hw7-workflow && docker rm hw7-workflow

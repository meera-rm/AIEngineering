# Ollama Container Configuration

Ollama already provides the HTTP server used by the LLM service. Use its
existing container image rather than writing another API or Dockerfile.

## Configuration

- **Image:** `ollama/ollama:0.34.1`
- **Model:** `qwen2.5:1.5b-instruct-q4_K_M`
- **Container model directory:** `/root/.ollama`
- **Named volume:** `homework7_ollama`
- **Container API port:** `11434`

The named volume preserves the downloaded model when the container is removed
and is reused by the Docker Compose deployment in Task 5.

## Start Ollama

Create the model volume:

```text
docker volume create homework7_ollama
```

Start the container:

```text
docker run -d --name homework7-ollama -p 8003:11434 -v homework7_ollama:/root/.ollama ollama/ollama:0.34.1
```

Port `8003` is used on the host so this container does not conflict with the
Ollama installation from Homework 4. Ollama still listens on port `11434` inside
the container.

## Download the Course Model

Download the required model into the named volume:

```text
docker exec homework7-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M
```

## Verify the Container

Use `http://localhost:8003/api/version` to confirm the API is reachable and
`http://localhost:8003/api/tags` to confirm the response contains
`qwen2.5:1.5b-instruct-q4_K_M`.

No Python test file is required for these checks.

For the Docker Compose health check in Task 5, use the configuration below.
Docker runs this command automatically inside the Ollama container, just as it
runs the HTTP health-check commands inside the other containers. The Ollama CLI
checks server availability and model installation without generating a response:

```yaml
healthcheck:
  test: ["CMD", "ollama", "show", "qwen2.5:1.5b-instruct-q4_K_M"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

## Stop the Container

```text
docker stop homework7-ollama
docker rm homework7-ollama
```

Removing the container does not remove the `homework7_ollama` volume or its
downloaded model.

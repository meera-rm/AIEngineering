# Task 3 - LLM (Ollama) container commands

No Dockerfile or HTTP wrapper: this uses the prebuilt `ollama/ollama:0.34.1` image.
Configuration source: `ollama_container_config.md`.

## 1. Create the model volume

    docker volume create homework7_ollama

## 2. Run the container (host 8003 -> container 11434)

    docker run -d --name homework7-ollama -p 8003:11434 -v homework7_ollama:/root/.ollama ollama/ollama:0.34.1

## 3. Download the course model into the volume

    docker exec homework7-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M

## 4. Verify

    curl http://localhost:8003/api/version
    curl http://localhost:8003/api/tags                # response should list qwen2.5:1.5b-instruct-q4_K_M
    docker exec homework7-ollama ollama show qwen2.5:1.5b-instruct-q4_K_M

## 5. Stop and remove the container (the volume and model are kept)

    docker stop homework7-ollama
    docker rm homework7-ollama

To confirm the model survived, run step 2 again and then step 4. The model should still be listed without a new pull.

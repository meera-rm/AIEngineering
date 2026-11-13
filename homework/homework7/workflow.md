
100%
# Homework 7 - Package and Deploy the Services

## Goal

Turn the Homework 6 ticket-preparation workflow into a reproducible local
deployment. Package the router, retrieval system, workflow, and local LLM as four
services, connect them with Docker Compose, and process one ticket through the
deployed application.

## Provided Materials

| Material | Purpose                                                               |
| --- |-----------------------------------------------------------------------|
| `requirements.txt` | Cumulative pinned dependencies through Homework 7                     |
| `example_http_service/` | Example of exposing ordinary Python service functions through FastAPI |
| `example_docker_setup/` | Example Docker setup from the Lesson 14 Docker walkthrough            |
| `ollama_container_config.md` | Pinned local-LLM image, model, and volume configuration               |

Bring forward your Homework 6 routing, retrieval, LLM, workflow, and tracing
implementations, including their contracts and required runtime artifacts.

## Task 1 - Containerize the Router

Wrap the Homework 6 routing service in an HTTP API and run it in its own container.
We are going to use `uvicorn` to run a FastAPI app in the container (included in `requirements.txt`).
To start an API-container, your Dockerfile's last line will be something like:
```dockerfile
CMD ["uvicorn", "router_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Requirements

- Create an HTTP API for the routing service using FastAPI 
  (provided `example_http_service/` gives an example).
- API includes `GET /health` endpoint for health check
- API includes `POST /route` endpoint that runs `route_ticket` using the HW6 routing contract.
- Set Docker `WORKDIR /app` and copy the router's application code and runtime
  artifacts under `/app`, preserving the model's required module paths.
- Publish host port `8001` to container port `8000`.
- Container works successfully in isolation.

### Deliverables

- Dockerfile + files required to build the image. This includes:
  - API code
  - Service code
  - Preprocessing code
  - Persisted classifier
- Command(s) used to build and run the container.

### Implementation Notes

- When you serialize a classifier, you are saving the data corresponding to 
  a single instance of the class, but not the actual class definition/code itself.
  When you deserialize a classifier, it expects the model class
  to be under the same path and class name as when the model was serialized.
  As a result, you will need to copy the necessary python files into the
  container under an identical module/import path so the deserialization can find them.

## Task 2 - Containerize Retrieval

Wrap the Homework 6 retrieval service in an HTTP API and run it in its own
container.

### Requirements

- Create an HTTP API for the retrieval service using FastAPI
  (provided `example_http_service/` gives an example).
- API includes `GET /health` endpoint for health check.
- API includes `POST /search` endpoint that runs `retrieve_evidence` using the
  HW6 retrieval contract.
- Set Docker `WORKDIR /app` and place the retrieval application code and runtime
  assets under `/app`; retrieval data may use a subdirectory.
- Configure the Dockerfile to download the pinned embedding model from homework
  5 while building the image, and include the model in the image.
- Publish host port `8002` to container port `8000`.
- Container works successfully in isolation.

### Deliverables

- Dockerfile + files required to build the image. This includes:
  - API code
  - Service code
  - Vector-store code
  - Persisted vector store
- Command(s) used to build and run the container.

## Task 3 - Configure the LLM Container

Unlike Tasks 1 and 2, you will not build an image or HTTP API for this service.
Ollama already provides both. Use `ollama_container_config.md` to run its
prebuilt image and make the approved course model available through its existing
API.

### Requirements

- Use the supplied pinned image and documented model volume.
- Do not create another LLM server or LLM Dockerfile.
- Download the specified LLM model into the Docker volume specified in
  `ollama_container_config.md` so it's not deleted when the LLM container is
  removed.
- Publish host port `8003` to container port `11434`.
- Container works successfully in isolation.

### Deliverables

- Command(s) used to create the volume, run the container, and download the
  model.

## Task 4 - Containerize the Workflow

Turn the Homework 6 workflow into the primary ticket-processing HTTP service.

### Requirements

- Create an HTTP API for the workflow using FastAPI
  (provided `example_http_service/` gives an example).
- API includes `GET /health` endpoint for health check.
- API includes `POST /tickets/process` endpoint that runs `process_ticket`
  using `WORKFLOW_CONTRACT.md`.
- Set Docker `WORKDIR /app` and copy the workflow's application code, prompt, and
  other runtime assets under `/app`.
- Replace existing Python calls to the Retrieval and Routing services with HTTP requests.
- Update LLM service to call the Ollama container.
- Preserve Homework 6 prompt construction, validation, result assembly,
  failures, and parallelism.
- Workflow logging should write to a volume-mounted directory for persistence.
- Publish host port `8000` to container port `8000`.

### Deliverables

- Dockerfile + files required to build the image. This includes:
  - API code
  - Workflow code
  - Logging code
  - Prompt
- Command(s) used to build and run the container.

## Task 5 - Connect the Services with Docker Compose

Create one Docker Compose configuration for the complete application.

### Requirements

- Docker Compose builds the workflow, router, and retrieval images.
- Docker Compose starts the supplied Ollama image.
- Supply the 3 service URLs via environment variables.
- Persist the Ollama model and workflow traces.
- Publish all four services on the host ports listed in tasks 1-4.
- Each of the 4 services should have a `healthcheck` configured.
  For Ollama, use the command `ollama show qwen2.5:1.5b-instruct-q4_K_M`.

### Deliverables

- One four-service Docker Compose file.
- Any configuration used by the Compose deployment.

## Task 6 - Run the Deployment

Start the complete application and test it using ticket `28763` from the
canonical dataset supplied in Homework 2.

### Requirements

- Use one Docker Compose command to build and start all four services.
- Write and run a test file `test_deployment.py` containing a test that: 
  - Submits ticket `28763` to the workflow service's `POST /tickets/process`
  - Ensures the response conforms to `WORKFLOW_CONTRACT.md`.
  - Asserts the exact workflow result keys, including `ticket_body`.
  - Requires `ticket_body` to equal the submitted request `Body` exactly.
  - Saves the result. 
- Stop the deployment with Docker Compose.

### Deliverables

- `test_deployment.py` file.
- Result from submitting ticket `28763` to the workflow service. Treat this
  saved artifact as sensitive because it contains raw ticket text.

## Submission Guidelines

- Submit the complete homework as one `.zip` file. Do not submit individual
  files or multiple `.zip` files.
- Name the archive `Firstname_Lastname_HW7.zip`, using the same first and last
  name shown in Google Classroom. For example: `Tanner_Gilligan_HW7.zip`.
- Organize the archive with one folder per task at its root. Each task folder
  should contain that task's deliverables:

  ```text
  Tanner_Gilligan_HW7.zip
  ├── Task1/
  ├── Task2/
  ├── Task3/
  ├── Task4/
  ├── Task5/
  └── Task6/
  ```

- Upload the `.zip` file itself. Do not submit a Google Drive, GitHub, or other
  external link in place of the file.
- Submit data tables as static CSV files, not Excel files or links to Google
  Sheets.
- Submit writeups as `.txt` or `.md` files.
- Do not include duplicate or extraneous files unless they are relevant to
  running or interpreting your submission.
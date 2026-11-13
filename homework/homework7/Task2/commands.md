# Task 2 - Retrieval container commands

Run from `Task2/`.

## Build (downloads the pinned embedding model into the image)

    docker build -t hw7-retrieval:1 .

## Run (host 8002 -> container 8000)

    docker run -d --name hw7-retrieval -p 8002:8000 hw7-retrieval:1

## Health check

    curl http://localhost:8002/health

Expected: `{"status":"ok"}`

## Search

    curl -X POST http://localhost:8002/search \
      -H "Content-Type: application/json" \
      -d '{"body": "I was charged twice for my subscription this month"}'

Expected: 200 with `results` (1 to 5 records, each with rank, chunk_id, distance, content, metadata).

## Error checks

    curl -i -X POST http://localhost:8002/search -H "Content-Type: application/json" -d '{"body": "   "}'   # 422

## Logs and cleanup

    docker logs hw7-retrieval
    docker stop hw7-retrieval && docker rm hw7-retrieval

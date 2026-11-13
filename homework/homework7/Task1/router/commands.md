# Task 1 - Router container commands

Run from `Task1/router/`.

## Build

    docker build -t hw7-router:1 .

## Run (host 8001 -> container 8000)

    docker run -d --name hw7-router -p 8001:8000 hw7-router:1

## Health check

    curl http://localhost:8001/health

Expected: `{"status":"ok"}`

## Route a ticket

    curl -X POST http://localhost:8001/route \
      -H "Content-Type: application/json" \
      -d '{"body": "I was charged twice for my subscription this month"}'

Expected: 200 with `recommended_department` and `class_scores` for all departments.

## Error checks

    curl -i -X POST http://localhost:8001/route -H "Content-Type: application/json" -d '{"body": "   "}'   # 422

## Logs and cleanup

    docker logs hw7-router
    docker stop hw7-router && docker rm hw7-router

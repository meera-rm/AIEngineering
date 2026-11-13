# Task 6 - Run the deployment and test

Run from `Task6/`. The deployment comes from `Task5/compose.yaml`.

## 1. Start all four services with one Compose command

    cd ../Task5
    docker compose up --build -d
    docker compose ps          # wait until all four show "healthy"
    cd ../Task6

## 2. Run the test

    pip install pytest requests
    pytest test_deployment.py -v

The test submits ticket 28763 to `POST /tickets/process`, checks the response against
WORKFLOW_CONTRACT.md, asserts the exact result keys and the exact `ticket_body`, and saves
the response to `ticket_28763_result.json`.

## 3. Stop the deployment

    cd ../Task5
    docker compose down

## Sensitive file

`ticket_28763_result.json` contains the raw ticket text. Treat it as sensitive and do not
share it outside the submission.

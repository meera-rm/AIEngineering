from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from workflow import TicketWorkflow

workflow: TicketWorkflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the workflow once; it holds the trace logger and service clients.
    global workflow
    workflow = TicketWorkflow()
    yield


app = FastAPI(title="Ticket workflow service", lifespan=lifespan)


@app.get("/health")
def health():
    # Healthy only when every dependency answers: routing, retrieval, and Ollama.
    checks = {
        "routing": f"{workflow.routing.base_url}/health",
        "retrieval": f"{workflow.retrieval.base_url}/health",
        "llm": f"{workflow.llm.base_url}/api/version",
    }
    failing = []
    for name, url in checks.items():
        try:
            if requests.get(url, timeout=5).status_code != 200:
                failing.append(name)
        except requests.RequestException:
            failing.append(name)
    if failing:
        return JSONResponse({"status": "unavailable", "failing": failing}, status_code=503)
    return {"status": "ok"}


@app.post("/tickets/process")
def process_ticket(request: Any = Body(...)) -> dict:
    # Every terminal status (including input_rejected) is a contract result, so it returns 200.
    return workflow.process_ticket(request)

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from retrieval_service import (
    InvalidRequestError,
    RetrievalServiceError,
    RetrievalService,
    RetrievalUnavailableError,
)

service: RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open the vector store and embedding model once at startup.
    global service
    service = RetrievalService()
    yield


app = FastAPI(title="Ticket retrieval service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search")
def search(request: dict) -> dict:
    try:
        return service.retrieve_evidence(request)
    except InvalidRequestError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RetrievalUnavailableError as exc:
        raise HTTPException(503, str(exc)) from exc
    except RetrievalServiceError as exc:
        raise HTTPException(500, str(exc)) from exc

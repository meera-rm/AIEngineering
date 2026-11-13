from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .service import EmbeddingService

service = EmbeddingService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Keep /health available while the GPU model loads and warms up.
    Thread(target=service.load, daemon=True).start()
    yield


app = FastAPI(title="GPU embeddings", lifespan=lifespan)


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


@app.get("/health")
def health():
    if not service.ready:
        raise HTTPException(503, "Model not ready")
    return {"status": "ready"}


@app.post("/embed")
def embed(request: EmbedRequest):
    try:
        return {"embeddings": service.embed(request.texts)}
    except RuntimeError as exc:
        raise HTTPException(503, "Embedding service unavailable") from exc

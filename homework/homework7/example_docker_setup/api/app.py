import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .service import DependencyUnavailable, DocumentService

service: DocumentService


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    service = DocumentService()
    await asyncio.to_thread(service.initialize)
    yield


app = FastAPI(title="Semantic document search", lifespan=lifespan)


class Document(BaseModel):
    id: str
    text: str


class DocumentsRequest(BaseModel):
    documents: list[Document] = Field(min_length=1)


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=3, ge=1)


@app.get("/health")
def health():
    try:
        service.check_health()
    except DependencyUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"status": "ready"}


@app.post("/documents")
def add_documents(request: DocumentsRequest):
    try:
        indexed = service.add_documents(
            [document.model_dump() for document in request.documents]
        )
        return {"indexed": indexed}
    except DependencyUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.post("/search")
def search(request: SearchRequest):
    try:
        results = service.search(request.query, request.limit)
        return {"results": results}
    except DependencyUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc

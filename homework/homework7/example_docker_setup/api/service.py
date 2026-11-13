import json
import os

import httpx
import psycopg
from psycopg.rows import dict_row


class DependencyUnavailable(RuntimeError):
    pass


class DocumentService:
    def __init__(self):
        self.ready = False
        self.model_url = os.environ.get("MODEL_URL", "http://model:8000").rstrip("/")
        self.database = {
            "host": os.environ.get("DATABASE_HOST", "vectors"),
            "port": 5432,
            "dbname": os.environ.get("DATABASE_NAME", "search"),
            "user": os.environ.get("DATABASE_USER", "search"),
            "password": os.environ["DATABASE_PASSWORD"],
            "connect_timeout": 5,
            "row_factory": dict_row,
        }

    def initialize(self):
        self.ready = False
        try:
            with psycopg.connect(**self.database) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS documents ("
                    "id TEXT PRIMARY KEY, text TEXT NOT NULL, "
                    "embedding vector(384) NOT NULL)"
                )
        except psycopg.Error as exc:
            raise DependencyUnavailable("Database initialization failed") from exc
        self.ready = True

    def check_health(self):
        if not self.ready:
            raise DependencyUnavailable("Service not initialized")
        try:
            httpx.get(f"{self.model_url}/health", timeout=5).raise_for_status()
        except httpx.HTTPError as exc:
            raise DependencyUnavailable("Model service unavailable") from exc

        try:
            with psycopg.connect(**self.database) as conn:
                conn.execute("SELECT 1")
        except psycopg.Error as exc:
            raise DependencyUnavailable("Vector store unavailable") from exc

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = httpx.post(
                f"{self.model_url}/embed", json={"texts": texts}, timeout=60
            )
            response.raise_for_status()
            embeddings = response.json()["embeddings"]
            if not isinstance(embeddings, list) or len(embeddings) != len(texts):
                raise ValueError("Invalid embedding batch size")
            return embeddings
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise DependencyUnavailable("Embedding dependency unavailable") from exc

    def add_documents(self, documents: list[dict[str, str]]) -> int:
        embeddings = self._embed([document["text"] for document in documents])
        try:
            with psycopg.connect(**self.database) as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO documents (id, text, embedding) VALUES (%s, %s, %s::vector) "
                        "ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, "
                        "embedding = EXCLUDED.embedding",
                        [
                            (document["id"], document["text"], json.dumps(vector))
                            for document, vector in zip(documents, embeddings, strict=True)
                        ],
                    )
        except psycopg.Error as exc:
            raise DependencyUnavailable("Vector store unavailable") from exc
        return len(documents)

    def search(self, query: str, limit: int = 3) -> list[dict]:
        vector = self._embed([query])[0]
        try:
            with psycopg.connect(**self.database) as conn:
                return conn.execute(
                    "SELECT id, text, embedding <=> %s::vector AS distance "
                    "FROM documents ORDER BY distance, id LIMIT %s",
                    (json.dumps(vector), limit),
                ).fetchall()
        except psycopg.Error as exc:
            raise DependencyUnavailable("Vector store unavailable") from exc

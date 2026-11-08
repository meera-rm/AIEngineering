"""Build and query the vector store used in Homework 5."""

import json
from pathlib import Path

import lancedb
from fastembed import TextEmbedding
from huggingface_hub import snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError


MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_REPOSITORY = "qdrant/bge-small-en-v1.5-onnx-q"
MODEL_REVISION = "52398278842ec682c6f32300af41344b1c0b0bb2"
MODEL_FILES = (
    "config.json",
    "model_optimized.onnx",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
)
TABLE_NAME = "homework5_chunks"
EMBEDDING_BATCH_SIZE = 32


class VectorStore:
    """Small interface around the course embedding model and LanceDB."""

    def __init__(self, database_path: str | Path) -> None:
        # Connecting creates a database here or reopens one built by an earlier run.
        self._database = lancedb.connect(database_path)
        # Resolve the exact snapshot ourselves; FastEmbed's default download is unpinned.
        try:
            model_path = snapshot_download(
                repo_id=MODEL_REPOSITORY,
                revision=MODEL_REVISION,
                allow_patterns=MODEL_FILES,
                local_files_only=True,
            )
        except LocalEntryNotFoundError:
            model_path = snapshot_download(
                repo_id=MODEL_REPOSITORY,
                revision=MODEL_REVISION,
                allow_patterns=MODEL_FILES,
            )
        self._embedder = TextEmbedding(
            model_name=MODEL_NAME,
            specific_model_path=model_path,
            cache_dir=model_path,
            local_files_only=True,
        )

    def build(self, records: list[dict]) -> None:
        """Embed prepared Task 5 records and save them in LanceDB."""
        if not records:
            raise ValueError("records must contain at least one prepared chunk")

        chunk_ids = [record["chunk_id"] for record in records]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("every record must have a unique chunk_id")

        # Only embedding_text becomes a vector. The original content is kept
        # separately so query results can return the exact source text.
        vectors = list(
            self._embedder.embed(
                [record["embedding_text"] for record in records],
                batch_size=EMBEDDING_BATCH_SIZE,
            )
        )

        stored_records = [
            {
                "chunk_id": record["chunk_id"],
                # LanceDB stores ordinary Python lists rather than NumPy arrays.
                "vector": vector.tolist(),
                "content": record["content"],
                # JSON keeps the student's metadata together in one database column.
                "metadata": json.dumps(record["metadata"]),
            }
            for record, vector in zip(records, vectors, strict=True)
        ]

        # Overwrite makes build() a reproducible rebuild rather than an append.
        # LanceDB automatically looks for the "vector" field in the provided records.
        self._database.create_table(
            TABLE_NAME,
            stored_records,
            mode="overwrite",
        )

    def query(self, ticket_body: str, top_k: int = 5) -> list[dict]:
        """Return the top-ranked chunks for an unaltered ticket body."""
        if not ticket_body.strip():
            raise ValueError("ticket_body must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        query_vector = next(iter(self._embedder.query_embed(ticket_body)))
        table = self._database.open_table(TABLE_NAME)
        # Cosine distance is smaller for chunks that are more similar to the query.
        matches = (
            table.search(query_vector)
            .distance_type("cosine")
            .limit(top_k)
            .to_list()
        )
        return [
            {
                "rank": rank,
                "chunk_id": match["chunk_id"],
                "distance": float(match["_distance"]),
                "content": match["content"],
                "metadata": json.loads(match["metadata"]),
            }
            for rank, match in enumerate(matches, start=1)
        ]

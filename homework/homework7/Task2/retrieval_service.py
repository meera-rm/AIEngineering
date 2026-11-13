import math
from pathlib import Path

from VectorStore import VectorStore

DEFAULT_DATABASE_PATH = Path(__file__).parent / "homework5_vector_store"
RETRIEVAL_COUNT = 5


class InvalidRequestError(Exception):
    """The request breaks the request schema."""

class RetrievalServiceError(Exception):
    """The vector store could not be set up, failed, or returned invalid output."""

class RetrievalUnavailableError(Exception):
    """The vector store is temporarily unavailable; the workflow may retry."""


class RetrievalService:
    """Retrieves the chunks most similar to a ticket body."""

    def __init__(self, database_path: str | Path | None = None, top_k: int = RETRIEVAL_COUNT):
        self.database_path = Path(database_path) if database_path is not None else DEFAULT_DATABASE_PATH

        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            raise RetrievalServiceError("top_k must be a positive integer.")
        self.top_k = top_k

        # lancedb.connect() creates an empty database for a missing path, so check first.
        if not self.database_path.is_dir():
            raise RetrievalServiceError(f"Vector store not found at {self.database_path}")

        try:
            self.store = VectorStore(self.database_path)
        except Exception as e:
            raise RetrievalServiceError(f"Failed to open vector store at {self.database_path}") from e


    def _check_records(self, records: list[dict]) -> None:
        """Raise RetrievalServiceError unless records satisfy the response schema."""
        if not isinstance(records, list):
            raise RetrievalServiceError("Retrieved records must be a list.")
        if len(records) == 0:
            raise RetrievalServiceError("No evidence was retrieved.")
        if len(records) > self.top_k:
            raise RetrievalServiceError("More records than the retrieval count were returned.")

        expected_keys = {"rank", "chunk_id", "distance", "content", "metadata"}
        seen_ids = set()
        previous_distance = None

        for position, record in enumerate(records, start=1):
            if not isinstance(record, dict) or set(record) != expected_keys:
                raise RetrievalServiceError("Each record must be a dict with exactly the five evidence fields.")

            rank = record["rank"]
            if isinstance(rank, bool) or not isinstance(rank, int) or rank != position:
                raise RetrievalServiceError("rank must count 1, 2, 3... in order.")

            chunk_id = record["chunk_id"]
            if not isinstance(chunk_id, str) or not chunk_id.strip() or chunk_id in seen_ids:
                raise RetrievalServiceError("chunk_id must be a unique non-empty string.")
            seen_ids.add(chunk_id)

            distance = record["distance"]
            if not isinstance(distance, float) or not math.isfinite(distance) or distance < 0:
                raise RetrievalServiceError("distance must be a finite float that is not negative.")
            if previous_distance is not None and distance < previous_distance:
                raise RetrievalServiceError("distance must not decrease as rank increases.")
            previous_distance = distance

            content = record["content"]
            if not isinstance(content, str) or not content.strip():
                raise RetrievalServiceError("content must be a non-empty string.")

            if not isinstance(record["metadata"], dict):
                raise RetrievalServiceError("metadata must be a dictionary.")

        
    
    def retrieve_evidence(self, request: dict) -> dict:
        """Return the closest chunks for request["body"].

        Raises:
            InvalidRequestError: the request breaks the request schema.
            RetrievalUnavailableError: temporary store trouble (the workflow may retry).
            RetrievalServiceError: any other failure, including zero results.
        """
        if not isinstance(request, dict):
            raise InvalidRequestError("Request must be a dictionary.")
        body = request.get("body")
        if not isinstance(body, str) or not body.strip():
            raise InvalidRequestError("body must be a string with at least one non-whitespace character")

        try:
            records = self.store.query(body, top_k=self.top_k)    # body passed unaltered
        except FileNotFoundError as e:
            raise RetrievalServiceError("The vector store data is missing.") from e
        except (OSError, TimeoutError, ConnectionError) as e:
            raise RetrievalUnavailableError("The vector store is temporarily unavailable.") from e
        except Exception as e:
            raise RetrievalServiceError("An error occurred during retrieval.") from e

        self._check_records(records)          # raises RetrievalServiceError if invalid
        return {"results": records}
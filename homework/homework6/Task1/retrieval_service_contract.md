# Retrieval Service Contract

**Contract parts:** purpose, entry point, request schema, response schema, errors.

**Purpose:** Return the knowledge-base chunks most relevant to a ticket body, using the Homework 5 `VectorStore.query()`.
**Entry point:** `RetrievalService.retrieve_evidence(request: dict) -> dict` (vector store opened and retrieval count `top_k = 5` stored once in `__init__`)

## Request schema

| Field | Type | Required | Rules |
|---|---|---|---|
| `body` | str | yes | At least one non-whitespace character. Must be the same unaltered `Body` sent to routing. |

Extra fields are ignored.

## Response schema (success)

| Field | Type | Required | Rules |
|---|---|---|---|
| `results` | list of records | yes | 1 to `top_k` (the count set in `__init__`) records, ordered by `rank` ascending, as returned by `VectorStore.query()`. |

Each record contains exactly these five fields: `rank`, `chunk_id`, `distance`, `content` and `metadata`. A record with a missing or extra field is invalid.

| Field | Type | Rules |
|---|---|---|
| `rank` | int | Starts at 1 and increases by 1 with no gaps. |
| `chunk_id` | str | Non-empty, unique within `results`. |
| `distance` | float | Finite and not negative; never decreases as `rank` increases (smaller means more similar). |
| `content` | str | Non-empty chunk text. |
| `metadata` | dict | A JSON object; may be empty. |

## Error handling

| Error | When | Retryable? |
|---|---|---|
| `InvalidRequestError` | The request is not a dict, or `body` is missing, is not a string, or is blank. The vector store is not queried. | No. The same input fails the same way. |
| `RetrievalServiceError` | The vector store cannot be set up: the database or embedding files are missing or unreadable. | No. The files will not appear by themselves. |
| `RetrievalServiceError` | The table is missing, or embedding fails. | No. This is a permanent problem; someone has to repair it. |
| `RetrievalServiceError` | The query succeeds but returns **zero** records. An empty list is never returned as a success, because the workflow needs evidence to build the RAG prompt. | No. The same query returns the same nothing. |
| `RetrievalServiceError` | A returned record breaks the record rules in the response schema. | No. The same data gives the same problem. |
| `RetrievalUnavailableError` | The vector store is temporarily unreachable or locked, or the query raises an I/O or connection error. | **Yes**: up to 2 retries with backoff (0.5 s, 1 s). |

- **No success-shaped fallback:** the service never returns an empty or placeholder `results` list when something fails.
- **Zero results is a failure,** because the workflow needs evidence to build the RAG prompt.
- Error messages never contain the ticket body or any chunk content.
- The workflow retries only `RetrievalUnavailableError`, up to 2 times. Every other error ends the workflow as `workflow_failed`.
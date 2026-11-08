# LLM Service Contract

**Contract parts:** purpose, entry point, request schema, response schema, errors.

**Purpose:** A general-purpose client for the local Ollama API. It sends **any** chat messages with **any** model settings and returns the model's output. It is *not* a summarization service: it holds no prompt, no model choice, and no output schema of its own.
**Entry point:** `LLMClient.call_llm(request: dict) -> dict`. `__init__` stores only the Ollama base URL (e.g. `http://localhost:11434`). It does not load a model into Python.

The caller decides the messages, model, settings and output schema. The service forwards them to Ollama and does not interpret them.

## Request schema

| Field | Type | Required | Rules |
|---|---|---|---|
| `messages` | list[dict] | yes | Non-empty list. Each item is `{"role": "system" \| "user" \|"assistant", "content": str}` with non-blank content. Sent to Ollama `/api/chat`. |
| `model` | str | yes | Non-empty Ollama model tag. The service has no default model.|
| `options` | dict | no | Generation settings forwarded to Ollama (e.g. `temperature`, `seed`, `num_predict`). Numeric values must be finite. Default `{}`. |
| `output_schema` | dict \| null | no | A JSON Schema forwarded to Ollama `format`. If given, the output must parse as JSON. Default `null` (plain text). |
| `timeout_s` | float | no | Must be > 0. Default `300`. |

The request must be a dictionary. Extra fields are ignored. Every call sends `stream: false`.

## Response schema (success)

| Field | Type | Required | Rules |
|---|---|---|---|
| `model` | str | yes | The model Ollama reports it used. |
| `text` | str | yes | Raw `message.content` from Ollama; non-empty. |
| `parsed` | dict \| null | yes | When `output_schema` was given: the JSON-parsed `text`, checked against that schema. Otherwise `null`. |
| `duration_ms` | int | yes | Wall-clock time of the Ollama call (≥ 0). Used for tracing. |


If `output_schema` was given, `text` must be valid JSON that satisfies the schema, and `parsed` holds that decoded JSON object. If it does not, the call fails with `LLMOutputError` instead of returning partial output. If no `output_schema` was given, `parsed` is `null`.



## Error handling

| Error | When | Retryable? |
|---|---|---|
| `InvalidRequestError` | The request is not a dict, or `messages` / `model` is missing or invalid, or `options`, `output_schema` or `timeout_s` has the wrong type or value. Ollama is not called. | No. The same input fails the same way. |
| `LLMUnavailableError` | Connection refused, timeout, or Ollama 5xx. | **Yes**: the workflow retries up to 2 times with backoff (1 s, 2 s). |
| `LLMModelError` | Ollama returns 404 (model not pulled) or another 4xx. | No. This is a permanent setup problem. |
| `LLMOutputError` | The output is empty, or `output_schema` was given and the output is not valid JSON or does not match the schema. | Not retried by default. The same request can give different output when `temperature` > 0, so the workflow may choose to retry; with `temperature` 0 a retry gives the same result. |

- No success-shaped fallback: the service never returns a default, empty, or made-up output.
- Error messages never contain the request messages, the model output, or hidden model reasoning.
- The workflow retries only `LLMUnavailableError`, up to 2 times. Every other error ends the workflow as `workflow_failed`.
- Before returning, the service checks the response against the response schema above.
# Task 4: Local LLM setup check

Model: Ollama `qwen2.5:1.5b-instruct-q4_K_M`, set up following `LLM_SETUP.md` (macOS). installed with the Ollama install script instead of the .dmg, which produced the same app in /Applications.
The local API is `http://localhost:11434`.

## 1. Install and start Ollama

Installed with the Ollama install script, which replaced the earlier installation and started Ollama:

```text
% curl -fsSL https://ollama.com/install.sh | sh
>>> Stopping running Ollama instance...
>>> Removing existing Ollama installation...
>>> Downloading Ollama for macOS...
######################################################################## 100.0%
>>> Installing Ollama to /Applications...
>>> Starting Ollama...
>>> Install complete. You can now run 'ollama'.
```

## 2. Verify the runtime

The client and the local API report the same version:

```text
% ollama --version
ollama version is 0.40.6

% curl http://localhost:11434/api/version
{"version":"0.40.6"}
```

## 3. Download the course model

```text
% ollama pull qwen2.5:1.5b-instruct-q4_K_M
pulling manifest
pulling 183715c43589: 100% ▕██████████████████▏ 986 MB
pulling 66b9ea09bd5b: 100% ▕██████████████████▏   68 B
pulling eb4402837c78: 100% ▕██████████████████▏ 1.5 KB
pulling 832dd9e00a68: 100% ▕██████████████████▏  11 KB
pulling 377ac4d7aeef: 100% ▕██████████████████▏  487 B
verifying sha256 digest
writing manifest
removing unused layers
success

% ollama list
NAME                            ID              SIZE      MODIFIED
qwen2.5:1.5b-instruct-q4_K_M    65ec06548149    986 MB    8 seconds ago
llama3.2:latest                 a80c4f17acd5    2.0 GB    2 months ago
```

`ollama list` contains exactly `qwen2.5:1.5b-instruct-q4_K_M`.

## 4. Smoke test

The test from `LLM_SETUP.md`, with `temperature` 0 and `seed` 42:

```text
% curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:1.5b-instruct-q4_K_M",
    "messages": [
      {
        "role": "user",
        "content": "Reply with exactly READY."
      }
    ],
    "stream": false,
    "options": {
      "temperature": 0,
      "seed": 42
    }
  }'
{"model":"qwen2.5:1.5b-instruct-q4_K_M","created_at":"2026-10-17T22:10:04.246627Z","message":{"role":"assistant","content":"READY"},"done":true,"done_reason":"stop","total_duration":598865666,"load_duration":539019000,"prompt_eval_count":34,"prompt_eval_cached_count":0,"prompt_eval_duration":47273000,"eval_count":2,"eval_duration":9762000}
```

The request completed and `message.content` is "READY", which is non-empty.

## 5. Structured output check

An additional call with a JSON schema in `format`, the way Tasks 5 to 7 will call the model:

```text
% curl http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
  "model": "qwen2.5:1.5b-instruct-q4_K_M",
  "messages": [{"role": "user", "content": "Summarize: My invoice was charged twice, please refund the extra charge."}],
  "format": {
    "type": "object",
    "properties": {
      "summary": {"type": "string"},
      "customer_request": {"type": "string"},
      "missing_information": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["summary", "customer_request", "missing_information"]
  },
  "stream": false,
  "options": {"temperature": 0, "seed": 42}
}'
```

The response was a valid JSON object with the three required fields:

```json
{
  "summary": "The customer is requesting a refund for an extra charge on their invoice.",
  "customer_request": "refund extra charge",
  "missing_information": ["invoice number", "amount of extra charge", "reason for extra charge"]
}
```

## Result

The model is installed and the API works, including schema-constrained output, so the ticket-summary feature can be built on it.

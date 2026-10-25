# Homework 4 Local LLM Setup

Homework 4 uses one fixed local model:

- **Runtime:** Ollama
- **Model:** `qwen2.5:1.5b-instruct-q4_K_M`
- **API base URL:** `http://localhost:11434`

Use this exact model tag. Do not substitute another size, quantization, or model.
The model download is approximately 986 MB.

## 1. Install and Start Ollama

Complete the instructions for your operating system.

### Windows

Windows 10 22H2 or newer is required.

```powershell
winget install --id Ollama.Ollama --exact
```

Open Ollama from the Start menu after installation. It runs in the background.
Close and reopen your terminal if the `ollama` command is not initially found.

### macOS

macOS Sonoma 14 or newer is required. Download the installer from
[ollama.com/download](https://ollama.com/download), open the `.dmg`, move Ollama
to `Applications`, and launch it. Allow Ollama to add its command-line tool when
prompted.

### Linux

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

If the installer did not start Ollama as a service, run it in a separate terminal
and leave that terminal open:

```bash
ollama serve
```

## 2. Verify the Runtime

Check the installed version:

```text
ollama --version
```

Confirm that the local API is reachable.

**PowerShell**

```powershell
Invoke-RestMethod http://localhost:11434/api/version
```

**macOS or Linux**

```bash
curl http://localhost:11434/api/version
```

The command must return an Ollama version. The API endpoint is
`http://localhost:11434`; it does not require an API key.

## 3. Download the Course Model

```text
ollama pull qwen2.5:1.5b-instruct-q4_K_M
ollama list
```

Confirm that `ollama list` contains exactly
`qwen2.5:1.5b-instruct-q4_K_M`. Keep this model fixed throughout the assignment.

## 4. Run the Task 4 Smoke Test

The first request may take longer while Ollama loads the model.

**PowerShell**

```powershell
$request = @{
    model = "qwen2.5:1.5b-instruct-q4_K_M"
    messages = @(
        @{
            role = "user"
            content = "Reply with exactly READY."
        }
    )
    stream = $false
    options = @{
        temperature = 0
        seed = 42
    }
}

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:11434/api/chat" `
    -ContentType "application/json" `
    -Body ($request | ConvertTo-Json -Depth 10)

$response.message.content
```

**macOS or Linux**

```bash
curl http://localhost:11434/api/chat \
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
```

The response is successful when the HTTP request completes and
`message.content` is non-empty. Nothing from this smoke test is submitted.

## API Contract for Later Tasks

Tasks 5-7 use `POST http://localhost:11434/api/chat`. The request contains:

| Field | Purpose |
| --- | --- |
| `model` | The fixed model tag |
| `messages` | Chat messages containing stable instructions and ticket input |
| `format` | A JSON Schema representing the Task 5 output contract |
| `stream` | Set to `false` so one complete response is returned |
| `options` | Fixed generation settings |

Pass a JSON Schema representing the complete Task 5 output contract as the value
of `format`. Ollama uses it to constrain generation.

Use `temperature: 0` and `seed: 42` for the Homework 4 prompt comparison. Keep
the model, settings, schema, request code, and ticket bodies unchanged while
comparing prompt versions.

## Troubleshooting

- **`ollama` is not recognized on Windows:** Close and reopen the terminal. If
  needed, launch Ollama from the Start menu first.
- **Connection refused at port 11434:** Start the Ollama application or run
  `ollama serve`. Do not start a second server if the desktop application is
  already running.
- **Model not found:** Run
  `ollama pull qwen2.5:1.5b-instruct-q4_K_M` and confirm the exact tag with
  `ollama list`.
- **The first request times out:** Wait for the model to finish loading and retry
  the smoke test. Later requests should be faster while the model remains loaded.
- **Insufficient disk space:** Ollama's installation and models use several
  gigabytes. See the official platform documentation for changing the model
  storage location.

## Verified Reference Environment

This workflow was verified on Windows with:

- Ollama `0.34.1`
- `qwen2.5:1.5b-instruct-q4_K_M`
- Model size: 986 MB
- A successful non-streaming `/api/chat` smoke test
- A successful `/api/chat` request using a JSON Schema in `format`

Official documentation:

- [Ollama Windows setup](https://docs.ollama.com/windows)
- [Ollama macOS setup](https://docs.ollama.com/macos)
- [Ollama Linux setup](https://docs.ollama.com/linux)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
"""Task 5: call the local LLM to summarize one support ticket, and validate the result.

Usage:  python summarize_ticket.py [ticket_id]      (default test ticket: 26456)

The request follows LLM_SETUP.md: fixed model, temperature 0, seed 42, a JSON
schema in `format`, and stream=false. Only the prompt text changes between
prompt versions.
"""
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parent / "Task1" / "support_tickets.csv"   # canonical dataset

URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b-instruct-q4_K_M"
OPTIONS = {"temperature": 0, "seed": 42}
FIELDS = ["summary", "customer_request", "missing_information"]

# JSON Schema for the Task 5 output contract
SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "customer_request": {"type": "string"},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": FIELDS,
    "additionalProperties": False,
}


def build_request(prompt: str, body: str) -> dict:
    """Stable instructions go in the system message; the ticket Body, wrapped in <ticket> tags, is the user message."""
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Summarize the following ticket:\n<ticket>\n{body}\n</ticket>"},
        ],
        "format": SCHEMA,
        "stream": False,
        "options": OPTIONS,
    }


def call_llm(request: dict, timeout: int = 300) -> str:
    """POST the request to the local Ollama API and return message.content."""
    data = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as err:
        raise RuntimeError(f"Could not reach Ollama at {URL}: {err}") from err
    return reply["message"]["content"]


def validate_summary(raw: str) -> dict:
    """Check the model output against the Task 5 contract; return the parsed dict or raise ValueError."""
    try:
        out = json.loads(raw)
    except json.JSONDecodeError as err:
        raise ValueError(f"Output is not valid JSON: {err}") from err
    if not isinstance(out, dict):
        raise ValueError("Output is not a JSON object")

    problems = []
    missing, extra = set(FIELDS) - set(out), set(out) - set(FIELDS)
    if missing:
        problems.append(f"missing fields: {sorted(missing)}")
    if extra:
        problems.append(f"unexpected fields: {sorted(extra)}")

    for field in ("summary", "customer_request"):
        if field in out and not (isinstance(out[field], str) and out[field].strip()):
            problems.append(f"{field} must be a non-empty string")
    if isinstance(out.get("summary"), str):
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", out["summary"].strip()) if s]
        if len(sentences) > 2:
            problems.append(f"summary has {len(sentences)} sentences (limit is 2)")

    info = out.get("missing_information")
    if "missing_information" in out:
        if not isinstance(info, list):
            problems.append("missing_information must be a list")
        elif not all(isinstance(x, str) and x.strip() for x in info):
            problems.append("missing_information must contain only non-empty strings")

    if problems:
        raise ValueError("Invalid output: " + "; ".join(problems))
    return out


def summarize_ticket(body: str, prompt: str) -> dict:
    """Summarize one ticket Body with the given prompt text. Returns the validated dict."""
    return validate_summary(call_llm(build_request(prompt, body)))


def load_ticket(ticket_id: int) -> str:
    with open(DATASET, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["ticket_id"]) == ticket_id:
                return row["Body"]
    raise KeyError(f"ticket {ticket_id} not found")


if __name__ == "__main__":
    ticket_id = int(sys.argv[1]) if len(sys.argv) > 1 else 26456
    prompt = (HERE / "prompt_v1.txt").read_text(encoding="utf-8")
    body = load_ticket(ticket_id)
    result = summarize_ticket(body, prompt)
    print(json.dumps(result, indent=2))
    record = {"ticket_id": ticket_id, "prompt_file": "prompt_v1.txt", "model": MODEL,
              "options": OPTIONS, "body": body, "output": result}
    (HERE / "test_ticket_output.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

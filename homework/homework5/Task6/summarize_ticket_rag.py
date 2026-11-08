"""Task 6: RAG-informed ticket summary (HW4 summarize_ticket.py + retrieved context).

What is the same as HW4 (homework4/Task5/summarize_ticket.py):
  model, temperature 0, seed 42, stream=false, the JSON schema in `format`, the
  output validation, the system/user message split, and the unaltered ticket Body.

What was added (only what is needed to get RAG results into the prompt):
  1. retrieve(): query the Task 4 vector store with the unaltered Body, top K = 5,
     keeping chunks with cosine distance <= MAX_DISTANCE (0.21). See k_selection.md.
  2. format_reference_articles(): put the kept chunks in a <reference_articles> block
     after the <ticket> block, so ticket (user input) and articles (external context)
     are clearly separated. If nothing passes the cut-off, the block says so.
  3. num_predict: 512 in the options (required by the HW5 assignment for every summary).
  4. Each run saves the retrieval results, the exact user message, and the output.

--no-rag runs the original HW4 prompt and user message unchanged (same settings,
including num_predict 512), for a fair RAG vs. no-RAG comparison.

Needs: Ollama running locally with the model pulled; HW5 .venv active.
Usage:
  python summarize_ticket_rag.py 28763              # RAG, one ticket
  python summarize_ticket_rag.py 28763 29206 28921  # RAG, several tickets
  python summarize_ticket_rag.py --no-rag 28763     # baseline with the HW4 prompt
"""
import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE / "support_tickets.csv"   # canonical dataset, copied unchanged from homework4/Task1
MATERIALS = HERE.parent / "HW5_materials"
DB_PATH = HERE.parent / "Task4" / "homework5_vector_store"
RAG_PROMPT = HERE / "prompt_v2_rag.txt"
NO_RAG_PROMPT = HERE / "prompt_v1.txt"   # accepted HW4 prompt, brought forward unchanged
OUT_DIR = HERE / "outputs"

URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b-instruct-q4_K_M"
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 512}   # num_predict added for HW5
FIELDS = ["summary", "customer_request", "missing_information"]

# Retrieval settings, chosen in k_selection.md
K = 5
MAX_DISTANCE = 0.21
NO_ARTICLES = "No relevant reference articles were found."

# JSON Schema for the output contract (unchanged from HW4)
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

_store = None


def get_store():
    """Open the persisted Task 4 vector store once (supplied VectorStore class)."""
    global _store
    if _store is None:
        sys.path.insert(0, str(MATERIALS))
        from VectorStore import VectorStore
        if not DB_PATH.exists():
            raise SystemExit(f"{DB_PATH} not found; run Task4/build_vector_store.py first")
        _store = VectorStore(DB_PATH)
    return _store


def retrieve(body: str) -> tuple[list[dict], list[dict]]:
    """Query with the unaltered Body. Returns (kept chunks, all top-K hits)."""
    hits = get_store().query(body, top_k=K)
    kept = [h for h in hits if h["distance"] <= MAX_DISTANCE]
    return kept, hits


def format_reference_articles(chunks: list[dict]) -> str:
    """Build the <reference_articles> block from the kept chunks' unmodified content."""
    if not chunks:
        inner = NO_ARTICLES
    else:
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk["metadata"]
            content = chunk["content"].replace("\r\n", "\n").strip()
            parts.append(f"[{i}] {meta['title']} — {meta['section_heading']}\n{content}")
        inner = "\n\n".join(parts)
    return f"<reference_articles>\n{inner}\n</reference_articles>"


def build_request(prompt: str, body: str, reference_block: str | None = None) -> dict:
    """Instructions in the system message; the ticket (and, with RAG, the articles) in the user message."""
    user = f"Summarize the following ticket:\n<ticket>\n{body}\n</ticket>"
    if reference_block is not None:
        user += f"\n\n{reference_block}"
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user},
        ],
        "format": SCHEMA,
        "stream": False,
        "options": OPTIONS,
    }


def call_llm(request: dict, timeout: int = 300) -> str:
    """POST the request to the local Ollama API and return message.content. (unchanged from HW4)"""
    data = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as err:
        raise RuntimeError(f"Could not reach Ollama at {URL}: {err}") from err
    return reply["message"]["content"]


def validate_summary(raw: str) -> dict:
    """Check the model output against the output contract. (unchanged from HW4)"""
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


def summarize_ticket_rag(body: str, prompt: str) -> tuple[dict, dict]:
    """RAG run: retrieve, insert the articles, call the model. Returns (output, details)."""
    kept, hits = retrieve(body)
    block = format_reference_articles(kept)
    request = build_request(prompt, body, block)
    output = validate_summary(call_llm(request))
    details = {
        "retrieval": {"k": K, "max_distance": MAX_DISTANCE,
                      "top_k_hits": [{"rank": h["rank"], "chunk_id": h["chunk_id"],
                                      "distance": round(h["distance"], 4),
                                      "title": h["metadata"]["title"],
                                      "section_heading": h["metadata"]["section_heading"],
                                      "kept": h["distance"] <= MAX_DISTANCE} for h in hits]},
        "user_message": request["messages"][1]["content"],
    }
    return output, details


def summarize_ticket(body: str, prompt: str) -> dict:
    """No-RAG run: the HW4 request, unchanged except for num_predict."""
    return validate_summary(call_llm(build_request(prompt, body)))


def load_ticket(ticket_id: int) -> str:
    with open(DATASET, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["ticket_id"]) == ticket_id:
                return row["Body"]
    raise KeyError(f"ticket {ticket_id} not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG-informed ticket summary (HW5 Task 6).")
    parser.add_argument("ticket_ids", type=int, nargs="+")
    parser.add_argument("--no-rag", action="store_true", help="run the original HW4 prompt without retrieval")
    args = parser.parse_args()

    mode = "no_rag" if args.no_rag else "rag"
    prompt_path = NO_RAG_PROMPT if args.no_rag else RAG_PROMPT
    prompt = prompt_path.read_text(encoding="utf-8")
    OUT_DIR.mkdir(exist_ok=True)

    for ticket_id in args.ticket_ids:
        body = load_ticket(ticket_id)
        if args.no_rag:
            output, details = summarize_ticket(body, prompt), {}
        else:
            output, details = summarize_ticket_rag(body, prompt)
        record = {"ticket_id": ticket_id, "mode": mode, "prompt_file": prompt_path.name,
                  "model": MODEL, "options": OPTIONS, **details, "output": output}
        out_file = OUT_DIR / f"{ticket_id}_{mode}.json"
        out_file.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(f"\n=== {ticket_id} ({mode}) -> outputs/{out_file.name}")
        if not args.no_rag:
            for h in details["retrieval"]["top_k_hits"]:
                mark = "kept" if h["kept"] else "cut "
                print(f"  {mark} {h['rank']}. {h['distance']:.4f} {h['chunk_id']}  {h['title'][:40]} / {h['section_heading']}")
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

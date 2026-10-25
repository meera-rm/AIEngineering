"""Task 7: run a prompt version on the 10 Task 6 tickets.

Usage:  python run_iteration.py <prompt_file> <output_folder>

Only the prompt file differs between runs. The model, settings, schema, request code
and ticket bodies are the Task 5/6 ones (see LLM_SETUP.md). Failures are recorded, not hidden.
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "Task6"))
import run_task6 as t6   # noqa: E402  (Task 6 runner: same tickets, same request code)


def main(prompt_file: str, out_dir: str) -> None:
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for tid in t6.TICKETS:
        r = t6.run_one(prompt, tid)
        results.append(r)
        print(tid, "valid" if r["schema_valid"] else f"INVALID: {r['validation_error']}")
    (out / "outputs.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    with open(out / "outputs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "department", "schema_valid", "validation_error",
                    "summary", "customer_request", "missing_information"])
        for r in results:
            o = r["output"] or {}
            w.writerow([r["ticket_id"], r["department"], r["schema_valid"], r["validation_error"] or "",
                        o.get("summary", ""), o.get("customer_request", ""),
                        json.dumps(o.get("missing_information", []))])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

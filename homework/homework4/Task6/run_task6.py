"""Task 6: run the initial prompt (Task 5, prompt_v1.txt) unchanged on the 10 listed tickets.

Reuses the Task 5 request code and validator, so only the tickets differ from Task 5.
Failures are recorded, not hidden: the raw model reply is saved even if it does not validate.

Usage:  python run_task6.py
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "Task5"))
import summarize_ticket as st   # noqa: E402  (Task 5 request code and validator)

PROMPT_FILE = HERE.parent / "Task5" / "prompt_v1.txt"

TICKETS = {   # ticket_id: department, from the assignment (longest Body per department)
    28907: "Billing and Payments",
    28399: "Customer Service",
    28381: "General Inquiry",
    28921: "Human Resources",
    28736: "IT Support",
    28763: "Product Support",
    28563: "Returns and Exchanges",
    28571: "Sales and Pre-Sales",
    28642: "Service Outages and Maintenance",
    29206: "Technical Support",
}


def run_one(prompt: str, ticket_id: int) -> dict:
    body = st.load_ticket(ticket_id)
    request = st.build_request(prompt, body)
    raw = st.call_llm(request)
    try:
        parsed, error = st.validate_summary(raw), None
    except ValueError as err:
        parsed, error = None, str(err)
    return {"ticket_id": ticket_id, "department": TICKETS[ticket_id], "body": body,
            "request": request, "raw_output": raw,
            "schema_valid": error is None, "validation_error": error, "output": parsed}


if __name__ == "__main__":
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    results = []
    for tid in TICKETS:
        r = run_one(prompt, tid)
        results.append(r)
        print(tid, "valid" if r["schema_valid"] else f"INVALID: {r['validation_error']}")
    (HERE / "task6_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    with open(HERE / "task6_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "department", "schema_valid", "validation_error",
                    "summary", "customer_request", "missing_information"])
        for r in results:
            o = r["output"] or {}
            w.writerow([r["ticket_id"], r["department"], r["schema_valid"], r["validation_error"] or "",
                        o.get("summary", ""), o.get("customer_request", ""),
                        json.dumps(o.get("missing_information", []))])

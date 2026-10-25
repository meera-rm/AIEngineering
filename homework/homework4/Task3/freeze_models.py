"""Freeze both models and the Task 2 decision before the test split is opened.

Writes freeze_record.json with SHA-256 hashes. predict_test.py refuses to run
if any frozen file has changed since this record was written.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["original/ticket_router.py", "original/ticket_router.joblib",
         "candidate/ticket_router.py", "candidate/ticket_router.joblib"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {
    "frozen_at": datetime.now().isoformat(timespec="seconds"),
    "task2_decision": "KEEP the stop-word change (stop_words='english' in the TF-IDF vectorizer). "
                      "Evidence: validation accuracy 0.4746 -> 0.4932, macro-F1 0.4873 -> 0.5096, "
                      "net +70 tickets (281 fixed, 211 broken). See Task2/experiment_log.md.",
    "original": "Homework 3 retrained router (immutable baseline)",
    "candidate": "Homework 4 Task 2 revision router (stop-word removal)",
    "sha256": {f: sha256(HERE / f) for f in FILES},
}
(HERE / "freeze_record.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))

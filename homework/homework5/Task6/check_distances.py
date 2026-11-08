"""Task 6, step 1: see how far retrieved chunks are for real ticket bodies.

Queries the Task 4 vector store with each ticket's unaltered Body (top 10) and prints
the distances, so a distance cut-off can be chosen from real numbers.
Tickets: the 3 Task 7 tickets (28763, 29206 supported; 28921 unsupported) plus the
other 2 Task 2 tickets for extra reference.

Run (HW5 .venv active):  python check_distances.py
                          python check_distances.py --dataset <path to support_tickets.csv>
"""

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATERIALS = HERE.parent / "HW5_materials"
DB = HERE.parent / "Task4" / "homework5_vector_store"
# Canonical dataset, copied unchanged from homework4/Task1; override with --dataset.
DEFAULT_DATASET = HERE / "support_tickets.csv"
TICKETS = [(28763, "Task 7: supported"), (29206, "Task 7: supported multi-source"),
           (28921, "Task 7: UNSUPPORTED"), (28907, "Task 2 only"), (28571, "Task 2 only")]

sys.path.insert(0, str(MATERIALS))
from VectorStore import VectorStore  


def load_bodies(path: Path) -> dict[int, str]:
    if not path.is_file():
        raise SystemExit(f"{path} not found; pass the dataset with --dataset")
    with path.open(newline="", encoding="utf-8") as f:
        return {int(r["ticket_id"]): r["Body"] for r in csv.DictReader(f)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="path to support_tickets.csv")
    bodies = load_bodies(parser.parse_args().dataset)
    store = VectorStore(DB)
    for ticket_id, case in TICKETS:
        print(f"\n=== {ticket_id} ({case}) ===")
        for hit in store.query(bodies[ticket_id], top_k=10):
            m = hit["metadata"]
            print(f"  {hit['rank']:>2}. {hit['distance']:.4f}  {hit['chunk_id']:<20} {m['title'][:45]} / {m['section_heading']}")


if __name__ == "__main__":
    main()

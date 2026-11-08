"""Task 5, step 1: run the 5 evaluation queries through the vector store (top 10 each).

Writes retrieval_results.csv with one row per (query, rank) and an empty `relevant`
column for manual labeling (1 = relevant, 0 = not relevant). "Relevant" means the chunk
contains information that helps address the query.

If retrieval_results.csv already exists with labels, it is NOT overwritten; the new
results go to retrieval_results_new.csv so labels are never lost.

Run (HW5 virtual environment active, after Task 4 built the store):
  python run_queries.py
"""

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP_K = 10
DEFAULT_DB = HERE.parent / "Task4" / "homework5_vector_store"
MATERIALS_CANDIDATES = [HERE.parent / "HW5_materials", HERE.parent / "materials", Path("homework/homework5/materials")]
FIELDS = ["query_id", "query", "rank", "chunk_id", "distance", "article_id", "title",
          "section_heading", "content", "relevant", "label_note"]


def find_materials(cli: Path | None) -> Path:
    for folder in ([cli] if cli else MATERIALS_CANDIDATES):
        if (folder / "VectorStore.py").is_file() and (folder / "evaluation_queries.json").is_file():
            return folder
    raise SystemExit("materials folder (VectorStore.py + evaluation_queries.json) not found; pass --materials")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materials", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    materials = find_materials(args.materials)
    sys.path.insert(0, str(materials.resolve()))
    from VectorStore import VectorStore

    if not args.db.exists():
        raise SystemExit(f"{args.db} not found; run Task4/build_vector_store.py first")
    store = VectorStore(args.db)
    queries = json.loads((materials / "evaluation_queries.json").read_text(encoding="utf-8"))

    rows = []
    for q in queries:
        for hit in store.query(q["query"], top_k=TOP_K):
            meta = hit["metadata"]
            rows.append({
                "query_id": q["query_id"], "query": q["query"], "rank": hit["rank"],
                "chunk_id": hit["chunk_id"], "distance": f"{hit['distance']:.4f}",
                "article_id": meta["article_id"], "title": meta["title"],
                "section_heading": meta["section_heading"],
                "content": hit["content"].replace("\r\n", "\n"),
                "relevant": "", "label_note": "",
            })

    out = HERE / "retrieval_results.csv"
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            if any(r.get("relevant", "").strip() for r in csv.DictReader(f)):
                out = HERE / "retrieval_results_new.csv"
                print("retrieval_results.csv already has labels; writing retrieval_results_new.csv instead")
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (HERE / "retrieval_results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(queries)} queries x top {TOP_K} = {len(rows)} rows -> {out.name}")
    for q in queries:
        print(f"\n{q['query_id']}: {q['query']}")
        for r in (r for r in rows if r["query_id"] == q["query_id"]):
            print(f"  {r['rank']:>2}. {r['chunk_id']:<22} {r['distance']}  {r['title'][:40]} / {r['section_heading']}")


if __name__ == "__main__":
    main()

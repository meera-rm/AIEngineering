"""Task 4: build the persistent vector store from the prepared Task 3 records.

Uses only the supplied VectorStore class (FastEmbed BAAI/bge-small-en-v1.5 at the
pinned revision, LanceDB, cosine distance), as VECTOR_STORE_SETUP.md requires.

Steps
  1. Load ../Task3/records.json and check every record has the four required fields.
  2. VectorStore(DB_PATH).build(records): embeds embedding_text, stores content + metadata.
     build() replaces the table, so re-running gives a clean rebuild, not duplicates.
  3. Reopen the database in a NEW VectorStore instance (proves it persisted) and check
     that every one of the records comes back exactly once with its content and metadata.
  4. Run one sample query and print the top results.

Run (with the HW5 virtual environment active):
  python build_vector_store.py
  python build_vector_store.py --materials <folder with VectorStore.py> --db <db folder>
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RECORDS = HERE.parent / "Task3" / "records.json"
DEFAULT_DB = HERE / "homework5_vector_store"
MATERIALS_CANDIDATES = [
    HERE.parent / "HW5_materials",                 # this homework folder's layout
    HERE.parent / "materials",
    Path("homework/homework5/materials"),          # course repo layout, run from repo root
]
REQUIRED_FIELDS = ("chunk_id", "embedding_text", "content", "metadata")
SAMPLE_QUERY = (
    "My Samsung QN90A TV keeps flickering even after I changed the brightness. "
    "Is this covered by warranty and can a technician look at it?"
)


def import_vector_store(materials: Path | None):
    """Import the supplied VectorStore class from the course materials folder."""
    candidates = [materials] if materials else MATERIALS_CANDIDATES
    for folder in candidates:
        if (folder / "VectorStore.py").is_file():
            sys.path.insert(0, str(folder.resolve()))
            from VectorStore import VectorStore
            return VectorStore
    raise SystemExit("VectorStore.py not found; pass its folder with --materials")


def load_records(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    for i, record in enumerate(records):
        missing = [f for f in REQUIRED_FIELDS if f not in record]
        if missing:
            raise SystemExit(f"record {i} is missing {missing}")
    return records


def verify(store, records: list[dict]) -> None:
    """Query with top_k = all records; every chunk must come back once, unchanged."""
    returned = store.query(SAMPLE_QUERY, top_k=len(records))
    by_id = {r["chunk_id"]: r for r in returned}
    expected = {r["chunk_id"]: r for r in records}
    assert len(returned) == len(records), f"expected {len(records)} rows, got {len(returned)}"
    assert by_id.keys() == expected.keys(), "stored chunk_ids differ from the records"
    for chunk_id, record in expected.items():
        assert by_id[chunk_id]["content"] == record["content"], f"content changed: {chunk_id}"
        assert by_id[chunk_id]["metadata"] == record["metadata"], f"metadata changed: {chunk_id}"
    distances = [r["distance"] for r in returned]
    assert distances == sorted(distances), "results are not ordered by cosine distance"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HW5 vector store from Task 3 records.")
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="where LanceDB persists its files")
    parser.add_argument("--materials", type=Path, help="folder containing the supplied VectorStore.py")
    args = parser.parse_args()

    VectorStore = import_vector_store(args.materials)
    records = load_records(args.records)

    VectorStore(args.db).build(records)
    print(f"Built {args.db.name}: {len(records)} records from {args.records}")

    reopened = VectorStore(args.db)   # new instance, no build(): reads the persisted table
    verify(reopened, records)
    print(f"Verified: reopened store returns all {len(records)} chunks with unchanged content and metadata")

    print(f"\nSample query: {SAMPLE_QUERY}")
    for hit in reopened.query(SAMPLE_QUERY, top_k=5):
        meta = hit["metadata"]
        print(f"  {hit['rank']}. {hit['chunk_id']:<22} distance={hit['distance']:.4f}  "
              f"{meta['title'][:45]} / {meta['section_heading']}")


if __name__ == "__main__":
    main()

"""Task 5, step 3: compute retrieval metrics from the labeled results.

Reads retrieval_results.csv (relevant column filled with 1/0 for every row) and
reports, for k = 3, 5, 10:
  - Precision@k : share of the top k that is relevant.
  - Recall@k    : share of the query's relevant chunks found in the top k.
                  Denominator = relevant chunks labeled in the top 10 (pooled judgments;
                  chunks never retrieved in the top 10 were not judged).
  - NDCG@k      : rewards relevant chunks ranked near the top (binary gain, log2 discount).
Per query and as the mean across queries (macro average).

A query with no relevant chunk in its top 10 has precision 0, but recall and NDCG are
undefined (nothing to find). They are left blank for that query and the recall/NDCG
means are taken over the queries that have at least one relevant chunk; the summary
reports how many queries each mean covers.

Writes metrics_per_query.csv and metrics_summary.csv.

Run:  python compute_metrics.py
"""

import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
KS = (3, 5, 10)


def precision_at_k(labels: list[int], k: int) -> float:
    return sum(labels[:k]) / k


def recall_at_k(labels: list[int], k: int) -> float | None:
    total = sum(labels)
    return sum(labels[:k]) / total if total else None


def ndcg_at_k(labels: list[int], k: int) -> float | None:
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(labels[:k]))
    ideal = sorted(labels, reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg else None


METRICS = {"precision": precision_at_k, "recall": recall_at_k, "ndcg": ndcg_at_k}


def main() -> None:
    with (HERE / "retrieval_results.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    unlabeled = [f"{r['query_id']} rank {r['rank']}" for r in rows if r["relevant"].strip() not in ("0", "1")]
    if unlabeled:
        raise SystemExit(f"Label every row 1 or 0 first. Missing/invalid: {', '.join(unlabeled[:10])}"
                         + (" ..." if len(unlabeled) > 10 else ""))

    by_query: dict[str, list[int]] = {}
    for r in sorted(rows, key=lambda r: (r["query_id"], int(r["rank"]))):
        by_query.setdefault(r["query_id"], []).append(int(r["relevant"]))

    per_query = []
    for qid, labels in by_query.items():
        row = {"query_id": qid, "relevant_in_top10": sum(labels)}
        for k in KS:
            for name, fn in METRICS.items():
                value = fn(labels, k)
                row[f"{name}@{k}"] = "" if value is None else round(value, 4)
        per_query.append(row)

    summary = []
    for k in KS:
        entry = {"k": k}
        for name in METRICS:
            values = [r[f"{name}@{k}"] for r in per_query if r[f"{name}@{k}"] != ""]
            entry[f"mean_{name}"] = round(sum(values) / len(values), 4) if values else ""
            entry[f"{name}_queries"] = len(values)
        summary.append(entry)

    for name, data in (("metrics_per_query.csv", per_query), ("metrics_summary.csv", summary)):
        with (HERE / name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)

    print("Per query:")
    header = ["query", "rel@10"] + [f"{n}@{k}" for k in KS for n in METRICS]
    print("  " + "  ".join(f"{h:>12}" for h in header))
    for r in per_query:
        vals = [r["query_id"], r["relevant_in_top10"]] + [r[f"{n}@{k}"] for k in KS for n in METRICS]
        print("  " + "  ".join(f"{v:>12}" for v in vals))
    print("\nMean across queries:")
    fmt = lambda v: "n/a" if v == "" else f"{v:.3f}"
    for s in summary:
        print(f"  k={s['k']:>2}  precision={fmt(s['mean_precision'])} (n={s['precision_queries']})"
              f"  recall={fmt(s['mean_recall'])} (n={s['recall_queries']})"
              f"  ndcg={fmt(s['mean_ndcg'])} (n={s['ndcg_queries']})")


if __name__ == "__main__":
    main()

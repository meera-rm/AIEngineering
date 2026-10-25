"""Homework 3 metrics and confusion matrices for both frozen models on the test split."""
import json
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

import compute_metrics as cm

HERE = Path(__file__).resolve().parent
VAL = {"original": HERE.parent / "Task1" / "validation_predictions.csv",
       "candidate": HERE.parent / "Task2" / "validation_predictions.csv"}
source = pd.read_csv(cm.DATA / "support_tickets.csv")


def load(path):
    df = pd.read_csv(path).merge(source[["ticket_id", "Body"]], on="ticket_id", how="left", validate="one_to_one")
    assert df["Body"].notna().all()
    df["class_scores"] = df["class_scores"].apply(json.loads)
    return df


def evaluate(df):
    labels = sorted(df["true_label"].unique())
    conf = cm.confusion_matrix(df["true_label"], df["recommended_department"], labels)
    per_class = cm.per_class_metrics(cm.one_vs_rest(conf))
    return conf, per_class, cm.summary_metrics(per_class, df).set_index("metric")["value"]


test = {n: load(HERE / f"test_predictions_{n}.csv") for n in ("original", "candidate")}
val = {n: load(p) for n, p in VAL.items()}
assert list(test["original"]["ticket_id"]) == list(test["candidate"]["ticket_id"])

res = {n: evaluate(df) for n, df in test.items()}
val_sum = {n: evaluate(df)[2] for n, df in val.items()}

# --- summary: test and validation, both models
summary = pd.DataFrame({"test_original": res["original"][2], "test_candidate": res["candidate"][2]})
summary["test_change"] = summary["test_candidate"] - summary["test_original"]
summary["val_original"] = val_sum["original"]
summary["val_candidate"] = val_sum["candidate"]
summary["val_change"] = summary["val_candidate"] - summary["val_original"]
print(summary.round(4).to_string())
summary.round(4).to_csv(HERE / "test_summary_metrics.csv")

# --- per-class
pc = pd.DataFrame({
    "support": res["original"][1].set_index("department")["support"],
    "recall_orig": res["original"][1].set_index("department")["recall"],
    "recall_cand": res["candidate"][1].set_index("department")["recall"],
    "precision_orig": res["original"][1].set_index("department")["precision"],
    "precision_cand": res["candidate"][1].set_index("department")["precision"],
    "f1_orig": res["original"][1].set_index("department")["f1"],
    "f1_cand": res["candidate"][1].set_index("department")["f1"]})
pc["f1_change"] = pc["f1_cand"] - pc["f1_orig"]
print(pc.round(3).sort_values("f1_change").to_string())
pc.round(4).to_csv(HERE / "test_per_class_metrics.csv")

# --- confusion matrices (full department names)
for n in ("original", "candidate"):
    res[n][0].to_csv(HERE / f"test_confusion_matrix_{n}.csv", index_label="true \\ predicted")

# --- body-length slices (cut points from training data only, as in Homework 3)
q1, q2 = cm.slice_cut_points(source)
rows = []
for n, df in test.items():
    d = df.assign(words=cm.word_count(df["Body"]))
    d["slice"] = pd.cut(d["words"], bins=[-1, q1, q2, float("inf")], labels=["short", "medium", "long"])
    for s in ["short", "medium", "long"]:
        sub = d[d["slice"] == s]
        _, pcs, sm = evaluate(sub)
        rows.append({"model": n, "slice": s, "n": len(sub), "accuracy": sm["accuracy"], "macro_f1": sm["macro_f1"]})
slices = pd.DataFrame(rows).pivot(index="slice", columns="model", values=["n", "accuracy", "macro_f1"])
print(f"\nSlice cut points: short <= {q1:.0f} < medium <= {q2:.0f} < long")
print(slices.round(4).to_string())
slices.round(4).to_csv(HERE / "test_slice_metrics.csv")

# --- ticket-level comparison
m = test["original"][["ticket_id", "true_label", "recommended_department"]].merge(
    test["candidate"][["ticket_id", "recommended_department"]], on="ticket_id", suffixes=("_o", "_c"))
ok_o, ok_c = m.true_label == m.recommended_department_o, m.true_label == m.recommended_department_c
fixed, broken = int((~ok_o & ok_c).sum()), int((ok_o & ~ok_c).sum())
print(f"\nTest: fixed {fixed}, broken {broken}, net {fixed - broken}, "
      f"McNemar exact p = {binomtest(fixed, fixed + broken, 0.5).pvalue:.4f}")
pair = {"Technical Support", "IT Support"}
t = m[m.true_label.isin(pair)]
print(f"Tech/IT true-label tickets correct: original {int((t.true_label == t.recommended_department_o).sum())} "
      f"-> candidate {int((t.true_label == t.recommended_department_c).sum())} of {len(t)}")

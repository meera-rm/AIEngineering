"""Compare the HW3 baseline against the HW4 Task 2 candidate on the validation set."""
from pathlib import Path
import json
import pandas as pd

import compute_metrics as cm

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "Task1" / "validation_predictions.csv"   # HW3 predictions, unchanged
CANDIDATE = HERE / "validation_predictions.csv"
ANNOTATIONS = HERE.parent / "Task1" / "annotations.csv"
TECH, IT = "Technical Support", "IT Support"


def load(path):
    df = pd.read_csv(path)
    df["class_scores"] = df["class_scores"].apply(json.loads)
    return df


def metrics(df):
    labels = sorted(df["true_label"].unique())
    ovr = cm.one_vs_rest(cm.confusion_matrix(df["true_label"], df["recommended_department"], labels))
    per_class = cm.per_class_metrics(ovr)
    summary = cm.summary_metrics(per_class, df)
    return per_class.set_index("department"), summary.set_index("metric")["value"]


base, cand = load(BASELINE), load(CANDIDATE)
assert list(base["ticket_id"]) == list(cand["ticket_id"]), "Prediction files cover different tickets"
assert (base["true_label"] == cand["true_label"]).all(), "True labels differ between files"

base_pc, base_sum = metrics(base)
cand_pc, cand_sum = metrics(cand)

summary = pd.DataFrame({"baseline": base_sum, "candidate": cand_sum})
summary["change"] = summary["candidate"] - summary["baseline"]
print(summary.round(4).to_string())

per_class = pd.DataFrame({
    "recall_base": base_pc["recall"], "recall_cand": cand_pc["recall"],
    "precision_base": base_pc["precision"], "precision_cand": cand_pc["precision"],
    "f1_base": base_pc["f1"], "f1_cand": cand_pc["f1"]})
per_class["f1_change"] = per_class["f1_cand"] - per_class["f1_base"]
print(per_class.round(3).sort_values("f1_change").to_string())

summary.round(4).to_csv(HERE / "comparison_summary.csv")
per_class.round(4).to_csv(HERE / "comparison_per_class.csv")

# --- records: baseline vs candidate on each ticket
m = base[["ticket_id", "true_label", "recommended_department"]].merge(
    cand[["ticket_id", "recommended_department"]], on="ticket_id", suffixes=("_base", "_cand"))
m["ok_base"] = m["true_label"] == m["recommended_department_base"]
m["ok_cand"] = m["true_label"] == m["recommended_department_cand"]
print(f"\nAll tickets: fixed {(~m.ok_base & m.ok_cand).sum()}, broken {(m.ok_base & ~m.ok_cand).sum()}, "
      f"changed prediction {(m.recommended_department_base != m.recommended_department_cand).sum()}")

# targeted category B (the 13 inspected tickets)
ann = pd.read_csv(ANNOTATIONS)[["ticket_id", "failure_category"]]
b = m.merge(ann, on="ticket_id")
print("\nInspected tickets, newly correct by category:")
print(b.groupby("failure_category")["ok_cand"].agg(["sum", "count"]).to_string())
print("Category B tickets:")
print(b[b["failure_category"].str.startswith("B")][
    ["ticket_id", "true_label", "recommended_department_base", "recommended_department_cand", "ok_cand"]].to_string(index=False))

# the full Tech <-> IT slice
pair = {TECH, IT}
sl = m[(~m.ok_base) & m.true_label.isin(pair) & m.recommended_department_base.isin(pair)]
print(f"\nBaseline Tech<->IT slice errors: {len(sl)}; now correct: {sl.ok_cand.sum()}; "
      f"now Tech<->IT other direction/other dept: {(~sl.ok_cand).sum()}")
t = m[m.true_label.isin(pair)]
print(f"Tech+IT tickets correct: baseline {t.ok_base.sum()} -> candidate {t.ok_cand.sum()} of {len(t)}")

"""Paired bootstrap on the validation set: how often does the candidate beat the baseline?

Resamples validation tickets with replacement (same tickets for both models),
recomputes accuracy and macro-F1 for each model, and reports the difference.
Uses the Homework 3 baseline predictions in ../Task1 and this folder's predictions.
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
N_BOOT, SEED = 2000, 42

base = pd.read_csv(HERE.parent / "Task1" / "validation_predictions.csv")
cand = pd.read_csv(HERE / "validation_predictions.csv")
assert list(base["ticket_id"]) == list(cand["ticket_id"])

labels = sorted(base["true_label"].unique())
idx = {l: i for i, l in enumerate(labels)}
y = base["true_label"].map(idx).to_numpy()
pb = base["recommended_department"].map(idx).to_numpy()
pc = cand["recommended_department"].map(idx).to_numpy()
K = len(labels)


def macro_f1(y_true, y_pred):
    conf = np.bincount(y_true * K + y_pred, minlength=K * K).reshape(K, K)
    tp = np.diag(conf).astype(float)
    precision = np.divide(tp, conf.sum(0), out=np.zeros(K), where=conf.sum(0) > 0)
    recall = np.divide(tp, conf.sum(1), out=np.zeros(K), where=conf.sum(1) > 0)
    f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(K), where=(precision + recall) > 0)
    return f1.mean()


rng = np.random.default_rng(SEED)
n = len(y)
d_acc, d_f1 = [], []
for _ in range(N_BOOT):
    s = rng.integers(0, n, n)
    d_acc.append((pc[s] == y[s]).mean() - (pb[s] == y[s]).mean())
    d_f1.append(macro_f1(y[s], pc[s]) - macro_f1(y[s], pb[s]))

rows = []
for name, d, observed in [("accuracy", d_acc, (pc == y).mean() - (pb == y).mean()),
                          ("macro_f1", d_f1, macro_f1(y, pc) - macro_f1(y, pb))]:
    d = np.array(d)
    lo, hi = np.percentile(d, [2.5, 97.5])
    rows.append({"metric": name, "observed_change": observed, "ci95_low": lo, "ci95_high": hi,
                 "share_of_resamples_candidate_better": (d > 0).mean()})
out = pd.DataFrame(rows)
print(out.round(4).to_string(index=False))
out.round(4).to_csv(HERE / "bootstrap_summary.csv", index=False)

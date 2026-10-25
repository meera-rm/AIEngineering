"""Apply one frozen model to the test split. Run once per model:

    python predict_test.py original
    python predict_test.py candidate

Each model runs in its own process because both define a class called
TicketRouter in a module called ticket_router. Refuses to run if a frozen
file has changed, or if predictions already exist (no reruns).
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "Task1"   # canonical dataset and split manifest
EXPECTED = ["ticket_id", "true_label", "recommended_department", "class_scores"]

name = sys.argv[1]
assert name in ("original", "candidate"), "usage: predict_test.py original|candidate"
out_path = HERE / f"test_predictions_{name}.csv"
assert not out_path.exists(), f"{out_path.name} already exists: the models are frozen, do not rerun"

record = json.loads((HERE / "freeze_record.json").read_text())
for rel, expected in record["sha256"].items():
    actual = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
    assert actual == expected, f"{rel} changed since the freeze"

sys.path.insert(0, str(HERE / name))
from ticket_router import TicketRouter   # noqa: E402

router = TicketRouter.load(HERE / name / "ticket_router.joblib")

source = pd.read_csv(DATA / "support_tickets.csv")
manifest = pd.read_csv(DATA / "split_manifest.csv")
manifest["split"] = manifest["split"].str.strip().str.lower()
test = source.merge(manifest[["ticket_id", "split"]], on="ticket_id", how="inner", validate="one_to_one")
test = test[test["split"] == "test"].sort_values("ticket_id").reset_index(drop=True)
assert len(test) > 0, "Test split is empty"

rows = []
for tid, body, label in zip(test["ticket_id"], test["Body"], test["Department"]):
    out = router.predict(body)
    rows.append({"ticket_id": tid, "true_label": label,
                 "recommended_department": out["recommended_department"],
                 "class_scores": json.dumps(out["class_scores"])})
preds = pd.DataFrame(rows)
assert list(preds.columns) == EXPECTED
assert preds["ticket_id"].is_unique and len(preds) == len(test)
preds.to_csv(out_path, index=False)
print(f"{name}: wrote {len(preds):,} test predictions -> {out_path.name}")

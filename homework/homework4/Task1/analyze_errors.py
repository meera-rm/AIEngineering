from pathlib import Path
import json
import pandas as pd

          # point at the ORIGINAL saved outputs

preds    = pd.read_csv("validation_predictions.csv")
source   = pd.read_csv("support_tickets.csv")
manifest = pd.read_csv("split_manifest.csv")

# 1. Canonical validation IDs (same normalization as train_and_predict.py)
manifest["split"] = manifest["split"].str.strip().str.lower()
val_ids = manifest.loc[manifest["split"] == "validation", "ticket_id"]

# 2. Join Body (and Department, for a label cross-check)
df = preds.merge(source[["ticket_id", "Body", "Department"]],
                 on="ticket_id", how="left", validate="one_to_one")

missing = set(val_ids) - set(df["ticket_id"])
extra = set(df["ticket_id"]) - set(val_ids)
assert not missing and not extra, f"missing: {missing}, extra: {extra}"

assert len(df) == len(val_ids), f"count mismatch: {len(df)} vs {len(val_ids)}"
assert set(df["ticket_id"]) == set(val_ids), "ticket_id mismatch"
print(f"OK: {len(df)} rows, ticket IDs match")   # same actual tickets



# 3. Parse scores and derive confidence

# Step 1: turn the JSON text into a dict (once per row)
df["class_scores"] = df["class_scores"].apply(json.loads)
df["confidence"] = df.apply(lambda r: r["class_scores"][r["recommended_department"]], axis=1)

# 4. Integrity checks

assert df["ticket_id"].is_unique

assert df["Body"].notna().all(), "Some tickets have no Body"

assert (df["true_label"] == df["Department"]).all(), "Saved labels differ from source"

assert (df["confidence"] == df["class_scores"].apply(lambda s: max(s.values()))).all(), \
       "Recommended dept is not the top-scoring one"




# 5. Select the slice: Technical Support <-> IT Support (both directions)
pair = {"Technical Support", "IT Support"}
slice_df = df[(df["true_label"] != df["recommended_department"])
              & df["true_label"].isin(pair)
              & df["recommended_department"].isin(pair)].sort_values("ticket_id")
print(slice_df.groupby(["true_label", "recommended_department"]).size())

# deterministic: fixed seed on a sorted frame
records = slice_df.sample(n=40, random_state=42).sort_values("ticket_id")
records = records[["ticket_id", "true_label", "recommended_department", "confidence", "Body"]]
records.to_csv("selected_records.csv", index=False)

# annotations live in their own file so rerunning this script never overwrites them
if not Path("annotations.csv").exists():
    template = records[["ticket_id", "true_label", "recommended_department", "Body"]].copy()
    for col in ["failure_category", "rationale", "why_model_chose"]:
        template[col] = ""
    template.to_csv("annotations.csv", index=False)


# 6. After filling in annotations.csv by hand
annotated = pd.read_csv("annotations.csv")
assert set(annotated["ticket_id"]) == set(records["ticket_id"]), "annotations.csv doesn't match selected_records.csv"
if annotated["failure_category"].notna().any():
    assert annotated["failure_category"].notna().all(), "A record has no category"
    counts = annotated["failure_category"].value_counts()
    assert counts.sum() == len(annotated)
    print(counts)



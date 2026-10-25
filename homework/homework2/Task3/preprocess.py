
"""
preprocess.py  —  Task 3: Preprocessing
=========================================
Inputs : support_tickets_cleaned.csv   (Task 1 output)
         split_manifest.csv            (Task 2 output)
Outputs: artifacts/
           X_train.joblib, X_validation.joblib, X_test.joblib
           y_train.npy,    y_validation.npy,    y_test.npy
           ids_train.csv,  ids_validation.csv,  ids_test.csv
           tfidf_vectorizer.joblib
           label_encoder.joblib
           class_weight.json

Design decisions
----------------
- Body only: Priority and Tags may be assigned after routing (leakage risk).
- Normalization: lowercase, replace URLs/emails/numbers with tokens, collapse WS.
- TF-IDF fit on train only; val and test are transformed, never fitted.
- class_weight="balanced" to handle 20.9x class imbalance.
"""

import argparse
import json

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from text_utils import normalize
# ── CLI ───────────────────────────────────────────────────────────────────────
_p = argparse.ArgumentParser()
_p.add_argument("--cleaned",  default="support_tickets_cleaned.csv")
_p.add_argument("--manifest", default="split_manifest.csv")
_p.add_argument("--out-dir",  default="artifacts")
args = _p.parse_args()

CLEANED_PATH  = args.cleaned
MANIFEST_PATH = args.manifest
OUT_DIR       = Path(args.out_dir)
OUT_DIR.mkdir(exist_ok=True)

SPLITS = ["train", "validation", "test"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def _section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


# ── Load ──────────────────────────────────────────────────────────────────────
_section("Load")
cleaned  = pd.read_csv(CLEANED_PATH)
manifest = pd.read_csv(MANIFEST_PATH)
print(f"Cleaned rows : {len(cleaned)}")
print(f"Manifest rows: {len(manifest)}")

# ── Schema checks ─────────────────────────────────────────────────────────────
_section("Schema checks")
assert len(cleaned) > 0 and len(manifest) > 0, "Empty input file"
assert {"ticket_id", "Body", "Department"} <= set(cleaned.columns)
assert {"ticket_id", "split"} <= set(manifest.columns)
assert cleaned["ticket_id"].is_unique,  "Duplicate ticket_ids in cleaned"
assert manifest["ticket_id"].is_unique, "Duplicate ticket_ids in manifest"
assert cleaned["ticket_id"].notna().all()
assert manifest["ticket_id"].notna().all()
print("Schema checks passed ✓")

# ── Merge ─────────────────────────────────────────────────────────────────────
_section("Merge")
df = cleaned.merge(
    manifest[["ticket_id", "split"]],
    on="ticket_id", how="outer",
    validate="one_to_one", indicator=True,
)
print(df["_merge"].value_counts().to_string())
assert (df["_merge"] == "both").all(), "Cleaned data and manifest don't match"
df = df.drop(columns="_merge")

# ── Text normalization ────────────────────────────────────────────────────────
_section("Text normalization")
print(f"NaN bodies (before fill): {df['Body'].isna().sum()}")
df["Body"] = df["Body"].fillna("").map(normalize)
print(f"Empty bodies (after normalization): {(df['Body'] == '').sum()}")
print(df["Body"].str.split().str.len().describe().to_string())

# ── Build splits ──────────────────────────────────────────────────────────────
_section("Build splits")
df["split"] = df["split"].str.strip().str.lower()
unexpected = set(df["split"]) - set(SPLITS)
assert not unexpected, f"Unexpected split values: {unexpected}"

parts = {s: df[df["split"] == s].reset_index(drop=True) for s in SPLITS}
train, val, test = parts["train"], parts["validation"], parts["test"]

for s, p in parts.items():
    assert len(p) > 0, f"{s} split is empty"
    print(f"{s:>12}: {len(p):6d} rows ({len(p)/len(df):.1%})")

# ticket_id overlap checks
ids = {s: set(p["ticket_id"]) for s, p in parts.items()}
assert not (ids["train"] & ids["validation"]), "Train/validation overlap"
assert not (ids["train"] & ids["test"]),       "Train/test overlap"
assert not (ids["validation"] & ids["test"]),  "Validation/test overlap"

# Shared-text report
bodies = {s: set(p["Body"]) - {""} for s, p in parts.items()}
for a, b in [("train","validation"), ("train","test"), ("validation","test")]:
    n = len(bodies[a] & bodies[b])
    print(f"Identical bodies shared by {a} and {b}: {n}")

# ── Label checks ──────────────────────────────────────────────────────────────
_section("Label checks + class distribution")
assert df["Department"].notna().all(), "Null labels"
unseen = (set(val["Department"]) | set(test["Department"])) - set(train["Department"])
assert not unseen, f"Labels missing from train: {unseen}"

counts = train["Department"].value_counts()
print(pd.DataFrame({"count": counts,
                    "pct": (counts / counts.sum() * 100).round(2)}).to_string())
imbalance_ratio = counts.max() / counts.min()
print(f"\nImbalance ratio (max/min): {imbalance_ratio:.1f}")

# ── TF-IDF — fit on train only ────────────────────────────────────────────────
_section("TF-IDF vectorization (fit on train only)")
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    max_features=50_000,
    sublinear_tf=True,
)
X_train = vectorizer.fit_transform(train["Body"])
X_val   = vectorizer.transform(val["Body"])
X_test  = vectorizer.transform(test["Body"])
print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")

# ── Label encoding — fit on train only ───────────────────────────────────────
_section("Label encoding (fit on train only)")
le      = LabelEncoder().fit(train["Department"])
y_train = le.transform(train["Department"])
y_val   = le.transform(val["Department"])
y_test  = le.transform(test["Department"])
print(f"Classes: {le.classes_.tolist()}")

# ── Feature / alignment checks ────────────────────────────────────────────────
_section("Feature and alignment checks")
for name, X, y, p in [("train",      X_train, y_train, train),
                       ("validation", X_val,   y_val,   val),
                       ("test",       X_test,  y_test,  test)]:
    assert X.shape[0] == len(y) == len(p), f"{name}: X/y/ID row mismatch"
    assert X.shape[1] == X_train.shape[1], f"{name}: feature count mismatch"
    zeros = (X.getnnz(axis=1) == 0).sum()
    print(f"{name:>12}: shape {X.shape}, all-zero rows: {zeros}")

# ── Class weights ─────────────────────────────────────────────────────────────
_section("Class weights (computed from train only)")
classes = np.arange(len(le.classes_))
weights = compute_class_weight("balanced", classes=classes, y=y_train)
class_weight = {int(c): float(w) for c, w in zip(classes, weights)}
for c, w in class_weight.items():
    print(f"  {le.classes_[c]:<35} {w:.2f}")

# ── Save artifacts ────────────────────────────────────────────────────────────
_section("Save artifacts")
for name, X, y, p in [("train",      X_train, y_train, train),
                       ("validation", X_val,   y_val,   val),
                       ("test",       X_test,  y_test,  test)]:
    joblib.dump(X, OUT_DIR / f"X_{name}.joblib")
    np.save(OUT_DIR / f"y_{name}.npy", y)
    p[["ticket_id"]].to_csv(OUT_DIR / f"ids_{name}.csv", index=False)

joblib.dump(vectorizer, OUT_DIR / "tfidf_vectorizer.joblib")
joblib.dump(le,         OUT_DIR / "label_encoder.joblib")
with open(OUT_DIR / "class_weight.json", "w") as f:
    json.dump({
        "class_weight":    class_weight,
        "classes":         le.classes_.tolist(),
        "imbalance_ratio": float(imbalance_ratio),
    }, f, indent=2)

# ── Reload verification ───────────────────────────────────────────────────────
_section("Reload verification")
X_check   = joblib.load(OUT_DIR / "X_train.joblib")
y_check   = np.load(OUT_DIR / "y_train.npy")
ids_check = pd.read_csv(OUT_DIR / "ids_train.csv")
assert X_check.shape == X_train.shape,        "Saved X_train shape differs"
assert (X_check != X_train).nnz == 0,         "Saved X_train values differ"
assert (y_check == y_train).all(),             "Saved y_train differs"
assert len(ids_check) == X_check.shape[0],    "Saved IDs don't align with X_train"

for name in SPLITS:
    saved    = pd.read_csv(OUT_DIR / f"ids_{name}.csv")["ticket_id"]
    expected = manifest.loc[manifest["split"] == name, "ticket_id"].reset_index(drop=True)
    assert saved.equals(expected), f"ids_{name}.csv does not match manifest"
    print(f"ids_{name}.csv OK, first IDs: {saved.head(5).tolist()}")

# ── Done ──────────────────────────────────────────────────────────────────────
_section("Done")
print(f"Python  : {sys.executable}")
print(f"pandas  : {pd.__version__}")
print(f"sklearn : {__import__('sklearn').__version__}")
print(f"Artifacts saved to: {OUT_DIR.resolve()}")
# Using Data for ML: Libraries and Code Guide

Companion code for the "Using Data" lecture. Every snippet uses one running example: a **support-ticket router** that classifies tickets as `billing`, `access`, or `security`. Run the sections in order as one script or notebook.

---

## 0. Setup

### Libraries used

| Library | What it's for in this lesson |
|---|---|
| `pandas`, `numpy` | Data handling and synthetic example data |
| `scikit-learn` | Splitting, cross-validation, class weights, baseline models, clustering |
| `imbalanced-learn` (`imblearn`) | Over/undersampling, SMOTE, leakage-safe pipelines |
| `pydantic` | Data contracts and validation for single API payloads |
| `fastapi` | Serving the model behind a validated endpoint |
| `pandera` | Data contracts and validation for whole DataFrames (batch) |
| `dvc` | Versioning datasets and split policies alongside Git |

```bash
pip install pandas numpy scikit-learn imbalanced-learn pydantic fastapi uvicorn pandera "dvc[s3]"
```

### Models used

The lesson is about data, not modeling, so the model is kept simple:
- **`DummyClassifier`**: a "always predict the majority class" baseline that exposes the accuracy trap.
- **`TfidfVectorizer` + `LogisticRegression`**: a fast, standard text classifier that supports `class_weight`.

### Create example data

```python
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
LABELS = ["billing", "access", "security"]

TEMPLATES = {
    "billing": [
        "I was charged twice on invoice {n}",
        "Please refund my last payment of ${n}",
        "My card was declined at checkout",
        "Can I get a copy of invoice {n}?",
        "Why did my subscription price go up?",
    ],
    "access": [
        "I can't log in to my account",
        "Password reset email never arrived",
        "Please add user {n} to our workspace",
        "My SSO login keeps failing",
        "Locked out after too many attempts",
    ],
    "security": [
        "I see a login from an unknown country",
        "Someone changed my email without permission",
        "Suspicious API key activity on key {n}",
        "Possible phishing email pretending to be you",
        "Please enable 2FA, I think I was hacked",
    ],
}
FILLER = ["", " asap", " please help", " thanks", " this is urgent", " (sent from mobile)"]


def make_tickets(n=5000):
    labels = rng.choice(LABELS, size=n, p=[0.86, 0.13, 0.01])          # heavy imbalance
    cust_p = rng.dirichlet(np.ones(50) * 0.5)                           # uneven customer sizes
    customers = rng.choice([f"C{i:03d}" for i in range(50)], size=n, p=cust_p)
    created = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365 * 24, size=n), unit="h")
    label_delay = pd.to_timedelta(rng.integers(1, 14 * 24, size=n), unit="h")  # label arrives later
    texts = [
        str(rng.choice(TEMPLATES[l])).format(n=rng.integers(100, 999)) + str(rng.choice(FILLER))
        for l in labels
    ]
    return (
        pd.DataFrame({
            "ticket_id": [f"T{i:05d}" for i in range(n)],
            "customer_id": customers,
            "channel": rng.choice(["email", "chat", "phone"], size=n, p=[0.5, 0.3, 0.2]),
            "created_at": created,
            "label_at": created + label_delay,
            "text": texts,
            "label": labels,
        })
        .sort_values("created_at")
        .reset_index(drop=True)
    )


df = make_tickets()
print(df["label"].value_counts())
```

### Helper: check what landed in each split

You'll call this after every split to confirm each set is representative.

```python
def show_dist(splits: dict, col="label"):
    table = pd.DataFrame(
        {name: d[col].value_counts(normalize=True).round(3) for name, d in splits.items()}
    ).fillna(0)
    table.loc["n_records"] = [len(d) for d in splits.values()]
    print(table, "\n")
```

---

## 1. Dataset Roles: Train / Validation / Test

**Library:** `sklearn.model_selection.train_test_split`

`train_test_split` only makes two pieces, so call it twice to get three. Here it produces 80/10/10.

```python
from sklearn.model_selection import train_test_split

train_df, temp_df = train_test_split(
    df, test_size=0.2, stratify=df["label"], random_state=SEED
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, stratify=temp_df["label"], random_state=SEED
)
show_dist({"train": train_df, "val": val_df, "test": test_df})
```

### Specialized evaluation sets

These are subsets carved out on purpose, each answering one question.

```python
# Slice set: "How do we do on our biggest customer?"
top_customer = df["customer_id"].value_counts().idxmax()
slice_set = test_df[test_df["customer_id"] == top_customer]

# Stress set: "How do we do on hard cases?" (here, short, vague tickets)
stress_set = test_df[test_df["text"].str.len() < 30]

# Regression set: "Did we re-break something we fixed?" (IDs you fixed in past iterations)
fixed_ids = ["T00012", "T00345", "T01200"]
regression_set = df[df["ticket_id"].isin(fixed_ids)]

# Gold set: a sample sent to experts for high-confidence labels
gold_candidates = test_df.groupby("label", group_keys=False).apply(
    lambda g: g.sample(min(len(g), 20), random_state=SEED)
)
```

### Test-set discipline in code

A simple guard against peeking at the test set too often:

```python
class TestSetGuard:
    def __init__(self, test_df, max_uses=3):
        self._df, self.uses, self.max_uses = test_df, 0, max_uses

    def aggregate_score(self, model, metric_fn):
        """Only returns an aggregate number, never individual records."""
        self.uses += 1
        if self.uses > self.max_uses:
            raise RuntimeError("Test set used too often; it's now effectively a validation set.")
        return metric_fn(self._df["label"], model.predict(self._df["text"]))
```

---

## 2. Split Strategies

### 2.1 Uniform random (usually avoid)

```python
u_train, u_temp = train_test_split(df, test_size=0.2, random_state=SEED)  # no stratify
u_val, u_test = train_test_split(u_temp, test_size=0.5, random_state=SEED)
show_dist({"train": u_train, "val": u_val, "test": u_test})
# Rare "security" counts can drift noticeably between splits; with smaller data they can vanish.
```

### 2.2 Stratified (default)

This is the `stratify=` argument from Section 1. To stratify on **more than one column**, combine them into a key:

```python
strat_key = df["label"] + "_" + df["channel"]
s_train, s_temp = train_test_split(df, test_size=0.2, stratify=strat_key, random_state=SEED)
# If some combined stratum has < 2 records, sklearn raises an error:
# that's the "too many dimensions" problem from the lecture. Merge rare strata into "other".
```

### 2.3 Time-based (with boundary exclusion)

**Library:** plain `pandas` / `numpy`

Each record must be **created and labeled** before its window's cutoff. Records whose label arrives after the cutoff are excluded.

```python
T1 = pd.Timestamp("2025-10-01")   # train  < T1
T2 = pd.Timestamp("2025-11-15")   # val    in [T1, T2), test >= T2

conditions = [
    (df["created_at"] < T1) & (df["label_at"] < T1),
    (df["created_at"] < T1),                            # created in train window, labeled later
    (df["created_at"] < T2) & (df["label_at"] < T2),
    (df["created_at"] < T2),                            # created in val window, labeled later
]
choices = ["train", "excluded", "val", "excluded"]
df["time_role"] = np.select(conditions, choices, default="test")

print(df["time_role"].value_counts())
t_splits = {r: df[df["time_role"] == r] for r in ["train", "val", "test"]}
show_dist(t_splits)
```

### 2.4 Group split

**Library:** `GroupShuffleSplit` (groups only) or `StratifiedGroupKFold` (groups plus label balance)

```python
from sklearn.model_selection import GroupShuffleSplit

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
train_idx, temp_idx = next(gss.split(df, groups=df["customer_id"]))
g_train, g_temp = df.iloc[train_idx], df.iloc[temp_idx]

# Caution: test_size=0.2 is 20% of CUSTOMERS, not records. Check the record share.
print(f"Record share in train: {len(g_train) / len(df):.1%}")

# Prove there's no leakage: no customer appears on both sides
assert set(g_train["customer_id"]).isdisjoint(g_temp["customer_id"])
```

### 2.5 Combining group + stratified (with relaxed ratios)

**Library:** `StratifiedGroupKFold`. This is the lecture's "combine strategies, accept 75/15/10 instead of 80/10/10" situation.

```python
from sklearn.model_selection import StratifiedGroupKFold

sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
folds = [val_part for _, val_part in sgkf.split(df, df["label"], groups=df["customer_id"])]

test_idx, val_idx = folds[0], folds[1]                       # ~10% each
train_idx = np.setdiff1d(np.arange(len(df)), np.concatenate([test_idx, val_idx]))

sg = {"train": df.iloc[train_idx], "val": df.iloc[val_idx], "test": df.iloc[test_idx]}
show_dist(sg)   # ratios will be close to, not exactly, 80/10/10. That's expected.
```

### 2.6 Cluster-aware split

**Libraries:** `TfidfVectorizer` + `KMeans` to discover groups, then any group splitter.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Unsupervised, used only to decide split assignment (labels aren't involved)
X_tfidf = TfidfVectorizer(min_df=2).fit_transform(df["text"])
df["cluster"] = KMeans(n_clusters=30, n_init="auto", random_state=SEED).fit_predict(X_tfidf)

print(pd.crosstab(df["cluster"], df["label"]).head(10))  # inspect what the clusters captured

ca_folds = [v for _, v in StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
            .split(df, df["label"], groups=df["cluster"])]
ca_test, ca_val = df.iloc[ca_folds[0]], df.iloc[ca_folds[1]]
ca_train = df.drop(ca_test.index).drop(ca_val.index)
show_dist({"train": ca_train, "val": ca_val, "test": ca_test})
```

> **Watch out:** If a rare class lives in only a few clusters, some splits may get none of it. Increase `n_clusters`, check the crosstab, and relax ratios if needed. This is the sensitivity to similarity settings and thresholds the lecture mentioned.

---

## 3. Rebalancing (training set only, after splitting)

### 3.0 Baseline: why imbalance is a trap

```python
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

dummy = DummyClassifier(strategy="most_frequent").fit(train_df["text"], train_df["label"])
print(classification_report(val_df["label"], dummy.predict(val_df["text"]), zero_division=0))
# ~86% accuracy while never predicting "security". Use macro-F1 / per-class recall instead.
```

### 3.1 Oversampling

**Option A, plain pandas** (works directly on DataFrames with text):

```python
def oversample(df, label_col="label", min_count=1000, seed=SEED):
    parts = []
    for _, g in df.groupby(label_col):
        if len(g) < min_count:
            extra = g.sample(n=min_count - len(g), replace=True, random_state=seed)
            g = pd.concat([g, extra])
        parts.append(g)
    return pd.concat(parts).sample(frac=1, random_state=seed)  # shuffle

train_over = oversample(train_df, min_count=1000)   # not perfectly balanced, and that's fine
print(train_over["label"].value_counts())
```

**Option B, `imblearn.RandomOverSampler`** with a target count per class:

```python
from imblearn.over_sampling import RandomOverSampler

ros = RandomOverSampler(sampling_strategy={"security": 1000}, random_state=SEED)
X_over, y_over = ros.fit_resample(train_df[["text"]], train_df["label"])
```

### 3.2 Undersampling

```python
from imblearn.under_sampling import RandomUnderSampler

rus = RandomUnderSampler(sampling_strategy={"billing": 1500}, random_state=SEED)
X_under, y_under = rus.fit_resample(train_df[["text"]], train_df["label"])
```

**Combine both** (shrink the majority and grow the minority):

```python
X_tmp, y_tmp = rus.fit_resample(train_df[["text"]], train_df["label"])
X_both, y_both = ros.fit_resample(X_tmp, y_tmp)
print(pd.Series(y_both).value_counts())
```

### 3.3 Weighted learning (usually the first thing to try)

```python
from sklearn.utils.class_weight import compute_class_weight

classes = np.unique(train_df["label"])
weights = compute_class_weight("balanced", classes=classes, y=train_df["label"])
print(dict(zip(classes, weights.round(2))))   # e.g. billing ≈ 0.39, security ≈ 33

weighted_model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), min_df=2),
    LogisticRegression(max_iter=1000, class_weight="balanced"),
)
weighted_model.fit(train_df["text"], train_df["label"])
print(classification_report(val_df["label"], weighted_model.predict(val_df["text"]), digits=3))

# If huge weights make training unstable or amplify noise, cap them manually:
capped = LogisticRegression(max_iter=1000, class_weight={"billing": 1, "access": 3, "security": 15})
```

> **How it works:** `class_weight` multiplies each class's contribution to the **loss**, so mistakes on rare classes push the model harder. That produces the "bigger steps" effect described in lecture.

### 3.4 SMOTE (synthetic interpolation in feature space)

```python
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import make_pipeline as imb_pipeline

smote_model = imb_pipeline(
    TfidfVectorizer(min_df=2),
    SMOTE(k_neighbors=3, random_state=SEED),   # k must be < rarest class count
    LogisticRegression(max_iter=1000),
)
smote_model.fit(train_df["text"], train_df["label"])
print(classification_report(val_df["label"], smote_model.predict(val_df["text"]), digits=3))
```

> SMOTE creates synthetic **feature vectors**, not readable text. For new readable tickets, use LLM-based synthetic generation (last homework) and review the outputs.

---

## 4. Versioning and Reproducibility

### 4.1 Split assignment manifest (not duplicated CSVs)

```python
import hashlib
import json

SPLIT_POLICY = {
    "version": "split_v1",
    "strategy": "time_based",
    "cutoffs": [str(T1), str(T2)],
    "seed": SEED,
}

def fingerprint(frame: pd.DataFrame) -> str:
    """Short hash of the dataset so you know exactly which snapshot was split."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(frame, index=False).values.tobytes()
    ).hexdigest()[:16]

reasons = {
    "train": "created and labeled before T1",
    "val": "created and labeled in [T1, T2)",
    "test": "created on/after T2",
    "excluded": "label arrived after its window's cutoff",
}

with open("split_manifest_v1.jsonl", "w") as f:
    for row in df[["ticket_id", "customer_id", "time_role"]].itertuples(index=False):
        f.write(json.dumps({
            "ticket_id": row.ticket_id,
            "split": row.time_role,
            "group": row.customer_id,
            "excluded": row.time_role == "excluded",
            "reason": reasons[row.time_role],
            "policy_version": SPLIT_POLICY["version"],
        }) + "\n")

with open("split_policy_v1.json", "w") as f:
    json.dump({**SPLIT_POLICY, "dataset_fingerprint": fingerprint(df.drop(columns=["time_role", "cluster"]))}, f, indent=2)

# Rebuild any split later from the manifest:
manifest = pd.read_json("split_manifest_v1.jsonl", lines=True)
rebuilt_train = df.merge(manifest[manifest["split"] == "train"][["ticket_id"]], on="ticket_id")
```

### 4.2 Hash-based assignment (stable as data grows)

This is a common production pattern. A record's split depends only on its ID, so it never moves when new data arrives.

```python
def hash_split(record_id: str, val_pct=10, test_pct=10) -> str:
    bucket = int(hashlib.md5(record_id.encode()).hexdigest(), 16) % 100
    if bucket < test_pct:
        return "test"
    if bucket < test_pct + val_pct:
        return "val"
    return "train"

df["hash_role"] = df["ticket_id"].map(hash_split)
# For group-aware hashing, hash the customer_id instead of the ticket_id.
```

### 4.3 Version data and policies with DVC

```bash
git init && dvc init
dvc add data/raw/tickets.csv                        # snapshot the source data
git add data/raw/tickets.csv.dvc .gitignore split_policy_v1.json
git commit -m "Source snapshot v1 + split policy v1"
git tag benchmark-v1                                # lock the benchmark

dvc remote add -d storage s3://my-bucket/dvc-store  # store data in S3
dvc push

# Later: restore the exact benchmark used for an old experiment
git checkout benchmark-v1 && dvc checkout
```

---

## 5. Small Data: Cross-Validation

We'll cross-validate on the **dev set** (train + val) and keep `test_df` held out.

```python
from sklearn.model_selection import StratifiedKFold, cross_validate

dev_df = pd.concat([train_df, val_df])
X_dev, y_dev = dev_df["text"], dev_df["label"]

pipe = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), min_df=2),
    LogisticRegression(max_iter=1000, class_weight="balanced"),
)
```

### 5.1 Stratified K-fold, with per-fold metrics

```python
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
res = cross_validate(pipe, X_dev, y_dev, cv=skf, scoring=["f1_macro", "recall_macro"])

per_fold = pd.DataFrame({k: v for k, v in res.items() if k.startswith("test_")})
print(per_fold.round(3))                       # look at each fold
print(per_fold.agg(["mean", "std"]).round(3))  # high std means results depend on the split
```

### 5.2 Re-run with different seeds when variance is high

```python
from sklearn.model_selection import RepeatedStratifiedKFold

rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
res = cross_validate(pipe, X_dev, y_dev, cv=rskf, scoring="f1_macro")
print(f"macro-F1: {res['test_score'].mean():.3f} ± {res['test_score'].std():.3f}")
```

### 5.3 Group-aware K-fold (match your split logic)

```python
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
res = cross_validate(pipe, X_dev, y_dev, cv=sgkf,
                     groups=dev_df["customer_id"], scoring="f1_macro")
print(res["test_score"].round(3))
```

### 5.4 Time-aware cross-validation (expanding window)

```python
from sklearn.model_selection import TimeSeriesSplit

dev_sorted = dev_df.sort_values("created_at")
tss = TimeSeriesSplit(n_splits=5)

for i, (tr, va) in enumerate(tss.split(dev_sorted)):
    tr_dates, va_dates = dev_sorted["created_at"].iloc[tr], dev_sorted["created_at"].iloc[va]
    print(f"Fold {i}: train {len(tr):>4} rows (to {tr_dates.max():%Y-%m-%d}) "
          f"→ validate {len(va):>4} rows ({va_dates.min():%Y-%m-%d} to {va_dates.max():%Y-%m-%d})")

res = cross_validate(pipe, dev_sorted["text"], dev_sorted["label"], cv=tss, scoring="f1_macro")
print(res["test_score"].round(3))   # early folds have less training data, so scores often lower
```

### 5.5 Rebalancing inside cross-validation: wrong vs. right

```python
# WRONG: rebalance first, then fold. Duplicates land in both train and validation (leakage).
over_all = oversample(dev_df, min_count=1000)
wrong = cross_validate(make_pipeline(TfidfVectorizer(min_df=2), LogisticRegression(max_iter=1000)),
                       over_all["text"], over_all["label"], cv=skf, scoring="f1_macro")

# RIGHT: the sampler sits inside an imblearn pipeline, so it only runs on each fold's training part.
right_pipe = imb_pipeline(
    TfidfVectorizer(min_df=2),
    RandomOverSampler(random_state=SEED),
    LogisticRegression(max_iter=1000),
)
right = cross_validate(right_pipe, X_dev, y_dev, cv=skf, scoring="f1_macro")

print(f"Leaky estimate:  {wrong['test_score'].mean():.3f}   (optimistic, not trustworthy)")
print(f"Honest estimate: {right['test_score'].mean():.3f}")
```

### 5.6 Final model: train on all folds, test once

```python
from sklearn.base import clone

final_model = clone(pipe).fit(X_dev, y_dev)
guard = TestSetGuard(test_df)
from sklearn.metrics import f1_score
print("Test macro-F1:", guard.aggregate_score(final_model, lambda y, p: f1_score(y, p, average="macro")))
```

---

## 6. Operational Validation

### 6.1 Data contract for single requests (Pydantic)

```python
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

MAX_TEXT = 2000

class TicketIn(BaseModel):
    ticket_id: str = Field(min_length=1)
    customer_id: str = Field(pattern=r"^C\d{3}$")
    channel: Literal["email", "chat", "phone"]
    text: str = Field(min_length=1, max_length=MAX_TEXT)
```

### 6.2 Validator with accept / correct / reject

```python
CUSTOMER_LOOKUP = {"Acme Corp": "C001", "Globex": "C002"}   # e.g. from a CRM table

def validate_ticket(payload: dict) -> dict:
    payload, corrections = dict(payload), []

    # Correction 1: missing ID but enough info to look it up
    if not payload.get("customer_id") and payload.get("customer_name") in CUSTOMER_LOOKUP:
        payload["customer_id"] = CUSTOMER_LOOKUP[payload["customer_name"]]
        corrections.append("customer_id looked up from customer_name")

    # Correction 2: text too long (in production you might summarize with an LLM instead)
    if isinstance(payload.get("text"), str) and len(payload["text"]) > MAX_TEXT:
        payload["text"] = payload["text"][:MAX_TEXT]
        corrections.append(f"text truncated to {MAX_TEXT} chars")

    try:
        ticket = TicketIn(**payload)
    except ValidationError as e:
        return {"status": "rejected", "errors": e.errors()}

    return {"status": "corrected" if corrections else "accepted",
            "ticket": ticket, "corrections": corrections}

print(validate_ticket({"ticket_id": "T1", "customer_id": "C001", "channel": "email", "text": "refund pls"}))
print(validate_ticket({"ticket_id": "T2", "customer_name": "Acme Corp", "channel": "chat", "text": "x" * 5000}))
print(validate_ticket({"ticket_id": "T3", "customer_id": "C001", "channel": "chat_v2", "text": "hi"}))
```

### 6.3 Serving behind the contract (FastAPI)

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def as_400(request: Request, exc: RequestValidationError):
    # FastAPI returns 422 by default; this makes it the 400 Bad Request from the lecture
    return JSONResponse(status_code=400, content={"errors": exc.errors()})

@app.post("/route-ticket")
def route_ticket(ticket: TicketIn):
    return {"ticket_id": ticket.ticket_id, "label": final_model.predict([ticket.text])[0]}

# Run with: uvicorn app:app --reload
```

### 6.4 Data contract for batches (Pandera)

```python
import pandera.pandas as pa   # on older pandera versions: import pandera as pa

batch_schema = pa.DataFrameSchema({
    "ticket_id":  pa.Column(str, unique=True),
    "customer_id": pa.Column(str, pa.Check.str_matches(r"^C\d{3}$"), nullable=False),
    "channel":    pa.Column(str, pa.Check.isin(["email", "chat", "phone"])),
    "text":       pa.Column(str, pa.Check.str_length(1, MAX_TEXT)),
    "created_at": pa.Column(pa.DateTime),
})

try:
    batch_schema.validate(df[["ticket_id", "customer_id", "channel", "text", "created_at"]], lazy=True)
    print("Batch passed the contract")
except pa.errors.SchemaErrors as err:
    print(err.failure_cases.head())   # every violation at once, thanks to lazy=True
```

### 6.5 Monitoring: new values, missingness, volume, class-mix drift

```python
def psi(expected: pd.Series, actual: pd.Series, eps=1e-6) -> float:
    """Population Stability Index. <0.1 stable, 0.1 to 0.25 moderate shift, >0.25 major shift."""
    cats = expected.index.union(actual.index)
    e = expected.reindex(cats, fill_value=0) + eps
    a = actual.reindex(cats, fill_value=0) + eps
    return float(((a - e) * np.log(a / e)).sum())


def monitor(ref: pd.DataFrame, cur: pd.DataFrame, expected_volume: int,
            cat_cols=("channel",), null_cols=("customer_id",), label_col="label") -> list:
    alerts = []

    for c in cat_cols:                                   # 1. new values
        new_vals = set(cur[c].dropna()) - set(ref[c].dropna())
        if new_vals:
            alerts.append(f"New values in '{c}': {sorted(new_vals)}")

    for c in null_cols:                                  # 2. rising missingness
        r, k = ref[c].isna().mean(), cur[c].isna().mean()
        if k - r > 0.05:
            alerts.append(f"Null rate of '{c}' rose from {r:.1%} to {k:.1%}")

    ratio = len(cur) / expected_volume                   # 3. volume spike or drop
    if ratio > 3 or ratio < 0.33:
        alerts.append(f"Volume is {ratio:.1f}x the expected level")

    score = psi(ref[label_col].value_counts(normalize=True),   # 4. class-mix shift
                cur[label_col].value_counts(normalize=True))
    if score > 0.1:
        alerts.append(f"Class mix shift detected (PSI = {score:.2f})")

    return alerts


# Simulate a bad day in production
cur = test_df.copy()
cur.loc[cur.sample(frac=0.10, random_state=1).index, "channel"] = "chat_v2"
cur.loc[cur.sample(frac=0.15, random_state=2).index, "customer_id"] = None
cur = pd.concat([cur, cur[cur["label"] == "security"].sample(200, replace=True, random_state=3)])

for a in monitor(ref=train_df, cur=cur, expected_volume=len(test_df)):
    print("ALERT:", a)
```

> In production you usually don't have true labels yet, so run the class-mix check on **predicted** labels and confirm with labeled samples later.

---

## 7. AWS Equivalents (for certification prep)

| Lecture concept | AWS service / feature |
|---|---|
| Train/val/test splitting, stratification | SageMaker Data Wrangler (split data transform), SageMaker Processing jobs running sklearn |
| Detecting class imbalance | SageMaker Clarify pre-training bias metrics (e.g. Class Imbalance, CI) |
| Over/undersampling, SMOTE | SageMaker Data Wrangler "Balance data" transform |
| Weighted learning | Built-in XGBoost `scale_pos_weight`; class weights in your own training script |
| Cross-validation | SageMaker Automatic Model Tuning plus K-fold logic in your training script |
| Versioning data and experiments | S3 versioning, SageMaker Experiments, SageMaker Model Registry, Feature Store |
| Data contracts (batch) | AWS Glue Data Quality (DQDL rules) |
| Data contracts (API) | API Gateway request validation |
| Monitoring and drift | SageMaker Model Monitor (data quality and model quality monitors), CloudWatch alarms |

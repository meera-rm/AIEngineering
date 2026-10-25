"""
task4_ticket_router.py - Homework 2, Task 4: Build an ML Baseline.

Task: given a newly arrived support ticket Body, predict the department.

This single file contains everything for Task 4:
  1. normalize()        deterministic text cleaning (imported from ../text_utils.py,
                        shared with Task 3)
  2. TicketRouter       the required class: fit(), predict(), save(), load()
  3. main()             trains on the train split, reports training accuracy,
                        saves the model, verifies reproducibility, checks that
                        predict() returns the required JSON shape (not saved),
                        and writes the Task 4 writeup.

Run from the Task4 folder (with the homework venv active):
    python task4_ticket_router.py
    python task4_ticket_router.py --data-dir ../Task3 --example-json ../ml_baseline_output_example.json

Use the saved model from a notebook or another script:
    from task4_ticket_router import TicketRouter
    router = TicketRouter.load("artifacts/ticket_router.joblib")
    router.predict("I was charged twice on my invoice, please refund me")

Outputs (written next to this file):
    artifacts/ticket_router.joblib     persisted model artifact (deliverable)
    artifacts/training_summary.json    training accuracy and run details
    TASK4_WRITEUP.md                   ML-baseline writeup (deliverable)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from text_utils import normalize, is_missing as _is_missing

# ---------------------------------------------------------------------------
# 1. The required class
# ---------------------------------------------------------------------------
class TicketRouter:
    """TF-IDF + logistic regression baseline that routes tickets to departments."""

    def __init__(self, C: float = 1.0, max_iter: int = 1000,
                 random_state: int = 42, decimals: int = 2):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.decimals = decimals
        self.pipeline: Pipeline | None = None

    # -- internals -----------------------------------------------------------
    def _build_pipeline(self) -> Pipeline:
        vectorizer = TfidfVectorizer(
            preprocessor=normalize,   # raw text in; normalization happens here
            ngram_range=(1, 2),       # words + two-word phrases
            min_df=2,                 # drop one-off terms
            max_df=0.95,              # drop near-universal terms
            max_features=50_000,      # bound vocabulary size
            sublinear_tf=True,        # 1 + log(count)
        )
        model = LogisticRegression(
            C=self.C,
            class_weight="balanced",  # Task 3 class-imbalance decision
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        return Pipeline([("tfidf", vectorizer), ("clf", model)])

    @staticmethod
    def _clean_inputs(texts) -> list[str]:
        """scikit-learn rejects NaN documents, so missing bodies become ''."""
        return ["" if _is_missing(t) else str(t) for t in texts]

    def _check_fitted(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("TicketRouter is not fitted. Call fit() or load() first.")

    @property
    def classes_(self) -> list[str]:
        self._check_fitted()
        return [str(c) for c in self.pipeline.named_steps["clf"].classes_]

    # -- required methods ----------------------------------------------------
    def fit(self, texts, labels) -> "TicketRouter":
        """Train the preprocessor (TF-IDF) and the model on raw ticket bodies."""
        texts = self._clean_inputs(texts)
        labels = [str(y) for y in labels]
        if len(texts) != len(labels):
            raise ValueError(f"{len(texts)} texts but {len(labels)} labels")
        self.pipeline = self._build_pipeline().fit(texts, labels)
        return self

    def predict(self, text) -> dict:
        """Preprocess one ticket body and return the required output dict."""
        self._check_fitted()
        probs = self.pipeline.predict_proba(self._clean_inputs([text]))[0]
        classes = self.classes_
        return {
            "recommended_department": classes[int(np.argmax(probs))],
            "class_scores": {c: round(float(p), self.decimals)
                             for c, p in zip(classes, probs)},
        }

    def save(self, path) -> Path:
        """Save the trained router to disk with joblib."""
        self._check_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path, compress=3)
        return path

    @classmethod
    def load(cls, path) -> "TicketRouter":
        """Load a router previously saved with save()."""
        obj = joblib.load(Path(path))
        if not isinstance(obj, cls):
            raise TypeError(f"{path} does not contain a {cls.__name__}")
        return obj

    # -- helper --------------------------------------------------------------
    def predict_labels(self, texts) -> np.ndarray:
        """Batch helper: predicted department per text (used for accuracy)."""
        self._check_fitted()
        return self.pipeline.predict(self._clean_inputs(texts))


# ---------------------------------------------------------------------------
# 2. Training run, checks, and writeup
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = HERE.parent / "Task3"
DEFAULT_OUT_DIR = HERE / "artifacts"


def load_train_split(data_dir: Path) -> pd.DataFrame:
    """Join the cleaned dataset to the split manifest and return train rows."""
    cleaned = pd.read_csv(data_dir / "support_tickets_cleaned.csv")
    manifest = pd.read_csv(data_dir / "split_manifest.csv")
    df = cleaned.merge(manifest[["ticket_id", "split"]], on="ticket_id",
                       how="inner", validate="one_to_one")
    assert len(df) == len(cleaned) == len(manifest), "Cleaned data and manifest don't match"
    df["split"] = df["split"].str.strip().str.lower()
    train = df[df["split"] == "train"].reset_index(drop=True)
    assert len(train) > 0, "Train split is empty"
    return train


def find_example_json(explicit: Path | None) -> Path | None:
    candidates = [explicit] if explicit else [
        HERE / "ml_baseline_output_example.json",
        HERE.parent / "ml_baseline_output_example.json",
        DEFAULT_DATA_DIR / "ml_baseline_output_example.json",
    ]
    return next((p for p in candidates if p and p.exists()), None)


def check_output_format(output: dict, classes: list[str], example_path: Path | None) -> None:
    """Verify predict() output matches ml_baseline_output_example.json."""
    assert set(output) == {"recommended_department", "class_scores"}, "Wrong top-level keys"
    scores = output["class_scores"]
    assert list(scores) == list(classes), "class_scores must list every department"
    assert output["recommended_department"] in classes, "Unknown department"
    assert scores[output["recommended_department"]] == max(scores.values()), \
        "Recommended department must have the highest score"
    assert abs(sum(scores.values()) - 1.0) <= 0.05, "Scores should sum to ~1"
    if example_path:
        example = json.loads(example_path.read_text())
        assert set(example) == set(output), "Keys differ from the example JSON"
        assert set(example["class_scores"]) == set(scores), "Departments differ from the example JSON"
        print(f"Output format matches {example_path.name}")
    else:
        print("Example JSON not found; checked the format against the documented schema only")


def write_writeup(path: Path, summary: dict) -> None:
    acc = summary["training_accuracy"]
    text = f"""# Task 4 – ML Baseline Writeup

Text featurization is TF-IDF on the ticket `Body` (unigrams and bigrams,
fit on training data only); the full rationale is in Task 3. `TicketRouter`
reuses those settings but fits the TF-IDF vectorizer and the model together
inside `fit()`, so they are always trained and applied as one unit.

## Model choice and rationale
- **Choice:** multinomial logistic regression (`C={summary["C"]}`,
  `class_weight="balanced"`, `max_iter={summary["max_iter"]}`,
  `random_state={summary["random_state"]}`), combined with TF-IDF in one
  scikit-learn `Pipeline`.
- **Why:** a strong, standard baseline for sparse text features. It trains in
  seconds on a CPU, provides `predict_proba` for the required `class_scores`
  (probabilities that sum to 1), and supports `class_weight="balanced"`, which
  applies the Task 3 imbalance decision (20.9x ratio between the largest and
  smallest departments). Its coefficients are interpretable per word and
  department, which helps error analysis in Homework 3.
- **Reproducibility:** deterministic preprocessing, a fixed `random_state`,
  and a deterministic solver. Verified automatically: refitting gives identical
  predictions, and the saved-then-loaded model gives identical outputs.

## Percentage of training records predicted correctly
- **Training accuracy: {acc:.2%}** ({summary["train_correct"]:,} of
  {summary["train_rows"]:,} training records).
- This is measured on the data the model was trained on, so it is optimistic
  and is not an estimate of performance on new tickets. Validation and test
  were intentionally not scored; formal evaluation begins in Homework 3.
- Training accuracy is moderate because `class_weight="balanced"` trades some
  majority-class accuracy for minority-class recall, `C=1.0` regularization
  limits memorization, and several departments (e.g., IT Support, Technical
  Support, Product Support) share similar vocabulary.

## Artifacts
- Model: `artifacts/ticket_router.joblib`
- Run summary: `artifacts/training_summary.json`
"""
    path.write_text(text)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Train and save the Task 4 ML baseline.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="Folder with support_tickets_cleaned.csv and split_manifest.csv")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                        help="Where to write the model and JSON outputs")
    parser.add_argument("--example-json", type=Path, default=None,
                        help="Path to ml_baseline_output_example.json (optional)")
    parser.add_argument("--skip-refit-check", action="store_true",
                        help="Skip the second training run used to prove determinism")
    args = parser.parse_args(argv)

    # Train
    train = load_train_split(args.data_dir)
    print(f"Training rows: {len(train):,}")
    router = TicketRouter().fit(train["Body"], train["Department"])

    # Training accuracy (the only score Task 4 asks for)
    y_true = train["Department"].astype(str).to_numpy()
    y_pred = router.predict_labels(train["Body"])
    correct = int((y_pred == y_true).sum())
    train_acc = correct / len(train)
    print(f"Training accuracy: {train_acc:.2%} ({correct:,} / {len(train):,})")

    # Save and reload
    model_path = router.save(args.out_dir / "ticket_router.joblib")
    loaded = TicketRouter.load(model_path)
    print(f"Model saved to {model_path}")

    # Reproducibility: saved/loaded model and a fresh refit must agree
    sample = train["Body"].iloc[0]
    assert loaded.predict(sample) == router.predict(sample), "Loaded model output differs"
    assert (loaded.predict_labels(train["Body"]) == y_pred).all(), "Loaded model predictions differ"
    if not args.skip_refit_check:
        refit = TicketRouter().fit(train["Body"], train["Department"])
        assert (refit.predict_labels(train["Body"]) == y_pred).all(), "Refit is not deterministic"
    print("Reproducibility checks passed")

    # Output format
    output = loaded.predict(sample)
    check_output_format(output, loaded.classes_, find_example_json(args.example_json))
    print(json.dumps(output, indent=2))

    # Write outputs (predictions are not saved; only the run summary)
    summary = {
        "train_rows": len(train),
        "train_correct": correct,
        "training_accuracy": train_acc,
        "vocabulary_size": len(router.pipeline.named_steps["tfidf"].vocabulary_),
        "classes": loaded.classes_,
        "C": router.C,
        "max_iter": router.max_iter,
        "random_state": router.random_state,
        "model_path": str(model_path),
    }
    (args.out_dir / "training_summary.json").write_text(json.dumps(summary, indent=2))
    write_writeup(HERE / "TASK4_WRITEUP.md", summary)
    print(f"Writeup written to {HERE / 'TASK4_WRITEUP.md'}")

if __name__ == "__main__":
    # Re-import under the file's real module name so joblib stores
    # task4_ticket_router.TicketRouter instead of __main__.TicketRouter.
    # Without this, the saved model could not be loaded from a notebook.
    import importlib
    importlib.import_module(Path(__file__).stem).main()

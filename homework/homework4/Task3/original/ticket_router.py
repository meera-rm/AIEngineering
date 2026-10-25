"""
ticket_router.py - Homework 3, Task 2: TicketRouter classifier.

Everything is embedded in the TicketRouter class. It takes raw ticket Body
text and, inside fit() and predict():
  1. cleans it            (HTML tags, whitespace, punctuation spacing; from HW2 Task 1)
  2. normalizes + TF-IDF  (lowercase, accents, URL/email/number tokens; fit on training data only)
  3. logistic regression  (class_weight="balanced", random_state=42)

Methods:
    fit(texts, labels)      clean -> TF-IDF -> model, trained on raw ticket bodies
    predict(text) -> dict   {"recommended_department": ..., "class_scores": {...}}
    save(path) / load(path) persist the trained router with joblib

Usage:
    from ticket_router import TicketRouter
    router = TicketRouter().fit(train_bodies, train_labels)
    router.predict("I was charged twice on my invoice, please refund me")
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, strip_accents_unicode
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class TicketRouter:
    """Routes raw support tickets to departments.

    fit() and predict() take raw ticket text and apply text cleaning,
    normalization, TF-IDF and logistic regression internally.
    """

    # -- patterns used by the cleaning and normalization steps ---------------
    # Tag-like patterns only: "<" must be followed by a letter (or "/" then a letter).
    HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]{0,50}>")
    WHITESPACE_RE = re.compile(r"\s+")
    URL_RE = re.compile(r"https?://\S+|www\.\S+")
    EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
    NUM_RE = re.compile(r"\b\d+(?:[.,:/-]\d+)*\b")

    def __init__(self, C: float = 1.0, max_iter: int = 1000,
                 random_state: int = 42, decimals: int = 2):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.decimals = decimals
        self.pipeline: Pipeline | None = None

    # =======================================================================
    # 1. Text cleaning (from HW2 Task 1)
    # =======================================================================
    @staticmethod
    def _is_missing(value) -> bool:
        return value is None or (isinstance(value, float) and math.isnan(value))

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        return TicketRouter.HTML_TAG_RE.sub(" ", text)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return TicketRouter.WHITESPACE_RE.sub(" ", text).strip()

    @staticmethod
    def _clean_punctuation_spacing(text: str) -> str:
        # Comma followed immediately by uppercase letter: Team,I -> Team, I
        text = re.sub(r",([A-Z])", r", \1", text)
        # Sentence punctuation followed immediately by uppercase letter: persists.Could -> persists. Could
        return re.sub(r"([.!?])([A-Z])", r"\1 \2", text)

    @staticmethod
    def _clean_inputs(texts) -> list[str]:
        """Clean raw bodies: missing -> '', then HTML, whitespace, punctuation."""
        out = []
        for t in texts:
            if TicketRouter._is_missing(t):
                out.append("")
                continue
            t = TicketRouter._remove_html_tags(str(t))
            t = TicketRouter._normalize_whitespace(t)
            t = TicketRouter._clean_punctuation_spacing(t)
            out.append(t)
        return out

    # =======================================================================
    # 2. Preprocessing: normalization + TF-IDF (from HW2 Task 3)
    # =======================================================================
    @staticmethod
    def _normalize(text) -> str:
        """Lowercase, strip accents, replace URLs/emails/numbers, collapse whitespace."""
        if TicketRouter._is_missing(text):
            return ""
        text = strip_accents_unicode(str(text).lower())
        text = TicketRouter.URL_RE.sub(" urltoken ", text)
        text = TicketRouter.EMAIL_RE.sub(" emailtoken ", text)
        text = TicketRouter.NUM_RE.sub(" numtoken ", text)
        return TicketRouter.WHITESPACE_RE.sub(" ", text).strip()

    # =======================================================================
    # 3. Model: TF-IDF + logistic regression pipeline (from HW2 Task 4)
    # =======================================================================
    def _build_pipeline(self) -> Pipeline:
        vectorizer = TfidfVectorizer(
            preprocessor=TicketRouter._normalize,
            ngram_range=(1, 2),       # words + two-word phrases
            min_df=2,                 # drop one-off terms
            max_df=0.95,              # drop near-universal terms
            max_features=50_000,      # bound vocabulary size
            sublinear_tf=True,        # 1 + log(count)
        )
        model = LogisticRegression(
            C=self.C,
            class_weight="balanced",  # HW2 Task 3 class-imbalance decision
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        return Pipeline([("tfidf", vectorizer), ("clf", model)])

    def _check_fitted(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("TicketRouter is not fitted. Call fit() or load() first.")

    @property
    def classes_(self) -> list[str]:
        self._check_fitted()
        return [str(c) for c in self.pipeline.named_steps["clf"].classes_]

    # =======================================================================
    # Required methods
    # =======================================================================
    def fit(self, texts, labels) -> "TicketRouter":
        """Clean raw ticket bodies, then train TF-IDF and the model on them."""
        texts = self._clean_inputs(texts)
        labels = [str(y) for y in labels]
        if len(texts) != len(labels):
            raise ValueError(f"{len(texts)} texts but {len(labels)} labels")
        self.pipeline = self._build_pipeline().fit(texts, labels)
        return self

    def predict(self, text) -> dict:
        """Clean and score one raw ticket body; return the required output dict."""
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
        """Batch helper: predicted department for each raw text."""
        self._check_fitted()
        return self.pipeline.predict(self._clean_inputs(texts))

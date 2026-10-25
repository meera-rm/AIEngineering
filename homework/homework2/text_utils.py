"""Shared ticket-body normalization used by Task 3 and Task 4."""
import math
import re
from sklearn.feature_extraction.text import strip_accents_unicode

URL_RE   = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
NUM_RE   = re.compile(r"\b\d+(?:[.,:/-]\d+)*\b")
WS_RE    = re.compile(r"\s+")

def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))

def normalize(text) -> str:
    """Lowercase, strip accents, replace URLs/emails/numbers, collapse whitespace."""
    if is_missing(text):
        return ""
    text = strip_accents_unicode(str(text).lower())
    text = URL_RE.sub(" urltoken ", text)
    text = EMAIL_RE.sub(" emailtoken ", text)
    text = NUM_RE.sub(" numtoken ", text)
    return WS_RE.sub(" ", text).strip()
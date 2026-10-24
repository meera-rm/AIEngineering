
#Task 2 — Inspect and profile the Tobi-Bueck customer support tickets dataset.



import hashlib
import json  
import os
from pathlib import Path

import pandas as pd

# ---------------- CONFIG ----------------
HERE = Path(__file__).resolve().parent

RAW = Path(os.environ.get("RAW_PARQUET", HERE / "tobibueck_dataset" / "tobi_bueck_ddf1c81a.parquet"))
OUT_DIR = HERE
REPO = "Tobi-Bueck/customer-support-tickets"
COMMIT = "ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb"

TEXT_COLS = ["subject", "body"]     
LABEL_COL = "queue"               
LANG_COL, LANG_KEEP = "language", "en"
SHORT_WORDS = 5                     
SAMPLE_N, SEED = 20, 42
SAMPLE_COLS = ["record_id", "subject", "body", "answer", "queue", "priority", "type", "language"]
NOTE_COLS = ["label_fits_text", "issues", "notes"]
OVERWRITE_SAMPLE = False           
GRAIN = ("One row = one customer support ticket: the customer's subject and body, "
         "the agent's answer, and ticket metadata (queue, priority, type, tags, language).")
# -----------------------------------------


def is_missing(s: pd.Series) -> pd.Series:
    """True for NaN/None AND for empty or whitespace-only strings."""
    return s.isna() | s.astype("string").str.strip().fillna("").eq("")


def derive_ids(raw: pd.DataFrame) -> pd.Series:
    """
    Deterministic ID scheme:
    'tb_' + first 12 hex chars of SHA-256 over "column=value" lines for all raw columns
    (columns sorted by name, missing values written as <NULL>).
    Fully identical rows: the first keeps the base ID, later ones get _1, _2, ...
    """
    raw_cols = sorted(raw.columns.tolist())

    def content_hash(row: pd.Series) -> str:
        parts = []
        for col in raw_cols:
            value = row[col]
            value = "<NULL>" if pd.isna(value) else str(value)
            parts.append(f"{col}={value}")
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]

    base = raw.apply(content_hash, axis=1)
    dup_number = base.groupby(base, sort=False).cumcount()
    record_id = base.where(dup_number == 0, base + "_" + dup_number.astype(str))
    return "tb_" + record_id


def build_text(df: pd.DataFrame) -> pd.Series:
    """ticket_text = subject + newline + body."""
    return (
        df["subject"].fillna("").astype(str).str.strip()
        + "\n"
        + df["body"].fillna("").astype(str).str.strip()
    ).str.strip()


def build_sample(df: pd.DataFrame) -> pd.DataFrame:
    """
    Shuffle with random_state=SEED, then take the
    1st ticket of each queue, then the 2nd of each queue, ... until SAMPLE_N records.
    """
    shuffled = df.sample(frac=1, random_state=SEED).copy()
    shuffled["_sample_order"] = range(len(shuffled))
    shuffled["_queue_round"] = shuffled.groupby(LABEL_COL, sort=False).cumcount()
    round_robin = shuffled.sort_values(["_queue_round", "_sample_order"])
    sample = round_robin.head(SAMPLE_N)[SAMPLE_COLS].copy()
    for col in NOTE_COLS:
        sample[col] = ""
    return sample


def missing_table(df: pd.DataFrame, cols: list) -> dict:
    return {c: {"count": int(is_missing(df[c]).sum()),
                "proportion": round(float(is_missing(df[c]).mean()), 4)} for c in cols}


def md_table(d: dict, cols: list, key_name: str = "field") -> str:
    lines = [f"| {key_name} | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for k, v in d.items():
        lines.append(f"| {k} | " + " | ".join(str(v[c]) for c in cols) + " |")
    return "\n".join(lines)


def clean(s: str, n: int = 100) -> str:
    return str(s).replace("\n", " ").replace("|", "\\|")[:n]


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Raw file not found: {RAW}\nSet RAW_PARQUET or update RAW in the CONFIG block.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_parquet(RAW)

    # --- IDs and text (on raw, before filtering) ---
    df = raw.copy()
    df.insert(0, "record_id", derive_ids(raw))
    assert df["record_id"].is_unique, "record_id is not unique"
    df["ticket_text"] = build_text(df)

    tag_cols = sorted(c for c in raw.columns if c.lower().startswith("tag"))
    context_cols = [c for c in ["answer", "type", "priority", "version", LANG_COL] if c in raw.columns]
    relevant = TEXT_COLS + [LABEL_COL] + context_cols + tag_cols + ["ticket_text"]

    rep = {
        "source": {"repo": REPO, "commit": COMMIT, "file": RAW.name},
        "grain": GRAIN,
        "ticket_text_fields": TEXT_COLS,
        "ticket_text_definition": "subject + newline + body (answer excluded: written after routing)",
        "routing_label_field": LABEL_COL,
        "context_fields": context_cols + tag_cols,
        "raw_records": int(raw.shape[0]),
        "raw_columns": int(raw.shape[1]),
        "column_names": list(map(str, raw.columns)),
        "record_id_method": ("'tb_' + first 12 hex chars of SHA-256 over 'column=value' lines for all "
                             "raw columns (sorted by name, missing = <NULL>); identical rows get _1, _2, ..."),
        "missing_raw": missing_table(df, relevant),
    }

    # --- Filter funnel ---
    funnel = {"raw": len(df)}
    lang = df[LANG_COL].astype("string").str.strip().str.lower()
    rep["language_counts_raw"] = {str(k): int(v) for k, v in lang.value_counts(dropna=False).items()}
    df = df[lang.eq(LANG_KEEP).fillna(False)]
    funnel[f"{LANG_COL} == '{LANG_KEEP}'"] = len(df)
    df = df[~is_missing(df["ticket_text"])]
    funnel["non-empty ticket_text"] = len(df)
    df = df[~is_missing(df[LABEL_COL])]
    funnel[f"non-empty {LABEL_COL}"] = len(df)
    df = df.reset_index(drop=True)
    rep["filter_funnel"] = funnel
    rep["filtered_records"] = len(df)
    rep["missing_filtered"] = missing_table(df, relevant)

    # --- Label distribution ---
    vc = df[LABEL_COL].value_counts()
    rep["n_labels"] = int(vc.size)
    rep["label_distribution"] = {str(k): {"count": int(v), "proportion": round(v / len(df), 4)}
                                 for k, v in vc.items()}

    # --- Text length ---
    chars = df["ticket_text"].str.len()
    words = df["ticket_text"].str.split().str.len()
    q = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    c_desc, w_desc = chars.describe(percentiles=q), words.describe(percentiles=q)
    rep["text_length"] = {s: {"chars": round(float(c_desc[s]), 1), "words": round(float(w_desc[s]), 1)}
                          for s in c_desc.index}

    # --- Suspiciously short texts (<= SHORT_WORDS words) ---
    short = df.assign(_w=words)[words <= SHORT_WORDS].sort_values(["_w", "record_id"])
    rep["short_texts"] = {
        "threshold_words": SHORT_WORDS,
        "rule": f"<= {SHORT_WORDS} words",
        "count": len(short),
        "examples": [{"record_id": r.record_id, LABEL_COL: str(r[LABEL_COL]), "text": r.ticket_text}
                     for _, r in short.head(15).iterrows()],
    }

    # --- Exact duplicate ticket texts ---
    dup_mask = df["ticket_text"].duplicated(keep=False)
    dups = df[dup_mask]
    n_labels_per_text = dups.groupby("ticket_text")[LABEL_COL].nunique()
    norm = df["ticket_text"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    rep["duplicates"] = {
        "rows_in_duplicate_groups": int(dup_mask.sum()),
        "redundant_rows (total - unique)": int(df["ticket_text"].duplicated().sum()),
        "duplicate_groups": int(dups["ticket_text"].nunique()),
        "groups_with_conflicting_labels": int((n_labels_per_text > 1).sum()),
        "redundant_rows_after_case_whitespace_normalisation": int(norm.duplicated().sum()),
        "example_record_ids": dups.sort_values(["ticket_text", "record_id"])["record_id"].head(10).tolist(),
    }

    # --- 20-record stratified sample for manual inspection ---
    sample = build_sample(df)
    sample_path = OUT_DIR / "inspection_sample_20.csv"
    if sample_path.exists() and not OVERWRITE_SAMPLE:
        existing_ids = pd.read_csv(sample_path)["record_id"].tolist()
        if existing_ids == sample["record_id"].tolist():
            sample_status = "kept existing file (record_ids match)"
        else:
            sample_status = "kept existing file - WARNING: record_ids differ from a fresh sample"
    else:
        sample.to_csv(sample_path, index=False, encoding="utf-8")
        sample_status = "written"

    rep["sample_method"] = (f"Filtered English records shuffled with random_state={SEED}; records then "
                            f"taken round-robin across '{LABEL_COL}' values (1st of each queue, then 2nd "
                            f"of each queue, ...) in shuffled order until n={SAMPLE_N}.")
    rep["sample_record_ids"] = sample["record_id"].tolist()


    md = [
        "# Profile: Tobi-Bueck customer support tickets",
        f"Source: `{REPO}` @ `{COMMIT}` (file `{RAW.name}`)\n",
        f"**Grain:** {GRAIN}\n",
        f"**Ticket text:** `{' + '.join(TEXT_COLS)}` (answer excluded)  |  **Routing label:** `{LABEL_COL}`\n",
        f"**Raw:** {rep['raw_records']:,} records x {rep['raw_columns']} columns\n",
        f"**Record ID:** {rep['record_id_method']}\n",
        "## Filter funnel",
        *[f"- {k}: {v:,}" for k, v in funnel.items()],
        "\n## Language values (raw)",
        *[f"- {k}: {v:,}" for k, v in rep["language_counts_raw"].items()],
        "\n## Missing values (raw)",
        md_table(rep["missing_raw"], ["count", "proportion"]),
        "\n## Missing values (after filtering)",
        md_table(rep["missing_filtered"], ["count", "proportion"]),
        f"\n## Routing-label distribution ({rep['n_labels']} labels, filtered)",
        md_table(rep["label_distribution"], ["count", "proportion"], key_name=LABEL_COL),
        "\n## Ticket-text length (filtered)",
        md_table(rep["text_length"], ["chars", "words"], key_name="stat"),
        f"\n## Suspiciously short texts (<= {SHORT_WORDS} words): {len(short):,}",
        *[f"- `{e['record_id']}` [{e[LABEL_COL]}]: {clean(e['text'])!r}" for e in rep["short_texts"]["examples"]],
        "\n## Exact duplicate ticket texts (filtered)",
        *[f"- {k}: {v}" for k, v in rep["duplicates"].items()],
        "\n## 20-record inspection sample",
        rep["sample_method"],
        "Record IDs: " + ", ".join(f"`{r}`" for r in rep["sample_record_ids"]),
    ]
    (OUT_DIR / "profile_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Done: {len(df):,} filtered records -> {OUT_DIR}")
    print(f"Inspection sample: {sample_status}")
    print(f"First sample ID: {rep['sample_record_ids'][0]}")


if __name__ == "__main__":
    main()
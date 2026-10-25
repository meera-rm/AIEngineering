"""
clean_support_tickets.py - Homework 2, Task 1: Clean the Data.

Script version of cleaning_analysis_task1.ipynb: same 10 decisions, same rules,
same order, same output file.

The canonical support_tickets.csv is read only and never overwritten. All changes
are made to a working copy (clean_df); df stays as the untouched reference.
Text changes to Body are applied in this order: HTML tags -> whitespace -> punctuation.
Department and Priority are never modified.

Usage (from the folder that contains support_tickets.csv):
    python clean_support_tickets.py
    python clean_support_tickets.py --input support_tickets.csv --output support_tickets_cleaned.csv
"""
from __future__ import annotations

import argparse
import ast
import re

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_EXAMPLES = 10

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_DEPARTMENTS = {
    "Technical Support",
    "Returns and Exchanges",
    "Billing and Payments",
    "Sales and Pre-Sales",
    "Service Outages and Maintenance",
    "Product Support",
    "IT Support",
    "Customer Service",
    "Human Resources",
    "General Inquiry",
}

# Tag-like patterns only: "<" must be followed by a letter (or "/" then a letter).
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]{0,50}>")
WHITESPACE_RE = re.compile(r"\s+")
PUNCTUATION_ISSUE_RE = re.compile(r",([A-Z])|([.!?])([A-Z])")
# Body starts with "{", "[" or a double quote (leading spaces are removed first).
STRUCTURED_RE = re.compile(r'^[\[{"]')
PLACEHOLDER_TOKENS = ["acc_num", "order_num", "tel_num", "email_address"]
PLACEHOLDER_RE = re.compile(r"\b(?:" + "|".join(PLACEHOLDER_TOKENS) + r")\b")


# ---------------------------------------------------------------------------
# Detection and cleaning functions (all missing-safe)
# ---------------------------------------------------------------------------
def parse_tags(value):
    """Parse the serialized Tags string into a list so checks work on whole tags."""
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return value
    return ast.literal_eval(value)


def has_duplicate_tags(tags) -> bool:
    return isinstance(tags, list) and len(tags) != len(set(tags))


def dedupe_tags(tags):
    """Remove repeated tags, keeping the first occurrence and the original order."""
    return list(dict.fromkeys(tags)) if isinstance(tags, list) else tags


def has_html_tag(text) -> bool:
    if pd.isna(text):
        return False
    return bool(HTML_TAG_RE.search(text))


def has_whitespace_issue(text) -> bool:
    if pd.isna(text):
        return False
    return text != normalize_whitespace(text)


def has_punctuation_spacing_issue(text) -> bool:
    if pd.isna(text):
        return False
    return bool(PUNCTUATION_ISSUE_RE.search(text))

def remove_html_tags(text):
    if pd.isna(text):
        return text
    return HTML_TAG_RE.sub(" ", text)


def normalize_whitespace(text):
    if pd.isna(text):
        return text
    return WHITESPACE_RE.sub(" ", text).strip()



def clean_punctuation_spacing(text):
    if pd.isna(text):
        return text
    # Comma followed immediately by uppercase letter: Team,I -> Team, I
    text = re.sub(r",([A-Z])", r", \1", text)
    # Sentence punctuation followed immediately by uppercase letter: persists.Could -> persists. Could
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)
    return text


def is_structured(text) -> bool:
    if pd.isna(text):
        return False
    return bool(STRUCTURED_RE.match(text))


def has_placeholder(text) -> bool:
    if pd.isna(text):
        return False
    return bool(PLACEHOLDER_RE.search(text))


# ---------------------------------------------------------------------------
# Output helpers (replace the notebook's display())
# ---------------------------------------------------------------------------
def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def show(frame: pd.DataFrame) -> None:
    if frame.empty:
        print("(none)")
    else:
        print(frame.to_string(max_colwidth=60))


def examples(frame: pd.DataFrame, mask: pd.Series, columns=("ticket_id", "Body")) -> pd.DataFrame:
    return frame.loc[mask, list(columns)].head(N_EXAMPLES)


# ---------------------------------------------------------------------------
# Main cleaning run
# ---------------------------------------------------------------------------
def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Task 1: clean the support-ticket dataset.")
    parser.add_argument("--input", default="support_tickets.csv",
                        help="Immutable canonical dataset (read only)")
    parser.add_argument("--output", default="support_tickets_cleaned.csv",
                        help="Where to write the cleaned dataset")
    args = parser.parse_args(argv)

    # Load ---------------------------------------------------------------------
    df = pd.read_csv(args.input)                 # never written back
    df["Tags"] = df["Tags"].apply(parse_tags)
    clean_df = df.copy()                          # all changes go here

    section("Load")
    print("Rows loaded:", len(df))
    print("First Tags value type:", type(df["Tags"].iloc[0]).__name__)

    # Decision 1 - Duplicate tags (change) ----------------------------------------
    section("Decision 1 - Duplicate tags within a ticket")
    duplicate_tags = df["Tags"].apply(has_duplicate_tags)
    duplicate_tags_count = int(duplicate_tags.sum())
    duplicate_tag_examples = examples(df, duplicate_tags, ("ticket_id", "Tags"))
    print("Affected tickets:", duplicate_tags_count)
    show(duplicate_tag_examples)

    clean_df["Tags"] = clean_df["Tags"].apply(dedupe_tags)
    duplicate_tags_after = clean_df["Tags"].apply(has_duplicate_tags)
    print("Duplicate-tag tickets remaining:", int(duplicate_tags_after.sum()))

    # Decision 2 - Missing Body (retain) --------------------------------------------
    section("Decision 2 - Missing Body")
    missing_body = df["Body"].isna()
    missing_body_count = int(missing_body.sum())
    missing_body_examples = examples(df, missing_body)
    print("Affected tickets:", missing_body_count)
    show(missing_body_examples)

    # Decision 3 - HTML tags (change) -----------------------------------------------
    section("Decision 3 - HTML tags in Body")
    html_issue = df["Body"].apply(has_html_tag)
    html_issue_count = int(html_issue.sum())
    html_examples = examples(df, html_issue)
    print("Affected tickets:", html_issue_count)
    show(html_examples)

    clean_df["Body"] = clean_df["Body"].apply(remove_html_tags)
    html_after = clean_df["Body"].apply(has_html_tag)
    print("HTML-tag tickets remaining:", int(html_after.sum()))

    # Decision 4 - Irregular whitespace (change) ------------------------------------
    section("Decision 4 - Irregular whitespace in Body")
    # Measured after HTML removal, so it includes the gaps left where tags were removed.
    whitespace_issue = clean_df["Body"].apply(has_whitespace_issue)
    whitespace_issue_count = int(whitespace_issue.sum())
    whitespace_examples = examples(clean_df, whitespace_issue)
    print("Affected tickets:", whitespace_issue_count)
    print("  of which already present in the original text:",
          int(df["Body"].apply(has_whitespace_issue).sum()))
    show(whitespace_examples)

    clean_df["Body"] = clean_df["Body"].apply(normalize_whitespace)

    # A body that contained only whitespace or markup is now empty: treat it as missing.
    became_empty = clean_df["Body"].notna() & (clean_df["Body"] == "")
    became_empty_ids = clean_df.loc[became_empty, "ticket_id"].tolist()
    clean_df.loc[became_empty, "Body"] = None
    print("Bodies empty after cleaning (set to missing):", len(became_empty_ids), became_empty_ids)

    whitespace_after = clean_df["Body"].apply(has_whitespace_issue)
    print("Whitespace issues remaining:", int(whitespace_after.sum()))

    # Decision 5 - Punctuation spacing (change) -------------------------------------
    section("Decision 5 - Missing spaces after punctuation in Body")
    punctuation_issue = df["Body"].apply(has_punctuation_spacing_issue)
    punctuation_issue_count = int(punctuation_issue.sum())
    punctuation_examples = examples(df, punctuation_issue)
    print("Affected tickets:", punctuation_issue_count)
    show(punctuation_examples)

    clean_df["Body"] = clean_df["Body"].apply(clean_punctuation_spacing)
    punctuation_after = clean_df["Body"].apply(has_punctuation_spacing_issue)
    print("Punctuation-spacing issues remaining:", int(punctuation_after.sum()))

    # Decision 6 - Structured (JSON / quoted) bodies (retain) -----------------------
    section("Decision 6 - Structured (JSON / quoted) bodies")
    structured = clean_df["Body"].apply(is_structured)
    structured_count = int(structured.sum())
    structured_examples = examples(clean_df, structured)
    first_char = clean_df.loc[structured, "Body"].str[0]
    print("Affected tickets:", structured_count)
    print("  JSON-like (starts with { or [):", int(first_char.isin(["{", "["]).sum()))
    print("  Quoted (starts with a double quote):", int((first_char == '"').sum()))
    show(structured_examples)

    # Decision 7 - Anonymization placeholders (retain) ------------------------------
    section("Decision 7 - Anonymization placeholders")
    placeholder = clean_df["Body"].apply(has_placeholder)
    placeholder_count = int(placeholder.sum())
    placeholder_examples = examples(clean_df, placeholder)
    print("Affected tickets:", placeholder_count)
    for token in PLACEHOLDER_TOKENS:
        token_re = re.compile(rf"\b{token}\b")
        n = clean_df["Body"].apply(lambda t: isinstance(t, str) and bool(token_re.search(t))).sum()
        print(f"  {token}: {int(n)}")
    show(placeholder_examples)

    # Decision 8 - Repeated Body values (retain) ------------------------------------
    section("Decision 8 - Repeated Body values")
    repeated_body = clean_df["Body"].notna() & clean_df["Body"].duplicated(keep=False)
    repeated_body_count = int(repeated_body.sum())
    repeated_body_examples = examples(clean_df, repeated_body)
    print("Repeated Body affected count:", repeated_body_count)
    print("Repeated Body representative ticket_ids:", repeated_body_examples["ticket_id"].tolist())

    # Identical cleaned Body associated with more than one Department (diagnostic only).
    body_department_count = (
        clean_df.dropna(subset=["Body"]).groupby("Body")["Department"].nunique()
    )
    conflicting_bodies = body_department_count[body_department_count > 1]
    conflicting_tickets = clean_df[
        clean_df["Body"].isin(conflicting_bodies.index)
    ][["ticket_id", "Body", "Department"]]
    conflicting_sorted = conflicting_tickets.sort_values(["Body", "Department", "ticket_id"])
    show(conflicting_sorted.head(30))
    print("Bodies with multiple departments:", len(conflicting_bodies))
    print("Tickets belonging to those bodies:", len(conflicting_tickets))

    # Decision 9 - Priority validity (check only) -----------------------------------
    section("Decision 9 - Priority validity")
    invalid_priority = df["Priority"].isna() | ~df["Priority"].isin(VALID_PRIORITIES)
    print("Invalid/missing Priority records:", int(invalid_priority.sum()))
    show(examples(df, invalid_priority, ("ticket_id", "Priority")))

    # Decision 10 - Department validity (check only) --------------------------------
    section("Decision 10 - Department validity")
    invalid_department = df["Department"].isna() | ~df["Department"].isin(VALID_DEPARTMENTS)
    print("Invalid/missing Department records:", int(invalid_department.sum()))
    show(examples(df, invalid_department, ("ticket_id", "Department")))

    # Final validation ---------------------------------------------------------------
    section("Final validation")
    html_final = int(clean_df["Body"].apply(has_html_tag).sum())
    whitespace_final = int(clean_df["Body"].apply(has_whitespace_issue).sum())
    punctuation_final = int(clean_df["Body"].apply(has_punctuation_spacing_issue).sum())

    assert df.shape[0] == clean_df.shape[0], "Row count changed during cleaning."
    assert df["ticket_id"].equals(clean_df["ticket_id"]), "ticket_id values changed."
    assert clean_df["ticket_id"].is_unique, "ticket_id is not unique."
    assert clean_df["Department"].equals(df["Department"]), "Department values changed."
    assert clean_df["Priority"].equals(df["Priority"]), "Priority values changed."
    assert int(duplicate_tags_after.sum()) == 0, "Duplicate tags remain."
    assert html_final == 0, "HTML tags remain."
    assert whitespace_final == 0, "Whitespace issues remain."
    assert punctuation_final == 0, "Punctuation-spacing issues remain."

    print("Original shape:", df.shape)
    print("Cleaned shape:", clean_df.shape)
    print("Ticket IDs unchanged:", df["ticket_id"].equals(clean_df["ticket_id"]))
    print("Duplicate-tag tickets remaining:", int(duplicate_tags_after.sum()))
    print("HTML-tag tickets remaining:", html_final)
    print("Whitespace issues remaining:", whitespace_final)
    print("Punctuation-spacing issues remaining:", punctuation_final)
    print("Missing values in cleaned dataset:")
    print(clean_df.isna().sum().to_string())

    # Save -------------------------------------------------------------------------
    section("Save cleaned dataset")
    output_df = clean_df.copy()
    output_df["Tags"] = output_df["Tags"].apply(
        lambda tags: repr(tags) if isinstance(tags, list) else tags
    )
    output_df.to_csv(args.output, index=False)
    print("Saved cleaned dataset to:", args.output)

    # Writeup values -----------------------------------------------------------------
    section("Cleaning writeup values")
    print("1. Duplicate tags affected count:", duplicate_tags_count)
    print("   representative ticket_ids:", duplicate_tag_examples["ticket_id"].tolist())
    print()
    print("2. Missing Body affected count:", missing_body_count)
    print("   representative ticket_ids:", missing_body_examples["ticket_id"].tolist())
    print("   bodies that became empty during cleaning:", became_empty_ids)
    print()
    print("3. HTML tags affected count:", html_issue_count)
    print("   representative ticket_ids:", html_examples["ticket_id"].tolist())
    print()
    print("4. Irregular whitespace affected count:", whitespace_issue_count)
    print("   representative ticket_ids:", whitespace_examples["ticket_id"].tolist())
    print()
    print("5. Punctuation spacing affected count:", punctuation_issue_count)
    print("   representative ticket_ids:", punctuation_examples["ticket_id"].tolist())
    print()
    print("6. Structured (JSON/quoted) bodies count:", structured_count)
    print("   representative ticket_ids:", structured_examples["ticket_id"].tolist())
    print()
    print("7. Placeholder tickets count:", placeholder_count)
    print("   representative ticket_ids:", placeholder_examples["ticket_id"].tolist())
    print()
    print("8. Repeated Body affected count:", repeated_body_count)
    print("   representative ticket_ids:", repeated_body_examples["ticket_id"].tolist())
    print("   bodies with multiple departments:", len(conflicting_bodies))
    print("   tickets belonging to those bodies:", len(conflicting_tickets))
    print("   conflicting-label representative ticket_ids:",
          conflicting_sorted["ticket_id"].head(N_EXAMPLES).tolist())
    print()
    print("9. Priority records requiring change:", int(invalid_priority.sum()))
    print("10. Department records requiring change:", int(invalid_department.sum()))


if __name__ == "__main__":
    main()

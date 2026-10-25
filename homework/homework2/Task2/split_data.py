"""
split_data.py  —  Task 2: Train / Validation / Test split
==========================================================
Input : support_tickets_cleaned.csv   (Task 1 output)
Output: split_manifest.csv            (columns: ticket_id, split)

Split        Target   Algorithm
-----------  -------  ------------------------------------------------
train          80 %   greedy, group-aware, size-balanced
validation     10 %   (department balance is verified, not optimized)
test           10 %

Groups
------
Tickets whose Body text is identical after trimming whitespace and
lowercasing are kept in the same split to prevent data leakage.
Missing bodies are treated as singleton groups.

Assignment
----------
Groups are shuffled with a fixed seed, sorted largest first, and each
group is assigned to the split currently furthest below its target
fraction.

Verification (automated; the manifest is saved only if every check passes)
------------
- Department balance: every department's share of each split is within
  ±1.5 percentage points of its overall share, and every department
  appears in every split.
- Leakage: no body group spans more than one split. This is re-derived
  from the final assignments, independently of the assignment loop.
- Manifest integrity: correct columns and row count, unique and non-null
  ticket_ids that match the input, valid split names, and split sizes
  within 0.5 percentage points of their targets.

Reproducibility
---------------
SEED = 42 -> local random.Random(42); global random state is untouched.
Verify:
    python split_data.py --output check_manifest.csv
    cmp check_manifest.csv split_manifest.csv && echo "Identical"
    rm check_manifest.csv
"""

import argparse
import random
import sys
from collections import defaultdict

import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
SEED = 42
# Dict order matters: it is the tie-breaking order of the greedy assignment.
TARGET = {"train": 0.80, "validation": 0.10, "test": 0.10}
SPLITS = list(TARGET)
BALANCE_TOL = 0.015   # ±1.5 pp per department per split (absolute)
SIZE_TOL = 0.005      # ±0.5 pp per split size
EXPECTED_COLUMNS = ["ticket_id", "Body", "Department", "Priority", "Tags"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the Task 2 split manifest.")
    parser.add_argument("--input", default="support_tickets_cleaned.csv",
                        help="Cleaned dataset from Task 1")
    parser.add_argument("--output", default="split_manifest.csv",
                        help="Where to write the manifest")
    return parser.parse_args(argv)


# ── Steps ─────────────────────────────────────────────────────────────────────
def load(path: str) -> pd.DataFrame:
    _section("Load")
    df = pd.read_csv(path)
    print(f"Rows loaded: {len(df)}")
    assert list(df.columns) == EXPECTED_COLUMNS, \
        "Unexpected columns — check --input points to the Task 1 output."
    assert df["ticket_id"].is_unique, "Duplicate ticket_ids in input"
    assert df["Department"].notna().all(), "Null Department labels in input"
    return df


def build_groups(df: pd.DataFrame) -> list[list[int]]:
    _section("Build body groups (case-insensitive)")

    # Normalized key used for grouping only; the Body column is not changed.
    df["_body_key"] = df["Body"].str.strip().str.lower().fillna("")

    # Missing/empty bodies become singleton groups.
    key_to_idxs: dict[str, list[int]] = defaultdict(list)
    for idx, key in zip(df.index, df["_body_key"]):
        key = key if key != "" else f"__missing__{idx}"
        key_to_idxs[key].append(idx)

    groups = list(key_to_idxs.values())   # list of lists of df indices
    rng = random.Random(SEED)
    rng.shuffle(groups)
    # Largest groups first; the sort is stable, so equal-size groups keep
    # their seeded shuffled order.
    groups.sort(key=len, reverse=True)

    print(f"Total groups : {len(groups)}")
    print(f"Singleton    : {sum(1 for g in groups if len(g) == 1)}")
    print(f"Multi-ticket : {sum(1 for g in groups if len(g) > 1)}")
    examples = [(len(g), df.loc[g[0], "Body"][:60]) for g in groups if len(g) > 1][:5]
    for size, body in examples:
        print(f"  size={size:4d}  body={body!r}")
    return groups


def assign_splits(df: pd.DataFrame, groups: list[list[int]]) -> dict[str, int]:
    _section("Greedy size-balanced assignment")
    n = len(df)
    counts = {s: 0 for s in SPLITS}
    assign: dict[int, str] = {}

    for group in groups:
        # Pick the split furthest below its target fraction.
        best_split = min(TARGET, key=lambda s: counts[s] / n - TARGET[s])
        for idx in group:
            assign[idx] = best_split
        counts[best_split] += len(group)

    df["split"] = df.index.map(assign)

    for s in SPLITS:
        print(f"  {s:<10s}: {counts[s]:6d} rows  ({counts[s] / n * 100:.2f} %)")
    return counts


def check_department_balance(df: pd.DataFrame) -> float:
    _section("Department balance")

    # Derived from the data, so every real department is checked.
    departments = sorted(df["Department"].unique())
    overall = df["Department"].value_counts(normalize=True)
    split_dists = {
        s: df.loc[df["split"] == s, "Department"].value_counts(normalize=True)
        for s in SPLITS
    }

    print(f"\n{'Department':<36} {'overall':>8} {'train':>8} {'val':>8} {'test':>8}")
    print("-" * 72)
    max_dev = 0.0
    for dept in departments:
        overall_frac = overall.get(dept, 0.0)
        row = f"{dept:<36} {overall_frac:8.4f}"
        for s in SPLITS:
            frac = split_dists[s].get(dept, 0.0)
            dev = abs(frac - overall_frac)
            max_dev = max(max_dev, dev)
            row += f" {frac:8.4f}{' !' if dev > BALANCE_TOL else ''}"
        print(row)

    print(f"\nMax deviation from overall: {max_dev:.4f}  (tolerance: {BALANCE_TOL:.4f})")
    assert max_dev <= BALANCE_TOL, (
        f"Department balance exceeds ±{BALANCE_TOL * 100:.1f} pp tolerance."
    )
    print("Department balance OK ✓")

    # The absolute tolerance is lenient for small departments, so also
    # confirm that every department is present in every split.
    presence = pd.crosstab(df["Department"], df["split"]).reindex(columns=SPLITS, fill_value=0)
    print("\nTickets per department per split:")
    print(presence.to_string())
    empty_cells = presence.eq(0).stack()
    empty_cells = empty_cells[empty_cells]
    assert empty_cells.empty, f"Departments missing from a split: {list(empty_cells.index)}"
    print("Every department appears in every split ✓")
    return max_dev


def check_leakage(df: pd.DataFrame) -> None:
    _section("Cross-split leakage check")
    # Re-derive from the final split column, independently of the assignment loop.
    splits_per_body = (
        df[df["_body_key"] != ""]
        .groupby("_body_key")["split"]
        .nunique()
    )
    leaks = splits_per_body[splits_per_body > 1]
    print(f"Body groups spanning multiple splits: {len(leaks)}")
    assert leaks.empty, (
        f"{len(leaks)} identical (case-insensitive) bodies span multiple splits."
    )
    print("No cross-split leakage ✓")


def build_and_check_manifest(df: pd.DataFrame, counts: dict[str, int]) -> pd.DataFrame:
    _section("Manifest integrity checks")
    n = len(df)
    manifest = df[["ticket_id", "split"]].copy()

    assert list(manifest.columns) == ["ticket_id", "split"], "Wrong columns"
    assert len(manifest) == n, "Row count differs from input"
    assert manifest["ticket_id"].is_unique, "Duplicate ticket_ids"
    assert manifest.notna().all().all(), "Nulls in manifest"
    assert set(manifest["ticket_id"]) == set(df["ticket_id"]), "ticket_ids don't match input"
    assert set(manifest["split"]) == set(SPLITS), "Unexpected split values"
    assert manifest["split"].value_counts().to_dict() == counts, "Split counts don't match assignment"
    for s, frac in TARGET.items():
        assert abs(counts[s] / n - frac) < SIZE_TOL, f"{s} size is off its {frac:.0%} target"

    print("Integrity checks passed ✓")
    return manifest


def save(manifest: pd.DataFrame, path: str) -> None:
    _section("Save manifest")
    manifest.to_csv(path, index=False)
    print(f"Saved: {path}  ({len(manifest)} rows)")
    print(manifest["split"].value_counts().to_string())


# ── Main ──────────────────────────────────────────────────────────────────────
def main(argv=None) -> None:
    args = parse_args(argv)

    df = load(args.input)
    groups = build_groups(df)
    counts = assign_splits(df, groups)

    # All checks run before saving, so a bad manifest is never written.
    check_department_balance(df)
    check_leakage(df)
    manifest = build_and_check_manifest(df, counts)
    save(manifest, args.output)

    _section("Done")
    print(f"Python : {sys.executable}")
    print(f"pandas : {pd.__version__}")
    print(f"SEED   : {SEED}")
    print("\nVerify reproducibility:")
    print("  python split_data.py --output check_manifest.csv")
    print("  cmp check_manifest.csv split_manifest.csv && echo 'Identical'")
    print("  rm check_manifest.csv")


if __name__ == "__main__":
    main()
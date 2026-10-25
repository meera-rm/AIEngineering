# Task 2 – Data Split Writeup

## Chosen proportions and rationale
- **80% train / 10% validation / 10% test** of 29,651 cleaned tickets
  → **23,721 / 2,965 / 2,965** (exactly 80.00 / 10.00 / 10.00).
- Train gets the largest share because it is used to fit the routing models
  (the preprocessor and classifier in Tasks 3–4).
- Validation and test each get 10%: roughly 2,965 tickets each, enough for
  model selection (validation) and an untouched final evaluation (test), while
  keeping most of the data for training.

## Assignment strategy
A custom, group-aware greedy algorithm (no pre-built splitting function),
implemented in `split_data.py`.

1. **Grouping to prevent leakage.** Tickets whose `Body` is identical after
   trimming whitespace and lowercasing form one group and are always assigned
   to the same split. This keeps identical ticket text from appearing in more
   than one split, which would inflate evaluation scores.
   - 25,045 groups: 20,450 single-ticket groups and 4,595 groups with more
     than one ticket (largest size: 4, e.g. "Assistance Required").
   - Case-insensitive matching merges 10 more duplicate groups than exact
     matching would (25,045 vs. 25,055 groups).
   - The one ticket with a missing body (ticket 28902) is its own group.
2. **Ordering.** Groups are shuffled with a fixed seed, then sorted largest
   first, so the multi-ticket groups are placed while there is the most room
   to balance them. The sort is stable, so equal-size groups keep their
   seeded shuffled order.
3. **Assignment.** Each group goes to the split currently furthest below its
   target fraction. This hits the 80/10/10 sizes exactly.

**Department balance** is not directly optimized; it is verified after
assignment. Every department's share of each split is within ±1.5 percentage
points of its overall share (maximum observed deviation: **1.15 pp**,
IT Support in test), and every department appears in every split.

## Reproducibility parameters
- `SEED = 42`, used through a dedicated `random.Random(42)` generator, so the
  global random state is untouched.
- The algorithm is otherwise deterministic (stable sort, fixed tie-breaking
  order train → validation → test).
- Verified: rerunning `split_data.py` produces a byte-identical
  `split_manifest.csv` (`cmp` reports no differences).

## Automated integrity checks (in `split_data.py`)
All checks run before the manifest is saved, so a failing run never writes a
manifest.
- **Input:** expected columns, unique `ticket_id`, no missing `Department`.
- **Department balance:** ±1.5 pp tolerance per department per split, and
  every department present in every split.
- **Leakage:** 0 body groups span more than one split. This is re-derived from
  the final split column, independently of the assignment loop.
- **Manifest:** columns are exactly `ticket_id, split`; 29,651 rows; unique,
  non-null `ticket_id`s that match the input; split values are only
  `train` / `validation` / `test`; split sizes within 0.5 pp of target.

## Output
- `split_manifest.csv` with columns `ticket_id, split`.

## Risks and limitations
- **Small departments vary more in relative terms.** The ±1.5 pp tolerance is
  absolute, so it is lenient for small departments. For example, Human
  Resources has 41 validation tickets against an expected ~57, and General
  Inquiry has 52 against ~42. Evaluation metrics for these departments will be
  noisier.
- **Only exact (case-insensitive) duplicates are grouped.** Near-duplicates
  (e.g. the same text with a small edit) can still land in different splits.
- **Department-balanced assignment was explored but not used.** A notebook
  prototype scored splits by department need as well as size and achieved
  tighter balance (within ~0.1 pp per department). The simpler size-balanced
  script was kept because its manifest is the one used by Tasks 3 and 4, and
  its balance passes the automated checks.

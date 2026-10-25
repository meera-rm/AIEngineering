# Task 3 – Preprocessing Writeup

## Input-field decisions
- **Used:** `Body` only, which is the text available when a ticket arrives.
- **Excluded `Priority` and `Tags`:** may be assigned after routing — leakage risk.
- **Excluded `ticket_id`:** row identifier with no predictive meaning.
- **Inputs:** `support_tickets_cleaned.csv` merged one-to-one with `split_manifest.csv` (all 29,651 rows matched; 80/10/10 = 23,721 / 2,965 / 2,965).

## Preprocessing rationale
1. **Normalization** (shared `text_utils.normalize`, also used by Task 4): lowercase;
   strip accents; replace URLs/emails/numbers with placeholder tokens; collapse
   whitespace. Placeholders keep the signal "this ticket contains a URL/number"
   without adding thousands of one-off tokens.
2. **Missing body:** ticket 28902 is filled with an empty string. It produces one
   all-zero feature vector in validation, so its prediction depends only on the
   model's intercept terms.
3. **TF-IDF, fit on train only** (validation and test are only transformed):
   - `ngram_range=(1,2)`: captures keywords ("invoice") and short phrases ("password reset").
   - `min_df=2`: drops one-off terms such as typos.
   - `max_df=0.95`: drops near-universal template text such as greetings and sign-offs.
   - `sublinear_tf=True`: uses 1 + log(count) so repeated words don't dominate.
   - `max_features=50,000`: bounds memory (uncapped vocabulary: 65,982).
   - **Why TF-IDF:** department routing is largely keyword-driven; TF-IDF is fast,
     deterministic, interpretable, and its sparse features suit linear models.
4. **Shared text:** 0 identical bodies shared across splits; case-insensitive
   grouping in Task 2 removed exact cross-split duplicates (near-duplicates are
   not checked).

## Class-imbalance decision
- Imbalance ratio: 20.9× (6,892 Technical Support vs 329 General Inquiry in train).
- Decision: `class_weight="balanced"` weights (0.34–7.21), computed from train only.
- Why not resampling: undersampling loses data; oversampling duplicates text and encourages memorization.
- Risk: higher weights on small classes may increase false positives — to be checked in Homework 3.

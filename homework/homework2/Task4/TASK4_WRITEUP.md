# Task 4 – ML Baseline Writeup

Text featurization is TF-IDF on the ticket `Body` (unigrams and bigrams,
fit on training data only); the full rationale is in Task 3. `TicketRouter`
reuses those settings but fits the TF-IDF vectorizer and the model together
inside `fit()`, so they are always trained and applied as one unit.

## Model choice and rationale
- **Choice:** multinomial logistic regression (`C=1.0`,
  `class_weight="balanced"`, `max_iter=1000`,
  `random_state=42`), combined with TF-IDF in one
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
- **Training accuracy: 78.56%** (18,636 of
  23,721 training records).
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

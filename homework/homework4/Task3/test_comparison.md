# Task 3: Final Holdout Comparison

**Selected routing model: the candidate (Homework 4 router with English stop-word removal).** The test results support the Task 2 decision to keep the change.

## 1. What was frozen, and when

Both models and the Task 2 decision were frozen before the test split was opened. `freeze_models.py` wrote `freeze_record.json` at 2026-10-16T22:23:17 with SHA-256 hashes of both router files and both saved models. `predict_test.py` checks those hashes before running and refuses to run a second time, so each model predicted the test split exactly once. Neither model was changed or retrained after seeing test results.

- **Original:** the Homework 3 retrained router (`original/`), the immutable baseline.
- **Candidate:** the Task 2 revision (`candidate/`): the same router with `stop_words="english"` added to the TF-IDF vectorizer.
- **Task 2 decision:** keep. Validation accuracy 0.4746 to 0.4932, macro-F1 0.4873 to 0.5096.

Test set: 3,755 tickets from the Homework 3 split manifest. Metrics are the unchanged Homework 3 functions (`compute_metrics.py`). Predictions use the Homework 3 4-column format: `test_predictions_original.csv` and `test_predictions_candidate.csv`.

## 2. Metrics on the test set

Macro-F1 is the primary metric and macro-recall the secondary metric, as set in the Homework 3 metric selection.

| Metric | Test: original | Test: candidate | Test change | Validation: original | Validation: candidate | Validation change |
|---|---|---|---|---|---|---|
| accuracy | 0.4714 | 0.4959 | 0.0245 | 0.4746 | 0.4932 | 0.0186 |
| macro_precision | 0.4467 | 0.4727 | 0.0260 | 0.4588 | 0.4838 | 0.0250 |
| macro_recall | 0.5288 | 0.5517 | 0.0229 | 0.5442 | 0.5585 | 0.0143 |
| macro_f1 | 0.4754 | 0.5005 | 0.0251 | 0.4873 | 0.5096 | 0.0223 |
| weighted_f1 | 0.4720 | 0.4966 | 0.0246 | 0.4751 | 0.4932 | 0.0181 |
| top2_accuracy | 0.6746 | 0.6735 | -0.0011 | 0.6674 | 0.6804 | 0.0130 |

## 3. Per-department results (test)

| Department | Support | Recall (orig) | Recall (cand) | Precision (orig) | Precision (cand) | F1 (orig) | F1 (cand) | F1 change |
|---|---|---|---|---|---|---|---|---|
| Sales and Pre-Sales | 114 | 0.605 | 0.623 | 0.330 | 0.343 | 0.427 | 0.442 | 0.015 |
| Returns and Exchanges | 185 | 0.578 | 0.584 | 0.365 | 0.387 | 0.448 | 0.466 | 0.018 |
| Technical Support | 1095 | 0.432 | 0.456 | 0.562 | 0.570 | 0.488 | 0.507 | 0.018 |
| IT Support | 449 | 0.428 | 0.445 | 0.381 | 0.403 | 0.403 | 0.423 | 0.020 |
| Product Support | 695 | 0.383 | 0.404 | 0.466 | 0.502 | 0.420 | 0.448 | 0.028 |
| Human Resources | 71 | 0.521 | 0.592 | 0.407 | 0.412 | 0.457 | 0.485 | 0.029 |
| Service Outages and Maintenance | 148 | 0.696 | 0.723 | 0.450 | 0.478 | 0.546 | 0.575 | 0.029 |
| General Inquiry | 53 | 0.528 | 0.509 | 0.384 | 0.443 | 0.444 | 0.474 | 0.029 |
| Billing and Payments | 380 | 0.734 | 0.758 | 0.742 | 0.778 | 0.738 | 0.768 | 0.030 |
| Customer Service | 565 | 0.382 | 0.423 | 0.381 | 0.411 | 0.382 | 0.417 | 0.035 |

## 4. Confusion matrices (test)

Rows are the true department, columns the predicted one.

**Original**

| true \ predicted | Billing | CustSvc | GenInq | HR | IT | Product | Returns | Sales | Outages | TechSup |
|---|---|---|---|---|---|---|---|---|---|---|
| Billing | 279 | 30 | 3 | 4 | 10 | 10 | 13 | 9 | 2 | 20 |
| CustSvc | 18 | 216 | 11 | 10 | 55 | 75 | 48 | 29 | 12 | 91 |
| GenInq | 2 | 7 | 28 | 1 | 5 | 4 | 2 | 1 | 0 | 3 |
| HR | 1 | 12 | 1 | 37 | 5 | 5 | 2 | 1 | 0 | 7 |
| IT | 13 | 59 | 3 | 7 | 192 | 36 | 16 | 13 | 25 | 85 |
| Product | 19 | 73 | 13 | 14 | 61 | 266 | 52 | 34 | 20 | 143 |
| Returns | 10 | 18 | 1 | 2 | 12 | 18 | 107 | 7 | 3 | 7 |
| Sales | 5 | 17 | 0 | 1 | 2 | 11 | 5 | 69 | 0 | 4 |
| Outages | 1 | 11 | 0 | 1 | 10 | 7 | 5 | 1 | 103 | 9 |
| TechSup | 28 | 124 | 13 | 14 | 152 | 139 | 43 | 45 | 64 | 473 |

**Candidate**

| true \ predicted | Billing | CustSvc | GenInq | HR | IT | Product | Returns | Sales | Outages | TechSup |
|---|---|---|---|---|---|---|---|---|---|---|
| Billing | 288 | 26 | 6 | 1 | 10 | 11 | 11 | 8 | 3 | 16 |
| CustSvc | 16 | 239 | 5 | 16 | 49 | 65 | 50 | 33 | 8 | 84 |
| GenInq | 0 | 7 | 27 | 2 | 4 | 3 | 3 | 2 | 0 | 5 |
| HR | 1 | 7 | 0 | 42 | 5 | 6 | 1 | 2 | 0 | 7 |
| IT | 9 | 59 | 2 | 7 | 200 | 38 | 15 | 6 | 17 | 96 |
| Product | 17 | 75 | 11 | 13 | 57 | 281 | 43 | 32 | 17 | 149 |
| Returns | 8 | 18 | 1 | 4 | 10 | 14 | 108 | 9 | 2 | 11 |
| Sales | 3 | 10 | 2 | 1 | 2 | 16 | 6 | 71 | 0 | 3 |
| Outages | 2 | 10 | 0 | 0 | 11 | 7 | 3 | 3 | 107 | 5 |
| TechSup | 26 | 130 | 7 | 16 | 148 | 119 | 39 | 41 | 70 | 499 |

The original gets 1,770 of 3,755 tickets right and the candidate 1,862. The Technical Support ↔ IT Support confusion that Task 1 analyzed did not shrink: Technical Support sent to IT Support went from 152 to 148, but IT Support sent to Technical Support went from 85 to 96. The gains come from other cells, for example Technical Support sent to Product Support fell from 139 to 119.

## 5. Body-length slices (test)

Cut points are from the training split, as in Homework 3: short is 39 words or fewer, medium 40 to 75, long above 75.

| Slice | Tickets | Accuracy: original | Accuracy: candidate | Macro-F1: original | Macro-F1: candidate |
|---|---|---|---|---|---|
| short | 1281 | 0.4387 | 0.4660 | 0.4410 | 0.4726 |
| medium | 1288 | 0.4798 | 0.5008 | 0.4681 | 0.4938 |
| long | 1186 | 0.4975 | 0.5228 | 0.5115 | 0.5325 |

## 6. Ticket-level comparison (test)

- Fixed by the candidate: 279. Broken by the candidate: 187. Net: +92 tickets.
- Exact McNemar test on those counts: p = 0.00002.
- Tickets whose true label is Technical Support or IT Support: correct predictions rose from 665 to 699 of 1,544.

## 7. Differences between validation and test

| | Validation | Test |
|---|---|---|
| Original accuracy | 0.4746 | 0.4714 |
| Candidate accuracy | 0.4932 | 0.4959 |
| Accuracy gain | +0.0186 | +0.0245 |
| Macro-F1 gain | +0.0223 | +0.0251 |
| Macro-recall gain | +0.0143 | +0.0229 |
| Top-2 accuracy change | +0.0130 | −0.0011 |
| Tickets fixed / broken | 281 / 211 | 279 / 187 |

- The original model scored slightly lower on test than on validation, and the candidate slightly higher, so the gap grew a little. The direction and rough size of the gain match across the two sets.
- Top-2 accuracy is the one metric that disagrees. It improved on validation but is flat on test (−0.0011, about 4 tickets).
- On validation, no department's F1 fell. On test, every department's F1 rose (+0.015 to +0.035). Recall fell for one department on test, General Inquiry (0.528 to 0.509), which has only 53 test tickets, so that is one ticket (28 correct to 27).
- Every body-length slice improved, by about 0.02 to 0.03 in macro-F1.

## 8. Do the test results support the Task 2 decision?

Yes. The Task 2 decision was to keep the stop-word change because of gains in accuracy and macro-F1 on validation. On the test split, which played no part in the decision, the candidate is better on the primary metric (macro-F1 +0.025), the secondary metric (macro-recall +0.023), accuracy, macro-precision and weighted F1, in every department's F1, and in every body-length slice. The net gain of 92 tickets is larger than the 70 on validation.

One concern raised in the Task 2 log was that the validation set was also used to design the change, which could overstate the gain. The test result did not show that: the gain held and was slightly larger.

Two things the test does not show:
- The change did not reduce the Technical Support ↔ IT Support confusion that Task 1 targeted. The test confusion between those two departments is 237 tickets for the original and 244 for the candidate.
- I did not check why the stop-word change helps, so the explanation from the Task 2 log (less function-word noise) is still unconfirmed.

## 9. Selected routing model and rationale

**The candidate (stop-word removal) is carried forward into the application.**

- It beats the original on both the primary and secondary metrics on validation and on test, and the improvement is consistent across departments and slices.
- The test gain is statistically clear (p = 0.00002 on 279 fixed versus 187 broken).
- The cost is small: top-2 accuracy is flat, and the change is one line with no extra latency.
- The overall accuracy is still below 50%, so tickets between Technical Support, IT Support, Product Support and Customer Service will keep being misrouted often. The routing model is better, not good.

## 10. Files

`freeze_models.py`, `freeze_record.json`, `predict_test.py`, `evaluate_test.py`, `compute_metrics.py` (Homework 3 metric functions), `original/` and `candidate/` (frozen router code and models), `test_predictions_original.csv`, `test_predictions_candidate.csv`, `test_summary_metrics.csv`, `test_per_class_metrics.csv`, `test_confusion_matrix_original.csv`, `test_confusion_matrix_candidate.csv`, `test_slice_metrics.csv`.

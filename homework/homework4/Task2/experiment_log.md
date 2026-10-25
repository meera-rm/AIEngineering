# Task 2: Experiment Log

**Decision: keep.** Every headline metric improved, no department's F1 got worse, and the net gain is 70 tickets out of 3,755 (exact McNemar p = 0.002). The gain is not concentrated in the targeted category, though: only 4 of the 16 category B tickets were fixed. Section 8 explains the limits of that evidence.

## 1. Targeted category and change

**Category B, "Clear ticket, model misled"** (16 of the 40 inspected Task 1 tickets). Task 1 marked it as the only category a model or preprocessing change could address, so it is the one targeted here. The other categories were ruled out in Task 1: A (mixed signals) has no separating signal in the text, and C (label conflicts with the department list) would need relabeling, not a model change.

**Diagnostic before choosing the change.** I checked which features pushed the baseline model toward its wrong answer on the tickets in my first-pass category B grouping (13 tickets; the final Task 1 grouping has 16). Troubleshooting words such as "restart", "reboot" and "cache" did not appear among the top drivers. The top drivers were function-word phrases and generic words, for example "could be", "this could", "be due", "the affected", "facing difficulties", "suspected that", and a lone "problems" (0.18 in ticket 10708, where the correct signal "api" was outweighed). Because the drivers are many small contributions, I judged function-word noise a plausible cause. I did not confirm it for every ticket, and in some tickets the drivers were topic words such as "network", "server" and "tools".

**Hypothesis:** if function words are dropped from the TF-IDF features, phrase features built from them disappear, and content words and content phrases carry more of the decision.

**What the hypothesis predicts:** the category B tickets should flip to correct, the primary metric (macro-F1) and the secondary metric (macro-recall) should not fall, and no department or body-length slice should get clearly worse.

**Change (one, model features):** `stop_words="english"` added to the `TfidfVectorizer` in `ticket_router.py`. The line is the only code change from the Homework 3 router (confirmed by `diff`). TF-IDF settings, the balanced logistic regression, and `random_state=42` are otherwise unchanged.

## 2. Setup

- Trained on the Homework 3 training split (17,524 tickets), predicted the Homework 3 validation split (3,755 tickets). The test split was not used.
- Baseline: the Homework 3 validation predictions at `homework4/Task1/validation_predictions.csv`, unchanged.
- Metrics: the Homework 3 `compute_metrics.py` functions, unchanged.
- Files in `Task2`: `ticket_router.py`, `train_and_predict.py`, `compute_metrics.py`, `compare_models.py`, `bootstrap_compare.py`, `artifacts/ticket_router.joblib` (retrained model), `validation_predictions.csv` (4 columns: `ticket_id`, `true_label`, `recommended_department`, `class_scores`), `summary_metrics.csv`, `per_class_metrics.csv`, `confusion_matrix.csv`, `one_vs_rest.csv`, `slice_metrics.csv`, `slice_per_class_metrics.csv` (candidate metrics), `comparison_summary.csv`, `comparison_per_class.csv`, `bootstrap_summary.csv`.

## 3. Performance on the targeted category

| Group | Fixed by the change | Total |
|---|---|---|
| **Category B, inspected tickets** | **4** | 16 |
| Category A, inspected tickets | 2 | 11 |
| Category C, inspected tickets | 4 | 13 |
| **All Technical Support ↔ IT Support slice errors** | **53** | 260 |

Category B: tickets 5683, 10661, 13238 and 23588 became correct. The other 12 kept a wrong prediction. Two of those moved to a different wrong department (17460 to Product Support, 29454 to Customer Service).

Slice errors fixed, by baseline margin (predicted score minus true-label score):

| Baseline margin | Fixed | Slice errors |
|---|---|---|
| 0.05 or less | 37 | 98 |
| 0.05 to 0.10 | 13 | 79 |
| above 0.10 | 3 | 83 |

Most fixes are near-ties, but 3 confident errors were also corrected.

## 4. Improvements against the baseline (validation)

| Metric | Baseline | Candidate | Change |
|---|---|---|---|
| Accuracy | 0.4746 | 0.4932 | +0.0186 |
| Macro precision | 0.4588 | 0.4838 | +0.0250 |
| Macro recall | 0.5442 | 0.5585 | +0.0143 |
| Macro F1 | 0.4873 | 0.5096 | +0.0223 |
| Weighted F1 | 0.4751 | 0.4932 | +0.0181 |
| Top-2 accuracy | 0.6674 | 0.6804 | +0.0130 |

All 10 departments have equal or higher F1. The largest gains are General Inquiry (+0.063), Customer Service (+0.032), Human Resources (+0.030), Billing (+0.023), IT Support (+0.021), Returns (+0.020) and Technical Support (+0.017).

281 tickets became correct. Among tickets whose true label is Technical Support or IT Support, 133 were fixed and 96 broken, so correct predictions went from 682 to 719 of 1,544.

## 5. Regressions against the baseline (validation)

No headline metric got worse and no department's F1 fell. The regressions are:

- **Recall fell for three departments:** General Inquiry (0.642 to 0.623), Product Support (0.363 to 0.355) and Service Outages and Maintenance (0.710 to 0.703).
- **211 tickets became wrong**, of 856 whose prediction changed.
- **General Inquiry** gained the most F1 through precision (0.405 to 0.508) while losing recall. It is the smallest department, so these shifts rest on few tickets.

## 6. Body-length slices (validation)

The Homework 3 slices, with cut points from the training split: short is 39 words or fewer, medium 40 to 75, long above 75. Each slice has more than 1,200 validation tickets.

| Slice | Tickets | Accuracy: baseline | Accuracy: candidate | Macro-F1: baseline | Macro-F1: candidate | Macro-recall: baseline | Macro-recall: candidate |
|---|---|---|---|---|---|---|---|
| short | 1,280 | 0.4594 | 0.4789 | 0.4636 | 0.5024 | 0.5219 | 0.5509 |
| medium | 1,245 | 0.4892 | 0.4996 | 0.5116 | 0.5137 | 0.5668 | 0.5656 |
| long | 1,230 | 0.4756 | 0.5016 | 0.4904 | 0.5215 | 0.5389 | 0.5570 |

Accuracy and macro-F1 rose in all three slices. The gain is largest on short tickets (macro-F1 +0.039) and smallest on medium ones (+0.002). Macro-recall fell slightly in the medium slice (−0.001), which is the only slice-level drop and is about the size of noise.

## 7. Keep-or-revert decision

**Keep.**

- **Primary metric (macro-F1):** up 0.022, from 0.4873 to 0.5096. **Secondary metric (macro-recall):** up 0.014, from 0.5442 to 0.5585. Both roles from the Homework 3 metric selection moved the right way.
- All six headline metrics improved, led by accuracy +1.9 points and macro F1 +0.022.
- The net gain is 70 tickets (281 fixed, 211 broken). An exact McNemar test on those counts gives p = 0.002, so the gain is unlikely to be chance.
- No body-length slice got worse on accuracy or macro-F1 (section 6).
- No department's F1 got worse. The three recall drops are 0.007 to 0.019.

## 8. Limits of the evidence

- **The gain is broad, not targeted.** Only 4 of 16 category B tickets were fixed. The metric gains come from across all departments, so the change helps the classifier but I have not shown it works for the reason I gave. Function-word noise is a plausible explanation, not a confirmed one.
- **The validation set was also used to design this change** (the diagnostic above used validation tickets). That can make the validation gain slightly optimistic, and the p-value above does not correct for it. The Task 3 test set is the fair check.
- **Category B is 16 tickets**, a small sample, so its result is only suggestive. The slice figures (53 of 260) do not depend on that sample.
- **I did not inspect which words drove the new predictions**, or test other stop-word lists, so I cannot say which removed words matter. Removing "it" in particular may have affected predictions, since the baseline treated it as IT-leaning.
- One run with one seed. I did not measure run-to-run variation.
- **Later check:** after the decision was frozen (`Task3/freeze_record.json`), I ran a paired bootstrap over the validation tickets (2,000 resamples, seed 42; `bootstrap_compare.py`). It agrees with the decision: accuracy +0.0186 (95% interval +0.0077 to +0.0296) and macro-F1 +0.0223 (+0.0079 to +0.0363), with the candidate better in 99.9% of resamples.

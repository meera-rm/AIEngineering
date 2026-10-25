
100%
# Homework 3 - Evaluate the Routing Classifier

## Goal

Choose appropriate classification metrics, retrain the Homework 2 ML model
against a canonical split, and evaluate it on validation data.

This homework is about evaluation, not model improvement. Do not change the
classifier in response to the results.

## Provided Materials

| File | Purpose |
| --- | --- |
| `split_manifest.csv` | Official train, validation, and test assignments for the retained `ticket_id` values from the Homework 2 dataset; omitted IDs are excluded |
| `requirements.txt` | Cumulative pinned dependencies through Homework 3 |

Continue using `support_tickets.csv` and its dataset card from Homework 2; they
are not provided again. Treat the carried-forward source dataset and provided
split manifest as immutable.

Also bring forward your Homework 2 curation, training-intervention,
preprocessing, ML training, persistence, and prediction code.

The canonical manifest overrides your Homework 2 curation and split policy for
this and later homeworks. Resolve its original `ticket_id` values against the
immutable source, not just your curated dataset, so previous cleaning cannot
drop canonical held-out records. Canonical validation and test records must not
be removed, changed, relabeled, deduplicated, sampled, or augmented. Fit the ML model and its
data-dependent preprocessing on canonical training only, and apply training
interventions only to canonical training.

Do not use the test split in this homework; use only the training and validation
splits.

## Task 1 - Select Classification Metrics

Select multiple metrics that capture different aspects of performance on the
ticket-routing problem.

### Requirements

- Select metrics to use for evaluation before viewing the validation results. 
  Include both cross-class summary metrics and per-class metrics.
- Explain your metric selection.
- Identify a primary and secondary metric to guide future model iteration, 
  and explain why you selected them.

### Deliverables

- Metric-selection writeup containing:
  - For each metric:
    - Define it, including the aggregation method where relevant.
    - Explain why it fits the ticket-routing task.
    - Explain its potential shortcomings or what it may hide.
  - Primary and secondary metric selection with rationale.

## Task 2 - Retrain and Apply the ML Model

Re-run your existing Homework 2 ML training workflow using the provided split
manifest, then apply the retrained model to the validation set.

### Requirements

- Replace the Homework 2 manifest input with `split_manifest.csv`.
- Retrain the classifier (ML model + preprocessor) using the new training split.
- Use the retrained model to predict every record in the validation set.
- Save the prediction results as a 4-column CSV containing `ticket_id`, `true_label`, `recommended_department`, and `class_scores` (serialized JSON-dict) returned by the Python classifier class.
- Ensure text-cleaning, preprocessing, and the model are all embedded in the Python classifier class
  (in case you designed it differently in the last homework).
- Ensure training and predictions are reproducible.

### Deliverables

- Classifier Python class from homework 2, with changes made, if any. This
  class should be taking raw ticket text(s) for `fit()` and `predict()`, and:
  - Applying text-cleaning
  - Training/applying the preprocessor
  - Training/applying the ML model
- Code for applying the data split, and feeding it into the classifier.
- Saved retrained ML model.
- Prediction results CSV.

## Task 3 - Compute and Interpret Classification Metrics

Compute the Task 1 metrics from the task 2 prediction CSV, and interpret
the results.

### Requirements

- Use the Task 2 prediction results as the input.
- Implement the Task 1 metrics directly from the predicted/true labels
  or class scores without using pre-built functions.
- Produce an evaluation report containing the computed metrics and explanations.
- Identify slices of body-length (e.g. short, medium, long), explain your
  slice definitions, and compute the same metrics for each slice.

### Deliverables

- Metric-computation code
- Evaluation report containing:
  - Per-class (one-vs-rest) confusion matrix
  - Multi-class confusion matrix
  - Computed metric values for each selected metric from Task 1.
  - Computed metrics per-slice.
  - How performance differs across the body-length slices and what those differences may indicate.
  - What the primary and secondary metrics indicate about overall performance, and whether the other summary metrics change that interpretation
  - Which departments perform best and worst, and which confusion patterns help explain those results
  - What the metrics and this validation set cannot establish

## Submission Guidelines

- Submit the complete homework as one `.zip` file. Do not submit individual files or multiple `.zip` files.
- Name the archive `Firstname_Lastname_HW3.zip`, using the same first and last name shown in Google Classroom. For example: `Tanner_Gilligan_HW3.zip`.
- Organize the archive with one folder per task at its root. Each task folder should contain that task's deliverables:

  ```text
  Tanner_Gilligan_HW3.zip
  ├── Task1/
  ├── Task2/
  └── Task3/
  ```

- Upload the `.zip` file itself. Do not submit a Google Drive, GitHub, or other external link in place of the file.
- Submit data tables as static CSV files, not Excel files or links to Google Sheets.
- Submit writeups as `.txt` or `.md` files.
- Do not include duplicate or extraneous files unless they are relevant to running or interpreting your submission.
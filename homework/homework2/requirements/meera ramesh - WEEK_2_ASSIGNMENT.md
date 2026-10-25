
# Homework 2 - Prepare Data and Establish Baselines

## Goal

Build a reusable classifier for this task:

> Given a newly arrived support ticket, predict the department that should
> receive it.

You will curate the provided dataset, create a deterministic
train/validation/test split, implement preprocessing, and build three routing
baselines. This homework checks that the complete modeling workflow runs; formal
model evaluation begins in Homework 3.

## Provided Materials

You receive a canonical dataset derived from
[IT Support Ticket Data](https://www.kaggle.com/datasets/parthpatil256/it-support-ticket-data),
version 1, published June 14, 2025 under the MIT License.

| File | Purpose |
| --- | --- |
| `support_tickets.csv` | Immutable canonical dataset |
| `DATASET_CARD.md` | Source, schema, field roles, and dataset summary |
| `ml_baseline_output_example.json` | Required ML-baseline prediction output example |
| `requirements.txt` | Pinned dependencies for Python 3.14.7 |

Treat the dataset as immutable: read it from your code, but do not overwrite or
hand-edit it.

`DATASET_CARD.md` provides the dataset's row grain, field roles, missing-value
counts, cardinalities, and routing-label distribution. Use that supplied summary
rather than repeating the broad dataset profiling from Homework 1.

## Task 1 - Clean the Data

Prepare the supplied data for splitting and modeling. Identify relevant
record-level quality issues and decide which to change, retain, or defer.

### Requirements

- Implement deterministic text cleaning in code.
- Do not use pre-defined text-cleaning libraries.
- Produce a cleaned dataset with the same `ticket_id`.
- For each decision, record representative `ticket_id` values, the action and
  reason, the affected count, and one risk or limitation.

### Deliverables

- Cleaning code.
- Cleaned dataset.
- Cleaning writeup containing, for each cleaning decision:
  - What the issue was.
  - Why you consider it an issue.
  - How you addressed the issue.
  - How many records are affected by the issue.
  - Some representative ticket_id's.
  - Risks or limitations of your solution

## Task 2 - Split the Data

Create reproducible train, validation, and test partitions from the cleaned
dataset.

### Requirements

- Choose and justify the proportions, assignment strategy, and reproducibility
  parameters of your split policy.
- Implement the assignment algorithm directly without a pre-built splitting
  function.
- Algorithm should output a CSV with 2 columns: `ticket_id` and `split`. 
  `split` is one of `train`, `validation`, or `test`.
- Include automated integrity checks (e.g. make sure your splitting worked as expected).

### Deliverables

- Split-generation code.
- Split verification code.
- Manifest CSV.
- Split writeup containing:
  - Chosen proportions and rationale.
  - Assignment strategy and reproducibility parameters.

## Task 3 - Build a Constant Baseline

Build a baseline that always predicts one department.

### Requirements

- Input: ticket `Body`.
- Output: One `Department` label listed in the dataset card.
- Implement a single Python class with functions for:
  - `fit()`: "Trains" the model
  - `predict()`: Predicts the label for a ticket body
  - `save()`: Saves the trained model to disk
  - `load()`: Loads the trained model from disk
- Ensure predictions are reproducible.

### Deliverables

- Python class code.
- Persisted model artifact.
- Writeup containing:
  - Selected label
  - Rationale
  - Percentage of training records that have the selected label

## Task 4 - Build a Rule-Based Baseline

Build a deterministic non-ML baseline and describe the signals its rules use.

### Requirements

- Input: ticket `Body`.
- Output: exactly one `Department` label listed in the dataset card.
- Implement a single Python class with functions for:
  - `predict()`: Predicts the label for a ticket body using your rules
  - `save()`: Saves the trained model to disk
  - `load()`: Loads the trained model from disk
- Ensure predictions are reproducible.
- Implement rules for `Product Support`, `Customer Service`, and `IT Support`,
  which are the second through fourth most frequent classes.
- Fall back to the majority class when no rule matches.
- Only use the train-partition data for rule development.
- Your rules should improve on the constant baseline's accuracy, even if only marginally.

### Deliverables

- Python class code.
- Persisted model artifact.
- Writeup containing:
  - General
    - How rule matches are resolved into a final label
    - Percentage of training records predicted correctly
  - For each rule
    - Description
    - Rationale
    - Number of in-class training records that match
    - Number of out-of-class training records that match

## Task 5 - Implement Preprocessing

Prepare the cleaned ticket-body for modeling.

### Requirements

- Take the cleaned dataset CSV and split manifest as inputs to construct the dataset-splits.
- Define and implement the preprocessing for `Body` to produce feature vectors.
- Decide whether and how to address class imbalance.
- You can use pre-built utilities for text preprocessing.

### Deliverables

- Preprocessing code.
- Preprocessing writeup containing:
  - Input-field decisions and rationale.
  - Preprocessing rationale.
  - Class-imbalance decision and rationale.

## Task 6 - Build an ML Baseline

Build one CPU-friendly classifier.

### Requirements

- Input: ticket `Body`.
- Output: dictionary matching `ml_baseline_output_example.json`.
  - Look at using `predict_proba` or `decision_function` (depends on model)
    to get the class scores.
- Implement a single Python class with functions for:
  - `fit()`: Trains the preprocessor and model
  - `predict()`: Applies preprocessing to the ticket body and predicts the label
  - `save()`: Saves the trained model to disk (use `joblib` Python lib)
  - `load()`: Loads the trained model from disk
- Ensure predictions are reproducible.
- You may use scikit-learn for model training.

### Deliverables

- Python class code.
- Persisted model artifact.
- ML-baseline writeup containing:
  - Text-featurization choice and rationale
  - Model choice and rationale
  - Percentage of training records predicted correctly
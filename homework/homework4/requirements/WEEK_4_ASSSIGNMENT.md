
# Homework 4 - Iterate on the Classifier and Introduce a Local LLM

## Goal

Improve the retrained Homework 3 learned classifier through controlled,
evidence-driven iteration. You will analyze validation errors, test one targeted
change, and compare the original model and iteration candidate once on the locked
test set.

You will also use a local LLM to produce a structured ticket summary, then perform
exactly two prompt revisions based on its outputs.

## Provided Materials

| File | Purpose |
| --- | --- |
| `LLM_SETUP.md` | CPU-based Ollama setup for `qwen2.5:1.5b-instruct-q4_K_M` |

Continue using the Python environment and `requirements.txt` from Homework 3;
Homework 4 adds no Python dependencies.

Bring forward the canonical dataset and split manifest, retrained Homework 3
learned model and training code, validation predictions, metric definitions,
evaluation code, and shared classifier interface. Only this learned classifier
is iterated in Part 1.

## Fixed Evaluation Rules

- Fit preprocessing and model state using canonical training data only.
- Keep classifier prediction features restricted to ticket `Body` text; other
  fields may support analysis, evaluation, or traceability, not prediction.
- Do not change canonical validation or test records, inputs, or labels.
- Keep the Homework 3 comparison metrics unchanged.
- Use validation data for error analysis and iteration.
- Preserve the Homework 3 model and validation predictions as the immutable
  iteration baseline.
- Do not inspect or predict the test split until Task 3.
- Do not make classifier changes after viewing the test results.

## Part 1: Evidence-Driven Classifier Iteration

## Task 1 - Analyze Validation Errors

Use the Homework 3 evaluation to investigate one recurring confusion pattern in depth.

### Requirements

- Use the Homework 3 metrics and confusion matrix to select one consequential confusion family or weak slice.
- Explain why you chose the slice you did.
- Deterministically select 30+ misclassified records from the slice for inspection.
- For each record, identify why (to the best of your ability) the classifier failed. 
  This will involve examining metrics by slice, ticket text, and/or model internals to understand signals.
- Identify failure categories; assign each ticket to one.
- Identify which categories are addressable via model or preprocessing changes.

### Deliverables

- Error-analysis writeup containing:
  - Selected slice and rationale.
  - For each record:
    - ID
    - True label
    - Predicted label (`recommended_department`)
    - Assigned failure category and rationale
    - Best explanation for why the model selected the predicted department
  - For each failure category:
    - Count of records assigned to that category
    - Likely impact on the classifier's performance
    - Whether the category is addressable via model or preprocessing changes

## Task 2 - Run a Controlled Classifier Iteration

Make one targeted change motivated by an addressable Task 1 failure category,
then decide whether to keep or revert it using validation evidence.

### Requirements

- Make one model or preprocessing change to address the selected task 1 failure category.
- Retrain the classifier with your change using the homework 3 training split.
- Evaluate the classifier against the homework 3 validation set.
- Compare against the original baseline to identify improvement(s) and regression(s).
- Make a validation-based keep-or-revert decision.

### Deliverables

- Modified training and/or preprocessing code.
- Retrained model.
- Predictions from the retrained model against the validation set.
  Use the same 4-column CSV format as Homework 3. 
- Experiment log containing:
  - Which failure category was targeted and the implemented change(s).
  - How did performance change for the records in the targeted failure category.
  - Improvements against pre-change (baseline) validation metrics.
  - Regressions against pre-change (baseline) validation metrics.
  - Keep-or-revert decision and rationale.

## Task 3 - Final Holdout Comparison

Compare the original retrained Homework 3 learned model with the Homework 4
iteration candidate on the test set, regardless of the Task 2 decision.

### Requirements

- Freeze both models and the Task 2 decision before opening the test set.
- Apply both models to the homework 3 test set.
- Compute the Homework 3 metrics and confusion matrices for both models.
- Determine if the results support your Task 2 decision.
- Select the routing model carried forward into the application.
- Do not change or rerun either model in response to the test results.

### Deliverables

- Test-set predictions for both models, preserving `recommended_department` and
  `class_scores`.
- Test-comparison report containing:
  - Metrics and confusion matrices for both models.
  - Notable differences between the validation and test set results.
  - Whether the test results support the Task 2 decision.
  - Selected routing model and rationale.

## Part 2: Prompt and Iterate on a Local LLM

The local LLM receives one new ticket body and produces an internal ticket summary for a
human support agent. It does not route the ticket, retrieve external information,
invent a resolution, or take an action.

## Task 4 - Set Up the Local LLM

Set up the course model, Ollama `qwen2.5:1.5b-instruct-q4_K_M`, and verify that
you can call its API before building the ticket-summary feature.

### Requirements

- Follow `LLM_SETUP.md`

## Task 5 - Write an Initial Prompt

Write an initial prompt for the structured ticket summary and produce one valid result.

The output must be a JSON object containing exactly:

| Field | Type | Contract |
| --- | --- | --- |
| `summary` | string | One or two concise sentences describing the reported issue |
| `customer_request` | string | The action or outcome the customer appears to want |
| `missing_information` | array of strings | Details needed to understand or act on the request; empty when none are clearly missing |

All fields are required. The output must be grounded only in the supplied ticket
body.

### Requirements

- Write a prompt that has:
  - Instructions of your choosing.
  - Input: Ticket's `Body`.
  - Output: JSON object matching the output contract.
- Create a reusable function to call the LLM with the prompt and ticket body.
  Include validation of the LLM output.
- Run the prompt successfully on one non-trivial ticket to ensure things are working.

### Deliverables

- Initial prompt.
- Code to call the LLM, and validate the result.
- Which ticket ID you used as your test-ticket.
- Generated output for your single test-ticket.

## Task 6 - Apply the Initial Prompt

Run the initial prompt on the following 10 records from the canonical ticket dataset and inspect its behavior. These are the longest `Body` in each department, measured by character count; ties use the lowest numeric `ticket_id`.

| Department | `ticket_id` |
| --- | ---: |
| Billing and Payments | `28907` |
| Customer Service | `28399` |
| General Inquiry | `28381` |
| Human Resources | `28921` |
| IT Support | `28736` |
| Product Support | `28763` |
| Returns and Exchanges | `28563` |
| Sales and Pre-Sales | `28571` |
| Service Outages and Maintenance | `28642` |
| Technical Support | `29206` |

### Requirements

- Use all 10 listed tickets without alteration.
- Review each output for general quality.

### Deliverables

- For each ticket, report:
  - The full input sent to the LLM.
  - The output returned by the LLM.
  - Did the output follow the JSON schema?
  - Was the output factually supported by the ticket body?
  - Did the output contain the most important information from the ticket body?
  - Do you agree with the identified missing information, and why?
  - What high-level issues do you notice?

## Task 7 - Run Two Controlled Prompt Iterations

Perform exactly two evidence-driven prompt revisions.

### Requirements

For each iteration:
- Select one prompt-addressable failure pattern.
- Change only the prompt.
- Run on all 10 tickets.
- Determine if the change improved the outputs.
- Determine if there were any regressions.
- Record a keep-or-revert decision.
- Iteration 2 must begin with the prompt accepted from iteration 1.
  If you reject the Iteration 1 prompt, use the original.

### Deliverables

For each iteration: 
- The updated prompt.
- LLM outputs for all 10 tickets.
- an experiment log containing:
  - The targeted failure pattern and why you selected it
  - The exact prompt change(s) you made to address the failure pattern.
  - Observed impact of the prompt change, including improvements and regressions.
  - Keep-or-revert decision and rationale.

## Submission Guidelines

- Submit the complete homework as one `.zip` file. Do not submit individual files or multiple `.zip` files.
- Name the archive `Firstname_Lastname_HW4.zip`, using the same first and last name shown in Google Classroom. For example: `Tanner_Gilligan_HW4.zip`.
- Organize the archive with one folder per task at its root. Each task folder should contain that task's deliverables:

```text
Tanner_Gilligan_HW4.zip
├── Task1/
├── Task2/
├── Task3/
├── Task4/
├── Task5/
├── Task6/
└── Task7/
```

- Upload the `.zip` file itself. Do not submit a Google Drive, GitHub, or other external link in place of the file.
- Submit data tables as static CSV files, not Excel files or links to Google Sheets.
- Submit writeups as `.txt` or `.md` files.
- Do not include duplicate or extraneous files unless they are relevant to
running or interpreting your submission.
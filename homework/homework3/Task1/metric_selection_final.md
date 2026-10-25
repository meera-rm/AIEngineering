# Task 1 - Metric Selection for the Ticket-Routing Classifier

These metrics were chosen **before** any validation predictions were produced or viewed.

## 1. The problem these metrics must describe

- **Task:** single-label, multi-class classification. Each ticket `Body` is routed to exactly one of 10 departments:
  Billing and Payments, Customer Service, General Inquiry, Human Resources, IT Support, Product Support,
  Returns and Exchanges, Sales and Pre-Sales, Service Outages and Maintenance, Technical Support.
- **Imbalanced classes.** Label counts in the canonical **training** split (17,524 tickets; computed from
  `support_tickets.csv` joined to `split_manifest.csv`, labels only, with no model predictions involved):

  | Department | Train tickets | Share |
  |---|---|---|
  | Technical Support | 5,113 | 29.2% |
  | Product Support | 3,244 | 18.5% |
  | Customer Service | 2,636 | 15.0% |
  | IT Support | 2,095 | 12.0% |
  | Billing and Payments | 1,770 | 10.1% |
  | Returns and Exchanges | 864 | 4.9% |
  | Service Outages and Maintenance | 690 | 3.9% |
  | Sales and Pre-Sales | 531 | 3.0% |
  | Human Resources | 332 | 1.9% |
  | General Inquiry | 249 | 1.4% |

  The largest department is about 20× the smallest, and the five smallest together make up only about 15% of tickets. A model that always predicts the largest class already scores roughly 29%
  accuracy (the Homework 2 constant baseline).
- **Cost of an error.** A misrouted ticket is not lost. It lands in the wrong queue, someone has to notice
  and re-route it, and the customer waits longer. Errors are costly but recoverable.
  - **False negative for department D:** a D ticket is sent elsewhere, so D's customers are delayed.
  - **False positive for department D:** D's queue receives work that isn't theirs, which wastes D's time.
- **Assumption:** `recommended_department` is used to route tickets directly, without an agent confirming
  each one first. If an agent did review each suggestion, top-k accuracy would matter more (see 3.8).
- **Every department matters.** HR or General Inquiry customers are no less important because there are
  fewer of them. A router that serves the big departments well and quietly fails a small one is not acceptable.

## 2. Building blocks (one-vs-rest)

For each department **c**, every validation ticket falls into exactly one cell:

| | predicted = c | predicted ≠ c |
|---|---|---|
| **true = c** | TP (true positive) | FN (false negative) |
| **true ≠ c** | FP (false positive) | TN (true negative) |

All metrics below are calculated from these counts, or from the multi-class confusion matrix they come from.
**Zero-division convention:** if a denominator is 0 (for example, a class is never predicted), the metric is set to 0 and the case is noted in the report if it occurs.

## 3. Selected metrics

Following the Lesson 6 idea of giving each metric a job, each metric below lists its **role**: primary, secondary, or diagnostic.

### 3.1 Per-class precision
- **Role:** Diagnostic. Together with recall and F1, it ranks departments from best to worst and shows whether a department's queue receives wrong tickets.
- **Definition:** for department c, `precision_c = TP_c / (TP_c + FP_c)`. Of the tickets the model sent to c,
  this is the fraction that truly belong to c. It is calculated separately for each department, without aggregation.
- **Why it fits:** it measures how much wrongly routed work each department's queue receives.
- **Shortcomings:** it ignores the tickets that c *missed*. A model that sends only one very obvious ticket to c
  gets precision 1.0 while missing almost all of c's real tickets. For small departments, a few tickets
  can move it a lot.

### 3.2 Per-class recall
- **Role:** Diagnostic. Shows which departments are missing their own tickets.
- **Definition:** `recall_c = TP_c / (TP_c + FN_c)`. Of the tickets that truly belong to c, this is the fraction
  routed to c. It is calculated separately for each department.
- **Why it fits:** it directly measures whether a department's customers reach the right team. Low recall
  for a department means its customers are systematically delayed.
- **Shortcomings:** it ignores false positives. Sending *everything* to c gives recall 1.0 for c. It is also
  noisy for departments with small support.

### 3.3 Per-class F1
- **Role:** Diagnostic. One score per department, used to rank departments from best to worst.
- **Definition:** `F1_c = 2 · precision_c · recall_c / (precision_c + recall_c)`, the harmonic mean of the two.
- **Why it fits:** it gives one number per department that is high only when the department both receives
  its own tickets and doesn't receive many wrong ones. This makes it easy to rank departments from best to worst.
- **Shortcomings:** it weights precision and recall equally, even if the business cares more about one.
  It also hides *which* of the two is the problem, so it is always reported next to precision and recall.

### 3.4 Per-class support
- **Role:** Diagnostic. Shows how reliable each per-class score is.
- **Definition:** `support_c = TP_c + FN_c`, the number of validation tickets whose true label is c.
- **Why it fits:** it shows how much evidence each per-class score rests on, and it supplies the weights for weighted averaging.
- **Shortcomings:** it isn't a performance measure. It only shows how far the other per-class numbers can be trusted.

### 3.5 Accuracy
- **Role:** Diagnostic. A simple overall score for stakeholders, compared with the ~29% always-Technical-Support baseline.
- **Definition:** `accuracy = (number of tickets where predicted == true) / (total tickets)`. It is calculated over
  all tickets at once, which for single-label multi-class is the same as micro-averaged precision, recall and F1.
- **Why it fits:** it's the simplest answer to "what share of tickets go to the right place?" Stakeholders
  understand it immediately, and it can be compared directly with the constant baseline (~29%).
- **Shortcomings:** it is dominated by large departments. Because of the imbalance, a model can have good
  accuracy while badly failing HR or General Inquiry. It also says nothing about which departments are confused.

### 3.6 Macro-averaged precision, recall and F1
- **Role:** Macro-F1 is the **primary** metric and macro-recall is the **secondary** metric (see section 4). Macro-precision is a diagnostic: the other half of macro-recall.
- **Definition:** compute the per-class metric for each of the K = 10 departments, then take the **unweighted mean**:
  `macro_metric = (1/K) · Σ_c metric_c`. Every department counts equally, whatever its size.
  Macro-recall is the same quantity as **balanced accuracy**.
- **Why it fits:** it treats every department's customers as equally important, so a failing small department
  pulls the score down visibly. Accuracy cannot do this.
- **Shortcomings:** small departments have the same influence as large ones, so their noisy scores make the macro
  average less stable between runs. It also doesn't reflect the overall ticket volume handled correctly.
  As a mean, it can hide one very bad department behind nine good ones. The per-class table is needed to catch that.
- **Macro-precision specifically:** it drops when the model over-predicts a small department, because that
  department's precision counts as much as a large one's. It ignores missed tickets, so on its own it can
  reward a model that routes too few tickets to each department. It is read next to macro-recall.

### 3.7 Weighted-averaged F1
- **Role:** Diagnostic. If it is much higher than macro-F1, the large departments are carrying the score.
- **Definition:** `weighted_F1 = Σ_c (support_c / N) · F1_c`, where N is the total number of validation tickets.
  Each department's F1 is weighted by its share of tickets.
- **Why it fits:** it reflects the experience of the *typical ticket*. Comparing it with macro-F1 shows whether
  the large departments are carrying the overall score. If weighted-F1 is much higher than macro-F1, the small departments are doing worse.
- **Shortcomings:** like accuracy, it is dominated by large departments and can hide small-class failure.
  It is used for comparison, not as a decision metric.

### 3.8 Top-2 accuracy (score-based)
- **Role:** Diagnostic. Shows how many errors are near-misses.
- **Definition:** using `class_scores`, the fraction of tickets whose true department is among the 2 highest-scoring departments. Ties are broken by department name so the result is reproducible.
- **Why it fits:** it shows whether a wrong prediction is "close." If top-2 is much higher than top-1 accuracy,
  showing agents the top two suggestions would fix many misroutes. It also helps explain overlapping departments
  (for example, Technical Support, IT Support and Product Support).
- **Shortcomings:** it doesn't affect the actual routing decision, which uses only the top choice. Scores are rounded to 2 decimals, so ties are possible. It doesn't measure whether the probabilities are well calibrated.

### 3.9 Confusion matrices (diagnostic)
- **Role:** Diagnostic. Shows which departments are confused with which.
- **Definition:** a **multi-class confusion matrix** (K×K). Rows are true departments, columns are predicted
  departments, and cell (i, j) is the number of tickets of department i routed to j. Plus a **one-vs-rest 2×2
  matrix** (TP, FP, FN, TN) for each department.
- **Why it fits:** these are not single scores. They show *where* errors go: which departments absorb each other's
  tickets. That is what explains the per-class numbers.
- **Shortcomings:** they are hard to compare across models at a glance, and raw counts favor large departments. Row-normalized views (each row divided by its support) would help with this.

## 4. Primary and secondary metrics

### Primary: Macro-F1
- It is a single number that rewards both getting each department's tickets to it (recall) and keeping queues clean (precision).
- Macro averaging matches the requirement that **every department matters equally**, which the class imbalance would otherwise hide. Accuracy and weighted-F1 would reward a model for ignoring small departments.
- It matches the Homework 2 design choice of `class_weight="balanced"`, which was made to trade some large-class accuracy for better small-class performance. A metric that ignores small classes would not measure what that choice was meant to improve.

### Secondary: Macro-recall (balanced accuracy)
- From the customer's point of view, the most important failure is a ticket that **doesn't reach the right department** (a false negative), because that's what delays help. Macro-recall measures this directly and equally for every department.
- It exposes a tradeoff macro-F1 can hide. Two models can have the same macro-F1 while one of them gets a smaller
  share of each department's tickets to the right place (it gains precision by losing recall), and macro-recall
  separates them.
- **How they guide iteration:** a future model should improve macro-F1 **without lowering macro-recall**. Any change should also be checked in the per-class table so that no single department's recall falls noticeably.

### Slices
In Task 3, the same metrics are also calculated for each body-length slice (short / medium / long).

## 5. Metrics considered and not selected

These metrics are covered in Lesson 6 but are not selected for ticket routing:

| Metric | Reason not selected |
|---|---|
| TPR | Same as recall, which is already selected |
| FNR | Equal to 1 − recall, so it adds no new information |
| TNR (specificity) / FPR (per class) | With 10 classes, TN is very large, so these stay close to 1 / 0 and say little |
| ROC-AUC / PR-AUC | They evaluate ranking across thresholds, but routing always takes the top choice. They are also more complex to implement without library functions |
| Calibration (reliability diagram, Platt / isotonic) | Checks whether scores match real probabilities. Routing uses only the highest score, not the score value, so calibration does not change routing quality |

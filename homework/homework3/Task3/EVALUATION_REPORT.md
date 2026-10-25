# Task 3 - Evaluation Report: TicketRouter on the Validation Set

## 1. Setup

I retrained the `TicketRouter` from Task 2 (text cleaning, TF-IDF on word 1–2-grams, logistic regression with `class_weight="balanced"`) on the 17,524 canonical training tickets. I then scored it on all 3,755 canonical validation tickets (`Task2/validation_predictions.csv`). I did not use the test split.

The metrics are the ones I chose in Task 1: macro-F1 as the primary and macro-recall as the secondary. Alongside them are accuracy, macro-precision, weighted-F1, top-2 accuracy, per-class precision / recall / F1 / support, and the confusion matrices.

`compute_metrics.py` computes from the true labels, the predicted labels and `class_scores`. It builds the confusion matrix with a loop, gets TP/FP/FN/TN for each department, and applies the formulas from Task 1. It uses no pre-built metric functions. A zero denominator would have been set to 0, but it did not occur.

The matrix adds up to 3,755. Total FP and total FN are both 1,973, because every error is one FN for one department and one FP for another. Total TP is 1,782, which equals the number of correct predictions. Accuracy comes out the same two ways. Top-2 is never below accuracy, and every metric stays between 0 and 1. 

Saved tables: `confusion_matrix.csv`, `one_vs_rest.csv`, `per_class_metrics.csv`, `summary_metrics.csv`, `slice_metrics.csv`, `slice_per_class_metrics.csv`.

Short names used in the tables: Billing = Billing and Payments, CustSvc = Customer Service, GenInq = General Inquiry, HR = Human Resources, IT = IT Support, Product = Product Support, Returns = Returns and Exchanges, Sales = Sales and Pre-Sales, Outages = Service Outages and Maintenance, TechSup = Technical Support.

## 2. Multi-class confusion matrix

Rows = true department, columns = predicted department, diagonal = correct.

| true \ predicted | Billing | CustSvc | GenInq | HR | IT | Product | Returns | Sales | Outages | TechSup | **Total (support)** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Billing** | **284** | 30 | 0 | 3 | 10 | 6 | 12 | 16 | 0 | 19 | 380 |
| **CustSvc** | 21 | **221** | 12 | 6 | 51 | 75 | 39 | 39 | 11 | 90 | 565 |
| **GenInq** | 0 | 5 | **34** | 1 | 3 | 4 | 1 | 2 | 0 | 3 | 53 |
| **HR** | 2 | 3 | 1 | **41** | 2 | 7 | 5 | 4 | 1 | 5 | 71 |
| **IT** | 7 | 47 | 7 | 6 | **192** | 36 | 14 | 17 | 21 | 102 | 449 |
| **Product** | 12 | 97 | 10 | 9 | 73 | **252** | 44 | 36 | 18 | 144 | 695 |
| **Returns** | 8 | 21 | 2 | 2 | 9 | 17 | **87** | 11 | 4 | 24 | 185 |
| **Sales** | 5 | 9 | 1 | 1 | 6 | 6 | 4 | **76** | 2 | 4 | 114 |
| **Outages** | 3 | 3 | 2 | 1 | 15 | 1 | 2 | 4 | **105** | 12 | 148 |
| **TechSup** | 30 | 113 | 15 | 12 | 158 | 130 | 51 | 39 | 57 | **490** | 1,095 |
| **Total predicted** | 372 | 549 | 84 | 82 | 519 | 534 | 259 | 244 | 219 | 893 | **3,755** |

## 3. Per-class (one-vs-rest) confusion matrices

For each department, I compare its own row and column against everything else. TP is the diagonal. FN is the rest of its row (its tickets sent elsewhere). FP is the rest of its column (other departments' tickets sent to it). TN is everything else.

| Department | TP | FP | FN | TN |
|---|---|---|---|---|
| Billing | 284 | 88 | 96 | 3,287 |
| CustSvc | 221 | 328 | 344 | 2,862 |
| GenInq | 34 | 50 | 19 | 3,652 |
| HR | 41 | 41 | 30 | 3,643 |
| IT | 192 | 327 | 257 | 2,979 |
| Product | 252 | 282 | 443 | 2,778 |
| Returns | 87 | 172 | 98 | 3,398 |
| Sales | 76 | 168 | 38 | 3,473 |
| Outages | 105 | 114 | 43 | 3,493 |
| TechSup | 490 | 403 | 605 | 2,257 |

## 4. Computed metric values

### Summary metrics

| Metric | Role (Task 1) | Value | Always-TechSup baseline |
|---|---|---|---|
| **Macro-F1** | **Primary** | **0.487** | 0.045 |
| **Macro-recall** (balanced accuracy) | **Secondary** | **0.544** | 0.100 |
| Macro-precision | Diagnostic | 0.459 | 0.029 |
| Accuracy | Diagnostic | 0.475 | 0.292 |
| Weighted-F1 | Diagnostic | 0.475 | 0.132 |
| Top-2 accuracy | Diagnostic | 0.667 | — |

*Baseline = always predict Technical Support, the largest class. On this validation set that scores accuracy 1,095 / 3,755 = 0.292. Only TechSup gets a non-zero F1 (0.452), so macro-F1 = 0.452 / 10 = 0.045.*

### Per-class metrics (sorted by F1)

| Department | Support | Precision | Recall | F1 |
|---|---|---|---|---|
| Billing | 380 | 0.763 | 0.747 | **0.755** |
| Outages | 148 | 0.479 | 0.709 | 0.572 |
| HR | 71 | 0.500 | 0.577 | 0.536 |
| GenInq | 53 | 0.405 | 0.642 | 0.496 |
| TechSup | 1,095 | 0.549 | 0.447 | 0.493 |
| Sales | 114 | 0.311 | 0.667 | 0.425 |
| Product | 695 | 0.472 | 0.363 | 0.410 |
| CustSvc | 565 | 0.403 | 0.391 | 0.397 |
| IT | 449 | 0.370 | 0.428 | 0.397 |
| Returns | 185 | 0.336 | 0.470 | **0.392** |

## 5. What the primary and secondary metrics say

**Macro-F1 is 0.487.** Averaged over the ten departments, the router is right about half the time in both directions. About half of a department's tickets reach it, and about half of what lands in its queue belongs there. That is far above the always-TechSup baseline (0.045), so the model has learned real signal. But for unreviewed routing, it is weak.

**Macro-recall (0.544) is higher than macro-precision (0.459).** The model would rather catch a department's tickets and send it some extras than miss them. That fits the `class_weight="balanced"` choice from Homework 2. The small departments get predicted more often than they occur (Sales 244 predicted vs 114 true, Outages 219 vs 148, GenInq 84 vs 53), which helps their recall and hurts their precision. TechSup and Product go the other way (893 predicted vs 1,095 true, and 534 vs 695).

**Do the other summary metrics change the story?** No. Accuracy and weighted-F1 are both 0.475, a little below macro-F1. In Task 1 I said that weighted-F1 well above macro-F1 would mean the big departments were carrying the score. Here it is the opposite. The big departments are among the weaker ones (TechSup 0.493, Product 0.410, CustSvc 0.397, IT 0.397), and some small ones do better. So the small departments are not being sacrificed. The weakness is in the large support queues that get mixed up with each other, which agrees with the macro-F1 reading.

Top-2 accuracy is 0.667, which is 19 points above top-1 accuracy. About 36% of the misrouted tickets (702 of 1,973) have the right department as the model's second choice. The top-2 gain is 724 tickets rather than 702 because a few tickets change places when the 2-decimal scores tie. Many errors are near-misses, so showing an agent the top two suggestions would recover a lot of them.

In plain terms, about 1 in 2 tickets goes to the right department, and about 2 in 3 have the right department in the top two.

## 6. Best and worst departments, and the confusions behind them

**Best.** Billing does best by a clear margin (F1 0.755), and its precision (0.763) and recall (0.747) are balanced. My guess is that Billing tickets use distinctive words like invoice, charge and payment. Its mistakes are scattered, and no single confusion involving Billing is bigger than 30 tickets. Outages (0.572) and HR (0.536) come next. Outages catches most of its own tickets (recall 0.709), but 57 TechSup tickets also end up in its queue.

**Worst.** Returns (0.392), IT (0.397), CustSvc (0.397) and Product (0.410).

**The support cluster.** TechSup, IT, Product and CustSvc account for 1,116 of the 1,973 errors (57%) among themselves. The biggest single confusions are all inside this group: TechSup → IT (158), Product → TechSup (144), TechSup → Product (130), TechSup → CustSvc (113), IT → TechSup (102), Product → CustSvc (97) and CustSvc → TechSup (90). My guess is that these departments get a lot of similar "something isn't working" tickets that TF-IDF can't separate. I haven't read the ticket text, so that is a hypothesis.

**Where the other low scores come from.**
- TechSup leaks the most tickets (605 FN): 158 to IT, 130 to Product, 113 to CustSvc, 57 to Outages and 51 to Returns. It also takes in 403 from others, mostly Product (144), IT (102) and CustSvc (90).
- Product has the lowest recall (0.363). Of its 695 tickets, 443 go elsewhere, mainly to TechSup (144), CustSvc (97) and IT (73).
- IT's low precision (0.370) mostly comes from TechSup's 158 tickets landing in its queue.
- Returns and Sales have low precision (0.336 and 0.311) because other departments' tickets get routed to them. Returns receives 51 from TechSup and 44 from Product. Sales receives 39 each from TechSup and CustSvc. Sales still has high recall (0.667), so its own tickets are usually found, but over half of its queue is wrong tickets.

GenInq (53 tickets) and HR (71) are small, so one or two tickets move their scores by a point or two.

## 7. Body-length slices

I sliced by the word count of the raw `Body`, splitting words on whitespace. I set the cut points at the 33rd and 67th percentiles of word count in the canonical training tickets. That gives each slice roughly a third of the data, and the validation data does not decide its own boundaries. The result is short ≤ 39 words, medium 40–75 words and long > 75 words. The validation slices hold short 1,280, medium 1,245 and long 1,230 tickets.

| Metric | Short | Medium | Long | Overall |
|---|---|---|---|---|
| Macro-F1 (primary) | 0.464 | **0.512** | 0.490 | 0.487 |
| Macro-recall (secondary) | 0.522 | **0.567** | 0.539 | 0.544 |
| Macro-precision | 0.440 | 0.480 | 0.473 | 0.459 |
| Accuracy | 0.459 | 0.489 | 0.476 | 0.475 |
| Weighted-F1 | 0.465 | 0.486 | 0.475 | 0.475 |
| Top-2 accuracy | 0.650 | 0.678 | 0.675 | 0.667 |

Per-department values for each slice are in `slice_per_class_metrics.csv`.

**How performance differs.** Short tickets score lowest on every metric and medium tickets highest, with long in between. The gap between short and medium is about 3 points of accuracy and about 5 points of macro-F1. By department the pattern is not uniform. Billing, GenInq and TechSup improve as tickets get longer, while IT (F1 0.427 → 0.325) and Outages (0.667 → 0.488) get worse.

**What might explain it.** Short tickets may simply give TF-IDF less to work with. A 30-word ticket has few distinctive words, so departments with similar vocabulary are harder to tell apart. Long tickets may mix topics, for example a technical problem plus a billing question or a return, which could pull the prediction toward another department. That might be why IT and Outages drop on long tickets. I haven't tested either idea.

**How far to trust it.** The differences are modest. With about 1,250 tickets per slice, a rough 95% margin on a slice's accuracy is about ±0.03. The short-vs-medium accuracy gap is about 0.03, and the margin on the gap itself is about ±0.04, so the gap is within what random variation could produce. Per-department scores inside a slice are noisier still. GenInq has only 14–23 tickets per slice. I treat all of this as something to check with error analysis, not as an established effect.

## 8. What these metrics and this validation set can't tell me

**How much the numbers would move.** These are single numbers from one split of 3,755 tickets. I have no confidence intervals (for example from a bootstrap) and no repeated splits, so I can't say how much they would change on another sample. Overall accuracy has a rough ±0.016 margin. The slice and small-department numbers are much less certain.

**Performance beyond this data.** Training and validation come from the same historical data. I don’t know how the model does on the held-out test set or on new kinds of tickets.

**Label quality.** I scored the model against the Department labels as given. In my Homework 2 cleaning, 9 ticket texts appeared under more than one department, covering 20 tickets. If labels like that are wrong, some of the model’s “errors” are really label noise. These metrics can’t tell a model mistake from a bad label.

**Real-world cost.** The metrics count errors but not what they cost: how long a misrouted ticket is delayed, whether some departments' mistakes matter more (an outage, say), or how agents would use the scores.

**Causes.** The confusion patterns and slice differences show where errors happen, not why. Ideas like overlapping vocabulary or mixed-topic long tickets need error analysis on the actual ticket text.

# Ticket Summary Quality Review

Source data: `homework/homework4/Task6/task6_results.csv` / `task6_results.json`

## Rubric

Dimensions are derived directly from the six recurring issues observed in the Homework 4 Task 6
review (`homework/homework4/Task6/task6_report.md`, "High-level issues" table), not from a generic
template.

### 1. JSON Schema Compliance
- **What it measures:** Whether the output is valid JSON with exactly the required keys
  (`summary`, `customer_request`, `missing_information`) and correct types.
- **Observed in HW4:** All 10/10 outputs passed this check — included as a baseline gate even
  though it was never the failure mode in practice.
- **Scoring scale:** Pass / Fail
- **Criteria:**
  - Pass: Valid JSON, all required keys present, correct types (strings/array), summary ≤ 2 sentences.
  - Fail: Malformed JSON, missing/extra keys, wrong field type, or summary exceeds 2 sentences.

### 2. Factual Accuracy (no hallucination or misattribution)
- **What it measures:** Whether every claim is directly supported by the ticket body, with no
  invented detail and no misattributed source (e.g. who provided a document, whose name a
  placeholder represents).
- **Observed in HW4:** 28907 misattributed the billing documentation's source; 29206 quoted the
  `company_name` placeholder as if it were a real company name (Issue 5 and part of Issue 2).
- **Scoring scale:** 0-2
- **Criteria:**
  - 2: Every statement matches the body, including who said/provided what.
  - 1: Supported overall, but one detail is misattributed or slightly overstated.
  - 0: Contains a claim contradicted by, or absent from, the body.

### 3. Missing-Information Validity
- **What it measures:** Whether each item in `missing_information` is (a) genuinely absent from
  the body, (b) not an anonymization placeholder mistaken for an absent fact, and (c) not simply a
  restatement of the customer's own question — as opposed to a fact an agent would actually need
  and doesn't have.
- **Observed in HW4:** The single largest failure mode — wrong or questionable in 7 of 10 tickets.
  Two concrete sub-patterns: (a) listing the customer's own questions as "missing" (28571: 5/5
  items, 28642: 3/3 items — Issue 1), and (b) flagging anonymization placeholders (`tel_num`,
  `acc_num`, `email`) as missing when they are actually present (28736, 28763, 29206 — Issue 2).
- **Scoring scale:** Per-item Valid/Invalid tally, rolled up to Agree / Partially Agree / Disagree
- **Criteria:**
  - Agree: Every listed item is valid (genuinely absent, not a placeholder, not a restated
    question); no obviously necessary absent fact is omitted.
  - Partially Agree: At least one item is valid, but at least one is a placeholder, a restated
    customer question, or otherwise not genuinely missing.
  - Disagree: Every listed item is invalid, or the list is empty while an obviously necessary fact
    is missing.

### 4. Completeness (secondary requests and useful context)
- **What it measures:** Whether the summary/customer_request keep the ticket's secondary requests
  and concrete context (troubleshooting already tried, urgency, specific constraints), not just
  the single main ask.
- **Observed in HW4:** 8 of 10 tickets dropped a secondary request (Issue 3); 4 of 10 dropped
  useful context like troubleshooting steps or stated urgency (Issue 6).
- **Scoring scale:** 0-2
- **Criteria:**
  - 2: Captures the main ask and all secondary requests/context an agent would need.
  - 1: Captures the main ask but drops at least one secondary request or concrete context detail.
  - 0: Misses or misrepresents the main ask itself.

### 5. Field Non-Redundancy
- **What it measures:** Whether `summary` (the reported issue) and `customer_request` (the desired
  action) say meaningfully different things, rather than one rephrasing the other.
- **Observed in HW4:** 3 of 10 tickets (28907, 28571, 28642) had near-duplicate summary/request
  pairs (Issue 4).
- **Scoring scale:** Pass / Fail
- **Criteria:**
  - Pass: The two fields are distinguishable — summary states the problem, customer_request states
    the desired action/outcome.
  - Fail: The two fields substantially repeat each other.

## Rubric Changes and Justifications

The first draft used generic, template-style dimensions (schema, factual support, key-info
coverage, missing-info agreement) not tied to any specific evidence. Per Task 1's requirement to
derive dimensions from Homework 4's actual observations, the rubric was rebuilt around the six
recurring issues named in the HW4 Task 6 report's "High-level issues" table: missing_information
restating the customer's own questions, anonymization placeholders mishandled, secondary requests
dropped, summary/customer_request redundancy, other misattributed facts, and dropped useful
context. This produced five dimensions (Schema Compliance, Factual Accuracy, Missing-Information
Validity, Completeness, Field Non-Redundancy) in place of the original four, each now citing the
specific HW4 evidence that motivated it. Completeness (0-2) and Factual Accuracy (0-2) keep a
graded scale so partial failures are distinguishable from full failures; Missing-Information
Validity keeps its 3-point Agree/Partially Agree/Disagree scale, now defined in terms of the two
concrete sub-patterns (restated questions, mishandled placeholders) rather than a vague "accuracy"
notion. No further edits were needed after scoring the five tickets below, so the rubric above is
frozen.

## Task 2: Scored Outputs (5 Specified Tickets)

### Ticket 28907 — Billing and Payments
- **Schema Compliance:** Pass.
- **Factual Accuracy:** 1 — the summary/request are accurate, but the `missing_information` item
  misattributes the billing documentation's source ("provided by the customer") when the body says
  the company provided it ("provided by you").
- **Missing-Information Validity:** Disagree — the one item both misattributes its source and
  restates a fact the customer already stated (the discrepancy), rather than identifying something
  genuinely absent.
- **Completeness:** 1 — captures the main request (review/breakdown of charges) but drops the
  secondary request (discount/billing-option eligibility and invoicing adjustments) and the fact
  that the discrepancy came from the customer's own internal audit.
- **Field Non-Redundancy:** Fail — `summary` describes what the customer wants rather than the
  reported issue, so it overlaps heavily with `customer_request`.

### Ticket 28921 — Human Resources
- **Schema Compliance:** Pass.
- **Factual Accuracy:** 1 — `customer_request` ("Implement a redesigned UI...") slightly overstates
  the ticket, which actually asks for a plan and timeline, not direct implementation.
- **Missing-Information Validity:** Partially Agree — the empty list is defensible since contact
  details are present, but an agent would still need to know which modules are hard to use and
  which reports/analyses are wanted, and that gap isn't flagged.
- **Completeness:** 1 — captures the core ask but drops the stated urgency and the request for a
  plan/timeline, and drops the underlying problem (navigation bottlenecks).
- **Field Non-Redundancy:** Pass — summary (UI/data-analysis enhancement) and request (implement
  redesign) are distinguishable.

### Ticket 28763 — Product Support
- **Schema Compliance:** Pass.
- **Factual Accuracy:** 1 — summary is accurate, but one `missing_information` item flags the
  account/order number as missing when `acc_num` is present in the body as an anonymized
  placeholder.
- **Missing-Information Validity:** Partially Agree — "details about the specific components
  causing the flickering" is actually asking the customer to self-diagnose rather than naming a
  genuine information gap, and the account-number item is a mishandled placeholder; a genuinely
  useful missing item (purchase date, relevant to warranty) is not flagged.
- **Completeness:** 1 — `customer_request` collapses everything to "resolve the flickering issue,"
  dropping the specific asks (diagnosis guidance, technician visit, repair/warranty policy
  information) and the troubleshooting already attempted.
- **Field Non-Redundancy:** Pass — summary (the flickering issue) and request (resolve it) are
  distinct, if the request is terse.

### Ticket 28571 — Sales and Pre-Sales
- **Schema Compliance:** Pass.
- **Factual Accuracy:** 2 — summary/request accurately reflect the pre-sales questions asked.
- **Missing-Information Validity:** Disagree — all five items (delivery time, shipping methods,
  expedited options, tracking, return policy) simply restate the customer's own questions; the one
  fact an agent would actually need (shipping destination/quantity) is not flagged.
- **Completeness:** 1 — covers all three topics, but drops that this is a pre-purchase inquiry
  tied to a time-sensitive project schedule.
- **Field Non-Redundancy:** Fail — summary and customer_request are nearly identical restatements
  of the same three topics.

### Ticket 29206 — Technical Support
- **Schema Compliance:** Pass.
- **Factual Accuracy:** 1 — summary quotes the `company_name` anonymization placeholder as if it
  were the company's real name.
- **Missing-Information Validity:** Agree — the new prioritization-policy details are genuinely
  absent from the body and are needed to configure the requested workflow changes.
- **Completeness:** 1 — captures the guidance request and timeline/plugin questions, but drops the
  concrete requirements (custom priority field, dynamic adjustments, new workflow statuses) and the
  request to schedule a discussion.
- **Field Non-Redundancy:** Pass — summary (the policy-driven need) and request (guidance on
  implementation) are distinguishable.

## High-Level Issue

Across all 10 HW4 tickets, `missing_information` was the weakest field (wrong or questionable in 7
of 10), driven by two concrete, prompt-addressable patterns: restating the customer's own questions
as "missing" (28571, 28642) and mishandling anonymization placeholders as absent facts (28736,
28763, 29206, and the `company_name` misquote in 29206). These two patterns are the targets of the
Homework 4 Task 7 prompt iterations and remain the clearest lever for improving these scores.

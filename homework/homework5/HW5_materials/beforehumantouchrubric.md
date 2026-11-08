# Homework 5, Task 1: Rubric for Ticket Summaries

Evaluates outputs of the accepted HW4 prompt (`homework4/Task5/prompt_v1.txt`, qwen2.5:1.5b, temperature 0, seed 42). Each output has three fields: `summary`, `customer_request`, `missing_information`.

Dimensions come from the HW4 Task 6 report (`homework4/Task6/task6_report.md`): its five per-ticket questions, split along the six "High-level issues" it found. Each dimension measures one thing, so a change in score after adding RAG can be traced to a specific cause.

## Placeholder rule (applies to dimensions 2 and 6)

Anonymization tokens such as `name`, `company_name`, `email`, `email_address`, `tel_num`, `acc_num` stand for real values that are present in the ticket. Listing one as missing is an invalid `missing_information` item (dimension 6). Quoting one as if it were a real name or value is a grounding error (dimension 2).

## Dimensions

### 1. Format and constraint compliance
- **Measures:** Whether the output is machine-usable and obeys the prompt's stated constraints.
- **Scale:** Pass / Fail
- **Criteria:**
  - Pass: valid JSON, exactly the keys `summary`, `customer_request`, `missing_information`; types are string, string, array of strings (`[]` if nothing is missing); summary is at most 2 sentences; `missing_information` items are short phrases; no solutions or advice appear in any field.
  - Fail: any parse error, missing or extra key, wrong type, summary over 2 sentences, an item that is a full sentence, or a proposed solution.
- **HW4 evidence:** 10/10 outputs passed the schema check, but 28399 had a full sentence as a missing-information item. This dimension also guards against RAG articles leaking solutions into the output.

### 2. Factual grounding
- **Measures:** Whether every claim is supported by the ticket body.
- **Scale:** 0-2
- **Criteria:**
  - 2: every claim is supported, including who said or provided what.
  - 1: one minor error: wrong attribution, an overstated detail, or a placeholder quoted as a real value.
  - 0: an invented or contradicted product, number, date, cause, or policy.
- **HW4 evidence:** 28907 attributed the billing documentation to the customer when the company provided it (Issue 5). 29206 quoted `company_name` as a real company (Issue 2). No output invented a product, number or date.

### 3. Summary describes the issue
- **Measures:** Whether `summary` states the reported problem or situation, as distinct from the request.
- **Scale:** 0-2
- **Criteria:**
  - 2: states the problem or context and adds information not already in `customer_request`.
  - 1: mostly restates the request, so the two fields overlap.
  - 0: describes a wrong or peripheral issue.
- **HW4 evidence:** Issue 4: summaries for 28907, 28571 and 28642 described what the customer wants instead of what happened.

### 4. Request accuracy and completeness
- **Measures:** Whether `customer_request` contains every distinct ask, with the correct type of ask.
- **Scale:** 0-2
- **Criteria:**
  - 2: all distinct asks captured and correctly typed (for example, "send a plan and timeline" is not "implement").
  - 1: main ask correct, but at least one secondary ask dropped (discount options, consultation or call, warranty information, contingency advice).
  - 0: main ask missing or misstated.
- **HW4 evidence:** Issue 3: secondary requests dropped in 8 of 10 tickets. 28921's request said "implement a redesigned UI" where the ticket asks for a plan and timeline.

### 5. Key context retained
- **Measures:** Whether facts an agent would use are kept somewhere in the output: concrete symptoms, troubleshooting already tried, urgency or deadlines, warranty status, and the specific changes or requirements the customer lists.
- **Scale:** 0-2
- **Criteria:**
  - 2: the important context is kept.
  - 1: some dropped, but the core problem is still concrete.
  - 0: the only concrete problem or the stated urgency is dropped.
- **HW4 evidence:** Issue 6: server latency (28399), head cleaning and brightness/software refresh tried (28563, 28763), navigation bottlenecks and urgency (28921). Dropped specifics: the custom priority field and new workflow statuses (29206), load balancing and reliability (28381).

### 6. Missing-information precision
- **Measures:** Whether every item in `missing_information` is truly absent from the ticket and needed by an agent.
- **Scale:** 0-2
- **Criteria:**
  - 2: every item valid, or `[]` where nothing is needed.
  - 1: one invalid item.
  - 0: two or more invalid items.
  - An item is invalid if it: restates the customer's own question; repeats a fact already in the body; is a placeholder token; asks the customer for something support must diagnose; or misattributes a source.
- **HW4 evidence:** Issue 1: 28571 (5 items) and 28642 (3 items) listed the customer's own questions. Issue 2: `tel_num`, `acc_num`, `email` flagged in 28736, 28763, 29206. Issue 5: 28763 asked the customer for the cause of a fault.

### 7. Missing-information recall
- **Measures:** Whether genuinely needed gaps are flagged.
- **Scale:** 0-2
- **Criteria:**
  - 2: all clear gaps flagged, or `[]` when nothing is missing.
  - 1: some clear gaps missed.
  - 0: a blocking gap missed.
- **HW4 evidence:** the report named gaps the model missed: purchase date for warranty (28763), shipping destination (28571), which AWS services are affected (28642), the prioritization matrix details (29206, which the model did catch).

## Design rationale

- **Mapping from HW4 questions.**
Q1 (schema) became dimension 1.
Q2 (factually supported) became dimension 2.
Q3 (most important information) was too broad to score consistently, so it is split into dimensions 3, 4 and 5 along Issues 4, 3 and 6.
Q4 (agree with missing information) is split into precision (6) and recall (7), since HW4's main failure was flagging wrong items, a different failure from missing real gaps.
Q5 (open-ended issues) is not a dimension; its findings are spread across the others.
- **Scales.**  Binary for objective checks (dimension 1). 0-2 where partial credit is meaningful, because HW4 outputs were often mostly right with one flaw. No 1-10 scales, which are hard to apply consistently.
- **Regression detection.** HW4 Task 7 showed this model fixing one pattern while breaking another, so dimensions 2, 4 and 6 are written to catch regressions as well as improvements. For RAG, dimension 2 detects details borrowed from retrieved articles that are not in the ticket, and dimensions 6 and 7 show whether retrieved context helps the model identify what is truly missing.
- **Known limits.** Several judgments (what counts as a "clear gap", which context is "important") are subjective. Task 2 will tighten these while scoring, then the rubric is frozen.


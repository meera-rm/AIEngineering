# Homework 5, Task 2: Updated Rubric for Ticket Summaries (frozen)

This rubric judges outputs from the accepted HW4 prompt (`homework4/Task5/prompt_v1.txt`, qwen2.5:1.5b-instruct-q4_K_M, temperature: 0, seed: 42, stream: false). Each output has three fields: `summary`, `customer_request`, `missing_information`.

Dimensions come from the HW4 Task 6 report (homework4/Task6/task6_report.md): its five per-ticket questions, split along the six 'High-level issues' it found. Each dimension measures one thing, so a change in score after adding RAG can be traced to a specific cause.

## One rule that applies across several dimensions

The ticket bodies anonymize real values with placeholders like `name`, `company_name`, `email`, `email_address`, `tel_num`, `acc_num`. Those are standing in for real information that is present in the ticket — so a model that lists one of these as "missing" is wrong (that's a `missing_information` error, dimension 6), and a model that quotes one as if it were an actual name or value is also wrong (that's a grounding error, dimension 2).

## Dimensions

### 1. Format and constraint compliance
- **Measures:** whether the output is actually usable — valid JSON, right fields, and it follows the prompt's own rules.
- **Scale:** Pass / Fail
- **Criteria:**
  - Pass: valid JSON with exactly `summary`, `customer_request`, `missing_information`; types are string, string, array of strings (`[]` when nothing's missing); summary is at most 2 sentences; missing_information items are short phrases, not sentences; nothing in any field proposes a solution or next step.
  - Fail: anything else — parse error, wrong/missing/extra key, wrong type, summary runs past 2 sentences, a full-sentence item, or a solution sneaking in.
- **Why this dimension:** All 10 HW4 outputs passed the basic schema check, but 28399's missing_information item was a full sentence rather than a short phrase, so that gets checked specifically here.This also guards against RAG-retrieved solutions leaking into the output in Part 2

### 2. Factual grounding
- **Measures:** whether every claim in the output actually traces back to something in the ticket body.
- **Scale:** 0-2
- **Criteria:**
  - 2: everything checks out, including who said or provided what.
  - 1: one small slip — wrong attribution, something slightly overstated, or a placeholder treated as a real value.
  - 0: something invented or contradicted outright — a product, number, date, cause, or policy that isn't in the ticket.
- **Why this dimension:** 28907 said the customer provided the billing documentation when the ticket actually says the company did. 29206 quoted `company_name` as if it were a real company. Neither output invented a product or number from scratch, so nobody scored a 0 in my HW4 pass, but the mechanism for catching that is here if it happens with RAG.

### 3. Summary describes the issue, not the ask
- **Measures:** whether `summary` actually reports what happened, rather than just repeating what the customer wants.
- **Scale:** 0-2
- **Criteria:**
  - 2: describes the problem/situation and tells me something `customer_request` doesn't.
  - 1: mostly just restates the request — the two fields blur together.
  - 0: describes the wrong issue, or something beside the point.
- **Why this dimension:** This was Issue 4 in my HW4 notes — 28907, 28571, and 28642 all wrote summaries that described the ask instead of the issue, so the two fields ended up saying almost the same thing twice.

### 4. Request accuracy and completeness
- **Measures:** whether `customer_request` captures everything the customer is actually asking for, and gets the *type* of each ask right.
- **Scale:** 0-2
- **Criteria:**
  - 2: every distinct ask is there, and correctly characterized (e.g. "send me a plan and timeline" isn't rewritten as "implement this").
  - 1: the main ask is right, but at least one secondary ask got dropped — things like discount eligibility, a requested call, warranty info, contingency advice.
  - 0: even the main ask is missing or wrong.
  - Wrong type of ask (added in Task 2): if the subject is right but the type of ask is wrong (e.g. "send a plan and timeline" became "implement it"), score 1. If the subject is also wrong, score 0.
- **Why this dimension:** Secondary requests got dropped in 8 of the 10 HW4 tickets (Issue 3). 28921 is a good example of the "wrong type" failure too — the ticket asked for a plan and a timeline, but the output said the customer wants the redesign *implemented*.

### 5. Key context retained
- **Measures:** whether the facts an agent would actually need are still somewhere in the output — concrete symptoms, what's already been tried, urgency/deadlines, warranty status, specific requirements the customer listed.
- **Scale:** 0-2
- **Criteria:**
  - 2: the important context survived.
  - 1: some of it got dropped, but the core problem is still concrete and usable.
  - 0: the one concrete detail that mattered, or the customer's stated urgency, got left out entirely.
- **Why this dimension:** This is Issue 6 from my notes — server latency vanished from 28399, the troubleshooting already tried (head cleaning, brightness, software refresh) disappeared from 28563 and 28763, and 28921 lost both the navigation-bottleneck detail and the stated urgency. 29206 and 28381 each lost specific requirements the customer actually listed.

### 6. Missing-information precision
- **Measures:** whether every item the model flags as "missing" is actually missing and actually needed.
- **Scale:** 0-2
- **Criteria:**
  - 2: every item is valid, or the list is empty because nothing is genuinely needed.
  - 1: one bad item slipped in.
  - 0: two or more bad items.
  - An item is bad if it restates the customer's own question, repeats something already stated in the body, is just an anonymization placeholder, asks the customer to diagnose something support should figure out, or gets the source of a fact wrong.
- **Why this dimension:** This was the single worst field across my HW4 review. 28571 listed all five of the customer's own questions as "missing"; 28642 did the same with three. 28736, 28763, and 29206 all flagged placeholder tokens (`tel_num`, `acc_num`, `email`) as missing even though those are present in the ticket. 28763 also asked the customer to diagnose their own TV, which isn't something the customer left out — it's something support has to figure out.

### 7. Missing-information recall
- **Measures:** the flip side of dimension 6 — whether the model actually catches the gaps that are real.
- **Scale:** 0-2
- **Criteria:**
  - 2: every clear gap got flagged, or the list is correctly empty.
  - 1: a clear gap or two got missed.
  - 0: a gap that actually blocks the request got missed.
- **Why this dimension:** There are several places where the model should have flagged something and didn't — the purchase date was missing for a warranty question (28763), the shipping destination for a delivery-timeline question (28571), which AWS services were affected (28642). 29206 is actually the one case where the model got this right, catching that the specific prioritization-matrix details were missing.


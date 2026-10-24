# Task 3 — Create and Inspect Synthetic Data
**Dataset:** Tobi-Bueck Customer Support Tickets @ `ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb` (`tobi_bueck_ddf1c81a.parquet`)
**Code:** `synth_tickets.py` → writes `synthetic_50.jsonl`

---

## 3.1 Augmentation plan

**Gap.** The routing label `queue` is imbalanced (Task 2 Section 2.6). **Service Outages and Maintenance** has only 1,106 English tickets (3.91%), against 8,149 for Technical Support (about 7:1). A router will tend to send outage tickets to the larger, overlapping queues (Technical Support, IT Support).

**Why this queue.** General Inquiry, HR and Sales are rarer, but every inspected ticket in those queues (2 each, in the stratified sample of 20) was mislabelled or unclear (Task 2 Section 3), so synthetic copies would multiply label noise. Both inspected outage tickets had correct labels, and outage vocabulary is distinctive, so seed labels can be checked with keywords.

**Slice to add.** 50 English tickets with `queue = Service Outages and Maintenance`:
- about 87% have a subject (matching the real 12.88% missing rate);
- `type` and `priority` come from clean seeds;
- each record is tagged `provenance = "synthetic"` with its `seed_record_ids`.

This is a pilot: 50 records only take the queue from 1,106 to 1,156 (3.91% → 4.08%), so the goal is to validate generator quality before generating at scale.

**Generation approach.** Sentence-level recombination of clean seed tickets, without an LLM.

1. Seed filters (each tied to Task 2): too short (< 12 words) or fewer than 3 sentences; placeholders (`<name>`, `[Your Name]`) or a literal `\n`; no outage vocabulary; off-topic terms (billing, returns, HR, sales, marketing, investment); duplicate texts.
2. Each record is built from 3–4 **different** seeds of the same `type`: an opener, 1–2 middle sentences and a closer. The subject and priority come from the main middle seed. Light synonym swaps are applied.
3. A candidate is rejected if it duplicates an earlier record or contains any complete source body.
4. A fixed random seed (42) and input sorted by `record_id` make the output reproducible.

**Why it fits.** The corpus is templated (greeting, issue, request, sign-off), so recombining sentences keeps realistic structure and domain language. Each record inherits its label only from clean, on-topic seeds. Mixing seeds prevents copying any source ticket.

---

## 3.2 Generation results

**Seed funnel** (printed by `python synth_tickets.py`): 1,106 outage tickets → **222 clean seeds**.

| Excluded because | Count |
|---|---|
| No outage vocabulary | 266 |
| Fewer than 3 sentences | 251 |
| Off-topic terms | 129 |
| Placeholder or escaped newline | 99 |
| Under 12 words | 90 |
| Duplicate text | 49 |

**Output:** exactly 50 records in `synthetic_50.jsonl`. Each has a unique content-hash `record_id` (`syn_…`) and `provenance: "synthetic"`. No candidates were rejected by the duplicate or no-copy checks.

**Determinism check:** generated twice; the SHA-1 of `synthetic_50.jsonl` was identical both times (`dc8d9e0f1d1b7c20cfcf53215ae15db8129607ba`).

---

## 3.3 Inspection of 10 records

Five records were chosen at random with `random.Random(43).sample(records, 5)` over the 50 records in file order. Five more were chosen by reading all 50 records and picking ones that looked suspicious, extreme or repetitive.

| record_id | Picked as | Acceptable | Issue |
|---|---|---|---|
| syn_0d5f3d1fa1b2 | random | Y | Minor: the customer lists all the troubleshooting they did and says the issue is still not resolved. It ends without an explicit request |
| syn_c2b62f34a30d | random | Y | Minor: high priority for an information request |
| syn_8b39fa9f59d5 | random | N | Starts as a customer ("I am facing difficulties…") but ends with "Kindly be assured that all measures are being taken…", which reads like a reply to the customer, not a request from one |
| syn_51fee5880b0f | random | N | First and last sentences are identical to syn_bd5077d6cb9f, so it is nearly a copy of another synthetic record. It also lists the measures taken while troubleshooting and ends without a request |
| syn_d39e7e338650 | random | N | No subject. Stitched ending: "This includes conducting a thorough investigation…" does not follow from "swift resolution", and a scalability request turns into investigating outage causes and adding security measures |
| syn_ae1bdf93963d | suspicious | N | Off-topic: digital strategy and brand growth request in an outage ticket; subject is about medical data, body mixes topics |
| syn_774a8e93bd9b | suspicious | N | Off-topic: opens with a request to revise the digital strategy for brand development, then reports outages |
| syn_cf335bf4d44a | suspicious | N | Longest body (69 words, median 46); two separate sentences list troubleshooting steps; long last sentence packs several points together |
| syn_966cab49737a | suspicious | N | Near-empty: asks to "update our maintenance schedule" without describing any outage; the rest is boilerplate closers ("I look forward to hearing from you soon", "Please let us know…"). Subject does not match the body and high priority is not justified |
| syn_1d79f83cffd8 | suspicious | N | Same subject and "root cause remains uncertain" sentence as syn_42ad7797de51; troubleshooting repeated |

**Summary:** 2 of 5 random records were acceptable, and all 5 suspicious records had real issues. Two contain off-topic brand-strategy content that does not belong in the outage queue, and one has no outage content at all. Other defects come from stitching sentences from different tickets and from repeated troubleshooting sentences. Some sentences also appear in several records (for example "The cause is unknown, but a recent software update or network failure is suspected." appears three times in the 50).

**Proposed generator changes**
1. Build each ticket by sentence role (issue, cause, troubleshooting, request), with at most one sentence per role. This fixes contradictory causes, repetition and missing requests, and rejects records with no issue sentence.
2. Filter out sentences written in the support agent's voice ("kindly be assured", "we are now observing", "will update once").
3. Only combine seeds from the same domain (overlapping `tag_1`–`tag_3`), and check that the subject's keywords appear in the body.
4. Cap reuse: each sentence at most once and each seed at most twice.
5. Extend the off-topic seed filter with words such as "brand" and "digital strategy", which let marketing-style sentences into outage records.

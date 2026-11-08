# Homework 5, Task 7: RAG-Informed Summaries vs. No-RAG

Rubric: frozen Task 2 rubric (`../Task2/rubric.md`). No-RAG scores: Task 2 (`../Task2/human_scores.csv`).
RAG run: `../Task6/summarize_ticket_rag.py` with `../Task6/prompt_v2_rag.txt`, k = 5, distance cut-off 0.21, `qwen2.5:1.5b-instruct-q4_K_M`, temperature 0, seed 42, stream false, num_predict 512.
Fairness check: the no-RAG prompt re-run with num_predict 512 gave outputs identical to the HW4 outputs for all three tickets (`outputs/*_no_rag.json`), so the Task 2 scores are a valid no-RAG baseline.

Full records (retrieval results, exact user message, output): `outputs/<ticket>_rag.json`.

## Ticket 28763 — Supported request

### Retrieval results (top 5, cut-off 0.21)

| Rank | Distance | Chunk | Article / section | Used in prompt |
|---|---|---|---|---|
| 1 | 0.1148 | `KB-SAM-TV-001#03` | Safe Troubleshooting for Intermittent Flicker on Samsung QN90A TVs / What support provides | yes |
| 2 | 0.1165 | `KB-SAM-TV-001#02` | Safe Troubleshooting for Intermittent Flicker on Samsung QN90A TVs / Safe checks the customer can perform | yes |
| 3 | 0.1197 | `KB-SAM-TV-001#01` | Safe Troubleshooting for Intermittent Flicker on Samsung QN90A TVs / Symptoms | yes |
| 4 | 0.1339 | `KB-SAM-TV-001#04` | Safe Troubleshooting for Intermittent Flicker on Samsung QN90A TVs / Limits and escalation | yes |
| 5 | 0.1972 | `KB-SAM-NEG-001#03` | Troubleshooting Audio Dropouts on Samsung QN90A Televisions / What support provides | yes |

### Generated summary (RAG)

- **summary:** The customer's Samsung QLED QN90A TV is experiencing persistent flickering issues, which they believe is a hardware-related problem rather than a software issue.
- **customer_request:** Provide guidance on the next steps to take, possibly including instructions for an at-home diagnosis or arranging a qualified technician's assessment.
- **missing_information:**
  - The customer needs to provide information about the specific sources that are affected by the flickering issue.

### No-RAG output (HW4)

- **summary:** Customer reports a persistent flickering issue with their Samsung QLED QN90A TV, which has become more pronounced over time and is causing significant hindrance to the viewing experience.
- **customer_request:** Resolve the flickering issue with their Samsung QLED QN90A TV promptly.
- **missing_information:**
  - Details about the specific components causing the flickering issue
  - Information about the customer's account or order number

### Grading and comparison

| Dimension | No-RAG (Task 2) | RAG | RAG rationale | Change |
|---|---|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Fail | The missing_information item is a full sentence ("The customer needs to provide information about..."), not a short phrase. | Worse (Pass → Fail) |
| 2. Factual grounding (0-2) | 2 | 1 | Says the customer believes it is hardware "rather than a software issue"; the ticket says "rather than something that could be adjusted with simple settings modifications" (slight overstatement). Everything else traces to the ticket. | Worse (2 → 1) |
| 3. Summary describes the issue, not the ask (0-2) | 2 | 2 | Describes the problem (persistent flickering, customer suspects a hardware fault) and adds detail customer_request does not have. | Same |
| 4. Request accuracy and completeness (0-2) | 1 | 1 | Main ask now captured precisely (next steps: at-home diagnosis or a technician's assessment), but the request for repair-policy and warranty information is still dropped. | Same score; main ask more accurate |
| 5. Key context retained (0-2) | 1 | 1 | Keeps the flickering and the hardware suspicion, but drops "more pronounced over time" (present in no-RAG) and all troubleshooting already tried. | Same |
| 6. Missing-information precision (0-2) | 0 | 2 | The one item (which sources are affected) is a real detail the customer can give, prompted by the retrieved safe-checks article; it does not ask the customer to diagnose the fault. | Better (0 → 2) |
| 7. Missing-information recall (0-2) | 1 | 1 | Still misses the purchase date needed for the warranty question; the warranty article was not in the top 5. | Same |

**Comparison:** RAG used the flicker-troubleshooting article as intended: `customer_request` now names the actual ask (at-home diagnosis or technician) instead of "resolve the issue", and `missing_information` went from two bad items (asking the customer to name failed components; an account number that is present as a placeholder) to one valid item (dimension 6: 0 → 2). The costs: the item is now a full sentence, which fails dimension 1, and the summary paraphrases "settings" as "software" and loses "more pronounced over time". The warranty part of the ticket gained nothing because the warranty article ranked 7th and 10th and was not in the top 5, so the purchase-date gap (dimension 7) is still missed. **Net:** dimensions 2–7 total 8/12 vs. 7/12 for no-RAG, but the output now fails dimension 1.

## Ticket 29206 — Supported multi-source request

### Retrieval results (top 5, cut-off 0.21)

| Rank | Distance | Chunk | Article / section | Used in prompt |
|---|---|---|---|---|
| 1 | 0.1139 | `KB-JIRA-001#03` | Custom Priority Configuration in Jira Software 8.20 / What support provides | yes |
| 2 | 0.1288 | `KB-JIRA-001#04` | Custom Priority Configuration in Jira Software 8.20 / Planning estimate | yes |
| 3 | 0.1311 | `KB-JIRA-002#04` | Adding Workflow Statuses and Transition Conditions in Jira Software 8.20 / Dynamic behavior and limits | yes |
| 4 | 0.1376 | `KB-JIRA-002#01` | Adding Workflow Statuses and Transition Conditions in Jira Software 8.20 / Overview | yes |
| 5 | 0.1417 | `KB-JIRA-001#02` | Custom Priority Configuration in Jira Software 8.20 / What the customer provides | yes |

### Generated summary (RAG)

- **summary:** Our team at company_name is seeking guidance on how to modify Jira Software 8.20 workflows to better align with our new company policies regarding ticket prioritization and project management.
- **customer_request:** We need assistance in implementing new custom workflows or modifying existing ones to include additional statuses and transition conditions that accurately reflect our updated prioritization strategies.
- **missing_information:**
  - The customer needs to provide the approved list of priority names, definitions, and intended order from highest to lowest urgency.
  - The customer should also inform support about which projects are affected, whether the customer uses a staging environment, and who has Jira administrator access to make the change safely.

### No-RAG output (HW4)

- **summary:** The customer team at company_name is seeking guidance on implementing modifications to Jira Software 8.20 to better align with their new company policies regarding ticket prioritization and project management.
- **customer_request:** Provide guidance on the best approach for implementing workflow modifications to Jira Software 8.20, including technical feasibility, potential timelines, and any necessary plugins or documentation.
- **missing_information:**
  - The specific details of the new company policies regarding ticket prioritization and project management.

### Grading and comparison

| Dimension | No-RAG (Task 2) | RAG | RAG rationale | Change |
|---|---|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Fail | Both missing_information items are full sentences, not short phrases. | Worse (Pass → Fail) |
| 2. Factual grounding (0-2) | 1 | 1 | Still quotes the placeholder company_name as a real name and adds "project management" to the policy scope; also written in the customer's voice ("Our team...", "We need..."). | Same |
| 3. Summary describes the issue, not the ask (0-2) | 1 | 1 | Summary still restates the ask ("seeking guidance on how to modify...") and overlaps with customer_request. | Same |
| 4. Request accuracy and completeness (0-2) | 1 | 1 | Captures the workflow change (new statuses, transition conditions) but drops the asks for technical feasibility, timelines, plugins, documentation and a discussion, which no-RAG kept. | Same score; content worse |
| 5. Key context retained (0-2) | 1 | 1 | Now keeps the requirement for additional statuses and transition conditions, but drops the custom priority field and dynamic adjustment. | Same score; slightly better content |
| 6. Missing-information precision (0-2) | 2 | 2 | Both items are real gaps the ticket does not state: priority names, definitions and order; affected projects, staging environment and Jira admin access. | Same |
| 7. Missing-information recall (0-2) | 2 | 2 | Catches the prioritization-matrix gap and adds further details support needs from the retrieved "What the customer provides" section. | Same score; more complete |

**Comparison:** Both Jira articles (custom priorities and workflow statuses) were retrieved, and their "What the customer provides" content appears in `missing_information` as real, useful gaps (priority names and order; affected projects, staging, admin access); precision and recall stay at 2. The rest of the output did not improve: the summary still restates the ask and still quotes `company_name`, `customer_request` lost the feasibility/timeline/plugin/documentation asks, and the model switched into the customer's voice ("We need..."). As with 28763, the article-style sentences in `missing_information` fail dimension 1. **Net:** 8/12 on dimensions 2–7, the same as no-RAG, with a dimension 1 failure.

## Ticket 28921 — Unsupported request

### Retrieval results (top 5, cut-off 0.21)

| Rank | Distance | Chunk | Article / section | Used in prompt |
|---|---|---|---|---|
| 1 | 0.2223 | `KB-DASH-NEG-001#02` | Intake for Dashboard and Reporting Enhancement Requests / What the customer provides | no (cut) |
| 2 | 0.2354 | `KB-DASH-NEG-001#03` | Intake for Dashboard and Reporting Enhancement Requests / What support provides | no (cut) |
| 3 | 0.2504 | `KB-DASH-NEG-001#05` | Intake for Dashboard and Reporting Enhancement Requests / Limits | no (cut) |
| 4 | 0.2636 | `KB-DASH-NEG-001#01` | Intake for Dashboard and Reporting Enhancement Requests / Overview | no (cut) |
| 5 | 0.2666 | `KB-CONSULT-001#02` | Scheduling and Intake for IT Consulting Sessions / What the customer provides | no (cut) |

### Generated summary (RAG)

- **summary:** The customer requests a significant enhancement to the internal human resources management system, focusing on improved user interface design and advanced data analysis capabilities to address user navigation and information retrieval issues.
- **customer_request:** Implement a redesigned user interface and advanced data analysis tools to improve user experience and efficiency.
- **missing_information:**
  - (empty)

### No-RAG output (HW4)

- **summary:** The customer requests enhancements to the internal human resources management system, focusing on improved user interface design and data analysis capabilities.
- **customer_request:** Implement a redesigned user interface and advanced data analysis tools to improve user experience and efficiency.
- **missing_information:**
  - (empty)

### Grading and comparison

| Dimension | No-RAG (Task 2) | RAG | RAG rationale | Change |
|---|---|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Pass | Valid JSON with the 3 fields; 1-sentence summary; empty list allowed; no fix proposed. | Same |
| 2. Factual grounding (0-2) | 2 | 2 | Every claim is in the ticket; nothing from the cut dashboard/consulting articles appears. | Same |
| 3. Summary describes the issue, not the ask (0-2) | 1 | 2 | Now adds the problem ("to address user navigation and information retrieval issues"), which customer_request does not contain. | Better (1 → 2) |
| 4. Request accuracy and completeness (0-2) | 1 | 1 | Identical to no-RAG: turns "send your plan and implementation timeline" into "implement it" (wrong-type rule: right subject, wrong type). | Same |
| 5. Key context retained (0-2) | 0 | 0 | Navigation issue now retained, but the customer's stated urgency is still dropped entirely. | Same |
| 6. Missing-information precision (0-2) | 2 | 2 | Empty list, so no bad items. | Same |
| 7. Missing-information recall (0-2) | 1 | 1 | Still does not flag which modules are hard to use or which reports are needed, both required to give a plan and timeline. | Same |

**Comparison:** The distance cut-off worked as designed: all five retrieved chunks (dashboard intake and IT consulting, distance ≥ 0.222) were removed, the model received "No relevant reference articles were found.", and no unrelated content leaked into the output. The output still changed slightly: the summary now names the underlying problem (navigation and information-retrieval issues), raising dimension 3 from 1 to 2. Because no articles were inserted, this change comes from the revised prompt wording, not from retrieved content. Request type and urgency problems are unchanged. **Net:** 8/12 vs. 7/12, still Pass on dimension 1.

## Overall comparison

| Ticket | Case | No-RAG: Dim 1 / Dims 2–7 | RAG: Dim 1 / Dims 2–7 | Dimensions that changed |
|---|---|---|---|---|
| 28763 | Supported | Pass / 7 of 12 | **Fail** / 8 of 12 | Dim 1 ↓, Dim 2 ↓ (2→1), Dim 6 ↑ (0→2) |
| 29206 | Supported multi-source | Pass / 8 of 12 | **Fail** / 8 of 12 | Dim 1 ↓ |
| 28921 | Unsupported | Pass / 7 of 12 | Pass / 8 of 12 | Dim 3 ↑ (1→2) |

**What RAG improved.** The retrieved "What the customer provides" sections helped where the knowledge base had a matching article: `missing_information` became more accurate on 28763 (precision 0 → 2) and more complete on 29206. On 28763, the troubleshooting article also helped the model state the real request (diagnosis or technician) instead of a generic "resolve the issue".

**What RAG made worse.** On both supported tickets the model copied the articles' sentence style into `missing_information` ("The customer needs to provide..."), so both outputs fail the short-phrase constraint (dimension 1). On 29206 it also wrote in the customer's voice and dropped several asks that the no-RAG output kept. The summaries themselves (dimensions 3 and 5) barely changed, and the persistent no-RAG problems (dropped secondary asks, lost urgency, placeholder quoted as a name) remain.

**Retrieval was the limit on 28763.** The ticket asks about troubleshooting *and* warranty coverage, but all four flicker sections filled the top 4, so the warranty article (which lists the purchase date as required) never reached the prompt. This is the same "one article fills the top ranks" failure found in Task 5.

**The unsupported ticket was handled safely.** The 0.21 distance cut-off kept unrelated dashboard and consulting text out of 28921's prompt, so there was no ungrounded content. Its small improvement came from the prompt wording alone, which also shows that prompt changes and retrieved content both affect the output and should be measured separately.

**Conclusion.** With this small model, RAG gave targeted gains in `missing_information` and request accuracy where a matching article was retrieved, but it did not improve the overall quality reliably and introduced a formatting failure on both supported tickets. This matches the assignment's expectation that a weak model may not show clear gains. The most promising next steps are a per-article cap in retrieval (so a second article such as warranty can enter the context) and an output example or rule that keeps `missing_information` items as short phrases, each tested one change at a time.

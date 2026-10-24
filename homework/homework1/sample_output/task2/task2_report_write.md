# Task 2 — Inspect and Profile the Dataset
**Dataset:** Tobi-Bueck Customer Support Tickets (`Tobi-Bueck/customer-support-tickets`, Hugging Face)
**Version:** commit `ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb` · DOI 10.57967/hf/6184 · CC BY-NC 4.0
**Profiled file:** `tobi_bueck_ddf1c81a.parquet` (raw, all languages)
**Code:** `profile_tobi_bueck.py` → writes `profile_report.md` and `inspection_sample_20.csv`


---

## 1. Approach

- **Data:** the raw Parquet file (`tobi_bueck_ddf1c81a.parquet`), pinned to commit `ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb`. Parquet is used instead of CSV because it keeps nulls and data types exactly and can't be broken by multi-line ticket text. The raw, all-language file is profiled, rather than the English-only copy, so the before/after filtering counts are computed by the script itself.
- **Filtering:** keep English records (`language == "en"`): 61,765 → 28,261 (45.76%). Checks for empty ticket text and empty `queue` removed no further records.
- **Fields:** ticket text = `subject + "\n" + body` (a missing subject is treated as empty); routing label = `queue`. `answer` is excluded: it's written after routing, so it would leak the label.
- **Record IDs:** the dataset has no identifier, so one is derived deterministically: `record_id = "tb_" + first 12 hex chars of SHA-256 over "column=value" lines for all 16 raw columns` (columns sorted by name, missing values written as `<NULL>`). Fully identical rows would get suffixes `_1`, `_2`, …, but none occurred. IDs are computed on the raw data before filtering, and all 61,765 are unique.
- **Inspection sample:** English records are shuffled with `random_state=42`, then selected round-robin by queue, taking turns across the 10 queues (one ticket from each, then a second from each). This gives 2 tickets per queue, 20 in total, so small queues are represented equally with large ones.
- **Reproducibility:** `profile_tobi_bueck.py` uses the pinned commit, a fixed seed (42), content-hash IDs, and no timestamps, so re-running it gives identical output.

---

## 2. Profile results

### 2.1 Total records and columns (raw)
- **61,765 records × 16 columns**
- Columns: `subject, body, answer, type, queue, priority, language, version, tag_1 … tag_8`
- Dtypes: all text columns are strings; `version` is float64.

### 2.2 Records after basic filtering
| Step | Records | % of raw |
|---|---|---|
| Raw | 61,765 | 100.00% |
| `language == "en"` | 28,261 | 45.76% |
| Non-empty ticket text | 28,261 | 45.76% |
| Non-empty `queue` | 28,261 | 45.76% |

Language distribution (raw): **German (`de`) 33,504 (54.24%)**, **English (`en`) 28,261 (45.76%)**. There are no null or blank language values.

### 2.3 Record grain
One row represents **one support ticket**: the customer's subject and body, the agent's answer, the routing queue, and associated metadata (type, priority, language, version, tag_1–tag_8).

### 2.4 Ticket-text and routing-label fields
- **Ticket text:** `ticket_text = subject + "\n" + body`, with each part stripped and a missing subject treated as empty.
- **Routing label:** `queue`, which is categorical.
- **Excluded:** `answer` is the agent's reply, written *after* routing, so including it would leak the label.
- **Context fields (profiled, not used as text):** `type`, `priority`, `version`, `language`, `tag_1`–`tag_8`.

### 2.5 Missing values
**Raw (key fields)**
| Field | Null / blank | % |
|---|---|---|
| subject | 5,299 | 8.58% |
| body | 2 | 0.00% |
| queue | 0 | 0.00% |

**Filtered English (relevant fields)**
| Field | Null / blank | % |
|---|---|---|
| subject | 3,639 | 12.88% |
| body | 1 | 0.00% |
| ticket_text | 0 | 0.00% |
| queue | 0 | 0.00% |
| language | 0 | 0.00% |
| version | 11,923 | 42.19% |
| tag_1 … tag_8 | 0 → 26,653 | 0.00% → 94.31% (structural, see 2.9) |

- No ticket has both subject and body empty, so every ticket has usable text.
- 12.88% of English tickets (about 1 in 8) have no subject, so for those tickets the body is the only text.

### 2.6 Routing-label counts and proportions (English, 10 queues)
| Queue | Count | Proportion |
|---|---|---|
| Technical Support | 8,149 | 28.83% |
| Product Support | 5,305 | 18.77% |
| Customer Service | 4,269 | 15.11% |
| IT Support | 3,333 | 11.79% |
| Billing and Payments | 2,897 | 10.25% |
| Returns and Exchanges | 1,402 | 4.96% |
| Service Outages and Maintenance | 1,106 | 3.91% |
| Sales and Pre-Sales | 843 | 2.98% |
| Human Resources | 553 | 1.96% |
| General Inquiry | 404 | 1.43% |

- **Class imbalance:** the largest queue (Technical Support) is about **20 times** the smallest (General Inquiry, 404). No queue has fewer than 100 tickets.
- **Label-space note:** the raw data contains **52 unique queue values**, but English has only 10. The extra 42 values occur only in the German records. This wasn't investigated further because German is filtered out, but it may point to label variants or noise in the German portion.
- Several queues overlap semantically (Technical Support / IT Support / Product Support), which is likely to make routing harder.

### 2.7 Ticket-text length (English)
| Stat | Characters | Words |
|---|---|---|
| mean | 410.17 | 60.36 |
| std | 203.52 | 31.33 |
| min | 4 | 1 |
| 25% | 244 | 35 |
| median | 404 | 59 |
| 75% | 568 | 83 |
| max | 1,825 | 276 |

- A typical ticket is about 60 words, and the distribution is moderate, with no extreme outliers. The longest ticket is 276 words.

### 2.8 Suspiciously short tickets (≤ 5 words): 32 (0.11% of English records)

Short tickets are rare, but they carry specific queue labels despite having no routable content, so they are a quality flag rather than a dataset-wide problem, and could be filtered before training.

Examples (10 of the 32):
| record_id | Subject | Body | Queue | Words |
|---|---|---|---|---|
| tb_a77e5adba818 | *(missing)* | Help | Billing and Payments | 1 |
| tb_53da7f0876bd | *(missing)* | Support needed | Billing and Payments | 2 |
| tb_d34b503b8291 | ConcernregardingSystemInvestmentAnalytics | Thecompanyisincapableofaccessinginvestmentanal… | Technical Support | 2 |
| tb_67d47e89ce69 | ConcernregardingSystemInvestmentAnalytics | Thecompanyisincapableofaccessinginvestmentanal… | Technical Support | 2 |
| tb_68d82e700a74 | *(missing)* | Hello support team | Customer Service | 3 |
| tb_9ba3caca0605 | *(missing)* | Hello support team | Customer Service | 3 |
| tb_5d2594cbbb29 | Issue Encountered | Assistance Needed | Technical Support | 4 |
| tb_f7f9d3698b9c | *(missing)* | Problems with the server | General Inquiry | 4 |
| tb_d09f37cf74e3 | *(missing)* | Several products are impacted | Technical Support | 4 |
| tb_e7baa45bbdb8 | *(missing)* | Several products are impacted. | Technical Support | 4 |

Observations:
- These tickets have **no routable content** ("Help", "Hello support team"), yet they carry specific queue labels. 
- Some texts have **all whitespace removed** ("Thecompanyisincapableof…"). The word count says 2 words, but the text is actually long.
- Near-identical short texts appear in pairs, which is consistent with the duplicate finding below.

### 2.9 Exact duplicate ticket texts (English)
| Metric | Value |
|---|---|
| Exact duplicate rows in raw data (all 16 columns) | **0** |
| Rows involved in duplicate `ticket_text` | 9,026 |
| **Duplicate ticket texts beyond first occurrence** | **4,513** (15.97% of English records) |
| Unique texts appearing more than once | 4,513 |
| Duplicate groups with conflicting queue labels | **0** |

- Since 9,026 rows form 4,513 groups, **every duplicate group is a pair**.
- No row is fully identical across all 16 columns, so each pair has the same text but differs in another field (for example `answer`, `priority`, `tags`, or `version`).
- The pairs never disagree on `queue`, so duplicates don't add label noise. Duplicates are an integrity issue to handle when cleaning (Lesson 3), after normalizing the text so near-identical copies are also caught.

### 2.10 Additional context fields (English)

**priority**
| Value | Count | % |
|---|---|---|
| medium | 11,570 | 40.94% |
| high | 10,917 | 38.63% |
| low | 5,774 | 20.43% |

**type**
| Value | Count | % |
|---|---|---|
| Incident | 11,213 | 39.68% |
| Request | 8,163 | 28.88% |
| Problem | 5,895 | 20.86% |
| Change | 2,990 | 10.58% |

**version**
| Value | Count | % |
|---|---|---|
| *(missing)* | 11,923 | 42.19% |
| 400.0 | 10,441 | 36.94% |
| 52.0 | 5,346 | 18.92% |
| 51.0 | 551 | 1.95% |

`version` isn't constant. It has three values plus a large missing share. Its meaning isn't documented in the data; it may indicate the dataset release a ticket came from, which should be checked against the dataset card. It isn't used as a feature.

**Tags (tag_1 – tag_8)**: multi-label topic keywords, stored left-to-right in fixed columns.
| Column | Filled | Missing | Fill % | Missing % |
|---|---|---|---|---|
| tag_1 | 28,261 | 0 | 100.00 | 0.00 |
| tag_2 | 28,245 | 16 | 99.94 | 0.06 |
| tag_3 | 28,148 | 113 | 99.60 | 0.40 |
| tag_4 | 25,677 | 2,584 | 90.86 | 9.14 |
| tag_5 | 16,301 | 11,960 | 57.68 | 42.32 |
| tag_6 | 7,908 | 20,353 | 27.98 | 72.02 |
| tag_7 | 3,699 | 24,562 | 13.09 | 86.91 |
| tag_8 | 1,608 | 26,653 | 5.69 | 94.31 |

- Tickets with zero tags: **0**. Tickets with position gaps: **0**.
- **The missingness is structural, not data loss.** Each ticket has a variable-length list of 1–8 tags, filled left-to-right, so later columns are empty when a ticket has fewer tags.
- Tags per ticket: 1 → 16 · 2 → 97 · 3 → 2,471 · **4 → 9,376 (33.2%)** · 5 → 8,393 (29.7%) · 6 → 4,209 · 7 → 2,091 · 8 → 1,608. The median is 5, and 99.6% of tickets have 3 or more tags.
- Tag position means order in the list, not importance. If agents assign tags after triage, they would not be available at intake, which is a potential leakage risk like `answer`.

---

## 3. 20-record inspection (Task 2.1)

**Selection method:** English records are shuffled with `random_state=42`, then selected round-robin by queue, taking turns across the 10 queues (one ticket from each, then a second from each). This gives **2 tickets per queue, 20 in total**, so small queues are represented equally with large ones. Because of this, the counts below describe this stratified sample of 20 only, not the whole dataset.

**Columns recorded:** `label_fits_text` (Y / N / Unclear), `issues` (short tags), `notes`. All notes were checked against the full subject, body, and answer text.

| record_id | Queue | Pri | Type | Fits? | Issues | Notes |
|---|---|---|---|---|---|---|
| tb_9f7be6738bab | Product Support | low | Change | Y | missing-subject | Request to update integration settings for device compatibility; Product Support fits. |
| tb_84b7d3d09f08 | Technical Support | high | Incident | Y | very-short, placeholder | Data breach from weak encryption; queue and priority fit. The body is only 8 words; the answer uses `<tel_num>` and `<acc_num>`. |
| tb_b53536bbb13a | Customer Service | low | Incident | Unclear | ambiguous-queue | Website traffic drop, possibly an SEO or technical cause; Technical Support could fit better. |
| tb_8036c45b7fa8 | IT Support | medium | Request | Y | — | Asks for BigCommerce–ClickUp integration instructions; IT Support fits. |
| tb_c2a1c0ab7224 | Returns and Exchanges | low | Request | N | label-mismatch, placeholder | Asks about investment and analytics services, a Sales/Pre-Sales topic, not returns. |
| tb_76e20cb17e4f | Sales and Pre-Sales | low | Problem | N | label-mismatch, missing-subject, very-short | SaaS integration problem; the agent's own answer escalates it to the technical team. |
| tb_8b3e787035fe | Billing and Payments | medium | Change | N | label-mismatch, priority-mismatch | Asks for stronger medical-data encryption, a security topic; the body demands "immediate action" but priority is medium. |
| tb_0c13eadd7198 | Human Resources | low | Incident | N | label-mismatch, missing-subject, placeholder, synthetic-oddity | WhatsApp Desktop connectivity "on a monitor" is an IT issue, not HR, and the device pairing is odd. |
| tb_8f26980acef2 | Service Outages and Maintenance | low | Incident | Y | placeholder | Sporadic outages, already mitigated, so low priority is defensible. The answer opens "`<name>` acknowledges…". |
| tb_57dbdac5ce03 | General Inquiry | high | Incident | N | label-mismatch, placeholder | An active medical-data breach needing immediate help, routed to General Inquiry. |
| tb_f27f1d924928 | Technical Support | medium | Problem | Y | missing-subject | Integration problems after an update (PowerDirector, DaVinci, Asana); the queue fits. |
| tb_efdfac0dc865 | Customer Service | high | Request | Unclear | priority-mismatch | A pre-sales-style question about Alteryx features; high priority for an information request is odd. |
| tb_a9eae478e2fd | Returns and Exchanges | high | Change | N | label-mismatch, placeholder | A request to improve investment analysis tools, a product or feature topic, not returns. |
| tb_6a8950b24ad7 | Product Support | medium | Problem | Unclear | ambiguous-queue, placeholder | Asks for marketing-strategy help; no queue fits well. The answer has `<acc_num>`. |
| tb_07cceb5cc5bc | Billing and Payments | low | Problem | Y | — | Patient billing discrepancies after a database migration; Billing fits. |
| tb_7fc4dae109d3 | IT Support | high | Incident | Y | — | Figma and Zapier inaccessible, disrupting workflows; the queue and priority fit. |
| tb_2a0b2b37e0c6 | Sales and Pre-Sales | high | Problem | N | label-mismatch, missing-subject, placeholder | Tasks vanishing from a dashboard (MongoDB/Chef), a technical issue misrouted to Sales. |
| tb_8e966b2c47de | Service Outages and Maintenance | high | Incident | Y | html, placeholder | Outage affecting ad performance; the queue fits. The body has `<br><br>`, and the answer uses `[Name]`. |
| tb_2f5e89e8c7a8 | Human Resources | low | Request | N | label-mismatch, placeholder, escaped-newline | Security and HIPAA advice for medical scanners isn't HR. The answer contains a literal `\n\n`. |
| tb_3b1b360a8838 | General Inquiry | low | Incident | Unclear | type-mismatch, priority-mismatch, placeholder | A marketing-strategy request typed as Incident; the subject says "urgently" but priority is low. |

### Inspection summary
- **Label problems in this stratified sample of 20:** 8 labels fit, 8 clearly don't, and 4 are unclear. The misroutes follow a pattern: security and medical-data tickets are sent to Billing, HR, or General Inquiry, technical problems to Sales, and investment topics to Returns.
- **The text looks synthetic or templated:** there's formulaic phrasing, recurring domains (medical data, investment analytics, marketing), and odd pairings (a WhatsApp Desktop connectivity problem "on a monitor").
- **Answers are anonymized with placeholders** (`<name>`, `<tel_num>`, `<acc_num>`, and also `[Name]`), which is another reason to keep `answer` out of the features.
- **`type` and `priority` are sometimes inconsistent with the text** (an "urgent" request marked low, "immediate action" marked medium, a strategy request typed as Incident).
- **Missing subjects:** 5 of 20 in this stratified sample (12.88% of all English tickets). There are minor artifacts (HTML `<br>` in one body, a literal `\n` in one answer).

---

## 4. Key takeaways for later tasks
1. Use the **28,261 English records**; `ticket_text = subject + body`; the label is `queue` (10 classes).
2. **Handle class imbalance** (about 20:1) with a stratified train/test split so every queue appears in both sets.
3. **Expect label noise to limit accuracy** (8 of 20 labels didn't fit in the stratified sample, which is not a dataset-wide rate), and consider dropping the ≤ 5-word tickets as errors.
4. **Keep `answer` out of the features**, and treat tags, priority, and type cautiously: they may be assigned after triage, and they're noisy.


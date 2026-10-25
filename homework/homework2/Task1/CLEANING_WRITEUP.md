# Task 1 – Cleaning Writeup

## Overview

| Item | Value |
|---|---|
| Input | `support_tickets.csv`: 29,651 rows, read-only, never overwritten |
| Output | `support_tickets_cleaned.csv`: 29,651 rows, identical `ticket_id` values |
| Code | `clean_support_tickets.py` (script version of the analysis notebook; same 10 decisions, same rules, same order) |
| Libraries | `pandas`, `re`, `ast` only, with no text-cleaning libraries |
| Approach | Every change is made to a working copy (`clean_df`). The raw data (`df`) stays in memory as the reference for detection and validation. |
| Order of text changes | HTML tags → whitespace → punctuation spacing |
| Fields never modified | `ticket_id`, `Department`, `Priority` (asserted in code) |

## Summary of decisions

| # | Decision | Action | Records affected | Representative ticket_ids |
|---|---|---|---:|---|
| 1 | Duplicate tags within a ticket | Changed | 41 | 95, 786, 1326, 1418, 2878 |
| 2 | Missing `Body` | Retained | 1 | 28902 |
| 3 | HTML tags in `Body` | Changed | 987 | 630, 633, 795, 796, 914 |
| 4 | Irregular whitespace in `Body` | Changed | 922 | 630, 795, 957, 963, 1057 |
| 5 | Missing space after punctuation | Changed | 1,924 | 1, 2, 3, 4, 5 |
| 6 | Structured (JSON / quoted) bodies | Retained (deferred) | 8 | 28787, 28919, 29189, 29269, 29355 |
| 7 | Anonymization placeholders | Retained | 607 | 14221, 17115, 17855, 21343, 26226 |
| 8 | Repeated `Body` text | Retained (handled in Task 2) | 9,190 | 2761, 5901, 5903, 5912, 5913 |
| 9 | `Priority` validity | Checked, no change | 0 | n/a |
| 10 | `Department` validity | Checked, no change | 0 | n/a |

---

## 1. Duplicate tags within a ticket

- **Issue:** Some tickets list the same tag more than once, e.g. `[Security, IT, Security, ...]`.
- **Why it is an issue:** Repeated tags are redundant and inflate tag-frequency counts in any analysis of the metadata.
- **How it was addressed:** `Tags` was parsed from its serialized string into a list with `ast.literal_eval`. Repeats were removed with `dict.fromkeys`, which keeps the first occurrence and the original order. The list was serialized back with `repr()` before saving. Verified: 0 duplicate-tag tickets remain.
- **Records affected:** 41
- **Representative ticket_ids:** 95, 786, 1326, 1418, 2878, 3036, 3427, 4741, 16484, 16718
- **Risk / limitation:** It assumes the repetition was accidental; if it signalled emphasis, that is lost. Near-duplicate tags such as `IT` and `IT Support` are not merged. `Tags` is not a model input, so the change affects analysis only.

## 2. Missing `Body`

- **Issue:** A ticket has no body text.
- **Why it is an issue:** `Body` is the only model input, so this ticket provides no text for routing, and scikit-learn rejects missing documents.
- **How it was addressed:** Retained unchanged, neither dropped nor imputed, so every `ticket_id` stays in the dataset and the split manifest. A body that became empty during cleaning would also be set to missing; none did. Preprocessing converts missing bodies to an empty string.
- **Records affected:** 1 (0 additional bodies became empty during cleaning)
- **Representative ticket_ids:** 28902
- **Risk / limitation:** The model has no text signal for this ticket; its prediction depends only on the model's intercept terms, so it will likely be misrouted.

## 3. HTML tags in `Body`

- **Issue:** Some bodies contain HTML markup from the source system, e.g. `... last night. <br><br>I am ...`.
- **Why it is an issue:** Markup is formatting, not content. It glues words together (`night.<br><br>I`) and adds meaningless tokens such as `br` to the vocabulary.
- **How it was addressed:** Every tag-like pattern (`</?[A-Za-z][^<>]{0,50}>`) was replaced with a space. The pattern requires a letter after `<`, so comparisons such as `x < 5 > 3` are left alone. The extra spaces are removed in Decision 4. Verified: 0 tickets with HTML tags remain.
- **Records affected:** 987
- **Representative ticket_ids:** 630, 633, 795, 796, 914, 957, 963, 1057, 1068, 1154
- **Risk / limitation:** Line-break structure is lost. HTML entities such as `&nbsp;` are not decoded. A ticket that legitimately discusses HTML (e.g. "the `<div>` won't render") would lose that tag.

## 4. Irregular whitespace in `Body`

- **Issue:** Leading or trailing spaces, line breaks, and repeated spaces inside the text, e.g. `"Dear Customer Support,  I am submitting ..."` (two spaces). This includes the gaps left where HTML tags were removed.
- **Why it is an issue:** Texts that differ only in spacing are treated as different strings, which hides duplicates and adds noise.
- **How it was addressed:** Every whitespace run was collapsed to one space and the ends were stripped. A body that became empty would be set to missing; none did. Verified: 0 whitespace issues remain.
- **Records affected:** 922 after HTML removal, of which 45 already had irregular whitespace in the original text and the rest came from the gaps left by removed tags.
- **Representative ticket_ids:** 630, 795, 957, 963, 1057, 1068, 1154, 1168, 1182, 1236
- **Risk / limitation:** Paragraph and line-break structure is lost. It is unused by a bag-of-words baseline but could matter for layout-aware models.

## 5. Missing space after punctuation

- **Issue:** Punctuation immediately followed by a capital letter, e.g. `Team,I` or `persists.Could`.
- **Why it is an issue:** Words and sentences run together, making the text inconsistent and affecting tokenization during modeling.
- **How it was addressed:** One space was inserted after `,` `.` `!` `?` when it is immediately followed by an uppercase letter. This step runs after the HTML and whitespace steps. The count is measured on the original text. Verified: 0 tickets still match the pattern.
- **Records affected:** 1,924
- **Representative ticket_ids:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Risk / limitation:** Legitimate patterns can be changed, e.g. acronyms (`U.S.A` becomes `U. S. A`) or names such as `Node.JS`. Restricting the rule to uppercase letters reduces this risk but does not eliminate it.

## 6. Structured (JSON / quoted) bodies

- **Issue:** Some bodies are JSON objects or are wrapped in quotation marks, e.g. `{"greeting": "Dear Customer Support,", "body": "..."}`.
- **Why it is an issue:** Field names such as `greeting`, `customer_support`, and `closing`, plus JSON punctuation, are not part of the customer's message and add noise tokens.
- **How it was addressed:** Retained unchanged and counted. The customer's words are still present inside the structure, and reliably parsing the mixed formats is out of scope for a baseline. **Deferred** to Homework 3 if error analysis shows these tickets are misrouted.
- **Records affected:** 8 (4 JSON-like, 4 quoted)
- **Representative ticket_ids:** 28787, 28919, 29189, 29269, 29355, 29468, 29564, 29634
- **Risk / limitation:** Field names may become spurious features, although with only 8 records the effect is small. A body that merely starts with a quotation is counted as structured, and malformed JSON such as ticket 29269 (`{"name" has reported ...}`) is counted but not parsed.

## 7. Anonymization placeholders

- **Issue:** Personal details are masked with placeholder tokens such as `acc_num`, `order_num`, `tel_num`, and `email_address`.
- **Why it is an issue:** These are not real words. They could be mistaken for content, and some (e.g. `order_num`) may correlate with particular departments.
- **How it was addressed:** Retained unchanged and counted. The masking is intentional privacy protection, real values must not be invented, and a placeholder can carry useful signal (e.g. "the customer has an order number").
- **Records affected:** 607 tickets contain at least one placeholder. By token: `tel_num` 471, `acc_num` 361, `order_num` 28, `email_address` 20. A ticket can contain several, so these sum to more than 607.
- **Representative ticket_ids:** 14221, 17115, 17855, 21343, 26226, 28265, 28267, 28268, 28270, 28272
- **Risk / limitation:** The model may over-rely on placeholder tokens. Other placeholder styles are not counted: the token `name` (ambiguous with the ordinary word) and bracketed forms such as `[Your Name]` and `[name]`. Some of the bracketed examples (14221, 17115, 21343) read like agent reply templates rather than customer tickets, which may be a further data-quality issue worth investigating in Homework 3.

## 8. Repeated `Body` text

- **Issue:** The same cleaned body text appears on more than one ticket. 9 of these texts are labelled with more than one department, covering 20 tickets (e.g. "Assistance Required" appears under Billing and Payments, Product Support, and Technical Support).
- **Why it is an issue:** Copies placed in different splits leak evaluation text into training and inflate scores. Identical text with different labels is label noise.
- **How it was addressed:** Retained. Each row is a separate historical ticket, and identical text (often a short template message) does not prove a duplicate record. Labels were not changed. The check runs on the fully cleaned text; the HTML and whitespace steps did not change the count. Leakage is handled in Task 2, which assigns all tickets with the same text to the same split.
- **Records affected:** 9,190 (9 texts with conflicting labels, covering 20 tickets)
- **Representative ticket_ids:** 2761, 5901, 5903, 5912, 5913, 5916, 5917, 5919, 5923, 5925. Conflicting labels: 9070, 21596, 5928, 19516, 20207, 7516, 9520, 17884, 16490, 6809
- **Risk / limitation:** Duplicates get extra weight in training. The 20 tickets whose identical text carries different departments cannot all be predicted correctly by any text-only model, which caps achievable accuracy. Texts that differ only in capitalisation (`Seeking Assistance` vs `Seeking assistance`) are not counted by this exact-match check.Task 2 groups bodies case-insensitively, so these near-identical texts are still kept in the same split.

## 9. `Priority` validity

- **Issue checked:** Missing values, or values outside `low`, `medium`, `high`.
- **Why it is an issue:** Inconsistent categories (e.g. `High` vs `high`) would split one category into several and distort any analysis of priority.
- **How it was addressed:** Checked only; no change was needed.
- **Records affected:** 0
- **Representative ticket_ids:** n/a
- **Risk / limitation:** This validates format only, not whether each ticket was given the semantically correct priority. The valid set is hard-coded.

## 10. `Department` validity

- **Issue checked:** Missing labels, or labels outside the 10 documented departments.
- **Why it is an issue:** `Department` is the prediction target, so a missing, misspelled, or unexpected label would create a spurious class or an unusable training record.
- **How it was addressed:** Checked only; no change was needed.
- **Records affected:** 0
- **Representative ticket_ids:** n/a
- **Risk / limitation:** This validates label membership only, not whether each ticket was routed correctly (see the conflicting labels in Decision 8). A legitimate new department would be flagged.

---

## Final validation (asserted in code)

- Row count unchanged: 29,651 → 29,651
- `ticket_id` values identical to the source, unique, and non-null
- `Department` and `Priority` identical to the source
- 0 duplicate-tag tickets, 0 HTML tags, 0 whitespace issues, and 0 punctuation-spacing issues remain in the final text
- Missing values in the cleaned dataset: `Body` = 1 (ticket 28902); all other columns 0

# Task 1 – Dataset Comparison and Selection

#  Candidate datasets

 | Dataset | Source URL | Version / retrieved | License | Ticket text | Routing label | Optional context | Usable records |
|---|---|---|---|---|---|---|---|
| Tobi-Bueck Customer Support Tickets | https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets | HF commit `ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb`; retrieved 2026-09-27 | CC BY-NC 4.0 (non-commercial; educational analysis allowed) | `subject` + `body` | `queue` (10 English values) | `priority`, `type`, `tag_1`–`tag_8` | 28,261 English (of 61,765) |
| IT Service Ticket Classification | https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset | Kaggle version 1 (SHA-256 `044fdace33fa564e1e60453f2941dafc95539c99878b0d32746950394b9dd4d4`); retrieved 2026-09-27 | CC0 1.0 (free Kaggle account needed to download) | `Document` | `Topic_group` (8 values) | None | 47,837 |
| Bitext Customer Support | https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset | HF commit `430d1a89bd93bd1fa23c16f29dd53e73f0087443`; retrieved 2026-09-27 | CDLA-Sharing 1.0 | `instruction` | `category` (11 values) | `intent`, `flags` | 26,872 |

# SELECTION

I selected the **Tobi-Bueck Customer Support Tickets** dataset because it is the only candidate whose target has an explicit routing decision: `queue` records the department a ticket is sent to, which directly matches the intended task. It also has the most useful arrival-time context (priority, type, tags), and its CC BY-NC 4.0 license permits educational analysis. Its limitations are that it is synthetic, bilingual (only English rows are used), and has more distinct queue values than documented. The IT Service Ticket dataset has team-like labels but no context fields, and Bitext contains short chatbot requests rather than support tickets.

*Selection was based on dataset cards and field inspection, before any profiling.*

## Notes
- Field names, types, and cardinalities: see the profile in `../../task2/profile_report.md`.
- The Tobi-Bueck raw parquet used in Tasks 2-3 is in `../../task2/tobibueck_dataset/`. To recreate the other raw downloads, see `../datasets/README.md` and the pinned versions in `../datasets/manifest.json`.
- Attribution: `../datasets/<name>/SOURCE.md`.






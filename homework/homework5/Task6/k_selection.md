# Homework 5, Task 6: Selected k and Rationale

## Selection

| Setting | Value |
|---|---|
| **k** (chunks retrieved per ticket) | **5** |
| **Distance cut-off** | keep a chunk only if its cosine distance is **≤ 0.21** |
| Query | the unaltered ticket `Body` (`VectorStore.query(body, top_k=5)`) |

Both settings are in `summarize_ticket_rag.py` (`K`, `MAX_DISTANCE`).

## Why k = 5 (from the Task 5 results)

| k | Mean Precision@k | Mean Recall@k | Mean NDCG@k |
|---|---|---|---|
| 3 | 0.600 | 0.399 | 0.765 |
| **5** | **0.560** | **0.643** | **0.758** |
| 10 | 0.440 | 1.000* | 0.876 |

*Recall@10 is 1.0 by construction (only the top 10 were labeled), so it is not evidence for k = 10.

- **k = 5 keeps most of the useful material without much extra noise.** Going from k = 3 to k = 5 raises recall from 0.40 to 0.64 while precision only drops from 0.60 to 0.56, and NDCG stays the same (0.765 → 0.758). Several tickets need two kinds of information (Q002, Q004 in Task 5; 29206 here needs both the priority and the workflow article), and k = 3 is often filled by one article.
- **k = 10 adds more noise than help.** Precision falls to 0.44, so more than half of the inserted context would be irrelevant. The local model is small (qwen2.5 1.5B), and irrelevant context is more likely to confuse it than help it; ten chunks would also roughly double the prompt length.

## Why a distance cut-off of 0.21

Task 5 showed that `query()` always returns k results, even for an out-of-scope query (Q005). Task 7 includes an **unsupported** ticket (28921, HR-system redesign), which has no matching article, so the context needs a relevance cut-off as well as a count.

**The Task 5 cut-off (0.35) does not transfer.** Task 5 used short evaluation queries; Task 6 queries with whole ticket bodies, which produce smaller distances overall (0.11–0.29 here vs. 0.17–0.39 in Task 5). A 0.35 cut-off would remove nothing. The cut-off was therefore chosen from the distances of the ticket bodies themselves (`check_distances.py`):

| Ticket | Case | Top-5 distance range | Articles retrieved |
|---|---|---|---|
| 29206 | supported (multi-source) | 0.114 – 0.142 | Jira custom priorities + Jira workflow |
| 28907 | supported | 0.144 – 0.169 | AWS billing review + adjustments |
| 28571 | supported | 0.142 – 0.183 | Cisco ISR4331 specs / firmware |
| 28763 | supported | 0.115 – 0.197 | Samsung flicker troubleshooting (+1 audio chunk) |
| **28921** | **unsupported** | **0.222** – 0.267 | Dashboard intake, IT consulting (not HR systems) |

The farthest top-5 chunk of any supported ticket is **0.197**; the closest chunk for the unsupported ticket is **0.222**. **0.21** sits in the middle of that gap, so:
- supported tickets keep all 5 chunks;
- 28921 keeps none, and the prompt receives "No relevant reference articles were found." instead of dashboard and consulting text that would invite ungrounded content.

The cut-off is based on five tickets, so it is a starting value, not a tuned one; it would need re-checking on more tickets.

## Known limitations

- **One article fills the top 5.** For 28763, all four flicker-troubleshooting sections rank 1–4, so the warranty and technician article (ranks 7 and 10) is not in the context even though the ticket asks about warranty coverage. This is the same clustering pattern found in Task 5. Capping chunks per article would address it, but that retrieval change was not evaluated in Task 5, so it is not applied here.
- **Same product, different issue.** 28763's 5th chunk is from the QN90A audio article (distance 0.197, under the cut-off). The prompt instructs the model to ignore articles that do not match the ticket's product and issue.

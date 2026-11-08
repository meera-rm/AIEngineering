# Homework 5, Task 5: Retrieval Evaluation Report

## 1. Setup

Each of the 5 evaluation queries was run against the Task 4 vector store with `top_k=10` (`run_queries.py`), and all 50 results were labeled by hand in `retrieval_results.csv`. Metrics are computed by `compute_metrics.py` at k = 3, 5 and 10.

**Labeling rule.** A chunk is relevant (1) if its `content` contains information that helps address at least one part of the query (the assignment's definition). Each query was first broken into the needs an answer must cover, then every chunk was checked against those needs. One consistency rule was applied to borderline cases: **a Limits section that only states what its article does not cover is labeled 0** (it gives no usable information and could mislead the generator). Limits sections that do contain actionable guidance (e.g. escalation criteria) were labeled on their content.

| Query | Needs | Relevant in top 10 |
|---|---|---|
| Q001 | Current regional incident status; time of last status update | 3 |
| Q002 | Jira workflow change (new status/transition); notification-scheme change; which are configured separately | 6 |
| Q003 | Change destination on an editable order; expedited availability after the change | 6 |
| Q004 | Safe flicker diagnostics (built-in menus); store-return route vs. manufacturer technician route | 7 |
| Q005 | Enroll a hardware security key for MFA; revoke a lost authenticator | 0 |

## 2. Metrics selected

| Metric | What it measures | Why it was selected |
|---|---|---|
| **Precision@k** | Share of the top k chunks that are relevant | In RAG, the top k chunks go straight into the prompt. Precision@k says how much of that context is useful vs. noise, which matters with a small 1.5B model that is easily distracted. |
| **Recall@k** | Share of a query's relevant chunks that appear in the top k | Shows how much useful material a given k cuts off, i.e. the cost of choosing a smaller k. Needed alongside precision to pick k for Task 6. |
| **NDCG@k** | Whether relevant chunks are ranked near the top (binary gain, log2 discount) | Rewards putting the strongest evidence first. The Class 11 lesson named NDCG as the ranking metric for RAG. |

**Not selected:** Hit rate and MRR. Both only check whether *one* good result appears (or how high the first one is). RAG wants as many relevant chunks as possible in the context, so they would overstate quality (e.g. Q001 has a relevant chunk at rank 2, so hit rate@3 = 1 even though 2 of its top 3 are wrong).

**How averages are computed.** Macro average (each query weighted equally). Q005 has no relevant chunk, so its precision is 0 but recall and NDCG are undefined (nothing to find); those two means are over the 4 answerable queries.

**Recall limitation (pooled judgments).** Only the top 10 results per query were labeled, so the recall denominator is the number of relevant chunks *found in the top 10*. Recall@10 is therefore 1.0 by definition, and recall at every k is an upper bound. Relevant chunks ranked below 10 are invisible to it; see failure pattern 3.

## 3. Results

### Precision@k

| Query | k = 3 | k = 5 | k = 10 |
|---|---|---|---|
| Q001 | 0.333 | 0.400 | 0.300 |
| Q002 | 1.000 | 1.000 | 0.600 |
| Q003 | 0.667 | 0.600 | 0.600 |
| Q004 | 1.000 | 0.800 | 0.700 |
| Q005 | 0.000 | 0.000 | 0.000 |
| **Mean (5 queries)** | **0.600** | **0.560** | **0.440** |

### Recall@k (pooled, upper bound)

| Query | k = 3 | k = 5 | k = 10 |
|---|---|---|---|
| Q001 | 0.333 | 0.667 | 1.000 |
| Q002 | 0.500 | 0.833 | 1.000 |
| Q003 | 0.333 | 0.500 | 1.000 |
| Q004 | 0.429 | 0.571 | 1.000 |
| Q005 | n/a | n/a | n/a |
| **Mean (4 queries)** | **0.399** | **0.643** | **1.000** |

### NDCG@k

| Query | k = 3 | k = 5 | k = 10 |
|---|---|---|---|
| Q001 | 0.296 | 0.478 | 0.645 |
| Q002 | 1.000 | 1.000 | 1.000 |
| Q003 | 0.765 | 0.684 | 0.901 |
| Q004 | 1.000 | 0.869 | 0.958 |
| Q005 | n/a | n/a | n/a |
| **Mean (4 queries)** | **0.765** | **0.758** | **0.876** |

**Reading the results.**
- **Q002 is the strongest query:** its 6 relevant Jira chunks occupy ranks 1–6, so precision@5 and NDCG are perfect.
- **Q004 is strong for the flicker part** (all four flicker-troubleshooting sections at ranks 1–4) but weak for the store-return part (see pattern 3).
- **Q001 is the weakest answerable query:** only 1 of its top 3 is relevant, and its best chunk sits at rank 6 (NDCG@3 = 0.296).
- **Q005 fails completely** because the knowledge base has no article on MFA or security keys.
- **Trade-off across k:** mean precision falls from 0.60 (k=3) to 0.44 (k=10) while recall rises from 0.40 to 1.0. k = 5 keeps precision near its k=3 level (0.56) while recovering most of the relevant material (recall 0.64).

## 4. Failure patterns

**1. One article fills the top ranks.** Section-level chunks from the same article share the title, product and summary prefix in `embedding_text`, and they are about the same subject, so they score alike and arrive together. In Q001, three sections of the 2023 maintenance notice (KB-AWS-MAINT-001) take ranks 1, 3 and 4; in Q003, the address-change article fills 4 of the top 5; in Q004, the four flicker sections take ranks 1–4. When the query has more than one need, this pushes the second need's chunks down or out (Q004's store-return chunks).

**2. Topical look-alikes outrank the right article.** Q001 asks about a *current* regional incident and the *last status update*. The planned-maintenance notice for an event on 18 November 2023 talks about "status refreshes", "updates are posted" and "health-status propagation", so it ranks above the general service-health article whose chunk KB-AWS-NEG-003#02 actually answers the query ("incident state… time of the last published update") at rank 6. Embeddings match vocabulary and topic, not time ("today" vs. a 2023 event). The same effect appears in Q004 (the QN90A *audio* article at ranks 5, 6 and 8) and Q005 ("hardware" pulls in hardware-return chunks; "multifactor" pulls in the password-reset article).

**3. A query's second need is under-retrieved (recall hidden by pooling).** Q004 asks for diagnostics *and* a comparison of the store-return route with technician service. The return-window article's Overview and Policy summary (KB-SAM-NEG-002#01, #02: "Store returns are accepted within 21 calendar days of delivery…") are the most useful chunks for the comparison, yet neither is in the top 10. Only that article's Limits section (rank 10) appears. Because recall is computed over the labeled top 10, Q004's recall@10 still reads 1.0; the true recall is lower. A single query vector averages two needs and leans toward whichever dominates the wording.

**4. "Limits" sections are retrieved for the topic they exclude.** Limits sections name the topics an article does *not* cover, which places them close to queries about exactly those topics. Examples: Q003 ranks 3–4 ("does not authorize shipping-address changes after carrier handoff"), Q001 rank 9 ("not a scheduled-maintenance notice"), Q005 rank 6. They take slots in the top k without adding usable information.

**5. Out-of-scope queries still return k results.** Q005 has no answer in the knowledge base, but `query()` always returns `top_k` chunks. Its distances (0.355–0.391) are the worst of all queries, but nothing marks them as irrelevant; without a cut-off they would be placed in the prompt as context.

## 5. Possible improvements

| # | Improvement | Addresses | How |
|---|---|---|---|
| 1 | **Limit chunks per article** (simple maximal-marginal-relevance) | Patterns 1, 3 | After retrieving the top 10–20, keep at most 2 chunks per `article_id` before taking the final k. Q004 would then free slots for the technician and store-return articles. No rebuild needed. |
| 2 | **Distance threshold** | Pattern 5 | Drop chunks whose cosine distance exceeds a cut-off. On these queries, **0.35 with k = 5** removes all of Q005's results while keeping every top-5 result of Q001–Q004 (their largest top-5 distance is 0.330). The value must be tuned on more queries; relevant chunks in Q003 appear up to 0.360 at lower ranks. |
| 3 | **Query decomposition** | Pattern 3 | Split a multi-need query into sub-queries ("safe flicker diagnostics", "store return window", "technician service"), retrieve for each, and merge the rankings (the multi-query flow from Class 11). |
| 4 | **Hybrid search (keyword + vector)** | Patterns 2, 3 | Keyword search on terms such as "return", "region" or "incident" rescues chunks that the embedding ranks low, and merging scores reduces look-alike matches. |
| 5 | **Metadata-aware re-ranking** | Pattern 2 | Use `topic` and `product` metadata, or a cross-encoder re-ranker, to move the article that matches the query's intent above articles that only share vocabulary (e.g. general health above a dated maintenance notice). |
| 6 | **Chunking adjustments** | Patterns 1, 4 | Add the article summary only to short sections, or merge short Limits sections into the preceding section, so they stop competing as separate chunks. Changes would be tested one at a time against these metrics, as the lesson recommends. |
| 7 | **Fuller relevance judgments** | Recall limitation | Label relevant chunks across the whole corpus (not just the top 10) so recall measures what retrieval actually misses. |

**Implication for Task 6.** k = 5 gives the best balance on these queries (precision 0.56, NDCG 0.76, recall 0.64), and a distance threshold keeps out-of-scope tickets from receiving irrelevant context.

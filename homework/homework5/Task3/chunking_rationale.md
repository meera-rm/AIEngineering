# Homework 5, Task 3: Chunking and Embedding-Text Design

**Code:** `chunk_kb.py` (standard library only) · **Output:** `records.json`

**Run:** `python chunk_kb.py` (reads `../HW5_materials/knowledge_base/`), or `python chunk_kb.py --kb-dir <path to knowledge_base>` if the course materials are elsewhere.

**Result:** 134 chunks from 32 articles; 16–150 words per chunk (mean 62).

## 1. Chunking strategy: one chunk per `##` section

Every article has a front-matter block (`article_id`, `title`, `product`, `topic`, …) followed by 3–5 `##` sections such as *Overview*, *Eligibility*, *What the customer provides*, *Limits*. Each section covers one sub-topic.

**Why section-based chunking:**

- **Each section covers one idea.** A ticket about warranty coverage should retrieve the *Eligibility* section, not a window of text that happens to start halfway through *Symptoms*. When a chunk follows the author's own section boundaries, it never cuts a rule or list in half.
- **Size fits the model.** Sections run 16–150 words (about 20–200 tokens). `bge-small-en-v1.5` accepts up to 512 tokens, so no section is truncated, and each chunk is focused enough that one off-topic sentence doesn't dilute its vector.
- **It's deterministic.** Files are processed in sorted filename order, splitting uses a fixed rule (a line starting with `## `), and there's no randomness or timestamps. Running the script twice produces byte-identical `records.json`.
- **Safety cap.** If a future section exceeded 300 words, it would be split at blank lines into pieces of at most 300 words. No section in the current corpus triggers this.

**Alternatives considered:**

| Option | Why not chosen |
|---|---|
| Whole article as one chunk (32 chunks) | One vector would mix symptoms, eligibility and limits. A ticket about one sub-topic would match the whole article loosely, and Task 6 would put irrelevant text into the prompt. |
| Fixed-size windows (e.g. 100 words, 20 overlap) | Ignores section boundaries, so it can cut a rule mid-sentence and produce chunks that start without context. The overlap also creates near-duplicate results that use up top-k slots. |
| Paragraph-level | Many paragraphs are 1–2 sentences, too small to carry enough meaning. Retrieval would return fragments without their surrounding rule. |

**Trade-off to watch in Task 5:** some closing sections are short (for example a 16-word *Limits* section). Their vectors may be weaker. The article context added to `embedding_text` (below) is meant to offset that.

## 2. Chunk ID: `{article_id}#{position:02d}`

Example: `KB-AWS-BILL-002#02` is the 2nd section of article `KB-AWS-BILL-002`.

- **Unique:** article IDs are unique, and positions are unique within an article. The script raises an error if a duplicate ID appears.
- **Stable:** built only from the article's own ID and the section's position. It doesn't depend on file order, run time, or a random UUID, so the same article always gives the same IDs.
- **Readable:** you can see which article a retrieved chunk came from without looking anything up, which helps when labeling results in Task 5.

## 3. `embedding_text`: document-level context + section text

```text
Title: AWS Management Service Adjustment and Discount Eligibility
Product: AWS Management Service
Article summary: This article explains when support may recommend a billing adjustment, service credit, or discount review after an AWS Management Service statement has been examined.
Section: Adjustment eligibility

An adjustment may be considered when support confirms one of three conditions: ...
```

This follows the Class 11 RAG walkthrough: chunk by section headers, and embed the document-level information (title and summary) into every chunk, because "information that applies to every chunk can be included in every chunk."

- **Why add title and product:** a section like *Limits* or *Eligibility* often never names the product. Without the prefix, its vector says nothing about "Samsung TV" vs. "Canon printer", so a ticket about a QN90A could retrieve the printer's *Eligibility* section. The prefix ties every chunk to its product.
- **Why add an article summary:** the title names the topic, and the summary says *when the article applies* (e.g. "Use this article when a customer wants to change the delivery address on an existing hardware order"). That's close to how tickets describe their problem, so it helps a section match the right ticket even when the section itself only lists rules.
- **Where the summary comes from:** the articles have no separate summary field, but every article opens with a sentence describing what it covers. The summary is the **first sentence of the article's first section**, extracted with a fixed rule, so it stays deterministic.
- **Not repeated in chunk 1:** the first section already contains that sentence, so chunk 1 gets only title, product and section.
- **Trade-off:** sharing the same summary makes chunks from one article more alike, which could blur the ranking *between* sections of the same article. The summary is limited to one sentence so the section text still dominates each vector. Task 5 will show whether same-article sections crowd out other articles.
- **Why not include everything:** `article_id`, `topic` slugs, `version` and `corpus_version` aren't natural language that appears in tickets, so they would only add noise to the vector. They're kept in `metadata` instead.
- **Why the `## ` marker is dropped:** markdown symbols carry no meaning for the embedding model. The heading text is kept as `Section: …`.
- **Size check:** longest chunk is 150 words + about 45 words of prefix, still well under the model's 512-token limit.
- **No query prefix:** `VectorStore.query()` uses FastEmbed's `query_embed`, which adds the BGE query instruction automatically. Passages are embedded as plain text, which is the intended BGE setup.
- **Line endings** are normalized to `\n` here, because `embedding_text` is constructed rather than source text.

## 4. `content`: the unmodified source text

`content` is the exact slice of the article file from the section's `## ` heading up to the next section, with only the whitespace between sections trimmed. It keeps the files' original CRLF line endings (each file is read with `newline=""`). This is what `VectorStore.query()` returns and what Task 6 will put into the prompt, so it has to be the authoritative source text, not the context-prefixed version.

**Verified:** all 134 `content` values are found character-for-character in their source files.

## 5. `metadata`

| Field | Required? | Purpose |
|---|---|---|
| `article_id` | ✅ | Parent article |
| `title` | ✅ | Parent article title |
| `chunk_position` | ✅ | 1-based section position within the article |
| `chunk_count` | — | Number of chunks in the article, so `2 of 5` is clear |
| `section_heading` | — | Lets Task 5 labels and Task 6 prompts show which section was retrieved |
| `product`, `topic` | — | Useful for analyzing failure patterns (e.g. right product, wrong topic) and possible metadata filtering |
| `source_file` | — | Traces a chunk back to its file |
| `article_version`, `corpus_version` | — | Records which knowledge-base version the index was built from |

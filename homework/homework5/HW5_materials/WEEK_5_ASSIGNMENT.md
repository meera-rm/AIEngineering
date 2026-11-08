# Homework 5 - Evaluate and Ground the Ticket Assistant

## Goal

Evaluate the ticket summaries created in Homework 4, build and evaluate retrieval
over a support knowledge base, and use retrieved context to improve the existing
ticket summary without changing its task.

Use five specified tickets from Homework 4 with the same accepted prompt, local
model, and generation settings.

## Provided Materials

| File | Purpose |
| --- | --- |
| `knowledge_base/` | Approved support articles with stable article IDs |
| `VectorStore.py` | Embedding, persistent vector storage, and cosine search |
| `vector_store_smoke_tests.py` | End-to-end check of the supplied vector-store interface |
| `VECTOR_STORE_SETUP.md` | Setup guide for the fixed local retrieval stack |
| `evaluation_queries.json` | Five unseen support queries for manual retrieval evaluation |
| `requirements.txt` | Cumulative pinned dependencies through Homework 5 |

Bring forward the final accepted Homework 4 prompt, reusable LLM-call function,
and its saved outputs for the five specified tickets. Continue using each
ticket's unaltered `Body` from the canonical dataset.

Use `qwen2.5:1.5b-instruct-q4_K_M` with `temperature: 0`, `seed: 42`, and
`stream: false` for every generation call. Set `options.num_predict: 512`
for ticket summaries; keep these settings fixed across comparisons.

## Part 1: Evaluate the Homework 4 Ticket Summaries

## Task 1 - Write a Rubric

Write a rubric for evaluating the ticket summaries from Homework 4.

### Requirements

- Use homework 4's observations to define rubric dimensions that
  capture the most important quality aspects of the ticket summaries.

### Deliverables

- Rubric, where each dimension at minimum defines:
  - What it measures.
  - The scoring scale (e.g. yes/no, 0-1, etc.).
  - Criteria for scoring.

## Task 2 - Manually Apply the Rubric

Use your designed rubric to judge the homework 4 outputs, and update the
rubric as needed.

Use these five tickets from homework 4:

| Department | `ticket_id` |
| --- | ---: |
| Billing and Payments | `28907` |
| Human Resources | `28921` |
| Product Support | `28763` |
| Sales and Pre-Sales | `28571` |
| Technical Support | `29206` |

### Requirements

- Manually apply the Task 1 rubric to the five outputs listed above.
- You may edit the rubric while applying it.
- If a rubric edit changes how an earlier output should be scored, re-score it.
- Freeze the rubric after this step so we can fairly compare RAG and no-RAG outputs.

### Deliverables

- Updated rubric.
- Doc containing:
  - Rubric changes and justifications.
  - For each ticket, for each rubric-dimension:
    - Human-generated score.
    - Rationale for why you gave that score.

## Part 2: Build and Evaluate Retrieval

## Task 3 - Prepare the Vector-Store Records

Convert the supplied knowledge-base articles into the records that will be added
to the vector store. Do not generate embeddings or build the vector store yet.

### Requirements

- Implement a deterministic chunking strategy, and explain your selection.
- Give every chunk a stable, unique ID.
- For every chunk, construct:
  - `embedding_text`: the text that will be embedded for retrieval.
  - `content`: the unmodified source chunk text that will be returned after retrieval.
  - `metadata`: at minimum the parent article ID, title, and chunk position.

### Deliverables

- Chunking code.
- Prepared vector-store records.
- Chunking and embedding-text design rationale.

## Task 4 - Build the Vector Store

Use the prepared Task 3 records to build a persistent vector store and a query
interface.

### Requirements

- Follow `VECTOR_STORE_SETUP.md` and use its provided embedding model,
  vector-store library, and cosine similarity.
- Use the supplied `VectorStore.py` to build and query the vector store.

### Deliverables

- Code that constructs and populates the VectorStore class from your prepared Task 3 records.

## Task 5 - Evaluate Retrieval

Evaluate retrieval quality manually using five supplied evaluation queries.

### Requirements

- Use the supplied `evaluation_queries.json` file containing five queries.
- Run each query through the VectorStore to retrieve the top 10 results.
- Label each result as relevant or not-relevant to the query. "Relevant"
  means the result contains information that helps address the query.
- Decide, justify, and compute retrieval metrics. You should test at least 3 `k`'s.
- Analyze retrieval failures and possible improvements.

### Deliverables

- Code for querying the vector store using the supplied queries.
- Labeled retrieval results for all five evaluation queries.
- Code for computing selected metrics.
- Report containing:
  - For each metric:
    - Which metrics you selected.
    - Justification for selecting it.
    - For each `k`-value:
      - Metric value for each query.
      - Metric value across all queries.
  - Failure patterns
  - Possible improvements

## Part 3: Add Retrieval to the Ticket Summary

## Task 6 - Add Retrieved Context to the Homework 4 Prompt

Extend the accepted Homework 4 prompt to include RAG results.

### Requirements

- Select `k` (number of RAG results) based on Task 5, and justify your selection.
- Query the vector store by embedding the unaltered ticket `Body`.
- Insert the RAG results into the prompt, and update the instructions to make use of them.
  Ensure the prompt differentiates between user-input (ticket `Body`) and external context (RAG results).
- Do not alter anything except for getting the RAG results into the prompt.

### Deliverables

- Selected `k` and rationale.
- Updated prompt.
- Updated LLM-call code.

## Task 7 - Check Three RAG-Informed Summaries

Run the RAG-informed interaction on these three representative tickets:

| `ticket_id` | Case |
| --- | --- |
| `28763` | Supported request |
| `29206` | Supported multi-source request |
| `28921` | Unsupported request |

### Requirements

- Apply the RAG-informed prompt to each ticket's unaltered `Body`.
- Manually grade the results using the rubric from Task 2.
- Compare the RAG vs. no-RAG manual grading results.

### Deliverables

- For each ticket:
  - Retrieval results
  - Generated ticket summaries
  - Grading results
  - Comparison with no-RAG output

### Note
- It is perfectly likely that your RAG-informed summaries will not be better than your
  no-RAG summaries due to the weak LLM we're using. The goal is to work through the process,
  not necessarily to produce demonstrable gains.

## Submission Guidelines

- Submit the complete homework as one `.zip` file. Do not submit individual
  files or multiple `.zip` files.
- Name the archive `Firstname_Lastname_HW5.zip`, using the same first and last
  name shown in Google Classroom. For example: `Tanner_Gilligan_HW5.zip`.
- Organize the archive with one folder per task at its root. Each task folder
  should contain that task's deliverables:

  ```text
  Tanner_Gilligan_HW5.zip
  ├── Task1/
  ├── Task2/
  ├── Task3/
  ├── Task4/
  ├── Task5/
  ├── Task6/
  └── Task7/
  ```

- Upload the `.zip` file itself. Do not submit a Google Drive, GitHub, or other
  external link in place of the file.
- Submit data tables as static CSV files, not Excel files or links to Google
  Sheets.
- Submit writeups as `.txt` or `.md` files.
- Do not include duplicate or extraneous files unless they are relevant to
  running or interpreting your submission.








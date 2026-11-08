# Homework 5 Local Vector Store Setup

Homework 5 uses one fixed local retrieval stack:

- **Embedding runtime:** FastEmbed `0.8.0`
- **Embedding model:** `BAAI/bge-small-en-v1.5`
- **Model download repository:** `qdrant/bge-small-en-v1.5-onnx-q`
- **Model revision:** `52398278842ec682c6f32300af41344b1c0b0bb2`
- **Vector store:** LanceDB `0.38.0`
- **Similarity:** cosine

Use these exact packages and model. The embedder runs locally on CPU through ONNX Runtime; it does not require Ollama, a model server, or an API key. The supplied helper resolves the exact revision with Hugging Face Hub, downloading it on first use if it is not cached, then passes that local directory to FastEmbed with
`local_files_only=True`. There is no fallback to FastEmbed's unpinned download. Both index building and querying use these same files.

The default snapshot directory is`~/.cache/huggingface/hub/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots/52398278842ec682c6f32300af41344b1c0b0bb2/`(on Windows, under `%USERPROFILE%\.cache\huggingface\hub`). Hugging Face's
`HF_HOME` or `HF_HUB_CACHE` environment variables can relocate this cache.An already cached snapshot is loaded without a network request.

The Homework 6 reference service imports this same helper. The Homework 7 retrieval Dockerfile downloads the same pinned revision at image build time into`/opt/models/bge-small-en-v1.5/52398278842ec682c6f32300af41344b1c0b0bb2`.
Its query-only helper loads that directory offline; missing files cause an error,not a startup download. `EMBEDDING_MODEL_PATH`, if supplied, must point to a local copy of this exact snapshot.

## 1. Create a Python Environment

From the repository root, create a virtual environment using Python 3.14.7:

```text
python -m venv .venv
```

Activate it:

**PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux**

```bash
source .venv/bin/activate
```

Confirm that the environment uses Python 3.14.7:

```text
python --version
```

## 2. Install the Homework Packages

```text
python -m pip install -r homework/homework5/materials/requirements.txt
```

Confirm the installed versions:

```text
python -m pip show fastembed lancedb
```

The output must report FastEmbed `0.8.0` and LanceDB `0.38.0`.

## 3. Understand the Supplied Vector Store

Homework 5 supplies two files in `homework/homework5/materials/`:

- `VectorStore.py` contains the class used to build and query the vector store.
- `vector_store_smoke_tests.py` checks the class and your local setup.

Import the class rather than interacting with FastEmbed or LanceDB directly:

```python
from VectorStore import VectorStore
```

Create the class with the path where LanceDB should persist its files:

```python
vector_store = VectorStore("homework5_vector_store")
```

The class has two public methods:

- `build(records)` embeds prepared Task 3 records and replaces any existing table.
  Each record must contain a unique `chunk_id` plus `embedding_text`, `content`,
  and `metadata`. Metadata uses ordinary `json.dumps` / `json.loads` semantics,
  including mixed string and numeric keys accepted by JSON serialization.
  Returned object keys are strings and tuples become lists, as in a normal JSON
  roundtrip; existing JSON values retain their semantics.
- `query(ticket_body, top_k=5)` embeds an unaltered ticket `Body` and returns
  ranked chunks with `rank`, `chunk_id`, `distance`, `content`, and `metadata`.

For example:

```python
vector_store.build(prepared_records)
results = vector_store.query(ticket_body, top_k=5)
```

Only `embedding_text` is embedded. The separate `content` value is the
authoritative chunk text returned after retrieval. Returned `distance` values
are cosine distances, so lower values are more similar.

The database persists at the path passed to `VectorStore`. A later process can
create a new instance with the same path and query the existing table without
calling `build()` again. Calling `build()` intentionally replaces the table
rather than appending records. Updating the helper does not rebuild any persisted
index. The revision used for existing vectors is not established by this change;
it does not imply that those vectors are incompatible or have been recalculated.

## 4. Run the Supplied Smoke Tests

From the repository root, run:

```text
python homework/homework5/materials/vector_store_smoke_tests.py
```

The first run downloads the embedding model and may take longer. The tests build
a temporary database, verify semantic retrieval and returned fields, reopen the
persisted database, check input validation, model pinning and mixed-key metadata,
and confirm that rebuilding replaces old records. Temporary test databases live
under the repository's ignored `ai_scratch/` directory and are removed automatically.

Setup is complete only when the command finishes with:

```text
All VectorStore smoke tests passed.
```

## Troubleshooting

- **`No matching distribution found`:** Confirm that the active interpreter is
  Python 3.14.7 and that pip belongs to it with
  `python -m pip --version`.
- **Model download fails:** Confirm internet access and rerun the smoke tests.
  Hugging Face Hub reuses completed files from the pinned snapshot cache above.
  For a fully cached local run, `HF_HUB_OFFLINE=1` prevents network access.
- **Windows symlink warning:** The Hugging Face cache may warn that symlinks are
  unavailable. The model still works; enabling Windows Developer Mode avoids the
  warning and reduces duplicate cached files.
- **Import error for `VectorStore`:** Run the supplied test by its path as shown
  above. Python then includes the materials directory in its import path.

## Verified Reference Environment

This workflow was verified on Windows with:

- Python `3.14.7`
- FastEmbed `0.8.0`
- LanceDB `0.38.0`
- `BAAI/bge-small-en-v1.5` producing 384-dimensional embeddings
- Successful batch embedding, cosine search, metadata return, and persistent
  database reopening

Official documentation:

- [FastEmbed](https://qdrant.github.io/fastembed/)
- [FastEmbed supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/)
- [LanceDB Python API](https://docs.lancedb.com/)
- [BGE Small model card](https://huggingface.co/BAAI/bge-small-en-v1.5)

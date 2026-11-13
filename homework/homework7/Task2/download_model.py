"""Build-time step: download the pinned embedding model into the image cache.

Uses the same repository, revision, and file list as VectorStore.py, so the
runtime (local_files_only=True) finds the files without network access.
"""

from huggingface_hub import snapshot_download

from VectorStore import MODEL_FILES, MODEL_REPOSITORY, MODEL_REVISION

path = snapshot_download(
    repo_id=MODEL_REPOSITORY,
    revision=MODEL_REVISION,
    allow_patterns=MODEL_FILES,
)
print(f"Embedding model cached at {path}")

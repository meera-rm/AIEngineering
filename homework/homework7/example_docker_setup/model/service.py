import torch
from sentence_transformers import SentenceTransformer

# Illustrative placeholders: choose a 384-dimensional model and a fixed revision.
MODEL_ID = "<model-id>"
MODEL_REVISION = "<revision>"


class EmbeddingService:
    def __init__(self):
        self.ready = False
        self._model = None

    def load(self):
        self.ready = False
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required")
        self._model = SentenceTransformer(
            MODEL_ID, revision=MODEL_REVISION, device="cuda"
        )
        if self._model.get_sentence_embedding_dimension() != 384:
            raise RuntimeError("Model embedding dimension must be 384")
        self._model.encode(["warmup"], normalize_embeddings=True)
        self.ready = True

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.ready:
            raise RuntimeError("Embedding model is not ready")
        return self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        ).tolist()

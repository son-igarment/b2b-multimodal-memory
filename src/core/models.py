from __future__ import annotations

from typing import List
import numpy as np

from .config import settings


def _random_embed(texts: List[str]) -> np.ndarray:
    rng = np.random.default_rng(seed=42)
    return rng.normal(size=(len(texts), settings.vector_dim)).astype(np.float32)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if len(texts) == 0:
        return []
    provider: str = settings.embedding_provider.lower()
    if provider == "random":
        vectors = _random_embed(texts)
        return [v.tolist() for v in vectors]
    if provider == "sentence":
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as err:
            raise RuntimeError(
                "sentence-transformers not installed. Install and retry."
            ) from err
        model = SentenceTransformer(settings.embedding_model_name)
        vectors = model.encode(texts, normalize_embeddings=True)
        return vectors.astype(np.float32).tolist()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")



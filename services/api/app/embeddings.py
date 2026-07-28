import hashlib
import math
import re
from abc import ABC, abstractmethod

from .config import get_settings

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]+")


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """Feature-hashing embeddings: stable, dependency-free, and useful for the demo corpus."""

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension or get_settings().embedding_dimension

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = TOKEN_RE.findall(text.lower())
        features = tokens + [f"{a}:{b}" for a, b in zip(tokens, tokens[1:], strict=False)]
        for feature in features:
            digest = hashlib.sha256(feature.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * (1.5 if ":" in feature else 1.0)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [round(value / norm, 8) for value in vector]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.engram_mode == "live":
        from .bedrock import BedrockEmbeddingProvider

        return BedrockEmbeddingProvider()
    return DeterministicEmbeddingProvider()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimension mismatch")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(-1.0, min(1.0, dot / (left_norm * right_norm)))

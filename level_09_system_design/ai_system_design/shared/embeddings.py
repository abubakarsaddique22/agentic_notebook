"""
Shared embeddings helper
========================

Do embedders:
  1. OllamaEmbedder : real semantic embeddings (local, free). Default model: nomic-embed-text
                      Setup: `ollama pull nomic-embed-text`
  2. HashingEmbedder: OFFLINE fallback. Words + character n-grams ko hash karke vector banata hai.
                      Semantic nahi hai (sirf lafzon ki milawat pakadta hai), lekin bina kisi
                      model/internet ke chalta hai, taake scripts hamesha run ho sakein.

`get_embedder()` pehle Ollama try karta hai; na mile to fallback par chala jata hai aur
saaf batata hai. Production mein HAMESHA real embedding model use karein.

Env vars (optional):
    OLLAMA_BASE_URL     default http://localhost:11434
    OLLAMA_EMBED_MODEL  default nomic-embed-text
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    name: str

    def __call__(self, texts: Sequence[str]) -> np.ndarray: ...


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


class HashingEmbedder:
    """Offline, deterministic, NOT semantic. Sirf demo / tests ke liye."""

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim
        self.name = f"hashing-{dim} (offline fallback, not semantic)"

    def _features(self, text: str) -> list[str]:
        text = text.lower()
        words = re.findall(r"[a-z0-9#]+", text)
        feats = [f"w:{w}" for w in words]
        for w in words:
            padded = f" {w} "
            feats += [f"c:{padded[i:i + 4]}" for i in range(max(1, len(padded) - 3))]
        return feats

    def __call__(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for f in self._features(text):
                h = int(hashlib.md5(f.encode()).hexdigest(), 16)
                out[row, h % self.dim] += 1.0 if (h >> 1) % 2 else -1.0
        return _normalize(out)


class OllamaEmbedder:
    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        import ollama  # lazy import

        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.client = ollama.Client(host=host or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        self.name = f"ollama/{self.model}"

    def __call__(self, texts: Sequence[str]) -> np.ndarray:
        resp = self.client.embed(model=self.model, input=list(texts))
        return _normalize(np.asarray(resp.embeddings, dtype=np.float32))


def get_embedder(prefer: str = "ollama", verbose: bool = True) -> Embedder:
    """prefer='ollama' -> try Ollama, fallback to hashing. prefer='offline' -> hashing directly."""
    if prefer == "ollama":
        try:
            emb = OllamaEmbedder()
            emb(["ping"])  # connection + model check
            if verbose:
                print(f"[embeddings] using {emb.name}")
            return emb
        except Exception as exc:  # noqa: BLE001
            if verbose:
                print(f"[embeddings] Ollama not available ({type(exc).__name__}). "
                      f"Falling back to OFFLINE hashing embedder.\n"
                      f"             Real results ke liye: Ollama chalu karein aur "
                      f"`ollama pull nomic-embed-text` karein.")
    emb = HashingEmbedder()
    if verbose:
        print(f"[embeddings] using {emb.name}")
    return emb


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Dono vectors pehle se normalized hon to dot product = cosine similarity."""
    return float(np.dot(a, b))


def approx_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token (English). Budgeting ke liye kaafi hai."""
    return max(1, len(text) // 4)

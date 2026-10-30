"""Pure RAG helpers: markdown chunking, similarity, index metadata."""
import hashlib
import math
from pathlib import Path


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunk_markdown(text: str, chunk_words: int = 85, overlap: int = 18) -> list[dict]:
    """Simple word-based chunks; keep some overlap between adjacent chunks."""
    if not (0 <= overlap < chunk_words):
        raise ValueError("overlap must be smaller than chunk_words")
    words = text.split()
    if not words:
        return []
    chunks = []
    stride = chunk_words - overlap
    for i, start in enumerate(range(0, len(words), stride)):
        selected = words[start:start + chunk_words]
        if not selected:
            break
        chunks.append({"chunk_id": f"policy-{i:03d}", "text": " ".join(selected)})
        if start + chunk_words >= len(words):
            break
    return chunks


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vector dimensions differ")
    numerator = sum(x*y for x,y in zip(a,b))
    denominator = math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))
    return numerator/denominator if denominator else 0.0

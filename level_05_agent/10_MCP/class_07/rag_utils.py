
import hashlib
import math


# 1. Generate document hash
def file_hash(path):

    with open(path, "rb") as file:
        content = file.read()

    return hashlib.sha256(content).hexdigest()


# 2. Split document into chunks
def chunk_markdown(text, chunk_words=85, overlap=18):

    words = text.split()
    chunks = []

    if chunk_words <= 0 or not 0 <= overlap < chunk_words:
        raise ValueError("Invalid chunk size or overlap")

    step = chunk_words - overlap

    for start in range(0, len(words), step):

        selected = words[start:start + chunk_words]

        chunks.append({
            "chunk_id": f"policy-{len(chunks):03d}",
            "text": " ".join(selected)
        })

        if start + chunk_words >= len(words):
            break

    return chunks


# 3. Calculate cosine similarity
def cosine(a, b):

    if len(a) != len(b):
        raise ValueError("Vector dimensions differ")

    dot_product = sum(x * y for x, y in zip(a, b))

    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)

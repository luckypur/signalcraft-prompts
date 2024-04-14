"""Small dependency-free vector retrieval for short incident runbooks.

Feature hashing is deliberately lightweight, not an embedding model.
"""
import hashlib
import math
import re

DIMS = 256


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def embed(text: str) -> list[float]:
    vector = [0.0] * DIMS
    for word in tokens(text):
        digest = hashlib.blake2b(word.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % DIMS
        sign = 1 if digest[4] % 2 else -1
        vector[index] += sign
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def search(query: str, runbooks: list[dict], limit: int = 3) -> list[dict]:
    query_vec = embed(query)
    matches = []
    for row in runbooks:
        score = cosine(query_vec, embed(row["title"] + " " + row["content"]))
        matches.append({**row, "score": round(score, 3)})
    return sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]

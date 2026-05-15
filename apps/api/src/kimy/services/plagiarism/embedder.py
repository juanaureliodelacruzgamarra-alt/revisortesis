"""Embedder with two backends.

Both produce L2-normalized vectors of dimension EMBEDDING_DIM so they can be
compared with cosine similarity via pgvector's `<=>` operator.

1. OpenAI text-embedding-3-small (1536 dims) — when OPENAI_API_KEY is set.
2. Hashed bag-of-words fallback — pure Python, deterministic, no API call.
   Tokenizes lowercased words, drops Spanish stopwords, hashes each token to a
   position in a 1536-dim vector. Two near-duplicate texts produce highly
   similar vectors; cosine similarity ≥ 0.85 is achievable for verbatim copies.
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter

from kimy.core.config import get_settings
from kimy.models.document_chunk import EMBEDDING_DIM

logger = logging.getLogger(__name__)


_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)

# Spanish + English minimal stopword list. Keeping it small so we don't strip
# domain words; the hashed embedding tolerates noise well.
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "a", "al", "en", "por", "para", "con", "sin", "sobre",
    "y", "o", "u", "ni", "que", "se", "es", "son", "ser", "ha", "han",
    "este", "esta", "estos", "estas", "ese", "esa", "esto", "eso",
    "su", "sus", "lo", "le", "les", "me", "mi", "tu", "te",
    "como", "pero", "porque", "cuando", "donde", "muy", "mas", "más",
    "the", "of", "and", "to", "in", "is", "for", "on", "with", "by",
}


class EmbedderUnavailableError(Exception):
    pass


def _tokenize(text: str) -> list[str]:
    return [
        t.lower() for t in _TOKEN_RE.findall(text)
        if t.lower() not in _STOPWORDS and len(t) > 2
    ]


def _hashed_bow(text: str) -> list[float]:
    """Hashed bag-of-words with L2 normalization.

    Two complementary hashes (with salts) are summed so single-token collisions
    don't dominate. Each token also contributes to neighbor cells via bigrams,
    which makes near-duplicate text produce highly similar vectors.
    """
    vec = [0.0] * EMBEDDING_DIM
    tokens = _tokenize(text)
    counts = Counter(tokens)

    for token, freq in counts.items():
        for salt in ("a", "b"):
            h = hashlib.blake2b(
                f"{salt}:{token}".encode(), digest_size=8
            ).digest()
            idx = int.from_bytes(h, "big") % EMBEDDING_DIM
            vec[idx] += float(freq)

    # Bigrams to capture local phrase structure.
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i + 1]}"
        h = hashlib.blake2b(bigram.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h, "big") % EMBEDDING_DIM
        vec[idx] += 0.5

    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        # Empty text → distinct sentinel vector so cosine with anything is 0.
        return vec
    return [x / norm for x in vec]


def _openai_embed(texts: list[str], api_key: str) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [d.embedding for d in resp.data]


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    """Embed a batch of texts. Returns (vectors, backend_name)."""
    if not texts:
        return [], "none"

    settings = get_settings()
    if settings.openai_api_key:
        try:
            vectors = _openai_embed(texts, settings.openai_api_key)
            return vectors, "openai:text-embedding-3-small"
        except Exception:
            logger.exception("openai embeddings failed — falling back to hashed-bow")

    return [_hashed_bow(t) for t in texts], "hashed-bow:v1"

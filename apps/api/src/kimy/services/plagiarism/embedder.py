"""Embedder — hashed bag-of-words.

Produces L2-normalized 1536-dim vectors compatible with the pgvector column.
Tokenizes lowercased words, drops Spanish stopwords, hashes each token to a
position in the vector. Two near-duplicate texts produce highly similar
vectors; cosine similarity ≥ 0.85 is achievable for verbatim copies.

Note: this used to delegate to OpenAI text-embedding-3-small when an API key
was set. After the migration to Gemini we removed that path because Gemini's
embedding models output 768 dimensions and the DB column is fixed at 1536.
Switching dimensions would require an Alembic migration that wipes existing
chunk embeddings — out of scope for this rebrand.
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter

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


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    """Embed a batch of texts. Returns (vectors, backend_name)."""
    if not texts:
        return [], "none"
    return [_hashed_bow(t) for t in texts], "hashed-bow:v1"

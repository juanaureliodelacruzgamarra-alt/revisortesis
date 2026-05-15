"""Chunk an ExtractedDocument into overlapping text windows for embedding.

Strategy: walk paragraphs left-to-right, accumulating into a chunk; emit a new
chunk when the accumulated char count crosses the target. Each chunk remembers
the section heading active when the chunk started.
"""
from __future__ import annotations

from dataclasses import dataclass

from kimy.services.documents.extractor import ExtractedDocument

TARGET_CHARS = 1500
MIN_CHARS_PER_CHUNK = 200


@dataclass(slots=True)
class TextChunk:
    chunk_index: int
    section: str | None
    text: str
    char_count: int


def chunk_document(doc: ExtractedDocument) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    current_paragraphs: list[str] = []
    current_section: str | None = None
    pending_section: str | None = None

    for para in doc.paragraphs:
        if para.heading_level is not None and para.heading_level >= 1:
            # New section starts. Treat it as a section marker for the next chunk
            # (and flush whatever we accumulated under the previous section).
            text = "\n".join(current_paragraphs).strip()
            if text and len(text) >= MIN_CHARS_PER_CHUNK:
                chunks.append(
                    TextChunk(
                        chunk_index=len(chunks),
                        section=current_section,
                        text=text,
                        char_count=len(text),
                    )
                )
            current_paragraphs = []
            pending_section = para.text.strip()
            continue

        if pending_section is not None:
            current_section = pending_section
            pending_section = None

        current_paragraphs.append(para.text)
        running = "\n".join(current_paragraphs)
        if len(running) >= TARGET_CHARS:
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    section=current_section,
                    text=running.strip(),
                    char_count=len(running),
                )
            )
            current_paragraphs = []

    tail = "\n".join(current_paragraphs).strip()
    if tail and len(tail) >= MIN_CHARS_PER_CHUNK:
        chunks.append(
            TextChunk(
                chunk_index=len(chunks),
                section=current_section,
                text=tail,
                char_count=len(tail),
            )
        )
    return chunks

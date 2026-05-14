from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from kimy.core.config import get_settings


@dataclass(slots=True)
class StoredFile:
    relative_path: str   # to be persisted in DB
    absolute_path: Path
    sha256: str
    size_bytes: int


_settings = get_settings()
_BASE = Path(_settings.storage_path).resolve()


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_bytes(
    namespace: str,
    *,
    content: bytes,
    extension: str,
) -> StoredFile:
    """Persist `content` under <storage_path>/<namespace>/<uuid>.<ext> and
    return the descriptor (relative path, sha256, size).
    """
    safe_ext = extension.lstrip(".").lower() or "bin"
    fname = f"{uuid4().hex}.{safe_ext}"
    rel = f"{namespace}/{fname}"
    abs_path = _BASE / namespace / fname
    _ensure_dir(abs_path)
    abs_path.write_bytes(content)

    digest = hashlib.sha256(content).hexdigest()
    return StoredFile(
        relative_path=rel,
        absolute_path=abs_path,
        sha256=digest,
        size_bytes=len(content),
    )


def resolve(relative_path: str) -> Path:
    """Resolve a stored relative path to an absolute Path inside storage root.
    Prevents directory traversal.
    """
    candidate = (_BASE / relative_path).resolve()
    if not str(candidate).startswith(str(_BASE)):
        raise ValueError("path traversal detected")
    return candidate


def delete(relative_path: str) -> None:
    path = resolve(relative_path)
    if path.is_file():
        path.unlink()


def iter_namespace(namespace: str) -> Iterable[Path]:
    folder = _BASE / namespace
    if not folder.is_dir():
        return ()
    return folder.iterdir()

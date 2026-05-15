"""OpenAI fine-tuning submission helper.

Only used when ``OPENAI_API_KEY`` is configured. The flow:
1. Upload the JSONL to OpenAI Files API (purpose=fine-tune).
2. Create a fine-tuning job referencing the file ID + base model.
3. Return (file_id, job_id) so the caller can persist them on FineTuningJob.

Status polling is *intentionally* left out of the request path — callers can
hit ``/api/v1/admin/fine-tuning/jobs/{id}/refresh`` to update on demand.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAINotConfiguredError(Exception):
    pass


class OpenAISubmitError(Exception):
    pass


@dataclass(slots=True)
class SubmitResult:
    file_id: str
    job_id: str
    base_model: str
    status: str


def is_available() -> bool:
    return bool(get_settings().openai_api_key)


def submit_jsonl(absolute_path: Path, *, base_model: str = "gpt-4o-mini") -> SubmitResult:
    settings = get_settings()
    if not settings.openai_api_key:
        raise OpenAINotConfiguredError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAISubmitError(f"openai package missing: {exc}") from exc

    client = OpenAI(api_key=settings.openai_api_key)

    try:
        with absolute_path.open("rb") as fp:
            file_obj = client.files.create(file=fp, purpose="fine-tune")
    except Exception as exc:  # noqa: BLE001
        raise OpenAISubmitError(f"file upload failed: {exc}") from exc

    try:
        job = client.fine_tuning.jobs.create(
            training_file=file_obj.id,
            model=base_model,
        )
    except Exception as exc:  # noqa: BLE001
        raise OpenAISubmitError(f"job creation failed: {exc}") from exc

    return SubmitResult(
        file_id=file_obj.id,
        job_id=job.id,
        base_model=base_model,
        status=getattr(job, "status", "queued"),
    )


def refresh_status(job_id: str) -> dict[str, str | None]:
    """Re-query OpenAI for a single job's status."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise OpenAINotConfiguredError("OPENAI_API_KEY is not set")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    job = client.fine_tuning.jobs.retrieve(job_id)
    return {
        "status": getattr(job, "status", None),
        "fine_tuned_model": getattr(job, "fine_tuned_model", None),
        "error": getattr(getattr(job, "error", None), "message", None) if getattr(job, "error", None) else None,
    }

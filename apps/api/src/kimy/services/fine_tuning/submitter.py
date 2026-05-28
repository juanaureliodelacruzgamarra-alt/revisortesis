"""Fine-tuning submission helper.

After the migration to Gemini, programmatic fine-tuning via the chat-JSONL
format that OpenAI exposed is no longer wired up. Gemini's tuning lives in a
different API surface (Vertex AI / Gemini Tuning API with input/output pairs
and parameter-efficient adapters), so this module returns a clear "not
supported" error.

The dataset export pipeline (``services.fine_tuning.exporter``) still produces
a JSONL snapshot of human-validated feedback, which remains useful for:
- Auditing the human-in-the-loop feedback quality.
- Manual import into a future tuning provider.
- Statistical analysis of severity/action distributions.

If you want to re-enable submission for a different provider, replace
``submit_jsonl`` and ``refresh_status`` with the corresponding SDK calls and
keep the dataclass shape so the admin UI keeps working unchanged.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)


class FineTuningNotSupportedError(Exception):
    """Raised when the active provider does not expose chat-format fine-tuning."""


# Legacy aliases — kept so existing imports in api/v1/fine_tuning.py still work.
OpenAINotConfiguredError = FineTuningNotSupportedError
OpenAISubmitError = FineTuningNotSupportedError


@dataclass(slots=True)
class SubmitResult:
    file_id: str
    job_id: str
    base_model: str
    status: str


def is_available() -> bool:
    """Return whether the active provider supports programmatic fine-tuning.

    Gemini does not (in this codebase), so this always returns False. The UI
    uses this to disable the "submit" button and surface an explanation.
    """
    return False


def submit_jsonl(absolute_path: Path, *, base_model: str = "gemini-2.0-flash") -> SubmitResult:
    settings = get_settings()
    _ = settings  # kept for future provider routing
    raise FineTuningNotSupportedError(
        "Fine-tuning programático no está disponible con Gemini en esta fase. "
        "Descarga el dataset JSONL y entrena offline en Vertex AI / Gemini Tuning."
    )


def refresh_status(job_id: str) -> dict[str, str | None]:
    raise FineTuningNotSupportedError(
        "Refresh no disponible: el job nunca se envió a un proveedor remoto."
    )

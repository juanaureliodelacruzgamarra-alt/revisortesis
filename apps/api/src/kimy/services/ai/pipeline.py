"""AI evaluation pipeline orchestrator.

Public function: ``run_for_version(version_id)``. Reads the version from DB,
extracts text, calls the LLM (or stub), persists ``ai_evaluations`` +
``ai_findings``, and updates the version's ``parsing_status``.

It is invoked from FastAPI BackgroundTasks today; in a later phase the same
function will be wrapped by a Celery task.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.db.session import AsyncSessionLocal
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import SEVERITY_ORDER, AIFinding
from kimy.models.submission_version import SubmissionVersion, VersionParsingStatus
from kimy.models.template_document import TemplateDocument
from kimy.services import storage
from kimy.services.ai import llm_evaluator, prompts, stub_evaluator
from kimy.services.ai.schemas import AIEvaluationDraft
from kimy.services.documents.extractor import extract

if TYPE_CHECKING:
    from kimy.models.submission import Submission

logger = logging.getLogger(__name__)

GRADING_SCALE_MAX = 20.0  # institucional, en Fase 8 viene de system_settings


async def run_for_version(version_id: UUID) -> None:
    """Run the pipeline for a version. Owns its own DB session.

    Designed to be called as a background task — never raises; failures are
    persisted in the version's parsing_error field.
    """
    async with AsyncSessionLocal() as session:
        try:
            await _run_inner(session, version_id)
        except Exception:  # noqa: BLE001
            logger.exception("AI pipeline crashed for version %s", version_id)
            # Best-effort: mark as failed on a fresh session in case the original
            # session is poisoned.
            async with AsyncSessionLocal() as recovery:
                version = await recovery.get(SubmissionVersion, version_id)
                if version is not None:
                    version.parsing_status = VersionParsingStatus.failed
                    version.parsing_error = "AI pipeline crashed (see API logs)"
                    await recovery.commit()


async def _run_inner(session: AsyncSession, version_id: UUID) -> None:
    version = await session.get(SubmissionVersion, version_id)
    if version is None:
        logger.warning("pipeline: version %s not found", version_id)
        return

    version.parsing_status = VersionParsingStatus.ai_processing
    await session.commit()

    submission = await _load_submission(session, version.submission_id)
    template = (
        await session.get(TemplateDocument, submission.template_id)
        if submission and submission.template_id
        else None
    )

    # Re-extract text from the stored file.
    path = storage.resolve(version.storage_path)
    raw_text = ""
    if path.is_file():
        content = path.read_bytes()
        try:
            extracted = extract(version.original_filename, content, version.mime_type)
            raw_text = extracted.full_text
        except Exception as exc:  # noqa: BLE001
            logger.warning("re-extract failed for %s: %s", version_id, exc)

    started = time.perf_counter()
    draft, backend, model_name = _evaluate(
        template=template,
        submission=submission,
        version=version,
        submission_text=raw_text,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)

    await _persist(
        session,
        version=version,
        draft=draft,
        backend=backend,
        model_name=model_name,
        duration_ms=duration_ms,
    )


def _evaluate(
    *,
    template: TemplateDocument | None,
    submission: "Submission | None",
    version: SubmissionVersion,
    submission_text: str,
) -> tuple[AIEvaluationDraft, str, str]:
    template_title = template.title if template else "(sin patrón asignado)"
    template_structure = template.structure_json if template else None
    submission_title = submission.title if submission else "(sin título)"
    submission_chapter = submission.chapter if submission else None
    submission_structure = version.structure_json

    try:
        return llm_evaluator.evaluate(
            template_title=template_title,
            template_structure=template_structure,
            submission_title=submission_title,
            submission_chapter=submission_chapter,
            submission_structure=submission_structure,
            submission_text=submission_text,
        )
    except llm_evaluator.LLMUnavailableError:
        logger.info("no LLM available — using stub evaluator")
    except Exception:
        logger.exception("LLM evaluator failed — falling back to stub")

    draft = stub_evaluator.evaluate(
        template_structure=template_structure,
        submission_structure=submission_structure,
        submission_text=submission_text,
    )
    return draft, stub_evaluator.BACKEND, stub_evaluator.MODEL_NAME


async def _persist(
    session: AsyncSession,
    *,
    version: SubmissionVersion,
    draft: AIEvaluationDraft,
    backend: str,
    model_name: str,
    duration_ms: int,
) -> None:
    total_percentage = draft.total_percentage()
    decimal_grade = (total_percentage / 100.0) * GRADING_SCALE_MAX

    # Wipe any prior evaluation for idempotency.
    existing = await session.execute(
        select(AIEvaluation)
        .options(selectinload(AIEvaluation.findings))
        .where(AIEvaluation.version_id == version.id)
    )
    for prev in existing.scalars():
        await session.delete(prev)
    await session.flush()

    evaluation = AIEvaluation(
        version_id=version.id,
        model=model_name,
        backend=backend,
        prompt_version=prompts.PROMPT_VERSION,
        duration_ms=duration_ms,
        structure_score=draft.scores.structure,
        content_score=draft.scores.content,
        form_score=draft.scores.form,
        originality_score=draft.scores.originality,
        total_percentage=total_percentage,
        decimal_grade=decimal_grade,
        executive_summary=draft.executive_summary,
    )
    session.add(evaluation)
    await session.flush()

    for f in draft.findings:
        session.add(
            AIFinding(
                evaluation_id=evaluation.id,
                section=f.section,
                page_approx=f.page_approx,
                type=f.type,
                severity=f.severity,
                severity_order=SEVERITY_ORDER[f.severity],
                description=f.description,
                instruction=f.instruction,
                example=f.example,
                recommendation=f.recommendation,
            )
        )

    version.parsing_status = VersionParsingStatus.ai_completed
    version.parsing_error = None
    await session.commit()


async def _load_submission(session: AsyncSession, submission_id: UUID) -> "Submission | None":
    from kimy.models.submission import Submission  # avoid circular import at module load
    return await session.get(Submission, submission_id)


def background_runner(version_id: UUID) -> "Iterable[None]":
    """Schedule helper for FastAPI BackgroundTasks. Wraps the async runner in
    asyncio.run so BackgroundTasks (sync) can call it.
    """
    import asyncio

    asyncio.run(run_for_version(version_id))
    return ()

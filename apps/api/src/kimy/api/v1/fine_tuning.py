"""Admin fine-tuning router.

Endpoints:
- ``GET    /api/v1/admin/fine-tuning/stats``         — eligible-example counters + threshold
- ``GET    /api/v1/admin/fine-tuning/dataset.jsonl`` — preview/download the latest export
- ``POST   /api/v1/admin/fine-tuning/jobs``          — build JSONL + create FineTuningJob (status=dataset_ready)
- ``POST   /api/v1/admin/fine-tuning/jobs/{id}/submit`` — upload to OpenAI and create FT job
- ``POST   /api/v1/admin/fine-tuning/jobs/{id}/refresh`` — pull status from OpenAI
- ``GET    /api/v1/admin/fine-tuning/jobs``          — list jobs (most recent first)
- ``GET    /api/v1/admin/settings/ai-model``         — read active-model preference
- ``PUT    /api/v1/admin/settings/ai-model``         — toggle base/fine-tuned model
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.fine_tuning_job import FineTuningJob, FineTuningStatus
from kimy.models.system_setting import KEY_AI_MODEL_PREFERENCE, KEY_FINE_TUNING_CONFIG
from kimy.models.user import UserRole
from kimy.schemas.fine_tuning import (
    FineTuningJobOut,
    FineTuningStats,
    ModelPreference,
    ModelPreferencePatch,
)
from kimy.services import settings as settings_service
from kimy.services import storage
from kimy.services.fine_tuning import exporter as ft_exporter
from kimy.services.fine_tuning import submitter as ft_submitter

router = APIRouter(
    prefix="/admin",
    tags=["admin", "fine-tuning"],
    dependencies=[Depends(require_roles(UserRole.admin))],
)


async def _threshold(session: AsyncSession) -> int:
    cfg = await settings_service.get(session, KEY_FINE_TUNING_CONFIG)
    return int(cfg.get("min_examples") or 500)


@router.get("/fine-tuning/stats", response_model=FineTuningStats)
async def stats(session: SessionDep) -> FineTuningStats:
    s = await ft_exporter.compute_stats(session)
    threshold = await _threshold(session)
    provider_ok = ft_submitter.is_available()
    return FineTuningStats(
        total_eligible=s.total_eligible,
        by_action=s.by_action,
        by_severity=s.by_severity,
        min_examples_threshold=threshold,
        ready_to_export=s.total_eligible > 0,
        ready_to_submit=s.total_eligible >= threshold and provider_ok,
        provider_available=provider_ok,
    )


@router.get("/fine-tuning/jobs", response_model=list[FineTuningJobOut])
async def list_jobs(session: SessionDep) -> list[FineTuningJobOut]:
    stmt = select(FineTuningJob).order_by(FineTuningJob.created_at.desc())
    rows = list((await session.execute(stmt)).scalars().all())
    return [FineTuningJobOut.model_validate(r) for r in rows]


@router.post(
    "/fine-tuning/jobs",
    response_model=FineTuningJobOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(session: SessionDep, user: CurrentUser) -> FineTuningJobOut:
    """Build the JSONL dataset from current feedback and persist a new job row.

    Idempotent in the sense that calling it twice produces two separate jobs,
    each with its own snapshot of the dataset at that moment.
    """
    text, count, _ = await ft_exporter.build_dataset(session)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="no eligible findings — no modified/rejected feedback yet",
        )
    relpath = await ft_exporter.persist_dataset(text)
    pref = await settings_service.get(session, KEY_AI_MODEL_PREFERENCE)
    base_model = str(pref.get("model") or "gemini-2.0-flash")

    job = FineTuningJob(
        status=FineTuningStatus.dataset_ready,
        dataset_path=relpath,
        examples_count=count,
        base_model=base_model,
        created_by=user.id,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return FineTuningJobOut.model_validate(job)


@router.get("/fine-tuning/jobs/{job_id}/dataset.jsonl")
async def download_dataset(job_id: UUID, session: SessionDep):
    job = await session.get(FineTuningJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="job not found"
        )
    path = storage.resolve(job.dataset_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="dataset file missing"
        )
    return Response(
        content=path.read_bytes(),
        media_type="application/jsonl",
        headers={
            "Content-Disposition": f'attachment; filename="kimy-ft-{job_id}.jsonl"'
        },
    )


@router.post(
    "/fine-tuning/jobs/{job_id}/submit", response_model=FineTuningJobOut
)
async def submit_job(
    job_id: UUID, session: SessionDep
) -> FineTuningJobOut:
    job = await session.get(FineTuningJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="job not found"
        )
    if job.status not in (FineTuningStatus.dataset_ready, FineTuningStatus.failed):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"job is {job.status.value}; cannot submit",
        )

    abs_path = storage.resolve(job.dataset_path)
    if not abs_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="dataset file missing"
        )

    job.status = FineTuningStatus.uploading
    job.submitted_at = datetime.now(UTC)
    await session.commit()

    try:
        result = ft_submitter.submit_jsonl(abs_path, base_model=job.base_model)
    except ft_submitter.OpenAINotConfiguredError as exc:
        job.status = FineTuningStatus.failed
        job.error = str(exc)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ft_submitter.OpenAISubmitError as exc:
        job.status = FineTuningStatus.failed
        job.error = str(exc)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    job.openai_file_id = result.file_id
    job.openai_job_id = result.job_id
    job.status = FineTuningStatus.queued
    job.error = None
    await session.commit()
    await session.refresh(job)
    return FineTuningJobOut.model_validate(job)


@router.post(
    "/fine-tuning/jobs/{job_id}/refresh", response_model=FineTuningJobOut
)
async def refresh_job(
    job_id: UUID, session: SessionDep
) -> FineTuningJobOut:
    job = await session.get(FineTuningJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="job not found"
        )
    if not job.openai_job_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="job has not been submitted to OpenAI yet",
        )
    try:
        info = ft_submitter.refresh_status(job.openai_job_id)
    except ft_submitter.OpenAINotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    raw_status = (info.get("status") or "").lower()
    mapping = {
        "validating_files": FineTuningStatus.queued,
        "queued": FineTuningStatus.queued,
        "running": FineTuningStatus.running,
        "succeeded": FineTuningStatus.succeeded,
        "failed": FineTuningStatus.failed,
        "cancelled": FineTuningStatus.cancelled,
    }
    new_status = mapping.get(raw_status, job.status)
    job.status = new_status
    if info.get("fine_tuned_model"):
        job.fine_tuned_model = info["fine_tuned_model"]
    if info.get("error"):
        job.error = info["error"]
    if new_status in (
        FineTuningStatus.succeeded,
        FineTuningStatus.failed,
        FineTuningStatus.cancelled,
    ):
        job.finished_at = job.finished_at or datetime.now(UTC)
    await session.commit()
    await session.refresh(job)
    return FineTuningJobOut.model_validate(job)


@router.get("/settings/ai-model", response_model=ModelPreference)
async def get_active_model(session: SessionDep) -> ModelPreference:
    cfg = await settings_service.get(session, KEY_AI_MODEL_PREFERENCE)
    return ModelPreference(**cfg)


@router.put("/settings/ai-model", response_model=ModelPreference)
async def set_active_model(
    payload: ModelPreferencePatch,
    session: SessionDep,
    user: CurrentUser,
) -> ModelPreference:
    cfg = await settings_service.get(session, KEY_AI_MODEL_PREFERENCE)
    if payload.provider is not None:
        cfg["provider"] = payload.provider
    if payload.model is not None:
        cfg["model"] = payload.model
    if payload.fine_tuned_model is not None:
        cfg["fine_tuned_model"] = payload.fine_tuned_model or None
    if payload.use_fine_tuned is not None:
        cfg["use_fine_tuned"] = bool(payload.use_fine_tuned)
        if cfg["use_fine_tuned"] and not cfg.get("fine_tuned_model"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot enable use_fine_tuned without a fine_tuned_model",
            )
    new = await settings_service.upsert(
        session, KEY_AI_MODEL_PREFERENCE, cfg, updated_by=user.id
    )
    return ModelPreference(**new)

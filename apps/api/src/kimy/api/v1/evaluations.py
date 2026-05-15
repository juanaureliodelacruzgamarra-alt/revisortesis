from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import AIFinding, HumanAction
from kimy.models.submission import Submission
from kimy.models.submission_version import SubmissionVersion
from kimy.models.user import UserRole
from kimy.schemas.evaluations import EvaluationOut, FindingHumanPatch, FindingOut
from kimy.services import evaluations as eval_service
from kimy.services import submissions as submissions_service
from kimy.services.push.sender import PushPayload, notify_user

router = APIRouter(tags=["evaluations"])


@router.get(
    "/submissions/{submission_id}/versions/{version_id}/evaluation",
    response_model=EvaluationOut,
)
async def get_evaluation(
    submission_id: UUID,
    version_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> EvaluationOut:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="submission not found")
    if not submissions_service.can_access(submission, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if not any(v.id == version_id for v in submission.versions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")

    evaluation = await eval_service.get_evaluation_for_version(session, version_id)
    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="evaluation not ready"
        )
    return EvaluationOut.model_validate(evaluation)


@router.patch(
    "/findings/{finding_id}",
    response_model=FindingOut,
    dependencies=[Depends(require_roles(UserRole.advisor, UserRole.coordinator, UserRole.admin))],
)
async def patch_finding(
    finding_id: UUID,
    payload: FindingHumanPatch,
    session: SessionDep,
    user: CurrentUser,
    background: BackgroundTasks,
) -> FindingOut:
    finding = await eval_service.get_finding(session, finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="finding not found")

    finding = await eval_service.set_human_action(
        session,
        finding=finding,
        reviewer=user,
        action=payload.action,
        comment=payload.comment,
        severity_override=payload.severity_override,
    )

    # Notify the student when the advisor modifies/rejects (acceptance alone is
    # silent — it would spam on every finding the advisor agrees with).
    if payload.action in (HumanAction.modified, HumanAction.rejected):
        student_id, submission_id, submission_title = await _resolve_student_context(
            session, finding.id
        )
        if student_id is not None:
            background.add_task(
                notify_user,
                student_id,
                PushPayload(
                    title="Tu asesor revisó un hallazgo",
                    body=f"{submission_title}: el asesor {payload.action.value} un hallazgo.",
                    data={
                        "type": "advisor_review",
                        "submission_id": str(submission_id) if submission_id else "",
                        "finding_id": str(finding.id),
                        "action": payload.action.value,
                    },
                ),
            )

    return FindingOut.model_validate(finding)


async def _resolve_student_context(
    session: SessionDep, finding_id: UUID
) -> tuple[UUID | None, UUID | None, str]:
    """Return (student_id, submission_id, submission_title) for a finding."""
    stmt = (
        select(Submission)
        .options(selectinload(Submission.versions))
        .join(SubmissionVersion, SubmissionVersion.submission_id == Submission.id)
        .join(AIEvaluation, AIEvaluation.version_id == SubmissionVersion.id)
        .join(AIFinding, AIFinding.evaluation_id == AIEvaluation.id)
        .where(AIFinding.id == finding_id)
        .limit(1)
    )
    submission = (await session.execute(stmt)).scalar_one_or_none()
    if submission is None:
        return None, None, ""
    return submission.student_id, submission.id, submission.title

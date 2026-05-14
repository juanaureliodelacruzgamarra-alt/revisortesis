from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.user import UserRole
from kimy.schemas.evaluations import EvaluationOut, FindingHumanPatch, FindingOut
from kimy.services import evaluations as eval_service
from kimy.services import submissions as submissions_service

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
    return FindingOut.model_validate(finding)

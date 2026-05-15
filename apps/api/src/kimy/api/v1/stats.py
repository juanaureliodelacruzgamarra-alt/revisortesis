from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from kimy.core.deps import SessionDep, require_roles
from kimy.models.user import UserRole
from kimy.schemas.stats import (
    ActivityItemOut,
    ProgramGradeOut,
    StatsOverviewOut,
    StatusCountOut,
)
from kimy.services import activity as activity_service
from kimy.services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["stats"])

_DASHBOARD_ROLES = [Depends(require_roles(UserRole.coordinator, UserRole.admin))]


@router.get("/overview", response_model=StatsOverviewOut, dependencies=_DASHBOARD_ROLES)
async def overview(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
) -> StatsOverviewOut:
    data = await stats_service.overview(session, program_id=program_id)
    return StatsOverviewOut(
        total_submissions=data.total_submissions,
        total_advisors_with_orcid=data.total_advisors_with_orcid,
        submissions_by_status=[
            StatusCountOut(status=s.status, count=s.count)
            for s in data.submissions_by_status
        ],
        avg_ai_grade=data.avg_ai_grade,
        avg_ai_percentage=data.avg_ai_percentage,
        ai_human_concordance_pct=data.ai_human_concordance_pct,
        plagiarism_alerts=data.plagiarism_alerts,
        advisor_fit_alerts=data.advisor_fit_alerts,
        low_compliance_submissions=data.low_compliance_submissions,
        citations_total=data.citations_total,
        citations_problematic=data.citations_problematic,
        grades_per_program=[
            ProgramGradeOut(
                program_id=p.program_id,
                program_code=p.program_code,
                program_name=p.program_name,
                average_grade=p.average_grade,
                submissions_count=p.submissions_count,
            )
            for p in data.grades_per_program
        ],
    )


@router.get(
    "/activity",
    response_model=list[ActivityItemOut],
    dependencies=_DASHBOARD_ROLES,
)
async def activity(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 15,
) -> list[ActivityItemOut]:
    items = await activity_service.recent(session, program_id=program_id, limit=limit)
    return [
        ActivityItemOut(
            kind=i.kind,
            occurred_at=i.occurred_at,
            submission_id=i.submission_id,
            submission_title=i.submission_title,
            actor_name=i.actor_name,
            description=i.description,
        )
        for i in items
    ]

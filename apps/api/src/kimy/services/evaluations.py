from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import AIFinding, FindingSeverity, HumanAction
from kimy.models.user import User


async def get_evaluation_for_version(
    session: AsyncSession, version_id: UUID
) -> AIEvaluation | None:
    stmt = (
        select(AIEvaluation)
        .options(selectinload(AIEvaluation.findings))
        .where(AIEvaluation.version_id == version_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_finding(session: AsyncSession, finding_id: UUID) -> AIFinding | None:
    return await session.get(AIFinding, finding_id)


async def set_human_action(
    session: AsyncSession,
    *,
    finding: AIFinding,
    reviewer: User,
    action: HumanAction,
    comment: str | None,
    severity_override: FindingSeverity | None,
) -> AIFinding:
    finding.human_action = action
    finding.human_comment = (comment or "").strip() or None
    finding.human_severity_override = severity_override
    finding.reviewed_by = reviewer.id
    finding.reviewed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(finding)
    return finding

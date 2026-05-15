"""Aggregate statistics for the coordinator/admin dashboard.

All queries are read-only and respect the optional ``program_id`` filter so the
same endpoint can drive a program-level view or a global view.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.models.academic_program import AcademicProgram
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import AIFinding, HumanAction
from kimy.models.citation import Citation, CitationStatus
from kimy.models.plagiarism_match import PlagiarismMatch
from kimy.models.submission import Submission, SubmissionStatus


@dataclass(slots=True)
class StatusCount:
    status: str
    count: int


@dataclass(slots=True)
class ProgramGrade:
    program_id: str
    program_code: str
    program_name: str
    average_grade: float
    submissions_count: int


@dataclass(slots=True)
class StatsOverview:
    total_submissions: int = 0
    total_advisors_with_orcid: int = 0
    submissions_by_status: list[StatusCount] = field(default_factory=list)
    avg_ai_grade: float | None = None
    avg_ai_percentage: float | None = None
    ai_human_concordance_pct: float | None = None
    plagiarism_alerts: int = 0
    advisor_fit_alerts: int = 0
    low_compliance_submissions: int = 0  # AI total_percentage < 60
    citations_total: int = 0
    citations_problematic: int = 0  # not_found + hallucinated + partial
    grades_per_program: list[ProgramGrade] = field(default_factory=list)


async def overview(
    session: AsyncSession, *, program_id: UUID | None = None
) -> StatsOverview:
    out = StatsOverview()

    base = select(Submission)
    if program_id is not None:
        base = base.where(Submission.program_id == program_id)

    out.total_submissions = (
        await session.scalar(select(func.count()).select_from(base.subquery()))
        or 0
    )

    # Counts by status.
    stmt = select(Submission.status, func.count(Submission.id)).group_by(
        Submission.status
    )
    if program_id is not None:
        stmt = stmt.where(Submission.program_id == program_id)
    rows = (await session.execute(stmt)).all()
    out.submissions_by_status = [
        StatusCount(
            status=(s.value if isinstance(s, SubmissionStatus) else str(s)),
            count=int(c),
        )
        for s, c in rows
    ]

    # Average AI grade (latest evaluation per version is the only one we keep — see _persist).
    from kimy.models.submission_version import SubmissionVersion

    grade_stmt = (
        select(
            func.avg(AIEvaluation.decimal_grade),
            func.avg(AIEvaluation.total_percentage),
            func.count(AIEvaluation.id),
        )
        .join(SubmissionVersion, SubmissionVersion.id == AIEvaluation.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
    )
    if program_id is not None:
        grade_stmt = grade_stmt.where(Submission.program_id == program_id)
    grade_row = (await session.execute(grade_stmt)).one()
    avg_grade, avg_pct, eval_count = grade_row
    if eval_count:
        out.avg_ai_grade = float(avg_grade) if avg_grade is not None else None
        out.avg_ai_percentage = float(avg_pct) if avg_pct is not None else None

    # AI-Human concordance: of the findings the advisor reviewed, how many did
    # they accept verbatim? (action = accepted).
    concord_stmt = (
        select(
            func.count(AIFinding.id),
            func.sum(
                case((AIFinding.human_action == HumanAction.accepted, 1), else_=0)
            ),
        )
        .join(AIEvaluation, AIEvaluation.id == AIFinding.evaluation_id)
        .join(SubmissionVersion, SubmissionVersion.id == AIEvaluation.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .where(AIFinding.human_action.is_not(None))
    )
    if program_id is not None:
        concord_stmt = concord_stmt.where(Submission.program_id == program_id)
    reviewed, accepted = (await session.execute(concord_stmt)).one()
    if reviewed and reviewed > 0:
        out.ai_human_concordance_pct = float(accepted or 0) * 100.0 / float(reviewed)

    # Plagiarism alerts: distinct submissions with any match.
    plag_stmt = (
        select(func.count(func.distinct(PlagiarismMatch.version_id)))
        .join(SubmissionVersion, SubmissionVersion.id == PlagiarismMatch.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
    )
    if program_id is not None:
        plag_stmt = plag_stmt.where(Submission.program_id == program_id)
    out.plagiarism_alerts = int((await session.execute(plag_stmt)).scalar() or 0)

    # Advisor-fit alerts: submissions with advisor_fit_alert=True.
    fit_stmt = select(func.count(Submission.id)).where(
        Submission.advisor_fit_alert.is_(True)
    )
    if program_id is not None:
        fit_stmt = fit_stmt.where(Submission.program_id == program_id)
    out.advisor_fit_alerts = int((await session.execute(fit_stmt)).scalar() or 0)

    # Low compliance (AI total_percentage < 60), counted at the submission level
    # via its evaluations.
    low_stmt = (
        select(func.count(func.distinct(Submission.id)))
        .join(SubmissionVersion, SubmissionVersion.submission_id == Submission.id)
        .join(AIEvaluation, AIEvaluation.version_id == SubmissionVersion.id)
        .where(AIEvaluation.total_percentage < 60)
    )
    if program_id is not None:
        low_stmt = low_stmt.where(Submission.program_id == program_id)
    out.low_compliance_submissions = int(
        (await session.execute(low_stmt)).scalar() or 0
    )

    # Citation breakdown.
    cit_stmt = (
        select(
            func.count(Citation.id),
            func.sum(
                case(
                    (
                        Citation.crossref_status.in_(
                            [
                                CitationStatus.not_found,
                                CitationStatus.hallucinated,
                                CitationStatus.partial,
                            ]
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
        )
        .join(SubmissionVersion, SubmissionVersion.id == Citation.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
    )
    if program_id is not None:
        cit_stmt = cit_stmt.where(Submission.program_id == program_id)
    cit_total, cit_bad = (await session.execute(cit_stmt)).one()
    out.citations_total = int(cit_total or 0)
    out.citations_problematic = int(cit_bad or 0)

    # Average grade per program (skipped when filtering by a single program).
    if program_id is None:
        per_prog_stmt = (
            select(
                AcademicProgram.id,
                AcademicProgram.code,
                AcademicProgram.name,
                func.avg(AIEvaluation.decimal_grade),
                func.count(func.distinct(Submission.id)),
            )
            .join(Submission, Submission.program_id == AcademicProgram.id)
            .join(SubmissionVersion, SubmissionVersion.submission_id == Submission.id)
            .join(AIEvaluation, AIEvaluation.version_id == SubmissionVersion.id)
            .group_by(AcademicProgram.id, AcademicProgram.code, AcademicProgram.name)
            .order_by(AcademicProgram.code)
        )
        per_prog_rows = (await session.execute(per_prog_stmt)).all()
        out.grades_per_program = [
            ProgramGrade(
                program_id=str(pid),
                program_code=code,
                program_name=name,
                average_grade=float(avg or 0),
                submissions_count=int(cnt or 0),
            )
            for pid, code, name, avg, cnt in per_prog_rows
        ]

    # Advisors with ORCID linked (not filterable by program — global).
    from kimy.models.advisor_profile import AdvisorProfile

    orcid_stmt = select(func.count(AdvisorProfile.user_id)).where(
        AdvisorProfile.orcid_id.is_not(None)
    )
    out.total_advisors_with_orcid = int((await session.execute(orcid_stmt)).scalar() or 0)

    return out

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class StatusCountOut(BaseModel):
    status: str
    count: int


class ProgramGradeOut(BaseModel):
    program_id: str
    program_code: str
    program_name: str
    average_grade: float
    submissions_count: int


class StatsOverviewOut(BaseModel):
    total_submissions: int
    total_advisors_with_orcid: int
    submissions_by_status: list[StatusCountOut]
    avg_ai_grade: float | None
    avg_ai_percentage: float | None
    ai_human_concordance_pct: float | None
    plagiarism_alerts: int
    advisor_fit_alerts: int
    low_compliance_submissions: int
    citations_total: int
    citations_problematic: int
    grades_per_program: list[ProgramGradeOut]


class ActivityItemOut(BaseModel):
    kind: str
    occurred_at: datetime
    submission_id: str
    submission_title: str
    actor_name: str
    description: str

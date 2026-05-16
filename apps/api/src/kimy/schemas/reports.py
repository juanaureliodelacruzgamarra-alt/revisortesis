from __future__ import annotations

from pydantic import BaseModel


class SubmissionReportRow(BaseModel):
    submission_id: str
    program_code: str
    program_name: str
    title: str
    chapter: str | None
    status: str
    student_name: str
    advisor_name: str | None
    decimal_grade: float | None
    total_percentage: float | None
    advisor_fit_score: float | None
    advisor_fit_alert: bool
    latest_version: int
    created_at: str


class SubmissionsReport(BaseModel):
    program_id: str | None
    status: str | None
    rows: list[SubmissionReportRow]
    total: int


class ProgramRollupRow(BaseModel):
    program_id: str
    program_code: str
    program_name: str
    submissions_count: int
    average_grade: float | None
    plagiarism_alerts: int
    fit_alerts: int


class ProgramsRollup(BaseModel):
    rows: list[ProgramRollupRow]

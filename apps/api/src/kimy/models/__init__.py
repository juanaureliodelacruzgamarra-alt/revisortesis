"""SQLAlchemy models.

Import all models here so Alembic autogenerate can find them.
"""
from kimy.models.academic_program import AcademicProgram, ProgramLevel
from kimy.models.advisor_profile import AdvisorProfile
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import (
    SEVERITY_ORDER,
    AIFinding,
    FindingSeverity,
    FindingType,
    HumanAction,
)
from kimy.models.student_profile import StudentProfile
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion, VersionParsingStatus
from kimy.models.template_document import TemplateDocument, TemplateParsingStatus
from kimy.models.user import User, UserRole

__all__ = [
    "AIEvaluation",
    "AIFinding",
    "AcademicProgram",
    "AdvisorProfile",
    "FindingSeverity",
    "FindingType",
    "HumanAction",
    "ProgramLevel",
    "SEVERITY_ORDER",
    "StudentProfile",
    "Submission",
    "SubmissionStatus",
    "SubmissionVersion",
    "TemplateDocument",
    "TemplateParsingStatus",
    "User",
    "UserRole",
    "VersionParsingStatus",
]

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
from kimy.models.citation import Citation, CitationStatus
from kimy.models.document_chunk import EMBEDDING_DIM, DocumentChunk
from kimy.models.fine_tuning_job import FineTuningJob, FineTuningStatus
from kimy.models.orcid_publication import OrcidPublication
from kimy.models.plagiarism_match import (
    PlagiarismMatch,
    PlagiarismSource,
    PlagiarismStatus,
)
from kimy.models.push_token import PushToken
from kimy.models.student_profile import StudentProfile
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion, VersionParsingStatus
from kimy.models.system_setting import (
    DEFAULT_AI_MODEL_PREFERENCE,
    DEFAULT_FINE_TUNING_CONFIG,
    KEY_AI_MODEL_PREFERENCE,
    KEY_FINE_TUNING_CONFIG,
    SystemSetting,
)
from kimy.models.template_document import TemplateDocument, TemplateParsingStatus
from kimy.models.user import User, UserRole

__all__ = [
    "AIEvaluation",
    "AIFinding",
    "AcademicProgram",
    "AdvisorProfile",
    "Citation",
    "CitationStatus",
    "DEFAULT_AI_MODEL_PREFERENCE",
    "DEFAULT_FINE_TUNING_CONFIG",
    "DocumentChunk",
    "FineTuningJob",
    "FineTuningStatus",
    "KEY_AI_MODEL_PREFERENCE",
    "KEY_FINE_TUNING_CONFIG",
    "SystemSetting",
    "EMBEDDING_DIM",
    "FindingSeverity",
    "FindingType",
    "HumanAction",
    "OrcidPublication",
    "PlagiarismMatch",
    "PushToken",
    "PlagiarismSource",
    "PlagiarismStatus",
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

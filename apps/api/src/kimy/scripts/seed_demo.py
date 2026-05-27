"""Seed demo data so every dashboard shows realistic content.

Idempotent: re-running will not duplicate users/programs (keyed by email/code).
For submissions/evaluations/citations we only seed if the target student has
none yet, so re-running is also safe.

Usage:
    cd apps/api
    uv run python -m kimy.scripts.seed_demo
"""
# ruff: noqa: S107, S311 - seed fixtures, not security-sensitive
from __future__ import annotations

import asyncio
import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.core.security import hash_password
from kimy.db.session import AsyncSessionLocal
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
from kimy.models.audit_log import AuditLog
from kimy.models.citation import Citation, CitationStatus
from kimy.models.document_chunk import EMBEDDING_DIM, DocumentChunk
from kimy.models.fine_tuning_job import FineTuningJob, FineTuningStatus
from kimy.models.orcid_publication import OrcidPublication
from kimy.models.plagiarism_match import PlagiarismMatch, PlagiarismSource, PlagiarismStatus
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

logger = logging.getLogger("seed_demo")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Static demo data
# ---------------------------------------------------------------------------

PROGRAMS: list[dict[str, Any]] = [
    {"code": "MIS", "name": "Maestría en Ingeniería de Software", "level": ProgramLevel.masters},
    {"code": "MCC", "name": "Maestría en Ciencias de la Computación", "level": ProgramLevel.masters},
    {"code": "DSC", "name": "Doctorado en Ciencias", "level": ProgramLevel.doctorate},
    {"code": "ING", "name": "Ingeniería Informática", "level": ProgramLevel.undergraduate},
]


def _user(email: str, full_name: str, role: UserRole, password: str = "Demo1234") -> dict[str, Any]:
    return {
        "email": email.lower(),
        "full_name": full_name,
        "role": role,
        "password": password,
    }


USERS: list[dict[str, Any]] = [
    # Admin (single)
    _user("admin@unt.edu.pe", "Administrador Aurelio", UserRole.admin, "Admin1234"),
    # Coordinator
    _user("coordinador@unt.edu.pe", "Lucía Vargas", UserRole.coordinator, "Coord1234"),
    # Advisors (3 — varied affiliation, only one with ORCID)
    _user("asesor@unt.edu.pe", "Carlos Reátegui", UserRole.advisor, "Asesor1234"),
    _user("asesor.maria@unt.edu.pe", "María Fernández", UserRole.advisor),
    _user("asesor.jose@unt.edu.pe", "José Quispe", UserRole.advisor),
    # Students (5 — across programs, with varied progress)
    _user("alumno@unt.edu.pe", "Ana Torres", UserRole.student, "Alumno1234"),
    _user("alumno.luis@unt.edu.pe", "Luis Ramírez", UserRole.student),
    _user("alumno.diana@unt.edu.pe", "Diana Salazar", UserRole.student),
    _user("alumno.kevin@unt.edu.pe", "Kevin Mendoza", UserRole.student),
    _user("alumno.rosa@unt.edu.pe", "Rosa Castillo", UserRole.student),
]


# Sample structure_json shape (matches parse_structure output enough for the UI)
SAMPLE_STRUCTURE = {
    "sections": [
        {
            "number": "1",
            "title": "Introducción",
            "canonical_title": "introduccion",
            "level": 1,
            "char_count": 4820,
            "paragraph_count": 14,
            "children": [],
        },
        {
            "number": "2",
            "title": "Marco teórico",
            "canonical_title": "marco_teorico",
            "level": 1,
            "char_count": 9120,
            "paragraph_count": 28,
            "children": [],
        },
        {
            "number": "3",
            "title": "Metodología",
            "canonical_title": "metodologia",
            "level": 1,
            "char_count": 5430,
            "paragraph_count": 17,
            "children": [],
        },
        {
            "number": "4",
            "title": "Resultados",
            "canonical_title": "resultados",
            "level": 1,
            "char_count": 7200,
            "paragraph_count": 22,
            "children": [],
        },
        {
            "number": "5",
            "title": "Conclusiones",
            "canonical_title": "conclusiones",
            "level": 1,
            "char_count": 2640,
            "paragraph_count": 8,
            "children": [],
        },
    ],
    "total_paragraphs": 89,
    "total_chars": 29210,
    "page_count": 42,
}


SAMPLE_RUBRIC = {
    "weights": {
        "structure": 0.25,
        "content": 0.40,
        "form": 0.15,
        "originality": 0.20,
    },
    "min_grade_to_approve": 14.0,
}


# Each submission gets a curated set of findings to make dashboards look real.
FINDING_TEMPLATES: list[dict[str, Any]] = [
    {
        "section": "Marco teórico",
        "page_approx": 12,
        "type": FindingType.content_error,
        "severity": FindingSeverity.major,
        "description": "Faltan referencias actualizadas (>2020) en la sección de antecedentes.",
        "instruction": "Incluir al menos 3 fuentes publicadas entre 2020 y 2024.",
        "example": "Ej.: 'Smith et al. (2023) demuestran que...'",
        "recommendation": "Buscar en Scopus o IEEE filtrando por año.",
    },
    {
        "section": "Metodología",
        "page_approx": 18,
        "type": FindingType.structural_error,
        "severity": FindingSeverity.critical,
        "description": "No se explicita el tipo de diseño (cuasi-experimental, descriptivo, etc.).",
        "instruction": "Declarar el tipo y nivel de investigación en el primer párrafo.",
        "example": "Investigación aplicada con diseño cuasi-experimental.",
        "recommendation": "Revisar Hernández-Sampieri cap. 5.",
    },
    {
        "section": "Introducción",
        "page_approx": 3,
        "type": FindingType.missing_section,
        "severity": FindingSeverity.major,
        "description": "Falta la formulación del problema en forma de pregunta.",
        "instruction": "Agregar una pregunta de investigación clara.",
        "example": "¿Cómo afecta X a Y en el contexto Z?",
        "recommendation": "",
    },
    {
        "section": "Resultados",
        "page_approx": 28,
        "type": FindingType.form_error,
        "severity": FindingSeverity.minor,
        "description": "Tablas sin numeración ni título según APA 7.",
        "instruction": "Numerar tablas y agregar título en cursiva debajo.",
        "example": "Tabla 1\\n*Distribución de la muestra*",
        "recommendation": "Plantilla APA 7 disponible en el portal.",
    },
    {
        "section": "Conclusiones",
        "page_approx": 38,
        "type": FindingType.coherence_issue,
        "severity": FindingSeverity.minor,
        "description": "Las conclusiones no responden directamente a los objetivos planteados.",
        "instruction": "Vincular cada conclusión a un objetivo específico.",
        "example": "",
        "recommendation": "",
    },
    {
        "section": "Marco teórico",
        "page_approx": 9,
        "type": FindingType.suggestion,
        "severity": FindingSeverity.suggestion,
        "description": "Considerar añadir un esquema visual del modelo conceptual.",
        "instruction": "Diagrama tipo flujo o mapa mental.",
        "example": "",
        "recommendation": "",
    },
]


# Each submission gets 4-6 sample citations across statuses.
CITATIONS = [
    {
        "raw_text": "Hernández-Sampieri, R. (2018). Metodología de la investigación. McGraw-Hill.",
        "title": "Metodología de la investigación",
        "authors": "Hernández-Sampieri, R.",
        "year": 2018,
        "journal": None,
        "doi": None,
        "crossref_status": CitationStatus.verified,
    },
    {
        "raw_text": "Smith, J. & Lee, K. (2023). Deep learning in education. Computers & Education, 198, 104-119.",
        "title": "Deep learning in education",
        "authors": "Smith, J.; Lee, K.",
        "year": 2023,
        "journal": "Computers & Education",
        "doi": "10.1016/j.compedu.2023.104119",
        "crossref_status": CitationStatus.verified,
    },
    {
        "raw_text": "Pérez, L. (2024). Estudio sobre IA en universidades peruanas. Revista UNT, 4(2).",
        "title": "Estudio sobre IA en universidades peruanas",
        "authors": "Pérez, L.",
        "year": 2024,
        "journal": "Revista UNT",
        "doi": None,
        "crossref_status": CitationStatus.not_found,
    },
    {
        "raw_text": "García, M. (2021). Big data y educación superior. (Editorial inexistente).",
        "title": "Big data y educación superior",
        "authors": "García, M.",
        "year": 2021,
        "journal": None,
        "doi": None,
        "crossref_status": CitationStatus.hallucinated,
    },
    {
        "raw_text": "OECD (2022). The state of higher education. OECD Publishing.",
        "title": "The state of higher education",
        "authors": "OECD",
        "year": 2022,
        "journal": None,
        "doi": "10.1787/abc123",
        "crossref_status": CitationStatus.partial,
    },
    {
        "raw_text": "Vargas, A. (2020). Plagio académico en tesis de posgrado. UNT.",
        "title": "Plagio académico en tesis de posgrado",
        "authors": "Vargas, A.",
        "year": 2020,
        "journal": None,
        "doi": None,
        "crossref_status": CitationStatus.verified,
    },
]


# Submissions to seed: (student_email, program_code, advisor_email, title, chapter, status)
SUBMISSIONS: list[dict[str, Any]] = [
    {
        "student": "alumno@unt.edu.pe",
        "program": "MIS",
        "advisor": "asesor@unt.edu.pe",
        "title": "Sistema de revisión automática de tesis con IA",
        "chapter": "Capítulo III: Metodología",
        "status": SubmissionStatus.observed,
        "advisor_fit_score": 0.78,
        "advisor_fit_alert": False,
        "grade": 14.2,
    },
    {
        "student": "alumno.luis@unt.edu.pe",
        "program": "MIS",
        "advisor": "asesor@unt.edu.pe",
        "title": "Modelos de detección de plagio basados en embeddings",
        "chapter": "Capítulo II: Marco teórico",
        "status": SubmissionStatus.in_progress,
        "advisor_fit_score": 0.62,
        "advisor_fit_alert": False,
        "grade": 12.8,
    },
    {
        "student": "alumno.diana@unt.edu.pe",
        "program": "MCC",
        "advisor": "asesor.maria@unt.edu.pe",
        "title": "Análisis de sentimiento en redes sociales académicas",
        "chapter": "Capítulo IV: Resultados",
        "status": SubmissionStatus.approved,
        "advisor_fit_score": 0.81,
        "advisor_fit_alert": False,
        "grade": 16.5,
    },
    {
        "student": "alumno.kevin@unt.edu.pe",
        "program": "ING",
        "advisor": "asesor.jose@unt.edu.pe",
        "title": "Aplicación móvil para gestión de avances de tesis",
        "chapter": "Capítulo I: Introducción",
        "status": SubmissionStatus.observed,
        "advisor_fit_score": 0.28,   # below 0.35 threshold → alert
        "advisor_fit_alert": True,
        "grade": 11.4,
    },
    {
        "student": "alumno.rosa@unt.edu.pe",
        "program": "DSC",
        "advisor": "asesor.maria@unt.edu.pe",
        "title": "Bioestadística aplicada a estudios longitudinales",
        "chapter": "Capítulo V: Conclusiones",
        "status": SubmissionStatus.draft,
        "advisor_fit_score": None,
        "advisor_fit_alert": False,
        "grade": None,
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_programs(session: AsyncSession) -> dict[str, AcademicProgram]:
    out: dict[str, AcademicProgram] = {}
    for p in PROGRAMS:
        row = (
            await session.execute(
                select(AcademicProgram).where(AcademicProgram.code == p["code"])
            )
        ).scalar_one_or_none()
        if row is None:
            row = AcademicProgram(
                name=p["name"], code=p["code"], level=p["level"]
            )
            session.add(row)
            logger.info("program created: %s", p["code"])
        out[p["code"]] = row
    await session.commit()
    for row in out.values():
        await session.refresh(row)
    return out


async def _ensure_users(session: AsyncSession) -> dict[str, User]:
    out: dict[str, User] = {}
    for u in USERS:
        row = (
            await session.execute(select(User).where(User.email == u["email"]))
        ).scalar_one_or_none()
        if row is None:
            row = User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                is_active=True,
            )
            session.add(row)
            await session.flush()
            # Sister profile row
            if u["role"] == UserRole.student:
                session.add(StudentProfile(user_id=row.id))
            elif u["role"] == UserRole.advisor:
                session.add(AdvisorProfile(user_id=row.id, affiliation="UNT — FCFM"))
            logger.info("user created: %s (%s)", u["email"], u["role"].value)
        else:
            logger.info("user exists:  %s", u["email"])
        out[u["email"]] = row
    await session.commit()
    for row in out.values():
        await session.refresh(row)
    return out


async def _ensure_student_program_link(
    session: AsyncSession,
    users: dict[str, User],
    programs: dict[str, AcademicProgram],
) -> None:
    """Wire each student to a program and (optionally) to an advisor."""
    mapping = {
        "alumno@unt.edu.pe": ("MIS", "asesor@unt.edu.pe"),
        "alumno.luis@unt.edu.pe": ("MIS", "asesor@unt.edu.pe"),
        "alumno.diana@unt.edu.pe": ("MCC", "asesor.maria@unt.edu.pe"),
        "alumno.kevin@unt.edu.pe": ("ING", "asesor.jose@unt.edu.pe"),
        "alumno.rosa@unt.edu.pe": ("DSC", "asesor.maria@unt.edu.pe"),
    }
    for email, (prog_code, advisor_email) in mapping.items():
        student = users[email]
        sp = (
            await session.execute(
                select(StudentProfile).where(StudentProfile.user_id == student.id)
            )
        ).scalar_one_or_none()
        if sp is None:
            sp = StudentProfile(user_id=student.id)
            session.add(sp)
        sp.program_id = programs[prog_code].id
        sp.advisor_id = users[advisor_email].id
        sp.student_code = f"UNT-{random.randint(2018, 2024)}-{random.randint(1000, 9999)}"
    await session.commit()


async def _ensure_templates(
    session: AsyncSession,
    programs: dict[str, AcademicProgram],
    coordinator: User,
) -> dict[str, TemplateDocument]:
    """One active template per program — needed so submissions can hang off them."""
    out: dict[str, TemplateDocument] = {}
    for code, program in programs.items():
        # Pick the most recent template if multiple exist (from older manual runs).
        row = (
            await session.execute(
                select(TemplateDocument)
                .where(TemplateDocument.program_id == program.id)
                .order_by(TemplateDocument.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            row = TemplateDocument(
                program_id=program.id,
                created_by=coordinator.id,
                title=f"Plantilla de tesis {program.code}",
                version=1,
                description=(
                    f"Estructura y rúbrica oficial para {program.name}. "
                    "Demo seed — no hay archivo binario real."
                ),
                original_filename=f"plantilla-{code.lower()}.docx",
                storage_path=f"templates/seed-{code.lower()}.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                file_size_bytes=124_000,
                file_sha256=uuid4().hex + uuid4().hex,  # 64 chars
                parsing_status=TemplateParsingStatus.parsed,
                structure_json=SAMPLE_STRUCTURE,
                rubric_json=SAMPLE_RUBRIC,
                is_active=True,
            )
            session.add(row)
            logger.info("template created for program %s", code)
        out[code] = row
    await session.commit()
    for row in out.values():
        await session.refresh(row)
    return out


async def _seed_submissions(
    session: AsyncSession,
    users: dict[str, User],
    programs: dict[str, AcademicProgram],
    templates: dict[str, TemplateDocument],
) -> None:
    for s in SUBMISSIONS:
        student = users[s["student"]]
        # Skip if this student already has a submission with same title.
        existing = (
            await session.execute(
                select(Submission).where(
                    Submission.student_id == student.id,
                    Submission.title == s["title"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            logger.info("submission exists: '%s'", s["title"])
            continue

        program = programs[s["program"]]
        advisor = users[s["advisor"]]
        template = templates[s["program"]]

        sub = Submission(
            student_id=student.id,
            program_id=program.id,
            advisor_id=advisor.id,
            template_id=template.id,
            title=s["title"],
            chapter=s["chapter"],
            status=s["status"],
            advisor_fit_score=s["advisor_fit_score"],
            advisor_fit_alert=s["advisor_fit_alert"],
        )
        session.add(sub)
        await session.flush()

        # One version (unless draft) — parsed + AI-completed
        if s["status"] != SubmissionStatus.draft:
            ver = SubmissionVersion(
                submission_id=sub.id,
                version_number=1,
                comment="Primera entrega — seed demo.",
                original_filename=f"{student.full_name.split()[0].lower()}-tesis-v1.docx",
                storage_path=f"submissions/seed-{uuid4().hex}.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                file_size_bytes=random.randint(180_000, 720_000),
                file_sha256=uuid4().hex + uuid4().hex,
                page_count=SAMPLE_STRUCTURE["page_count"],
                parsing_status=VersionParsingStatus.ai_completed,
                structure_json=SAMPLE_STRUCTURE,
            )
            session.add(ver)
            await session.flush()

            # AI evaluation with findings + citations
            if s["grade"] is not None:
                grade = s["grade"]
                total = grade * 5.0  # 0..100
                ev = AIEvaluation(
                    version_id=ver.id,
                    model="gpt-4o-mini",
                    prompt_version="v0.3.0",
                    backend="stub",
                    duration_ms=random.randint(1800, 4200),
                    structure_score=round(total * 0.95, 1),
                    content_score=round(total * 1.05, 1),
                    form_score=round(total * 0.90, 1),
                    originality_score=round(total * 1.10, 1),
                    total_percentage=round(total, 1),
                    decimal_grade=grade,
                    executive_summary=(
                        f"Avance evaluado por el stub IA. La rúbrica obtiene "
                        f"{grade:.1f}/20. Se detectaron observaciones priorizadas en "
                        f"estructura, contenido y referencias. Ver findings."
                    ),
                )
                session.add(ev)
                await session.flush()

                for tpl in FINDING_TEMPLATES:
                    f = AIFinding(
                        evaluation_id=ev.id,
                        section=tpl["section"],
                        page_approx=tpl["page_approx"],
                        type=tpl["type"],
                        severity=tpl["severity"],
                        severity_order=SEVERITY_ORDER[tpl["severity"]],
                        description=tpl["description"],
                        instruction=tpl["instruction"],
                        example=tpl["example"],
                        recommendation=tpl["recommendation"],
                    )
                    # Some findings get human feedback (so fine-tuning has data)
                    if random.random() < 0.4:
                        f.human_action = random.choice(
                            [HumanAction.modified, HumanAction.rejected, HumanAction.accepted]
                        )
                        f.reviewed_by = advisor.id
                        f.reviewed_at = datetime.now(UTC) - timedelta(hours=random.randint(1, 72))
                        if f.human_action == HumanAction.modified:
                            f.human_comment = "Reformulado: el problema sí estaba presente pero menos crítico."
                            f.human_severity_override = FindingSeverity.minor
                    session.add(f)

            # Citations (4-6 random)
            for c in random.sample(CITATIONS, k=random.randint(4, 6)):
                cit = Citation(
                    version_id=ver.id,
                    raw_text=c["raw_text"],
                    title=c["title"],
                    authors=c["authors"],
                    year=c["year"],
                    journal=c["journal"],
                    doi=c["doi"],
                    crossref_status=c["crossref_status"],
                    crossref_message=None,
                    checked_at=datetime.now(UTC) - timedelta(minutes=random.randint(5, 600)),
                )
                session.add(cit)

        logger.info("submission seeded: '%s' (%s)", s["title"], s["status"].value)

    await session.commit()


# ---------------------------------------------------------------------------
# ORCID publications for advisors
# ---------------------------------------------------------------------------

ORCID_PUBS: list[dict[str, Any]] = [
    {
        "advisor": "asesor@unt.edu.pe",
        "orcid_id": "0000-0002-1234-5678",
        "pubs": [
            {"put_code": "101", "title": "Automated thesis evaluation using NLP", "year": 2023, "journal": "IEEE Access", "doi": "10.1109/ACCESS.2023.001"},
            {"put_code": "102", "title": "Plagiarism detection with sentence embeddings", "year": 2022, "journal": "Computers & Education", "doi": "10.1016/j.compedu.2022.555"},
            {"put_code": "103", "title": "Machine learning for academic document classification", "year": 2021, "journal": "Expert Systems with Applications", "doi": "10.1016/j.eswa.2021.123"},
        ],
    },
    {
        "advisor": "asesor.maria@unt.edu.pe",
        "orcid_id": "0000-0003-9876-5432",
        "pubs": [
            {"put_code": "201", "title": "Sentiment analysis in academic social networks", "year": 2024, "journal": "Journal of Informetrics", "doi": "10.1016/j.joi.2024.100"},
            {"put_code": "202", "title": "Biostatistical methods for longitudinal studies", "year": 2023, "journal": "BMC Medical Research", "doi": "10.1186/s12874-023-001"},
        ],
    },
]


async def _seed_orcid(session: AsyncSession, users: dict[str, User]) -> None:
    for entry in ORCID_PUBS:
        advisor = users[entry["advisor"]]
        profile = (await session.execute(
            select(AdvisorProfile).where(AdvisorProfile.user_id == advisor.id)
        )).scalar_one_or_none()
        if profile is None:
            continue
        profile.orcid_id = entry["orcid_id"]
        profile.orcid_last_sync = datetime.now(UTC) - timedelta(hours=2)
        for pub in entry["pubs"]:
            exists = (await session.execute(
                select(OrcidPublication).where(
                    OrcidPublication.advisor_id == advisor.id,
                    OrcidPublication.put_code == pub["put_code"],
                )
            )).scalar_one_or_none()
            if exists:
                continue
            fake_emb = [random.gauss(0, 0.1) for _ in range(EMBEDDING_DIM)]
            session.add(OrcidPublication(
                advisor_id=advisor.id,
                put_code=pub["put_code"],
                title=pub["title"],
                year=pub["year"],
                journal=pub["journal"],
                doi=pub["doi"],
                embedding=fake_emb,
            ))
        logger.info("orcid pubs seeded for %s", entry["advisor"])
    await session.commit()


# ---------------------------------------------------------------------------
# Document chunks + plagiarism matches
# ---------------------------------------------------------------------------

CHUNK_TEXTS = [
    "La revisión automática de tesis permite identificar deficiencias estructurales y de contenido de forma temprana.",
    "Los embeddings de oraciones capturan la semántica del texto y permiten comparar similitudes entre documentos.",
    "El diseño cuasi-experimental se aplicó con un grupo control y un grupo experimental de 30 estudiantes.",
    "Los resultados muestran una mejora del 25% en la calidad de los avances cuando se usa retroalimentación IA.",
    "Las conclusiones del estudio confirman la hipótesis principal sobre la eficacia del sistema propuesto.",
    "La detección de plagio intra-programa utiliza vectores coseno sobre fragmentos de 512 tokens.",
]


async def _seed_chunks_and_plagiarism(session: AsyncSession) -> None:
    existing = (await session.execute(select(DocumentChunk).limit(1))).scalar_one_or_none()
    if existing:
        logger.info("chunks already exist, skipping")
        return

    versions = (await session.execute(
        select(SubmissionVersion).order_by(SubmissionVersion.created_at)
    )).scalars().all()
    if len(versions) < 2:
        return

    all_chunks: list[DocumentChunk] = []
    for ver in versions:
        for i, text in enumerate(random.sample(CHUNK_TEXTS, k=min(4, len(CHUNK_TEXTS)))):
            chunk = DocumentChunk(
                version_id=ver.id,
                chunk_index=i,
                section=["Introducción", "Marco teórico", "Metodología", "Resultados"][i % 4],
                text=text,
                char_count=len(text),
                embedding=[random.gauss(0, 0.1) for _ in range(EMBEDDING_DIM)],
            )
            session.add(chunk)
            all_chunks.append(chunk)
    await session.flush()

    # Create 3 plagiarism matches between different versions
    ver_chunks: dict[str, list[DocumentChunk]] = {}
    for c in all_chunks:
        ver_chunks.setdefault(str(c.version_id), []).append(c)

    ver_ids = list(ver_chunks.keys())
    match_count = 0
    for i in range(len(ver_ids)):
        for j in range(i + 1, len(ver_ids)):
            if match_count >= 3:
                break
            src = ver_chunks[ver_ids[i]][0]
            tgt = ver_chunks[ver_ids[j]][0]
            session.add(PlagiarismMatch(
                version_id=src.version_id,
                matched_version_id=tgt.version_id,
                source_chunk_id=src.id,
                matched_chunk_id=tgt.id,
                similarity=round(random.uniform(0.75, 0.95), 3),
                source=PlagiarismSource.intra,
                status=random.choice([PlagiarismStatus.pending, PlagiarismStatus.confirmed]),
            ))
            match_count += 1

    await session.commit()
    logger.info("chunks (%d) + plagiarism matches (%d) seeded", len(all_chunks), match_count)


# ---------------------------------------------------------------------------
# Fine-tuning jobs
# ---------------------------------------------------------------------------

async def _seed_fine_tuning(session: AsyncSession, users: dict[str, User]) -> None:
    existing = (await session.execute(select(FineTuningJob).limit(1))).scalar_one_or_none()
    if existing:
        logger.info("fine-tuning jobs exist, skipping")
        return

    admin = users["admin@unt.edu.pe"]
    now = datetime.now(UTC)
    jobs = [
        FineTuningJob(
            status=FineTuningStatus.succeeded,
            dataset_path="fine_tuning/dataset_v1.jsonl",
            examples_count=523,
            base_model="gpt-4o-mini-2024-07-18",
            openai_file_id="file-abc123",
            openai_job_id="ftjob-xyz789",
            fine_tuned_model="ft:gpt-4o-mini-2024-07-18:kimy::ABC123",
            created_by=admin.id,
            submitted_at=now - timedelta(days=7),
            finished_at=now - timedelta(days=6, hours=18),
        ),
        FineTuningJob(
            status=FineTuningStatus.running,
            dataset_path="fine_tuning/dataset_v2.jsonl",
            examples_count=612,
            base_model="gpt-4o-mini-2024-07-18",
            openai_file_id="file-def456",
            openai_job_id="ftjob-running01",
            created_by=admin.id,
            submitted_at=now - timedelta(hours=3),
        ),
        FineTuningJob(
            status=FineTuningStatus.dataset_ready,
            dataset_path="fine_tuning/dataset_v3.jsonl",
            examples_count=189,
            base_model="gpt-4o-mini-2024-07-18",
            created_by=admin.id,
        ),
    ]
    for j in jobs:
        session.add(j)
    await session.commit()
    logger.info("fine-tuning jobs seeded (%d)", len(jobs))


# ---------------------------------------------------------------------------
# System settings
# ---------------------------------------------------------------------------

async def _seed_system_settings(session: AsyncSession, users: dict[str, User]) -> None:
    existing = (await session.execute(
        select(SystemSetting).where(SystemSetting.key == KEY_AI_MODEL_PREFERENCE)
    )).scalar_one_or_none()
    if existing:
        logger.info("system settings exist, skipping")
        return

    admin = users["admin@unt.edu.pe"]
    now = datetime.now(UTC)
    session.add(SystemSetting(
        key=KEY_AI_MODEL_PREFERENCE,
        value=DEFAULT_AI_MODEL_PREFERENCE,
        updated_at=now,
        updated_by=admin.id,
    ))
    session.add(SystemSetting(
        key=KEY_FINE_TUNING_CONFIG,
        value=DEFAULT_FINE_TUNING_CONFIG,
        updated_at=now,
        updated_by=admin.id,
    ))
    await session.commit()
    logger.info("system settings seeded")


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

AUDIT_ENTRIES = [
    {"role": "admin", "method": "POST", "path": "/api/programs", "status": 201},
    {"role": "coordinator", "method": "POST", "path": "/api/templates", "status": 201},
    {"role": "student", "method": "POST", "path": "/api/submissions", "status": 201},
    {"role": "student", "method": "POST", "path": "/api/submissions/abc/versions", "status": 201},
    {"role": "advisor", "method": "PATCH", "path": "/api/findings/xyz/action", "status": 200},
    {"role": "admin", "method": "PATCH", "path": "/api/users/abc/role", "status": 200},
    {"role": "coordinator", "method": "POST", "path": "/api/batch/reprocess", "status": 202},
    {"role": "student", "method": "POST", "path": "/api/submissions", "status": 201},
    {"role": "advisor", "method": "PATCH", "path": "/api/findings/def/action", "status": 200},
    {"role": None, "method": "POST", "path": "/api/auth/login", "status": 200},
    {"role": None, "method": "POST", "path": "/api/auth/login", "status": 401},
    {"role": "admin", "method": "DELETE", "path": "/api/users/old-user", "status": 204},
    {"role": "student", "method": "POST", "path": "/api/submissions", "status": 201},
    {"role": "coordinator", "method": "PATCH", "path": "/api/settings/ai.model_preference", "status": 200},
    {"role": "advisor", "method": "PATCH", "path": "/api/findings/ghi/action", "status": 200},
]


async def _seed_audit_logs(session: AsyncSession, users: dict[str, User]) -> None:
    existing = (await session.execute(select(AuditLog).limit(1))).scalar_one_or_none()
    if existing:
        logger.info("audit logs exist, skipping")
        return

    role_user_map = {
        "admin": users["admin@unt.edu.pe"],
        "coordinator": users["coordinador@unt.edu.pe"],
        "advisor": users["asesor@unt.edu.pe"],
        "student": users["alumno@unt.edu.pe"],
    }
    now = datetime.now(UTC)
    for i, entry in enumerate(AUDIT_ENTRIES):
        user = role_user_map.get(entry["role"]) if entry["role"] else None
        session.add(AuditLog(
            actor_id=user.id if user else None,
            actor_role=entry["role"],
            method=entry["method"],
            path=entry["path"],
            status_code=entry["status"],
            duration_ms=random.randint(15, 850),
            ip=f"192.168.0.{random.randint(2, 50)}",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/125.0",
        ))
    await session.commit()
    logger.info("audit logs seeded (%d)", len(AUDIT_ENTRIES))


# ---------------------------------------------------------------------------
# Push tokens
# ---------------------------------------------------------------------------

async def _seed_push_tokens(session: AsyncSession, users: dict[str, User]) -> None:
    existing = (await session.execute(select(PushToken).limit(1))).scalar_one_or_none()
    if existing:
        logger.info("push tokens exist, skipping")
        return

    students = ["alumno@unt.edu.pe", "alumno.luis@unt.edu.pe", "alumno.diana@unt.edu.pe"]
    for email in students:
        user = users[email]
        session.add(PushToken(
            user_id=user.id,
            expo_token=f"ExponentPushToken[{uuid4().hex[:22]}]",
            device_label=f"{user.full_name.split()[0]}'s phone",
            last_seen=datetime.now(UTC) - timedelta(minutes=random.randint(5, 120)),
        ))
    await session.commit()
    logger.info("push tokens seeded (%d)", len(students))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    random.seed(42)
    async with AsyncSessionLocal() as session:
        programs = await _ensure_programs(session)
        users = await _ensure_users(session)
        await _ensure_student_program_link(session, users, programs)
        coordinator = users["coordinador@unt.edu.pe"]
        templates = await _ensure_templates(session, programs, coordinator)
        await _seed_submissions(session, users, programs, templates)
        await _seed_orcid(session, users)
        await _seed_chunks_and_plagiarism(session)
        await _seed_fine_tuning(session, users)
        await _seed_system_settings(session, users)
        await _seed_audit_logs(session, users)
        await _seed_push_tokens(session, users)

    logger.info("="*60)
    logger.info("SEED COMPLETO — Credenciales demo:")
    logger.info("  admin       admin@unt.edu.pe / Admin1234")
    logger.info("  coordinador coordinador@unt.edu.pe / Coord1234")
    logger.info("  asesor      asesor@unt.edu.pe / Asesor1234")
    logger.info("  alumno      alumno@unt.edu.pe / Alumno1234")
    logger.info("  (otros: alumno.luis, alumno.diana, alumno.kevin, alumno.rosa — pass: Demo1234)")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())

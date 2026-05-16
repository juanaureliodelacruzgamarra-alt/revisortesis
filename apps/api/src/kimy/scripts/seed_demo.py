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
from kimy.models.citation import Citation, CitationStatus
from kimy.models.student_profile import StudentProfile
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion, VersionParsingStatus
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


async def main() -> None:
    random.seed(42)
    async with AsyncSessionLocal() as session:
        programs = await _ensure_programs(session)
        users = await _ensure_users(session)
        await _ensure_student_program_link(session, users, programs)
        coordinator = users["coordinador@unt.edu.pe"]
        templates = await _ensure_templates(session, programs, coordinator)
        await _seed_submissions(session, users, programs, templates)

    logger.info("done. demo seed applied.")
    logger.info("admin       admin@unt.edu.pe / Admin1234")
    logger.info("coordinador coordinador@unt.edu.pe / Coord1234")
    logger.info("asesor      asesor@unt.edu.pe / Asesor1234")
    logger.info("alumno      alumno@unt.edu.pe / Alumno1234")


if __name__ == "__main__":
    asyncio.run(main())

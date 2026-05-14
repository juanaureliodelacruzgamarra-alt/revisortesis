"""Deterministic heuristic evaluator.

Used when no LLM API key is configured, so the pipeline still produces useful
output during development. The output shape is identical to the LLM evaluator,
so the rest of the system can't tell them apart.

Strategy: compare template structure (canonical sections) vs submission
structure, plus simple text-length heuristics, to generate findings + scores.
"""
from __future__ import annotations

from typing import Any

from kimy.models.ai_finding import FindingSeverity, FindingType
from kimy.services.ai.schemas import (
    AIEvaluationDraft,
    AIFindingDraft,
    AIScores,
)

BACKEND = "stub"
MODEL_NAME = "kimy-heuristic-v1"

# Sections we consider obligatory in a thesis advance (canonical names produced
# by the structure parser). Adjustable per program in future phases.
_REQUIRED_SECTIONS = {
    "Introducción",
    "Planteamiento del problema",
    "Objetivos",
    "Justificación",
    "Marco teórico",
    "Metodología",
}

# Approximate minimum chars per top-level section before we flag it as "thin".
_MIN_CHARS_PER_SECTION = 600


def _collect_canonical_titles(structure: dict[str, Any] | None) -> set[str]:
    if not structure:
        return set()
    titles: set[str] = set()
    def walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            ct = node.get("canonical_title") or node.get("title")
            if ct:
                titles.add(ct)
            walk(node.get("children") or [])
    walk(structure.get("sections") or [])
    return titles


def _top_level_sections(structure: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not structure:
        return []
    return [s for s in (structure.get("sections") or []) if s.get("level", 1) == 1]


def evaluate(
    *,
    template_structure: dict[str, Any] | None,
    submission_structure: dict[str, Any] | None,
    submission_text: str,
) -> AIEvaluationDraft:
    findings: list[AIFindingDraft] = []

    template_titles = _collect_canonical_titles(template_structure)
    submission_titles = _collect_canonical_titles(submission_structure)

    expected = (template_titles & _REQUIRED_SECTIONS) or _REQUIRED_SECTIONS
    missing = sorted(expected - submission_titles)

    for section in missing:
        findings.append(
            AIFindingDraft(
                section=section,
                type=FindingType.missing_section,
                severity=(
                    FindingSeverity.critical
                    if section in {"Introducción", "Objetivos", "Metodología"}
                    else FindingSeverity.major
                ),
                description=(
                    f"No se encontró la sección \"{section}\" en el avance. "
                    "Esta sección está marcada como obligatoria por el documento patrón."
                ),
                instruction=(
                    f"Agregar la sección \"{section}\" siguiendo la estructura del patrón institucional. "
                    "Verifica que tenga numeración consistente y un encabezado claro con estilo de heading."
                ),
                example=_example_for(section),
                recommendation=(
                    "Revisa el documento patrón para conocer la extensión y los subapartados sugeridos."
                ),
            )
        )

    # Thin-section heuristic on top-level sections actually present.
    for sec in _top_level_sections(submission_structure):
        chars = int(sec.get("char_count") or 0)
        title = sec.get("title") or sec.get("canonical_title") or "Sección"
        if 0 < chars < _MIN_CHARS_PER_SECTION:
            findings.append(
                AIFindingDraft(
                    section=title,
                    type=FindingType.content_error,
                    severity=FindingSeverity.minor,
                    description=(
                        f"La sección \"{title}\" tiene apenas {chars} caracteres, "
                        f"por debajo del mínimo sugerido (~{_MIN_CHARS_PER_SECTION})."
                    ),
                    instruction=(
                        "Amplía la sección con argumentación adicional, referencias y ejemplos. "
                        "Una sección de avance no debería ser un párrafo aislado."
                    ),
                    example=(
                        "Una buena introducción presenta el contexto del problema, su relevancia social/académica, "
                        "y desemboca naturalmente en los objetivos del estudio."
                    ),
                    recommendation="Compara extensión con tesis aprobadas del mismo programa.",
                )
            )

    # Form-level: if the document has zero detected headings, flag structural.
    if submission_structure and not (submission_structure.get("sections") or []):
        findings.append(
            AIFindingDraft(
                type=FindingType.structural_error,
                severity=FindingSeverity.major,
                description=(
                    "No se detectaron secciones en el documento. Probablemente no usaste estilos "
                    "de encabezado (Heading 1, Heading 2…) o numeración consistente (1., 1.1)."
                ),
                instruction=(
                    "Convierte los títulos en estilos de encabezado y numera consistentemente. "
                    "Esto permite que el sistema (y los revisores) localicen secciones rápidamente."
                ),
                example="Heading 1: \"1. Introducción\" → Heading 2: \"1.1 Planteamiento del problema\".",
                recommendation="En Word: pestaña Inicio → Estilos → Título 1, Título 2, etc.",
            )
        )

    # Coherence suggestion if very few chars overall.
    if len(submission_text) > 0 and len(submission_text) < 1500:
        findings.append(
            AIFindingDraft(
                type=FindingType.suggestion,
                severity=FindingSeverity.suggestion,
                description=(
                    f"El avance es muy breve ({len(submission_text)} caracteres)."
                ),
                instruction=(
                    "Considera ampliar el documento — un avance típico de capítulo supera los 8.000 caracteres."
                ),
                example="",
                recommendation="Profundiza en la metodología y la justificación antes de avanzar al siguiente capítulo.",
            )
        )

    # Scoring (heuristic): structure score is coverage of expected sections.
    coverage = (len(expected) - len(missing)) / max(len(expected), 1)
    structure_score = round(100 * coverage, 2)

    # Content score is a soft function of text length and number of sections.
    n_sections = len(_top_level_sections(submission_structure))
    content_score = round(
        min(100, n_sections * 15 + min(50, len(submission_text) / 200)), 2
    )

    # Form score: did the parser detect sections at all?
    form_score = 80.0 if submission_structure and (submission_structure.get("sections") or []) else 30.0

    # Originality: stub can't really judge — give a neutral score we'll mention as such.
    originality_score = 65.0

    scores = AIScores(
        structure=structure_score,
        content=content_score,
        form=form_score,
        originality=originality_score,
    )

    # Executive summary (templated).
    summary_lines = [
        f"Avance evaluado por el módulo heurístico KIMY (sin LLM activo, v1).",
        f"Cumplimiento estructural: {structure_score:.0f}/100 — "
        f"{len(missing)} secciones obligatorias faltantes de {len(expected)}.",
        f"Contenido: {content_score:.0f}/100. Forma: {form_score:.0f}/100. "
        f"Originalidad estimada: {originality_score:.0f}/100.",
        (
            "Prioridad alta: completar las secciones marcadas como críticas."
            if any(f.severity == FindingSeverity.critical for f in findings)
            else "No se detectaron problemas críticos en la estructura."
        ),
        "Nota: para retroalimentación de profundidad académica configura OPENAI_API_KEY o ANTHROPIC_API_KEY.",
    ]

    return AIEvaluationDraft(
        executive_summary=" ".join(summary_lines),
        scores=scores,
        findings=findings,
    )


def _example_for(section: str) -> str:
    mapping = {
        "Introducción": (
            "La presente investigación aborda el problema de la revisión manual de avances de tesis, "
            "que en la universidad X genera retrasos de hasta cuatro semanas por avance. Este estudio propone..."
        ),
        "Objetivos": (
            "Objetivo general: Desarrollar una plataforma automatizada para la revisión de avances de tesis. "
            "Objetivos específicos: (1) ..., (2) ..., (3) ..."
        ),
        "Metodología": (
            "Esta investigación es de tipo aplicada, con diseño cuasi-experimental. "
            "La población está conformada por ..., y la muestra ..."
        ),
        "Marco teórico": (
            "El marco teórico se organiza en torno a tres ejes: la revisión académica automatizada (autores X, Y), "
            "los modelos de evaluación rubrica-based (autor Z), y ..."
        ),
        "Planteamiento del problema": (
            "El problema central es la baja eficiencia del proceso de revisión de tesis, evidenciada por ..."
        ),
        "Justificación": (
            "El estudio se justifica por su contribución a la calidad académica y por su pertinencia social, dado que ..."
        ),
    }
    return mapping.get(section, f"Redacta la sección \"{section}\" siguiendo el patrón institucional.")

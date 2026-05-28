"""Export the human-validated AI findings as an OpenAI fine-tuning dataset.

Only findings the advisor actually engaged with end up here:
- ``modified``  →  the assistant message becomes the advisor's correction
- ``rejected``  →  the example becomes a negative one (assistant declines)
- ``accepted`` with a non-null ``human_severity_override`` →  treated as a
  severity correction (rare; we keep it for completeness)

Lines purely accepted without modification are skipped — they don't teach the
model anything new beyond "you got it right".

Output format follows the OpenAI Chat fine-tuning schema:
    {"messages": [{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]}

We deliberately rebuild a minimal user prompt per finding instead of dumping the
full original LLM context — far smaller files, fine-tunes still capture the
shape of severity assessment and corrective rewriting.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import AIFinding, FindingSeverity, HumanAction
from kimy.models.submission import Submission
from kimy.models.submission_version import SubmissionVersion
from kimy.services import storage

_SYSTEM_PROMPT = (
    "Eres Aurelio, un evaluador académico de tesis. Tu tarea: para el hallazgo "
    "descrito por el usuario, devolver UN ÚNICO objeto JSON con la severidad "
    "final (critical|major|minor|suggestion), la descripción corregida y, si "
    "corresponde, la instrucción de corrección. Si el hallazgo no debe "
    "reportarse, devuelve {\"action\":\"reject\",\"reason\":\"…\"}."
)


@dataclass(slots=True)
class ExportStats:
    total_eligible: int
    by_action: dict[str, int]
    by_severity: dict[str, int]


async def gather_eligible(session: AsyncSession) -> list[AIFinding]:
    """Findings whose human reviewer changed something or rejected the AI."""
    stmt = (
        select(AIFinding)
        .options(selectinload(AIFinding.evaluation))
        .where(
            AIFinding.reviewed_at.is_not(None),
            or_(
                AIFinding.human_action == HumanAction.modified,
                AIFinding.human_action == HumanAction.rejected,
                AIFinding.human_severity_override.is_not(None),
            ),
        )
        .order_by(AIFinding.reviewed_at)
    )
    return list((await session.execute(stmt)).scalars().all())


async def compute_stats(session: AsyncSession) -> ExportStats:
    findings = await gather_eligible(session)
    by_action: dict[str, int] = {ha.value: 0 for ha in HumanAction}
    by_severity: dict[str, int] = {fs.value: 0 for fs in FindingSeverity}
    for f in findings:
        if f.human_action:
            by_action[f.human_action.value] += 1
        effective = f.human_severity_override or f.severity
        by_severity[effective.value] += 1
    return ExportStats(
        total_eligible=len(findings),
        by_action=by_action,
        by_severity=by_severity,
    )


def _user_prompt(finding: AIFinding, submission_title: str | None) -> str:
    parts: list[str] = []
    if submission_title:
        parts.append(f"# Avance: {submission_title}")
    if finding.section:
        parts.append(f"Sección: {finding.section}")
    parts.append(f"Tipo de hallazgo: {finding.type.value}")
    parts.append(f"Severidad propuesta por IA: {finding.severity.value}")
    parts.append("")
    parts.append("# Hallazgo IA original")
    parts.append(f"Descripción: {finding.description}")
    if finding.instruction:
        parts.append(f"Instrucción: {finding.instruction}")
    if finding.example:
        parts.append(f"Ejemplo: {finding.example}")
    parts.append("")
    parts.append("Decide la severidad final, corrige la descripción si hace falta, o rechaza.")
    return "\n".join(parts)


def _assistant_message(finding: AIFinding) -> dict[str, Any]:
    if finding.human_action == HumanAction.rejected:
        return {
            "action": "reject",
            "reason": finding.human_comment or "El asesor descartó el hallazgo.",
        }
    severity = (finding.human_severity_override or finding.severity).value
    # `modified`: the human comment IS the corrected description (or a delta);
    # we surface it as the canonical "fixed" description.
    description = finding.human_comment or finding.description
    return {
        "action": "keep",
        "severity": severity,
        "description": description,
        "instruction": finding.instruction,
    }


def render_jsonl(findings: list[AIFinding], submission_title_map: dict[UUID, str]) -> str:
    lines: list[str] = []
    for f in findings:
        submission_id_for_title = _eval_to_submission(f)
        title = submission_title_map.get(submission_id_for_title, "") if submission_id_for_title else ""
        record = {
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(f, title or None)},
                {
                    "role": "assistant",
                    "content": json.dumps(_assistant_message(f), ensure_ascii=False),
                },
            ]
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


def _eval_to_submission(finding: AIFinding) -> UUID | None:
    ev = finding.evaluation
    if ev is None:
        return None
    # The relationship chain is finding -> evaluation -> version -> submission.
    # We only loaded `evaluation` here; the caller passes title_map keyed by
    # submission_id, computed separately for efficiency.
    return None  # placeholder — actual mapping resolved in build_dataset.


async def build_dataset(session: AsyncSession) -> tuple[str, int, dict[UUID, str]]:
    """Return (jsonl_text, examples_count, submission_title_map)."""
    findings = await gather_eligible(session)
    if not findings:
        return "", 0, {}

    # Resolve submission titles for context — one query for every finding's eval.
    evaluation_ids = {f.evaluation_id for f in findings}
    title_stmt = (
        select(AIEvaluation.id, Submission.id, Submission.title)
        .join(SubmissionVersion, SubmissionVersion.id == AIEvaluation.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .where(AIEvaluation.id.in_(evaluation_ids))
    )
    rows = (await session.execute(title_stmt)).all()
    eval_to_sub: dict[UUID, UUID] = {row[0]: row[1] for row in rows}
    sub_titles: dict[UUID, str] = {row[1]: row[2] for row in rows}

    # Build the per-finding submission title map: keyed by submission_id used in
    # render_jsonl. Since render needs the title per finding, we resolve here.
    lines: list[str] = []
    for f in findings:
        submission_id = eval_to_sub.get(f.evaluation_id)
        title = sub_titles.get(submission_id) if submission_id else None
        record = {
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(f, title)},
                {
                    "role": "assistant",
                    "content": json.dumps(_assistant_message(f), ensure_ascii=False),
                },
            ]
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    text = "\n".join(lines) + "\n"
    return text, len(findings), sub_titles


async def persist_dataset(text: str) -> str:
    """Write the JSONL to local storage and return its relative path."""
    stored = storage.save_bytes(
        "fine-tuning",
        content=text.encode("utf-8"),
        extension="jsonl",
    )
    return stored.relative_path

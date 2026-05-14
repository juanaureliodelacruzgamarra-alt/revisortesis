"""LLM-backed evaluator. Calls OpenAI (preferred) or Anthropic with JSON output.

Falls back to raising LLMUnavailableError if no API key is configured or the
client/library is missing; the pipeline will then use the stub evaluator.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from kimy.core.config import get_settings
from kimy.services.ai import prompts
from kimy.services.ai.schemas import AIEvaluationDraft

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    """Raised when no LLM backend is usable (missing key, import error, etc.)."""


class LLMResponseError(Exception):
    """Raised when the model replied with output we can't parse into a draft."""


# Models we default to; both support JSON / structured output.
_OPENAI_MODEL = "gpt-4o-mini"
_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"


def evaluate(
    *,
    template_title: str,
    template_structure: dict[str, Any] | None,
    submission_title: str,
    submission_chapter: str | None,
    submission_structure: dict[str, Any] | None,
    submission_text: str,
) -> tuple[AIEvaluationDraft, str, str]:
    """Return (draft, backend_name, model_name) using the first LLM that works."""
    settings = get_settings()
    user_prompt = prompts.build_user_prompt(
        template_title=template_title,
        template_structure=template_structure,
        submission_title=submission_title,
        submission_chapter=submission_chapter,
        submission_structure=submission_structure,
        submission_text=submission_text,
    )

    if settings.openai_api_key:
        try:
            raw = _call_openai(prompts.system_prompt(), user_prompt, settings.openai_api_key)
            return _parse(raw), "openai", _OPENAI_MODEL
        except (LLMResponseError, ValidationError) as exc:
            logger.warning("openai response unusable, falling through: %s", exc)
        except Exception:
            logger.exception("openai call failed, falling through")

    if settings.anthropic_api_key:
        try:
            raw = _call_anthropic(prompts.system_prompt(), user_prompt, settings.anthropic_api_key)
            return _parse(raw), "anthropic", _ANTHROPIC_MODEL
        except (LLMResponseError, ValidationError) as exc:
            logger.warning("anthropic response unusable, falling through: %s", exc)
        except Exception:
            logger.exception("anthropic call failed, falling through")

    raise LLMUnavailableError(
        "No usable LLM backend. Configure OPENAI_API_KEY or ANTHROPIC_API_KEY."
    )


def _parse(raw_json: str) -> AIEvaluationDraft:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"invalid JSON: {exc}") from exc
    return AIEvaluationDraft.model_validate(payload)


def _call_openai(system: str, user: str, api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("openai package not installed") from exc

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=_OPENAI_MODEL,
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = completion.choices[0].message.content
    if not content:
        raise LLMResponseError("openai returned empty content")
    return content


def _call_anthropic(system: str, user: str, api_key: str) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise LLMUnavailableError("anthropic package not installed") from exc

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=4096,
        temperature=0.2,
        system=system,
        messages=[
            {
                "role": "user",
                "content": user
                + "\n\nRecuerda: responde ÚNICAMENTE con el objeto JSON, sin texto adicional, sin Markdown.",
            }
        ],
    )
    if not resp.content:
        raise LLMResponseError("anthropic returned empty content")
    # The model may include leading whitespace or a single code fence.
    raw = "".join(
        getattr(block, "text", "") for block in resp.content if getattr(block, "type", "") == "text"
    ).strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if not raw:
        raise LLMResponseError("anthropic returned no text block")
    return raw

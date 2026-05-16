"""LLM-backed evaluator — Google Gemini (primary) with Anthropic legacy fallback.

Falls back to raising LLMUnavailableError if no provider is usable; the pipeline
will then use the stub evaluator.
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


# Defaults; both support JSON / structured output.
_GEMINI_MODEL = "gemini-2.0-flash"
_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"


def evaluate(
    *,
    template_title: str,
    template_structure: dict[str, Any] | None,
    submission_title: str,
    submission_chapter: str | None,
    submission_structure: dict[str, Any] | None,
    submission_text: str,
    model_override: str | None = None,
) -> tuple[AIEvaluationDraft, str, str]:
    """Return (draft, backend_name, model_name) using the first LLM that works.

    ``model_override`` lets the caller swap the active model at request time —
    used by the pipeline to honour the admin's ``ai.model_preference`` setting.
    """
    settings = get_settings()
    user_prompt = prompts.build_user_prompt(
        template_title=template_title,
        template_structure=template_structure,
        submission_title=submission_title,
        submission_chapter=submission_chapter,
        submission_structure=submission_structure,
        submission_text=submission_text,
    )

    gemini_model = model_override or _GEMINI_MODEL
    if settings.gemini_api_key:
        try:
            raw = _call_gemini(
                prompts.system_prompt(),
                user_prompt,
                settings.gemini_api_key,
                model=gemini_model,
            )
            return _parse(raw), "gemini", gemini_model
        except (LLMResponseError, ValidationError) as exc:
            logger.warning("gemini response unusable, falling through: %s", exc)
        except Exception:
            logger.exception("gemini call failed, falling through")

    # Legacy fallback — only triggers if Anthropic key is set AND Gemini failed.
    if settings.anthropic_api_key:
        try:
            raw = _call_anthropic(prompts.system_prompt(), user_prompt, settings.anthropic_api_key)
            return _parse(raw), "anthropic", _ANTHROPIC_MODEL
        except (LLMResponseError, ValidationError) as exc:
            logger.warning("anthropic response unusable, falling through: %s", exc)
        except Exception:
            logger.exception("anthropic call failed, falling through")

    raise LLMUnavailableError(
        "No usable LLM backend. Configure GEMINI_API_KEY (or ANTHROPIC_API_KEY as fallback)."
    )


def _parse(raw_json: str) -> AIEvaluationDraft:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"invalid JSON: {exc}") from exc
    return AIEvaluationDraft.model_validate(payload)


def _call_gemini(system: str, user: str, api_key: str, *, model: str = _GEMINI_MODEL) -> str:
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError as exc:
        raise LLMUnavailableError("google-genai package not installed") from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=genai_types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    text = getattr(response, "text", None)
    if not text:
        raise LLMResponseError("gemini returned empty content")
    return text


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

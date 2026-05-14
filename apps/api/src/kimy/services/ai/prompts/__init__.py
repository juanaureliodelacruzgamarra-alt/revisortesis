"""Versioned prompts. Always reference by version so AIEvaluation.prompt_version
can be replayed/audited later.

Current default: v1.
"""
from kimy.services.ai.prompts.v1 import PROMPT_VERSION, build_user_prompt, system_prompt

__all__ = ["PROMPT_VERSION", "build_user_prompt", "system_prompt"]

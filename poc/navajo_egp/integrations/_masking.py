"""
Request masking shared by the SDK wrappers (E014/E015).

Every message of one request is masked with one session, so the same person keeps the same
placeholder across the conversation (earlier assistant replies carry restored real names).
Plain text and lists of text blocks are masked; anything the wrapper cannot mask (images, tool
calls, extra message fields) is refused before the provider is called.
"""

from __future__ import annotations

import re
from typing import Any

_MESSAGE_FIELDS = {"role", "content"}
_ROLES = {"system", "developer", "user", "assistant"}
_TEXT_BLOCK_FIELDS = {"type", "text", "cache_control"}
_CACHE_CONTROL = {"type": "ephemeral"}  # the only cache setting forwarded (E018)
# request arguments that carry no free text; anything else (tools, extra_body, metadata, user,
# response_format, stream …) is refused, because the wrapper would forward it unmasked (E016)
OPENAI_ARGS = {"model", "messages", "temperature", "top_p", "max_tokens", "max_completion_tokens", "n", "seed",
               "presence_penalty", "frequency_penalty", "timeout"}
_MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}")
ANTHROPIC_ARGS = {"model", "messages", "system", "max_tokens", "temperature", "top_p", "top_k", "timeout"}


def check_args(kwargs: dict, allowed: set) -> None:
    """Only messages and system text are masked; the model name and numeric settings pass as given (E017)."""
    extra = set(kwargs) - allowed
    if extra:
        raise TypeError(f"arguments {sorted(extra)} cannot be masked; refusing to send them")
    model = kwargs.get("model")
    if model is not None and not (isinstance(model, str) and _MODEL_NAME.fullmatch(model)):
        raise TypeError("model must be a plain model name")
    for key, value in kwargs.items():
        if key not in {"model", "messages", "system"} and value is not None and not isinstance(value, (int, float)):
            raise TypeError(f"argument {key!r} must be a number")


def blocked(name: str):
    raise AttributeError(f"'{name}' is not protected by the shield; call the original client knowingly")


def mask_request(egp: Any, messages: list, system: Any = None) -> tuple[list, Any, Any]:
    """Return (masked messages, masked system, session or None). Destroys the session on refusal."""
    holder: list = []

    def text(value: str) -> str:
        anon, session = egp.anonymize(value, session=holder[0] if holder else None)
        if not holder:
            holder.append(session)
        return anon

    def content(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return text(value)
        if isinstance(value, list):
            blocks = []
            for block in value:
                if (isinstance(block, dict) and block.get("type") == "text"
                        and isinstance(block.get("text"), str) and set(block) <= _TEXT_BLOCK_FIELDS
                        and block.get("cache_control", _CACHE_CONTROL) == _CACHE_CONTROL):
                    blocks.append({**block, "text": text(block["text"])})
                else:
                    kind = block.get("type") if isinstance(block, dict) else type(block).__name__
                    raise TypeError(f"content block {kind!r} cannot be masked; refusing to send it")
            return blocks
        raise TypeError(f"message content of type {type(value).__name__} cannot be masked; refusing to send it")

    try:
        masked = []
        for msg in messages:
            extra = set(msg) - _MESSAGE_FIELDS
            if extra:
                raise TypeError(f"message fields {sorted(extra)} cannot be masked; refusing to send them")
            if msg.get("role") not in _ROLES:
                raise TypeError("unknown message role; refusing to send it")
            masked.append({**msg, "content": content(msg.get("content"))})
        masked_system = content(system)
    except Exception:
        for session in holder:
            session.destroy()
        raise
    return masked, masked_system, (holder[0] if holder else None)

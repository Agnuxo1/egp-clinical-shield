"""
Request masking shared by the SDK wrappers (E014/E015).

Every message of one request is masked with one session, so the same person keeps the same
placeholder across the conversation (earlier assistant replies carry restored real names).
Plain text and lists of text blocks are masked; anything the wrapper cannot mask (images, tool
calls, extra message fields) is refused before the provider is called.
"""

from __future__ import annotations

from typing import Any

_MESSAGE_FIELDS = {"role", "content"}
_TEXT_BLOCK_FIELDS = {"type", "text", "cache_control"}
# request arguments that carry no free text; anything else (tools, extra_body, metadata, user,
# response_format, stream …) is refused, because the wrapper would forward it unmasked (E016)
OPENAI_ARGS = {"model", "messages", "temperature", "top_p", "max_tokens", "max_completion_tokens", "n", "seed",
               "presence_penalty", "frequency_penalty", "timeout"}
ANTHROPIC_ARGS = {"model", "messages", "system", "max_tokens", "temperature", "top_p", "top_k", "timeout"}


def check_args(kwargs: dict, allowed: set) -> None:
    extra = set(kwargs) - allowed
    if extra:
        raise TypeError(f"arguments {sorted(extra)} cannot be masked; refusing to send them")


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
                        and isinstance(block.get("text"), str) and set(block) <= _TEXT_BLOCK_FIELDS):
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
            masked.append({**msg, "content": content(msg.get("content"))})
        masked_system = content(system)
    except Exception:
        for session in holder:
            session.destroy()
        raise
    return masked, masked_system, (holder[0] if holder else None)

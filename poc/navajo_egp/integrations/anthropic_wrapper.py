"""
Anthropic SDK wrapper — NavajoAnthropic.

Wraps ``anthropic.Anthropic`` (sync).
Intercepts ``messages.create()`` transparently.

Usage:
    import anthropic
    from navajo_egp import EGPMiddleware

    egp = EGPMiddleware()
    client = egp.wrap(anthropic.Anthropic())

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Patient Juan García, DNI 12345678A…"}]
    )
    # message.content[0].text is already de-anonymised
"""

from __future__ import annotations

import logging
from typing import Any

from navajo_egp.integrations._masking import ANTHROPIC_ARGS, blocked, check_args, mask_request

logger = logging.getLogger(__name__)


class _NavajoMessages:
    """Proxy for client.messages with EGP applied."""

    def __init__(self, original_messages: Any, egp: Any) -> None:
        self._original = original_messages
        self._egp = egp

    def _prepare(self, kwargs: dict) -> Any:
        check_args(kwargs, ANTHROPIC_ARGS)
        messages, system, session = mask_request(self._egp, kwargs.get("messages", []), kwargs.get("system"))
        kwargs["messages"] = messages
        if "system" in kwargs:
            kwargs["system"] = system
        return session

    def _restore(self, response: Any, session: Any) -> None:
        for block in response.content:
            if getattr(block, "text", None):
                block.text = self._egp.deanonymize(block.text, session)

    def create(self, **kwargs: Any) -> Any:
        session = self._prepare(kwargs)
        # the session is destroyed even if the provider call fails
        try:
            response = self._original.create(**kwargs)
            if session is not None:
                self._restore(response, session)
        finally:
            if session is not None:
                session.destroy()
        return response

    async def acreate(self, **kwargs: Any) -> Any:
        """Async variant (for AsyncAnthropic)."""
        session = self._prepare(kwargs)
        try:
            response = await self._original.acreate(**kwargs)
            if session is not None:
                self._restore(response, session)
        finally:
            if session is not None:
                session.destroy()
        return response


class NavajoAnthropic:
    """
    Wraps ``anthropic.Anthropic`` with automatic EGP anonymisation.
    """

    def __init__(self, client: Any, egp: Any) -> None:
        self._client = client
        self._egp = egp
        self.messages = _NavajoMessages(client.messages, egp)

    def __getattr__(self, name: str) -> Any:
        # other client APIs would bypass masking (E016)
        blocked(name)

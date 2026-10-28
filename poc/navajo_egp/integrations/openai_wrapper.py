"""
OpenAI SDK wrapper — NavajoOpenAI.

Wraps ``openai.OpenAI`` (sync) and ``openai.AsyncOpenAI`` (async).
Intercepts ``chat.completions.create()`` calls transparently.

Usage:
    from openai import OpenAI
    from navajo_egp import EGPMiddleware

    egp = EGPMiddleware()
    client = egp.wrap(OpenAI())

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Patient Juan García, DNI 12345678A…"}]
    )
    # response.choices[0].message.content is already de-anonymised
"""

from __future__ import annotations

import logging
from typing import Any

from navajo_egp.integrations._masking import OPENAI_ARGS, blocked, check_args, mask_request

logger = logging.getLogger(__name__)


class _NavajoChatCompletions:
    """Proxy for client.chat.completions with EGP applied."""

    def __init__(self, original_completions: Any, egp: Any) -> None:
        self._original = original_completions
        self._egp = egp

    def _restore(self, response: Any, session: Any) -> None:
        for choice in response.choices:
            if getattr(choice.message, "content", None):
                choice.message.content = self._egp.deanonymize(choice.message.content, session)

    def create(self, **kwargs: Any) -> Any:
        check_args(kwargs, OPENAI_ARGS)
        kwargs["messages"], _, session = mask_request(self._egp, kwargs.get("messages", []))
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
        """Async variant."""
        check_args(kwargs, OPENAI_ARGS)
        kwargs["messages"], _, session = mask_request(self._egp, kwargs.get("messages", []))
        try:
            response = await self._original.acreate(**kwargs)
            if session is not None:
                self._restore(response, session)
        finally:
            if session is not None:
                session.destroy()
        return response


class _NavajoChatNamespace:
    def __init__(self, chat_ns: Any, egp: Any) -> None:
        self.completions = _NavajoChatCompletions(chat_ns.completions, egp)


class NavajoOpenAI:
    """
    Wraps ``openai.OpenAI`` with automatic EGP anonymisation.

    All other attributes are proxied transparently to the original client,
    so ``client.models.list()`` etc. still work unchanged.
    """

    def __init__(self, client: Any, egp: Any) -> None:
        self._client = client
        self._egp = egp
        self.chat = _NavajoChatNamespace(client.chat, egp)

    def __getattr__(self, name: str) -> Any:
        # other client APIs (responses, files …) would bypass masking (E016)
        blocked(name)

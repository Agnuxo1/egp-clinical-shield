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

logger = logging.getLogger(__name__)


class _NavajoChatCompletions:
    """Proxy for client.chat.completions with EGP applied."""

    def __init__(self, original_completions: Any, egp: Any) -> None:
        self._original = original_completions
        self._egp = egp

    def create(self, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        sessions: list = []

        # Anonymise every message that carries text
        new_messages = []
        for msg in messages:
            # every role, assistant included: earlier replies carry restored real names (E014)
            if isinstance(msg.get("content"), str):
                # one session per request: the same person keeps the same placeholder in every message
                anon_content, session = self._egp.anonymize(msg["content"], session=sessions[0] if sessions else None)
                if not sessions:
                    sessions.append(session)
                new_msg = dict(msg)
                new_msg["content"] = anon_content
                new_messages.append(new_msg)
            else:
                new_messages.append(msg)

        kwargs["messages"] = new_messages

        # Call the real API and restore the reply; sessions are destroyed even if the call fails
        try:
            response = self._original.create(**kwargs)
            for choice in response.choices:
                if hasattr(choice.message, "content") and choice.message.content:
                    restored = choice.message.content
                    for session in reversed(sessions):
                        restored = self._egp.deanonymize(restored, session)
                    choice.message.content = restored
        finally:
            for session in sessions:
                session.destroy()

        return response

    async def acreate(self, **kwargs: Any) -> Any:
        """Async variant."""
        messages = kwargs.get("messages", [])
        sessions: list = []

        new_messages = []
        for msg in messages:
            # every role, assistant included: earlier replies carry restored real names (E014)
            if isinstance(msg.get("content"), str):
                # one session per request: the same person keeps the same placeholder in every message
                anon_content, session = self._egp.anonymize(msg["content"], session=sessions[0] if sessions else None)
                if not sessions:
                    sessions.append(session)
                new_msg = dict(msg)
                new_msg["content"] = anon_content
                new_messages.append(new_msg)
            else:
                new_messages.append(msg)

        kwargs["messages"] = new_messages

        try:
            response = await self._original.acreate(**kwargs)
            for choice in response.choices:
                if hasattr(choice.message, "content") and choice.message.content:
                    restored = choice.message.content
                    for session in reversed(sessions):
                        restored = self._egp.deanonymize(restored, session)
                    choice.message.content = restored
        finally:
            for session in sessions:
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
        return getattr(self._client, name)

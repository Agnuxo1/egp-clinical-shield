"""
Tests for extended navajo-egp features:
  - Custom PII patterns (add_pattern)
  - AsyncEGPMiddleware
  - Streaming wrapper
"""

import asyncio
import pytest
from navajo_egp import EGPMiddleware, AsyncEGPMiddleware, stream_with_egp


# ---------------------------------------------------------------------------
# Custom patterns
# ---------------------------------------------------------------------------

class TestCustomPatterns:
    def test_custom_pattern_detected(self):
        egp = EGPMiddleware(use_spacy=False)
        egp.add_pattern(
            label="HOSPITAL_ID",
            pattern=r"\bHID-\d{6}\b",
            placeholder_prefix="HID_",
        )
        anon, session = egp.anonymize("Patient HID-123456 presented with fever.")
        assert "HID-123456" not in anon
        assert "HID_001" in anon
        session.destroy()

    def test_custom_pattern_roundtrip(self):
        egp = EGPMiddleware(use_spacy=False)
        egp.add_pattern(
            label="EMPLOYEE_ID",
            pattern=r"\bEMP-\d{4}\b",
            placeholder_prefix="EMP_",
        )
        original = "Employee EMP-1234 requested leave. Contact EMP-1234 for details."
        anon, session = egp.anonymize(original)
        assert "EMP-1234" not in anon
        # Same ID should get same placeholder
        assert anon.count("EMP_001") == 2
        restored = egp.deanonymize(anon, session)
        assert "EMP-1234" in restored
        session.destroy()

    def test_custom_and_builtin_patterns_coexist(self):
        egp = EGPMiddleware(use_spacy=False)
        egp.add_pattern(
            label="CASE_NUM",
            pattern=r"\bCASE-\d{5}\b",
            placeholder_prefix="CASE_",
        )
        text = "Client email@example.com filed CASE-98765."
        anon, session = egp.anonymize(text)
        assert "email@example.com" not in anon
        assert "CASE-98765" not in anon
        assert "EMAIL_" in anon
        assert "CASE_001" in anon
        session.destroy()

    def test_custom_pattern_default_prefix(self):
        """If no placeholder_prefix is given, it defaults to label + '_'."""
        egp = EGPMiddleware(use_spacy=False)
        egp.add_pattern(label="BADGE", pattern=r"\bB\d{5}\b")
        anon, session = egp.anonymize("Badge B12345 scanned at gate.")
        assert "B12345" not in anon
        assert "BADGE_" in anon
        session.destroy()


# ---------------------------------------------------------------------------
# AsyncEGPMiddleware
# ---------------------------------------------------------------------------

class TestAsyncMiddleware:
    def test_async_anonymize_returns_same_as_sync(self):
        """async_anonymize should produce identical output to synchronous anonymize."""
        egp_sync = EGPMiddleware(use_spacy=False)
        egp_async = AsyncEGPMiddleware(use_spacy=False)

        text = "Contact alice@example.com and SSN 123-45-6789"

        anon_sync, sess_sync = egp_sync.anonymize(text)
        anon_async, sess_async = asyncio.run(egp_async.async_anonymize(text))

        # Both should have anonymised the same entity types
        assert "alice@example.com" not in anon_sync
        assert "alice@example.com" not in anon_async
        assert "123-45-6789" not in anon_sync
        assert "123-45-6789" not in anon_async

        sess_sync.destroy()
        sess_async.destroy()

    def test_async_wrap_llm_call(self):
        egp = AsyncEGPMiddleware(use_spacy=False)

        async def mock_async_llm(prompt: str) -> str:
            return f"Response to prompt of {len(prompt)} chars."

        result = asyncio.run(egp.async_wrap_llm_call(
            prompt="Send to bob@clinic.org for review.",
            llm_fn=mock_async_llm,
        ))
        # Result should be a string (session auto-destroyed)
        assert isinstance(result, str)

    def test_async_roundtrip(self):
        """Full async anonymize → deanonymize roundtrip."""
        egp = AsyncEGPMiddleware(use_spacy=False)

        async def run():
            original = "Patient DNI 12345678A has IBAN ES91 2100 0418 4502 0005 1332"
            anon, session = await egp.async_anonymize(original)
            assert "12345678A" not in anon
            assert "ES91" not in anon
            restored = await egp.async_deanonymize(anon, session)
            assert "12345678A" in restored
            assert "ES91" in restored
            session.destroy()

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Streaming wrapper
# ---------------------------------------------------------------------------

class TestStreaming:
    def test_stream_basic(self):
        egp = EGPMiddleware(use_spacy=False)

        def mock_stream(anon_prompt: str):
            """Yields chunks of a mocked LLM response."""
            words = ["The", " patient", " ENTITY_A", " has", " diabetes."]
            for word in words:
                yield word

        chunks = list(stream_with_egp(
            prompt="Patient Juan Garcia has diabetes.",
            egp=egp,
            stream_fn=mock_stream,
            chunk_text_fn=lambda c: c,  # identity — the chunk IS the string
        ))
        full = "".join(chunks)
        # The full response should have the name restored
        assert "ENTITY_A" not in full or "Juan Garcia" in full

    def test_stream_single_chunk_output(self):
        """By default (word_by_word=False) only one chunk is yielded."""
        egp = EGPMiddleware(use_spacy=False)

        def mock_stream(prompt: str):
            yield "EMAIL_001 has been notified."

        chunks = list(stream_with_egp(
            prompt="alice@example.com has been notified.",
            egp=egp,
            stream_fn=mock_stream,
            chunk_text_fn=lambda c: c,
        ))
        assert len(chunks) == 1
        assert "alice@example.com" in chunks[0]

    def test_stream_word_by_word(self):
        """word_by_word=True should yield multiple chunks."""
        egp = EGPMiddleware(use_spacy=False)

        def mock_stream(prompt: str):
            yield "Sending to EMAIL_001 now."

        chunks = list(stream_with_egp(
            prompt="Sending to alice@example.com now.",
            egp=egp,
            stream_fn=mock_stream,
            chunk_text_fn=lambda c: c,
            word_by_word=True,
        ))
        # Should have multiple word-level chunks
        assert len(chunks) > 1
        # Reassembled text should contain the restored email
        full = "".join(chunks)
        assert "alice@example.com" in full

    def test_stream_no_pii_passthrough(self):
        """Texts with no PII should pass through unchanged."""
        egp = EGPMiddleware(use_spacy=False)

        def mock_stream(prompt: str):
            yield "The sky is blue and the grass is green."

        chunks = list(stream_with_egp(
            prompt="The sky is blue and the grass is green.",
            egp=egp,
            stream_fn=mock_stream,
            chunk_text_fn=lambda c: c,
        ))
        full = "".join(chunks)
        assert "sky" in full
        assert "green" in full

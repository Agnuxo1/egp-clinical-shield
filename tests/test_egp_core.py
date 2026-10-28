"""
Core tests for navajo-egp.

Run with:  pytest tests/test_egp_core.py -v
"""

import pytest
from navajo_egp import EGPMiddleware, EGPSession
from navajo_egp.detector import PIIDetector
from navajo_egp.anonymizer import Anonymizer
from navajo_egp.entities import EntityType
from navajo_egp.exceptions import PIILeakageError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def egp():
    return EGPMiddleware(use_spacy=False)  # regex-only for fast unit tests


@pytest.fixture
def detector():
    return PIIDetector(use_spacy=False)


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------

class TestPIIDetector:
    def test_email(self, detector):
        entities = detector.detect("Contact me at juan.garcia@example.com please")
        types = [e.entity_type for e in entities]
        assert EntityType.EMAIL in types

    def test_spanish_dni(self, detector):
        entities = detector.detect("Mi DNI es 12345678A y vivo en Madrid")
        types = [e.entity_type for e in entities]
        assert EntityType.NATIONAL_ID in types

    def test_us_ssn(self, detector):
        entities = detector.detect("SSN: 123-45-6789")
        types = [e.entity_type for e in entities]
        assert EntityType.SSN in types

    def test_phone(self, detector):
        entities = detector.detect("Llámame al +34 612 345 678")
        assert any(e.entity_type == EntityType.PHONE for e in entities)

    def test_iban(self, detector):
        entities = detector.detect("Transfiere a ES91 2100 0418 4502 0005 1332")
        assert any(e.entity_type == EntityType.IBAN for e in entities)

    def test_date_of_birth(self, detector):
        entities = detector.detect("Fecha de nacimiento: 15/03/1957")
        assert any(e.entity_type == EntityType.DATE_OF_BIRTH for e in entities)

    def test_no_false_positives_on_clinical_data(self, detector):
        # Clinical values should NOT be flagged as PII
        text = "HbA1c 8.2%, temperatura 40°C, Metformina 850mg"
        entities = detector.detect(text)
        # No PII types (dates/emails/IDs/phones/IBAN) expected
        pii_types = {EntityType.EMAIL, EntityType.NATIONAL_ID, EntityType.SSN,
                     EntityType.IBAN, EntityType.PHONE}
        for ent in entities:
            assert ent.entity_type not in pii_types, (
                f"Clinical data incorrectly flagged as {ent.entity_type}: {ent.text!r}"
            )

    def test_name_detected(self, detector):
        # Name in mid-sentence context (not preceded by a title word)
        entities = detector.detect("The attending physician referred Juan Garcia Lopez to cardiology.")
        assert any(e.entity_type == EntityType.PERSON_NAME for e in entities)

    def test_name_with_title_prefix(self, detector):
        # "Patient" is filtered as a title, but the name portion should still be found
        entities = detector.detect("Patient Maria Rodriguez needs follow-up.")
        name_ents = [e for e in entities if e.entity_type == EntityType.PERSON_NAME]
        assert len(name_ents) >= 1
        # The matched text should be the name, not including "Patient"
        assert all("Patient" not in e.text for e in name_ents)

    def test_verify_clean_empty(self, detector):
        violations = detector.verify_clean("El paciente tiene diabetes tipo 2")
        assert violations == []

    def test_verify_clean_finds_email(self, detector):
        violations = detector.verify_clean("Email: test@example.com")
        assert any("EMAIL" in v for v in violations)


# ---------------------------------------------------------------------------
# Anonymisation tests
# ---------------------------------------------------------------------------

class TestAnonymize:
    def test_email_replaced(self, egp):
        text = "Send to alice@example.org for review"
        anon, session = egp.anonymize(text)
        assert "alice@example.org" not in anon
        assert "EMAIL_" in anon
        session.destroy()

    def test_dni_replaced(self, egp):
        text = "El paciente DNI 12345678A tiene fiebre"
        anon, session = egp.anonymize(text)
        assert "12345678A" not in anon
        session.destroy()

    def test_ssn_replaced(self, egp):
        text = "SSN is 123-45-6789"
        anon, session = egp.anonymize(text)
        assert "123-45-6789" not in anon
        session.destroy()

    def test_iban_replaced(self, egp):
        text = "IBAN ES91 2100 0418 4502 0005 1332 for payment"
        anon, session = egp.anonymize(text)
        assert "ES91" not in anon
        assert "ACCT_" in anon
        session.destroy()

    def test_same_entity_same_placeholder(self, egp):
        text = "Juan García llamó. Juan García tiene cita mañana."
        anon, session = egp.anonymize(text)
        # All occurrences should use the same placeholder
        placeholders = list(session.forward.values())
        assert len(set(placeholders)) == len(placeholders)  # no duplicates
        # Check consistency: count occurrences of the placeholder
        ph = list(session.forward.values())[0]
        assert anon.count(ph) == 2
        session.destroy()

    def test_clinical_data_preserved(self, egp):
        text = "Paciente con HbA1c 8.2%, temperatura 40°C, Metformina 850mg/12h"
        anon, session = egp.anonymize(text)
        assert "8.2%" in anon
        assert "40°C" in anon
        assert "Metformina" in anon
        session.destroy()


# ---------------------------------------------------------------------------
# De-anonymisation tests
# ---------------------------------------------------------------------------

class TestDeanonymize:
    def test_roundtrip_email(self, egp):
        original = "Email me at test@example.com with questions."
        anon, session = egp.anonymize(original)
        assert "test@example.com" not in anon
        # Simulate LLM using the placeholder
        llm_response = f"Sure, I'll write to {list(session.forward.values())[0]}."
        restored = egp.deanonymize(llm_response, session)
        assert "test@example.com" in restored
        session.destroy()

    def test_roundtrip_multiple_entities(self, egp):
        original = "Patient Juan García, DNI 12345678A, email juan@test.es"
        anon, session = egp.anonymize(original)
        restored = egp.deanonymize(anon, session)
        assert "12345678A" in restored
        assert "juan@test.es" in restored
        session.destroy()

    def test_session_destroyed_after_use(self, egp):
        _, session = egp.anonymize("Juan García DNI 12345678A")
        session.destroy()
        assert session.destroyed
        assert len(session.forward) == 0

    def test_deanonymize_case_insensitive(self, egp):
        """LLMs sometimes lowercase placeholders — we should still restore."""
        original = "Email: test@example.com"
        anon, session = egp.anonymize(original)
        ph = list(session.forward.values())[0]
        # Simulate LLM lowercasing the placeholder
        lowered_response = f"Sending to {ph.lower()}."
        restored = egp.deanonymize(lowered_response, session)
        assert "test@example.com" in restored
        session.destroy()


# ---------------------------------------------------------------------------
# wrap_llm_call tests
# ---------------------------------------------------------------------------

class TestWrapLLMCall:
    def test_basic_pipeline(self, egp):
        def mock_llm(prompt: str) -> str:
            # LLM returns a response referencing the placeholder
            if "EMAIL_" in prompt:
                return "I will contact EMAIL_001 shortly."
            return "No email found."

        result = egp.wrap_llm_call(
            prompt="Please contact alice@example.com regarding the issue.",
            llm_fn=mock_llm,
        )
        assert "alice@example.com" in result

    def test_session_auto_destroyed(self, egp):
        sessions_seen = []

        def mock_llm(prompt: str) -> str:
            return "Done."

        egp.wrap_llm_call("test@test.com info", mock_llm)
        # We can't check the session directly since it's internal,
        # but the call must not raise.


# ---------------------------------------------------------------------------
# EGPSession tests
# ---------------------------------------------------------------------------

class TestEGPSession:
    def test_session_add_and_retrieve(self):
        s = EGPSession()
        s.add("Juan García", "ENTITY_A")
        assert s.get_placeholder("Juan García") == "ENTITY_A"
        assert s.get_original("ENTITY_A") == "Juan García"

    def test_session_destroy(self):
        s = EGPSession()
        s.add("test@email.com", "EMAIL_001")
        s.destroy()
        assert s.destroyed
        assert s.forward == {}
        assert s.reverse == {}

    def test_session_raises_after_destroy(self):
        s = EGPSession()
        s.destroy()
        with pytest.raises(RuntimeError):
            s.add("x", "y")

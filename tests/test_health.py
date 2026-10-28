"""Health pack (c2): behaviour on short invented notes. No real patient data."""

from deid import systems as S
from deid.health import HealthPatterns

NOTE = (
    "Datos del paciente.\n"
    "Nombre: Lucía.\n"
    "Apellidos: Ferrer Molina.\n"
    "NHC: 4471023.\n"
    "Domicilio: Calle Mayor 12, 3º Izq.\n"
    "Localidad/ Provincia: Zaragoza.\n"
    "Fecha de nacimiento: 02/02/1961.\n"
    "Médico: Pablo Ruiz Soto  NºCol: 50 50 12345.\n"
    "Informe clínico del paciente: Mujer de 65 años con HbA1c 8,2 % y metformina 850 mg.\n"
    "Dr. Pablo Ruiz Soto. Servicio de Endocrinología. Hospital Miguel Servet. Tfno: 976 76 55 00.\n"
)


def masked(text, spans):
    return [text[s:e] for _, s, e in spans]


def system():
    return S.Navajo(use_spacy=False, extra=HealthPatterns("c2"))


def test_identifiers_masked():
    got = masked(NOTE, system().spans(NOTE))
    for value in ["Lucía", "Ferrer Molina", "4471023", "Zaragoza", "02/02/1961", "50 50 12345", "976 76 55 00"]:
        assert value in got, value
    assert any(v.startswith("Calle Mayor 12") for v in got)
    assert any("Hospital Miguel Servet" in v for v in got)


def test_clinical_content_kept():
    got = " ".join(masked(NOTE, system().spans(NOTE)))
    for kept in ["65 años", "Mujer", "HbA1c", "metformina", "850 mg", "Servicio de Endocrinología"]:
        assert kept not in got, kept


def test_doctor_title_not_read_as_street():
    # v0.1.0 ADDRESS reads Spanish "Dr." as English "drive" and swallows the next 60 characters
    got = masked(NOTE, system().spans(NOTE))
    assert "Pablo Ruiz Soto" in got
    assert not any(v.startswith("Dr.") for v in got)


def test_roundtrip_is_byte_exact():
    exact, ws, anon = S.roundtrip(NOTE, system().spans(NOTE), lossless=True)
    assert exact and ws
    assert "Ferrer Molina" not in anon and "4471023" not in anon


def test_shield_wraps_openai_style_client():
    """End-to-end through the SDK wrapper with a fake client: what the model receives, what comes back."""
    from types import SimpleNamespace
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from deid.shield import ClinicalShield

    received = []

    class FakeCompletions:
        def create(self, **kwargs):
            prompt = kwargs["messages"][-1]["content"]
            received.append(prompt)
            reply = "Summary for " + prompt.split("Apellidos: ")[1].split(".")[0] + ": review HbA1c."
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    client = NavajoOpenAI(SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())), ClinicalShield())
    out = client.chat.completions.create(model="any", messages=[{"role": "user", "content": NOTE}])
    sent = received[0]
    for secret in ["Lucía", "Ferrer Molina", "4471023", "Zaragoza", "02/02/1961", "976 76 55 00"]:
        assert secret not in sent, secret
    assert "65 años" in sent and "metformina 850 mg" in sent
    assert out.choices[0].message.content == "Summary for Ferrer Molina: review HbA1c."


def test_shield_roundtrip_identity_model():
    from deid.shield import ClinicalShield

    shield = ClinicalShield()
    assert shield.wrap_llm_call(prompt=NOTE, llm_fn=lambda p: p) == NOTE


def test_v01_roundtrip_changes_whitespace():
    # documented limitation of navajo-egp 0.1.0 (experiments/LOG.md E002)
    spans = S.Navajo(use_spacy=False).spans(NOTE)
    exact, ws, _ = S.roundtrip(NOTE, spans, lossless=False)
    assert not exact and ws

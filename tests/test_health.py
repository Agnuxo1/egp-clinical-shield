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


def _fake_openai(received, reply=None, fail=False):
    from types import SimpleNamespace

    class FakeCompletions:
        def create(self, **kwargs):
            received.append([m["content"] for m in kwargs["messages"]])
            if fail:
                raise RuntimeError("provider down")
            text = reply or "ok"
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])

    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))


def test_multiturn_history_is_masked_consistently():
    """E014: earlier assistant replies hold restored real names and must be masked again."""
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from deid.shield import ClinicalShield

    received = []
    client = NavajoOpenAI(_fake_openai(received), ClinicalShield())
    history = [
        {"role": "user", "content": NOTE},
        {"role": "assistant", "content": "Summary for Ferrer Molina: review HbA1c."},
        {"role": "user", "content": "Draft a letter about Ferrer Molina for Dr. Pablo Ruiz Soto."},
    ]
    client.chat.completions.create(model="any", messages=history)
    sent = received[0]
    for msg in sent:
        for secret in ["Ferrer Molina", "Lucía", "Pablo Ruiz Soto", "4471023"]:
            assert secret not in msg, (secret, msg)
    # the same surname gets the same placeholder in every message of the request
    placeholder = sent[1].split("Summary for ")[1].split(":")[0]
    assert placeholder in sent[0] and placeholder in sent[2]


def test_anthropic_history_is_masked():
    from types import SimpleNamespace
    from navajo_egp.integrations.anthropic_wrapper import NavajoAnthropic
    from deid.shield import ClinicalShield

    received = []

    class FakeMessages:
        def create(self, **kwargs):
            received.append([m["content"] for m in kwargs["messages"]] + [kwargs.get("system", "")])
            return SimpleNamespace(content=[SimpleNamespace(text="ok")])

    client = NavajoAnthropic(SimpleNamespace(messages=FakeMessages()), ClinicalShield())
    client.messages.create(model="any", max_tokens=10, system="Patient file of Ferrer Molina.",
                           messages=[{"role": "user", "content": NOTE},
                                     {"role": "assistant", "content": "Noted for Ferrer Molina."}])
    assert not any("Ferrer Molina" in m for m in received[0])


def test_structured_text_blocks_are_masked():
    """E015: lists of text blocks (OpenAI and Anthropic formats) are masked with the same session."""
    from types import SimpleNamespace
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from navajo_egp.integrations.anthropic_wrapper import NavajoAnthropic
    from deid.shield import ClinicalShield

    blocks = [{"type": "text", "text": NOTE}, {"type": "text", "text": "Contact: lucia.ferrer@example.com"}]
    received = []
    NavajoOpenAI(_fake_openai(received), ClinicalShield()).chat.completions.create(
        model="any", messages=[{"role": "user", "content": blocks}])
    sent = " ".join(b["text"] for b in received[0][0])
    assert "Ferrer Molina" not in sent and "lucia.ferrer@example.com" not in sent and "65 años" in sent

    got = []

    class FakeMessages:
        def create(self, **kwargs):
            got.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text="ok")])

    NavajoAnthropic(SimpleNamespace(messages=FakeMessages()), ClinicalShield()).messages.create(
        model="any", max_tokens=10, system=[{"type": "text", "text": "Contact lucia.ferrer@example.com"}],
        messages=[{"role": "user", "content": blocks}])
    flat = str(got[0]["messages"]) + str(got[0]["system"])
    assert "lucia.ferrer@example.com" not in flat and "Ferrer Molina" not in flat


def test_unmaskable_content_is_refused_before_sending(monkeypatch):
    import pytest
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from navajo_egp.session import EGPSession
    from deid.shield import ClinicalShield

    destroyed = []
    original = EGPSession.destroy
    monkeypatch.setattr(EGPSession, "destroy", lambda self: destroyed.append(self) or original(self))
    received = []
    client = NavajoOpenAI(_fake_openai(received), ClinicalShield())
    image = [{"type": "text", "text": NOTE}, {"type": "image_url", "image_url": {"url": "data:..."}}]
    with pytest.raises(TypeError):
        client.chat.completions.create(model="any", messages=[{"role": "user", "content": image}])
    tool_call = {"role": "assistant", "content": None,
                 "tool_calls": [{"function": {"arguments": '{"patient": "Lucía Ferrer Molina"}'}}]}
    with pytest.raises(TypeError):
        client.chat.completions.create(model="any", messages=[{"role": "user", "content": NOTE}, tool_call])
    for bad in ([{"role": "user", "content": [{"type": "text", "text": "hi", "cache_control": {"type": "lucia.ferrer@example.com"}}]}],
                [{"role": "user12345678A", "content": "hi"}]):
        with pytest.raises(TypeError):
            client.chat.completions.create(model="any", messages=bad)
    assert received == []  # nothing reached the provider
    assert destroyed and all(s.destroyed for s in destroyed)


def test_unmasked_arguments_and_other_apis_are_blocked():
    """E016: free-text arguments and other client APIs would bypass masking, so they are refused."""
    import pytest
    from types import SimpleNamespace
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from navajo_egp.integrations.anthropic_wrapper import NavajoAnthropic
    from navajo_egp.integrations.langchain_wrapper import NavajoChatModel
    from deid.shield import ClinicalShield

    received = []
    raw = _fake_openai(received)
    raw.responses = SimpleNamespace(create=lambda **kw: received.append(kw))
    client = NavajoOpenAI(raw, ClinicalShield())
    msg = [{"role": "user", "content": "Contact lucia.ferrer@example.com"}]
    with pytest.raises(TypeError):
        client.chat.completions.create(model="any", messages=msg, extra_body={"note": "lucia.ferrer@example.com"})
    with pytest.raises(AttributeError):
        client.responses.create(model="any", input="Contact lucia.ferrer@example.com")

    class FakeMessages:
        def create(self, **kwargs):
            received.append(kwargs)

    anthropic = NavajoAnthropic(SimpleNamespace(messages=FakeMessages(), beta=None), ClinicalShield())
    with pytest.raises(TypeError):
        anthropic.messages.create(model="any", max_tokens=10, messages=msg,
                                  tools=[{"name": "t", "description": "for lucia.ferrer@example.com"}])
    with pytest.raises(AttributeError):
        anthropic.beta
    with pytest.raises(AttributeError):
        NavajoChatModel(llm=SimpleNamespace(stream=print), egp=ClinicalShield()).stream
    # E017: allowed arguments are validated: plain model name, numeric settings, no extra LangChain kwargs
    with pytest.raises(TypeError):
        client.chat.completions.create(model="lucia.ferrer@example.com", messages=msg)
    with pytest.raises(TypeError):
        client.chat.completions.create(model="any", messages=msg, temperature="lucia.ferrer@example.com")
    with pytest.raises(TypeError):
        anthropic.messages.create(model="Contact lucia.ferrer@example.com", max_tokens=10, messages=msg)
    lc = NavajoChatModel(llm=SimpleNamespace(invoke=lambda x, **kw: received.append((x, kw))), egp=ClinicalShield())
    with pytest.raises(TypeError):
        lc.invoke("Contact lucia.ferrer@example.com", stop=["lucia.ferrer@example.com"])
    assert received == []


def test_sessions_destroyed_when_provider_fails(monkeypatch):
    import pytest
    from navajo_egp.integrations.openai_wrapper import NavajoOpenAI
    from navajo_egp.session import EGPSession
    from deid.shield import ClinicalShield

    destroyed = []
    original = EGPSession.destroy
    monkeypatch.setattr(EGPSession, "destroy", lambda self: destroyed.append(self) or original(self))
    client = NavajoOpenAI(_fake_openai([], fail=True), ClinicalShield())
    with pytest.raises(RuntimeError):
        client.chat.completions.create(model="any", messages=[{"role": "user", "content": NOTE}])
    assert destroyed and all(s.destroyed for s in destroyed)


def test_langchain_wrapper_refuses_message_lists():
    import pytest
    from navajo_egp.integrations.langchain_wrapper import NavajoChatModel
    from deid.shield import ClinicalShield

    model = NavajoChatModel(llm=None, egp=ClinicalShield())
    with pytest.raises(TypeError):
        model.invoke([{"role": "user", "content": NOTE}])


def test_shield_roundtrip_identity_model():
    from deid.shield import ClinicalShield

    shield = ClinicalShield()
    assert shield.wrap_llm_call(prompt=NOTE, llm_fn=lambda p: p) == NOTE


def test_v01_roundtrip_changes_whitespace():
    # documented limitation of navajo-egp 0.1.0 (experiments/LOG.md E002)
    spans = S.Navajo(use_spacy=False).spans(NOTE)
    exact, ws, _ = S.roundtrip(NOTE, spans, lossless=False)
    assert not exact and ws

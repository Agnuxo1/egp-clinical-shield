"""De-identification systems compared in the PoC (see experiments/PREREGISTRO.md)."""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)  # vendored navajo_egp 0.1.0

Span = tuple[str, int, int]


def merge_overlaps(spans: list[Span]) -> list[Span]:
    """Union of spans; overlapping or touching spans become one (first label kept)."""
    out: list[Span] = []
    for label, start, end in sorted(spans, key=lambda s: (s[1], -s[2])):
        if out and start < out[-1][2]:
            prev = out[-1]
            out[-1] = (prev[0], prev[1], max(prev[2], end))
        else:
            out.append((label, start, end))
    return out


class Raw:
    """S0: the note is sent as is."""
    name = "S0_RAW"

    def spans(self, text: str) -> list[Span]:
        return []


class Navajo:
    """S1/S2: navajo-egp PIIDetector, unchanged. extra: optional health patterns (N3)."""

    def __init__(self, use_spacy: bool, extra=None, name: str | None = None):
        from navajo_egp import detector as det
        self._det_mod = det
        self.detector = det.PIIDetector(use_spacy=use_spacy)
        if not use_spacy:
            # spaCy state is module-global in v0.1.0; make the regex-only run independent of it
            det._SPACY_AVAILABLE = False
        self.use_spacy = use_spacy
        self.extra = extra
        self.name = name or ("S2_NAVAJO_SPACY" if use_spacy else "S1_NAVAJO_REGEX")

    def entities(self, text: str):
        self._det_mod._SPACY_AVAILABLE = self.use_spacy and self._det_mod._SPACY_NLP is not None
        ents = self.detector.detect(text)
        if self.extra is not None:
            ents = self.extra.combine(text, ents)
        return ents

    def spans(self, text: str) -> list[Span]:
        return [(e.entity_type.value, e.start, e.end) for e in self.entities(text)]


class PackOnly:
    """P3r (E012 ablation): the health pack's own patterns without navajo-egp's core detectors."""

    def __init__(self, cycle: str):
        from deid.health import HealthPatterns
        self.hp = HealthPatterns(cycle)
        self.name = f"P3r_PACK_ONLY_{cycle}"

    def spans(self, text: str) -> list[Span]:
        return [(e.entity_type.value, e.start, e.end) for e in self.hp.combine(text, [])]


class Presidio:
    """C1: Microsoft Presidio analyzer configured for Spanish."""
    name = "C1_PRESIDIO"

    def __init__(self, model: str = "es_core_news_lg"):
        from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_analyzer import predefined_recognizers as pr

        conf = {"nlp_engine_name": "spacy", "models": [{"lang_code": "es", "model_name": model}]}
        nlp_engine = NlpEngineProvider(nlp_configuration=conf).create_engine()
        registry = RecognizerRegistry(supported_languages=["es"])
        registry.load_predefined_recognizers(languages=["es"], nlp_engine=nlp_engine)
        have = {type(r).__name__ for r in registry.recognizers}
        # Language-agnostic pattern recognizers ship tagged "en" only; a Spanish deployment enables them for "es".
        added = []
        for cls_name in ["EmailRecognizer", "PhoneRecognizer", "IbanRecognizer", "CreditCardRecognizer",
                         "IpRecognizer", "UrlRecognizer", "DateRecognizer", "CryptoRecognizer",
                         "EsNifRecognizer", "EsNieRecognizer"]:
            cls = getattr(pr, cls_name, None)
            if cls is None or cls_name in have:
                continue
            kwargs = {"supported_language": "es"}
            if cls_name == "PhoneRecognizer":
                kwargs["supported_regions"] = ("ES", "US", "UK", "DE", "FR", "IT", "PT", "MX", "AR", "CO")
            try:
                registry.add_recognizer(cls(**kwargs))
                added.append(cls_name)
            except TypeError:
                pass
        self.recognizers = sorted({type(r).__name__ for r in registry.recognizers if r.supported_language == "es"})
        self.added = added
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["es"])

    def spans(self, text: str) -> list[Span]:
        res = self.analyzer.analyze(text=text, language="es")
        return merge_overlaps([(r.entity_type, r.start, r.end) for r in res])


class Union:
    """H4: union of several systems' spans."""

    def __init__(self, parts, name: str):
        self.parts = parts
        self.name = name

    def spans(self, text: str) -> list[Span]:
        allspans: list[Span] = []
        for p in self.parts:
            allspans.extend(p.spans(text))
        return merge_overlaps(allspans)


def to_entities(text: str, spans: list[Span]):
    """Spans from any system -> navajo-egp DetectedEntity list (overlaps merged)."""
    from navajo_egp.entities import DetectedEntity, EntityType

    ents = []
    for label, start, end in merge_overlaps(spans):
        try:
            etype = EntityType(label)
        except ValueError:
            etype = EntityType.PERSON_NAME if "NOMBRE" in label or label == "PERSON" else EntityType.MRN
        ents.append(DetectedEntity(text=text[start:end], entity_type=etype, start=start, end=end))
    return ents


def roundtrip(text: str, spans: list[Span], lossless: bool = False) -> tuple[bool, bool, str]:
    """Mask with the NAVAJO session and restore (identity 'LLM').

    lossless=False reproduces v0.1.0; True uses the health pack's anonymizer.
    Returns (exact, equal_after_whitespace_normalisation, anonymised_text)."""
    import re
    from navajo_egp.anonymizer import Anonymizer
    from navajo_egp.session import EGPSession

    ents = to_entities(text, spans)
    session = EGPSession()
    if lossless:
        from deid.health import lossless_anonymizer
        anon = lossless_anonymizer().apply(text, ents, session)
    else:
        anon = Anonymizer().apply(text, ents, session)
    restored = Anonymizer().restore(anon, session)
    session.destroy()
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    return restored == text, norm(restored) == norm(text), anon

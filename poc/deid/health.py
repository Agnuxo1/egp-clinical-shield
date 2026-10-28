"""NAVAJO health pack (N3): patterns for clinical documents, developed on MEDDOCAN train only.

Design policy, from NAVAJO's EGP v2 document ("67 años -> CLINICAL:AGE -> Keep"): age, sex and
kinship words stay in the text because the model needs them to reason clinically. Everything that
identifies a person, a place smaller than a country, an institution, a date or a record is masked.

Cycles are registered in experiments/LOG.md.
"""

from __future__ import annotations

import re

from navajo_egp import detector as det
from navajo_egp.entities import DetectedEntity, EntityType

# --- c1: labelled header fields ("NHC: 1234567.") -------------------------------------------
_FIELD_KEYS = {
    EntityType.PERSON_NAME: [r"nombre", r"apellidos?", r"m[ée]dico", r"doctora?", r"enfermer[oa]",
                             r"remitente", r"firmado por", r"responsable"],
    EntityType.MRN: [r"nhc", r"n\.?\s?º?\s?h\.?\s?c\.?", r"historia(?: cl[íi]nica)?", r"cipa?", r"episodio",
                     r"nass", r"nuss", r"n[ºo°]\.?\s?(?:de\s)?(?:la\s)?seguridad social", r"tarjeta sanitaria",
                     r"n[ºo°]\.?\s?col(?:egiado)?\.?", r"colegiado", r"dni", r"nif", r"nie", r"pasaporte"],
    EntityType.ADDRESS: [r"domicilio", r"direcci[óo]n", r"localidad(?:\s?/\s?provincia)?", r"provincia",
                         r"municipio", r"c\.?\s?p\.?", r"c[óo]digo postal", r"pa[íi]s(?: de nacimiento)?",
                         r"lugar de nacimiento", r"residencia"],
    EntityType.DATE_OF_BIRTH: [r"fecha de nacimiento", r"f\. nac\.?", r"fecha de ingreso", r"fecha de alta",
                               r"fecha(?: de (?:consulta|intervenci[óo]n|cirug[íi]a|informe))?"],
    EntityType.PHONE: [r"tel[ée]fono", r"tel\.?", r"m[óo]vil", r"fax"],
    EntityType.EMAIL: [r"e-?mail", r"correo(?: electr[óo]nico)?"],
}
_ALL_KEYS = "|".join(k for ks in _FIELD_KEYS.values() for k in ks)
# value runs to end of line, to two spaces, or to the next "Key:" on the same line
_FIELD_RE = re.compile(
    r"(?im)(?:^|(?<=[\s.|]))(?P<key>" + _ALL_KEYS + r")\s*:\s*(?P<val>[^\n:]*?)"
    r"(?=\s{2,}|\s*(?:" + _ALL_KEYS + r"|edad|sexo)\s*:|\s*\.?\s*$|\.\s)"
)
_KEY_TYPE = [(re.compile(r"(?i)^(?:" + "|".join(ks) + r")$"), t) for t, ks in _FIELD_KEYS.items()]

# --- c1: narrative patterns ------------------------------------------------------------------
_CAP = r"[A-ZÁÉÍÓÚÜÑ][\wáéíóúüñ'\-\.]*"
_LINK = r"(?:\s+(?:de|del|la|las|los|y|e|el|San|Santa|\"?\d+(?: de [A-Z]\w+)?\"?)\b)"
_INSTITUTION_RE = re.compile(
    r"\b(?:Complejo\s+Hospitalario|Hospital(?:es)?|Cl[íi]nica|Centro\s+(?:de\s+Salud|M[ée]dico|Penitenciario|"
    r"Hospitalario|de\s+[A-ZÁÉÍÓÚ]\w+)|Instituto|Fundaci[óo]n|Policl[íi]nica|Consultorio|Sanatorio|"
    r"Servicio\s+(?:Andaluz|Vasco|Madrile[ñn]o|Gallego|Canario|Navarro|Riojano|Murciano|Cántabro|Aragon[ée]s)"
    r"\s+de\s+Salud|Universidad|Facultad\s+de\s+\w+|Mutua|Residencia)"
    r"(?:" + _LINK + r"*\s+" + _CAP + r"){0,10}"
)
_STREET_RE = re.compile(
    r"(?i)\b(?:c/|c\.|calle|avda\.?|av\.|avenida|plaza|pza\.?|paseo|p[ºo°]\.|carretera|ctra\.?|camino|ronda|"
    r"glorieta|traves[íi]a|urbanizaci[óo]n|urb\.|pol[íi]gono|barrio|bloque)\s*"
    r"[^\n,;.]{1,50}?(?:,?\s*(?:n[ºo°]\.?\s*)?\d{1,4}\s*(?:[,º°ª-]?\s*\d{0,2}\s*[º°ª]?\s*[A-Z]?\b)?)"
)
_POSTCODE_CITY_RE = re.compile(r"\b(?:E-)?\d{5}\b(?:\s+" + _CAP + r"(?:\s+(?:de\s+)?" + _CAP + r"){0,2})?")
_DATE_TEXT_RE = re.compile(
    r"(?i)\b(?:\d{1,2}\s+de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    r"octubre|noviembre|diciembre)(?:\s+(?:de|del)\s+\d{4})?\b|\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b"
)
_TITLE_NAME_RE = re.compile(r"\b(?:Dr|Dra|Drs|Prof|Sr|Sra|D|Dña)\.\s*(" + _CAP + r"(?:\s+(?:de\s+|del\s+|la\s+)?" + _CAP + r"){0,4})")
_SPACY_EXTRA = {"LOC": EntityType.ADDRESS, "ORG": EntityType.ADDRESS}
_PRIORITY = {"field": 0, "navajo": 1, "inst": 2, "street": 2, "pc": 3, "date": 3, "title": 3, "spacy": 4}


def _trim(text: str, s: int, e: int) -> tuple[int, int]:
    while s < e and text[s] in " \t\"'(":
        s += 1
    while e > s and text[e - 1] in " \t.,;:\"')":
        e -= 1
    return s, e


def lossless_anonymizer():
    """v0.1.0 Anonymizer.apply collapses runs of spaces and strips the text, so restoration is never
    byte-exact. The health pack masks spans without touching the surrounding text."""
    from navajo_egp.anonymizer import Anonymizer

    class LosslessAnonymizer(Anonymizer):
        def apply(self, text, entities, session):
            result = text
            for ent in sorted(entities, key=lambda e: e.start, reverse=True):
                result = result[:ent.start] + self._get_or_create_placeholder(ent, session) + result[ent.end:]
            return result

    return LosslessAnonymizer()


class HealthPatterns:
    def __init__(self, cycle: str = "c1"):
        self.cycle = cycle

    def candidates(self, text: str) -> list[tuple[int, int, int, EntityType]]:
        out: list[tuple[int, int, int, EntityType]] = []

        def add(kind, s, e, etype):
            s, e = _trim(text, s, e)
            if e - s >= 1:
                out.append((_PRIORITY[kind], s, e, etype))

        for m in _FIELD_RE.finditer(text):
            key = re.sub(r"\s+", " ", m.group("key").strip())
            etype = next((t for rx, t in _KEY_TYPE if rx.match(key)), EntityType.MRN)
            add("field", m.start("val"), m.end("val"), etype)
        for m in _INSTITUTION_RE.finditer(text):
            add("inst", m.start(), m.end(), EntityType.ADDRESS)
        for m in _STREET_RE.finditer(text):
            add("street", m.start(), m.end(), EntityType.ADDRESS)
        for m in _POSTCODE_CITY_RE.finditer(text):
            add("pc", m.start(), m.end(), EntityType.ADDRESS)
        for m in _DATE_TEXT_RE.finditer(text):
            add("date", m.start(), m.end(), EntityType.DATE_OF_BIRTH)
        for m in _TITLE_NAME_RE.finditer(text):
            add("title", m.start(1), m.end(1), EntityType.PERSON_NAME)
        if det._SPACY_AVAILABLE and det._SPACY_NLP is not None:
            for ent in det._SPACY_NLP(text).ents:
                if ent.label_ in _SPACY_EXTRA:
                    add("spacy", ent.start_char, ent.end_char, _SPACY_EXTRA[ent.label_])
        return out

    def combine(self, text: str, navajo_ents: list[DetectedEntity]) -> list[DetectedEntity]:
        cands = self.candidates(text)
        cands += [(_PRIORITY["navajo"], e.start, e.end, e.entity_type) for e in navajo_ents]
        # higher priority first, then longer; keep spans that do not overlap an accepted one
        cands.sort(key=lambda c: (c[0], -(c[2] - c[1]), c[1]))
        taken: list[tuple[int, int]] = []
        kept: list[DetectedEntity] = []
        for _, s, e, etype in cands:
            if any(not (e <= ts or s >= te) for ts, te in taken):
                continue
            taken.append((s, e))
            kept.append(DetectedEntity(text=text[s:e], entity_type=etype, start=s, end=e, confidence=0.8))
        return sorted(kept, key=lambda x: x.start)

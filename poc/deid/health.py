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
# c3 (E009 audit): a byte-order mark before the first "Nombre:" hid the field
_FIELD_RE_C3 = re.compile(_FIELD_RE.pattern.replace(r"(?<=[\s.|])", r"(?<=[\s.|\ufeff])"), _FIELD_RE.flags)
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
_PRIORITY = {"field": 0, "navajo": 1, "navajo_addr": 1, "inst": 2, "street": 2, "pc": 3, "date": 3, "title": 3, "spacy": 4}

# --- c2: boundaries, Spanish phones, places (train error analysis, LOG.md E005) ---------------
# a new entity starts at these words; signature blocks in clinical letters chain several in one line
_BOUNDARY_RE = re.compile(
    r"\s+(?=(?:Hospital|Servicio|Unidad|Complejo|Cl[íi]nica|Centro|Departamento|Secci[óo]n|Instituto|"
    r"Fundaci[óo]n|Universidad|Facultad|Calle|C/|Avda\.?|Avenida|Paseo|Plaza|Ronda|Apartado|E-?mail|Email|"
    r"Correo|Tfno|Tel[ée]fono|Telef|Tlf|Fax|Dra?\.)\b)|(?<=[a-záéíóúñ\d)])\.\s+(?=[A-ZÁÉÍÓÚÑ])"
)
_NOT_PHI_START = re.compile(r"(?i)^(?:servicio|unidad|departamento|secci[óo]n|e-?mail|email|correo(?: electr[óo]nico)?|"
                            r"tfno|tel[ée]fono|telef|tlf|fax|apartado(?: de correos)?)\b[\s.:\-]*$|"
                            r"^(?:Servicio|Unidad|Departamento|Secci[óo]n)\s+de\b")
_EMAIL_PREFIX = re.compile(r"(?i)^(?:e-?mail|email|correo)[\s.:\-]*")
_DOCTOR_ADDR = re.compile(r"(?i)^dra?\.?\s")  # v0.1.0 ADDRESS reads Spanish "Dr." as English "drive"
_PHONE_ES = re.compile(r"(?<![\d+])(?:\+34[\s.]?)?[6789]\d{2}(?:[\s.]?\d{2,3}){2,3}(?:\s*ext\.?\s*\d{1,5})?(?!\d)")
_COUNTRIES = (r"España|Portugal|Francia|Italia|Alemania|Reino Unido|Inglaterra|Irlanda|Bélgica|Holanda|Países Bajos|"
              r"Suiza|Austria|Suecia|Noruega|Dinamarca|Finlandia|Polonia|Rumanía|Rumania|Bulgaria|Ucrania|Rusia|Grecia|"
              r"Turquía|Marruecos|Argelia|Túnez|Egipto|Senegal|Mali|Malí|Nigeria|Ghana|Guinea|Guinea Ecuatorial|Gambia|"
              r"Mauritania|Camerún|Kenia|Etiopía|Sudáfrica|Estados Unidos|EE\. ?UU\.?|EEUU|Canadá|México|Guatemala|"
              r"Honduras|El Salvador|Nicaragua|Costa Rica|Panamá|Cuba|República Dominicana|Puerto Rico|Colombia|"
              r"Venezuela|Ecuador|Perú|Bolivia|Chile|Argentina|Uruguay|Paraguay|Brasil|China|Japón|India|Pakistán|"
              r"Bangladesh|Filipinas|Indonesia|Tailandia|Vietnam|Corea|Irán|Irak|Siria|Israel|Arabia Saudí|Australia")
_PROVINCES = ("Álava|Araba|Albacete|Alicante|Almería|Asturias|Ávila|Badajoz|Barcelona|Burgos|Cáceres|Cádiz|Cantabria|"
              "Castellón|Ciudad Real|Córdoba|Cordoba|La Coruña|A Coruña|Coruña|Cuenca|Gerona|Girona|Granada|"
              "Guadalajara|Guipúzcoa|Gipuzkoa|Huelva|Huesca|Islas Baleares|Baleares|Jaén|León|Lérida|Lleida|"
              "La Rioja|Logroño|Lugo|Madrid|Málaga|Murcia|Navarra|Orense|Ourense|Palencia|Las Palmas|Pontevedra|"
              "Salamanca|Santa Cruz de Tenerife|Tenerife|Segovia|Sevilla|Soria|Tarragona|Teruel|Toledo|Valencia|"
              "Valladolid|Vizcaya|Bizkaia|Zamora|Zaragoza|Ceuta|Melilla|Bilbao|Pamplona|Iruña|Vitoria|Gasteiz|"
              "San Sebastián|Donostia|Santander|Oviedo|Gijón|Santiago de Compostela|Vigo|Elche|Cartagena|"
              "Alcalá de Henares|Móstoles|Getafe|Leganés|Fuenlabrada|Alcorcón|Terrassa|Sabadell|Badalona|"
              "L'Hospitalet|Mataró|Jerez|Marbella|Algeciras|Mérida|Palma|Palma de Mallorca|Ibiza|Menorca|"
              "Andalucía|Aragón|Canarias|Castilla y León|Castilla-La Mancha|Castilla La Mancha|Cataluña|Catalunya|"
              "Extremadura|Galicia|Comunidad Valenciana|País Vasco|Euskadi")
_PLACE_RE = re.compile(r"(?<![\wÁÉÍÓÚáéíóúñÑ])(?:" + _COUNTRIES + "|" + _PROVINCES + r")(?![\wáéíóúñ])")
_PC_ONLY = re.compile(r"\b(?:E-)?(\d{5})\b")
_STREET_TAIL = (r"(?:[,.]?\s*(?:\d{1,2}\s*[º°ª]?\s*(?:Dcha|Dch|Izq|Izda|Izquierda|Derecha|Centro|Bajo|[A-H])?\.?|"
                r"[A-Z]\d?(?:\s?\d[A-Z])?|s/n|bajo|planta\s+\d+|puerta\s+\d+|piso\s+\d+)){0,3}")
_STREET_RE_C2 = re.compile(
    r"(?i)\b(?:c/|c\.|calle|avda\.?|av\.|avenida|plaza|pza\.?|paseo|p[ºo°]\.|carretera|ctra\.?|camino|ronda|"
    r"glorieta|traves[íi]a|urbanizaci[óo]n|urb\.|pol[íi]gono|barrio)\s*"
    r"[^\n,;.]{1,50}?(?:,?\s*(?:n[ºo°]\.?\s*)?(?:\d{1,4}|s/n)\b" + _STREET_TAIL + r")"
)
_INSTITUTION_RE_C2 = re.compile(_INSTITUTION_RE.pattern + r"(?:\s+\"[^\"\n]{2,40}\")?")


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
        self.c2 = cycle >= "c2"
        self.c3 = cycle >= "c3"

    def _pieces(self, text: str, s: int, e: int) -> list[tuple[int, int]]:
        """c2: split a span where a new entity starts; drop pieces that are not PHI (department, labels)."""
        if not self.c2:
            return [(s, e)]
        cuts = [s] + [m.end() for m in _BOUNDARY_RE.finditer(text, s, e)] + [e]
        out = []
        for a, b in zip(cuts, cuts[1:]):
            a, b = _trim(text, a, b)
            if b <= a or _NOT_PHI_START.search(text[a:b]):
                continue
            m = _EMAIL_PREFIX.match(text[a:b])
            if m and "@" in text[a:b]:
                a, b = _trim(text, a + m.end(), b)
            if b > a:
                out.append((a, b))
        return out

    def candidates(self, text: str, navajo_ents=()) -> list[tuple[int, int, int, EntityType]]:
        out: list[tuple[int, int, int, EntityType]] = []

        def add(kind, s, e, etype):
            s, e = _trim(text, s, e)
            for a, b in self._pieces(text, s, e):
                if self.c2:
                    tier = 0 if kind == "field" else 2 if kind in ("spacy", "navajo_addr") else 1
                else:
                    tier = _PRIORITY[kind]
                out.append((tier, a, b, etype))

        for m in (_FIELD_RE_C3 if self.c3 else _FIELD_RE).finditer(text):
            key = re.sub(r"\s+", " ", m.group("key").strip())
            etype = next((t for rx, t in _KEY_TYPE if rx.match(key)), EntityType.MRN)
            add("field", m.start("val"), m.end("val"), etype)
        for m in (_INSTITUTION_RE_C2 if self.c2 else _INSTITUTION_RE).finditer(text):
            add("inst", m.start(), m.end(), EntityType.ADDRESS)
        for m in (_STREET_RE_C2 if self.c2 else _STREET_RE).finditer(text):
            add("street", m.start(), m.end(), EntityType.ADDRESS)
        if self.c2:
            for m in _PC_ONLY.finditer(text):
                add("pc", m.start(1), m.end(1), EntityType.ADDRESS)
            for m in _PLACE_RE.finditer(text):
                add("place", m.start(), m.end(), EntityType.ADDRESS)
            for m in _PHONE_ES.finditer(text):
                add("phone", m.start(), m.end(), EntityType.PHONE)
        else:
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
        if self.c3:
            # c3 (E009 audit): v0.1.0 drops an e-mail or ID that overlaps its false "Dr." address before
            # the health pack can discard that address, so take the high-precision patterns before deduplication
            navajo_ents = list(navajo_ents) + [e for e in det._regex_entities(text)
                                               if e.entity_type != EntityType.PERSON_NAME]
        for e in navajo_ents:
            if self.c2 and e.entity_type == EntityType.ADDRESS:
                if _DOCTOR_ADDR.match(e.text):
                    continue
                add("navajo_addr", e.start, e.end, e.entity_type)
            else:
                add("navajo", e.start, e.end, e.entity_type)
        return out

    def combine(self, text: str, navajo_ents: list[DetectedEntity]) -> list[DetectedEntity]:
        cands = self.candidates(text, navajo_ents)
        # c1: higher priority first, then longer; c2: tier first, then longer.
        # A span is kept only if it does not overlap one already accepted.
        cands.sort(key=lambda c: (c[0], -(c[2] - c[1]), c[1]))
        taken: list[tuple[int, int]] = []
        kept: list[DetectedEntity] = []
        for _, s, e, etype in cands:
            if any(not (e <= ts or s >= te) for ts, te in taken):
                continue
            taken.append((s, e))
            kept.append(DetectedEntity(text=text[s:e], entity_type=etype, start=s, end=e, confidence=0.8))
        return sorted(kept, key=lambda x: x.start)

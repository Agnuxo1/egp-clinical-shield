"""EGP Clinical Shield: navajo-egp's middleware with the evaluated health-pack detector.

    from deid.shield import ClinicalShield
    client = ClinicalShield().wrap(OpenAI())          # default mode: health pack, no ML model
    client = ClinicalShield(mode="max").wrap(OpenAI())  # maximum protection: health pack + Presidio

Detection is the exact code measured as N3r ("default") and H4r ("max") in experiments/LOG.md;
masking is lossless, so restoration of unchanged placeholders is exact.
"""

from __future__ import annotations

from navajo_egp.exceptions import PIILeakageError
from navajo_egp.middleware import EGPMiddleware
from navajo_egp.session import EGPSession

from deid import systems as S
from deid.health import HealthPatterns, lossless_anonymizer


class ClinicalShield(EGPMiddleware):
    def __init__(self, mode: str = "default", cycle: str = "c2", **kwargs):
        super().__init__(use_spacy=False, **kwargs)
        pack = S.Navajo(use_spacy=False, extra=HealthPatterns(cycle))
        if mode == "default":
            self._system = pack
        elif mode == "max":
            self._system = S.Union([pack, S.Presidio()], name="max")
        else:
            raise ValueError("mode must be 'default' or 'max'")
        self._anonymizer = lossless_anonymizer()

    def anonymize(self, text: str, session: EGPSession | None = None) -> tuple[str, EGPSession]:
        if session is None:
            session = EGPSession()
            self._anonymizer.reset_counters()
        entities = S.to_entities(text, self._system.spans(text))
        anon_text = self._anonymizer.apply(text, entities, session)
        if self._verify:
            violations = self._detector.verify_clean(anon_text)
            if violations and self._strict:
                session.destroy()
                raise PIILeakageError(violations)
        return anon_text, session

# Pre-registration — NAVAJO de-identification PoC (MIT Solve 2027 Global Health)

Written 2026-10-28, before any system was run on MEDDOCAN data. Changes after this point are logged in `LOG.md` with the reason.

## Question

When a frontline clinician pastes a case note into an AI assistant, how much patient-identifying information reaches the external model?
We compare what happens today (the note is sent as is) with NAVAJO (`navajo-egp` 0.1.0, commit `fab2b7f` of Agnuxo1/Project-NAVAJO) and with a professional open-source de-identifier (Microsoft Presidio).

## Data

MEDDOCAN corpus v1.0 (Marimon et al., 2019; Zenodo DOI 10.5281/zenodo.4279323, CC BY 4.0): synthetic Spanish clinical case reports with gold PHI annotations in brat format.
Splits: train 500 documents, dev 250, test 250. No real patient data.

- Development and all iteration: **train** only; **dev** as a check.
- **test** is run once, at the end, for every system at the same time.

## Systems

| Id | System | Configuration |
|---|---|---|
| S0 | RAW | No masking. The note is sent as is (current practice when clinicians paste notes into chatbots). |
| S1 | NAVAJO-regex | `PIIDetector(use_spacy=False)`, v0.1.0 unchanged. |
| S2 | NAVAJO-spaCy | `PIIDetector(use_spacy=True)` with `es_core_news_lg`, v0.1.0 unchanged. |
| C1 | PRESIDIO | `presidio-analyzer` with spaCy `es_core_news_lg`, every predefined recognizer that supports `es`, default score threshold, all entity types. |
| N3 | NAVAJO-health | S2 plus health-specific patterns developed on train only (at most two registered cycles). |
| H4 | HYBRID | Union of N3 and C1 spans, masked and restored through the NAVAJO session. |

Ablations for H4: without NAVAJO patterns (= C1), without Presidio (= N3), without spaCy.

## Metrics (lower is better unless stated)

1. **Primary — PHI span leak rate** `L = 1 − strict span recall`, from the official MEDDOCAN evaluation script (SPAN subtrack, strict), on test.
2. **Character exposure** `E` = gold PHI characters not covered by any predicted span / all gold PHI characters.
3. **Over-masking** `O` = non-whitespace non-PHI characters covered by predicted spans / all non-whitespace non-PHI characters (clinical content lost).
4. Strict span precision and F1 (official script).
5. The same `L` and `E` on the **direct-identifier subset**: labels starting with `NOMBRE_`, `ID_`, `NUMERO_`, `IDENTIF_`, plus `CORREO_ELECTRONICO`, `CALLE`, `URL_WEB`, `DIREC_PROT_INTERNET`, `FECHAS`.
6. Per-label recall.
7. Reversibility (NAVAJO only): share of test documents where `deanonymize(anonymize(x)) == x`.
8. CPU time per document.

Uncertainty: the systems are deterministic, so seeds do not apply to them. We report 95 % bootstrap intervals over documents (2,000 resamples), repeated with bootstrap seeds 0, 1 and 2, and paired bootstrap intervals for differences between systems. Dev results are reported as a second held-out sample.

## Hypotheses and decision rules

- **H1**: S2 (NAVAJO as is) has lower character exposure `E` than C1 (Presidio) on test. Confirmed if the paired 95 % interval of `E(S2) − E(C1)` lies below 0.
- **H2**: N3 improves on S2 on train and dev without raising over-masking `O` by more than 2 points.
- **H3**: H4 has lower `E` than both N3 and C1 (paired intervals below 0).
- If H1 is rejected, the application reports it. The submitted system is the best validated one in which NAVAJO is a component with its contribution measured by ablation (JEV decision 2026-10-28, `iterate_then_hybrid`, confidence 0.83).

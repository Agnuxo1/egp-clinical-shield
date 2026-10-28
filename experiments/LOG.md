# Experiment log

Metrics as pre-registered in `PREREGISTRO.md`: `L` = 1 − strict span recall (official MEDDOCAN script), `E` = PHI character exposure, `O` = over-masking of non-PHI characters, `DI_E` = exposure on direct identifiers. Lower is better for all four. Negative and null results are kept.

| Id | Date (UTC) | Where | Hypothesis | Config | Commit | Split | Result | Decision |
|---|---|---|---|---|---|---|---|---|
| E001 | 2026-10-28 | PC, CPU | The harness reproduces the official recall. | S0, S1 (regex) | 1f8967e (pre-commit tree) | train | S1: L 0.690, E 0.344, O 0.014, P 0.543, DI_E 0.211. Own strict recall = official recall (assert). | Harness accepted. |
| E002 | 2026-10-28 | PC | v0.1.0 round-trip is lossless. | S1 round-trip with identity LLM | same | train | Exact 0.0 %, 99.8 % after whitespace normalisation: `Anonymizer.apply` collapses spaces and strips the text. | Rejected. Fixed in the health pack (lossless anonymizer). v0.1.0 numbers are reported as they are. |
| E003 | 2026-10-28 | PC | H2 c1: labelled-field, institution, street, postcode and date patterns reduce exposure on train. | N3r c1 (no spaCy) | 1f8967e | train | L 0.385, E 0.180, O 0.014, P 0.796, DI_E 0.056; round-trip exact 100 %. | Accepted; error analysis for c2. |
| E004 | 2026-10-28 | PC | Error analysis on train (c1 misses). | — | 1f8967e | train | v0.1.0 ADDRESS regex reads Spanish "Dr." as English "drive" and swallows the doctor's name plus 60 characters; signature blocks chain name, department, hospital and street in one span; Spanish phone formats (3-2-2-2) missing; countries and provinces missing. | Design c2. |
| E005 | 2026-10-28 | PC | H2 c2: entity boundaries, dropping v0.1.0 "Dr." addresses, Spanish phones, country/province gazetteer, street tails. | N3r c2 | see git | train | L 0.317, E 0.142, O 0.011, P 0.819, DI_E 0.050; c1 reproduced exactly with the same code. | Accepted. Second and last cycle (JEV: up to two). |
| E006 | 2026-10-28 | PC | c2 does not overfit train. | S1, N3r c2 | see git | dev | S1: L 0.691, E 0.365, O 0.015, DI_E 0.241. N3r c2: L 0.318, E 0.134, O 0.012, P 0.802, DI_E 0.046. | No overfitting seen. Freeze c2. |

| E007 | 2026-10-28 12:48 | server-ia, CPU lane, job `d73b065c564c4731` (ticket 96) | Pre-registered H1, H2, H3 and ablations; test run once. | S0 S1 S2 C1 N3 N3r H4 H4r, health c2, 2,000 bootstrap resamples, seeds 0/1/2 | 57f1eba | train, dev, test | pending | — |

## Decisions and deviations

- **server-ia outage (2026-10-28 12:37–12:48 UTC):** SSH banner timeouts. JEV (`wait_then_local`, 0.94): wait up to 90 minutes, then run the same frozen code on the PC CPU. The server came back after 11 minutes; nothing ran locally.

- **Policy (2026-10-28):** age, sex and kinship words are kept, as NAVAJO's EGP v2 design document states ("67 años → CLINICAL:AGE → Keep"; the model needs them for dosing). MEDDOCAN counts them as PHI, so all-PHI metrics penalise NAVAJO for this choice. The pre-registered direct-identifier subset does not include them.
- **Presidio control (2026-10-28):** Presidio's language-agnostic pattern recognizers (email, phone, IBAN, card, IP, URL, date, crypto, Spanish NIF/NIE) are enabled for `es`, and the phone recognizer gets Spanish and Latin American regions. This makes the control stronger than the plain default, which is the conservative direction for H1.
- Local runs use 100–200 bootstrap resamples to save time; the reported runs on server-ia use 2,000.
- spaCy-based systems (S2, N3, H4) and Presidio need packages that are not installed on the PC; they run only on server-ia (E007).

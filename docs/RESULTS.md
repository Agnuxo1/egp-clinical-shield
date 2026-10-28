# Results — NAVAJO de-identification PoC on MEDDOCAN

Environment: `{"python": "3.13.5", "platform": "Linux-6.12.113+deb13-amd64-x86_64-with-glibc2.41", "numpy": "2.4.6", "spacy": "3.8.16", "presidio_analyzer": "?", "es_core_news_lg": "3.8.0", "build_seconds": 3.0, "presidio_recognizers_es": ["CreditCardRecognizer", "CryptoRecognizer", "DateRecognizer", "EmailRecognizer", "EsNieRecognizer", "EsNifRecognizer", "IbanRecognizer", "IpRecognizer", "MacAddressRecognizer", "MedicalLicenseRecognizer", "PhoneRecognizer", "SpacyRecognizer", "UrlRecognizer"], "presidio_added_for_es": []}`

### train (500 documents)

| System | Primary: span leak L (strict) | PHI characters left visible E [95% CI] | Direct-identifier characters left visible | Non-PHI text masked O | Span precision / F1 | ms/note | Exact restore (echo model) |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 / 0.000 | 0.0 | — |
| navajo-egp 0.1, regex | 69.0 % | 35.5 % [34.8–36.3] | 22.8 % | 1.4 % | 0.543 / 0.395 | 1.39 | 0.0 % |
| navajo-egp 0.1 + spaCy | 68.7 % | 32.4 % [31.6–33.1] | 19.1 % | 2.2 % | 0.475 / 0.377 | 32.68 | 1.2 % |
| Presidio (control) | 61.2 % | 33.1 % [32.4–33.9] | 29.0 % | 5.1 % | 0.379 / 0.384 | 51.59 | — |
| Shield default (health pack) | 31.7 % | 14.7 % [14.0–15.4] | 5.4 % | 1.1 % | 0.819 / 0.745 | 2.67 | 100.0 % |
| Health pack + spaCy | 30.6 % | 13.2 % [12.5–13.9] | 4.6 % | 4.3 % | 0.537 / 0.605 | 61.2 | 100.0 % |
| Shield max (pack + Presidio) | 40.7 % | 11.1 % [10.5–11.8] | 3.2 % | 5.5 % | 0.473 / 0.527 | 52.01 | 100.0 % |
| Pack + Presidio + spaCy | 40.6 % | 11.2 % [10.5–11.8] | 3.3 % | 5.6 % | 0.471 / 0.525 | 110.62 | 100.0 % |

### dev (250 documents)

| System | Primary: span leak L (strict) | PHI characters left visible E [95% CI] | Direct-identifier characters left visible | Non-PHI text masked O | Span precision / F1 | ms/note | Exact restore (echo model) |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 / 0.000 | 0.01 | — |
| navajo-egp 0.1, regex | 69.1 % | 37.6 % [36.4–38.7] | 25.8 % | 1.5 % | 0.546 / 0.395 | 1.48 | 0.0 % |
| navajo-egp 0.1 + spaCy | 69.3 % | 34.4 % [33.3–35.6] | 21.8 % | 2.3 % | 0.472 / 0.372 | 33.52 | 0.8 % |
| Presidio (control) | 61.0 % | 33.5 % [32.2–34.7] | 31.4 % | 5.0 % | 0.379 / 0.384 | 52.96 | — |
| Shield default (health pack) | 31.8 % | 13.9 % [13.0–14.8] | 5.0 % | 1.2 % | 0.802 / 0.737 | 2.91 | 100.0 % |
| Health pack + spaCy | 30.5 % | 12.1 % [11.4–12.9] | 4.2 % | 4.3 % | 0.529 / 0.600 | 64.67 | 100.0 % |
| Shield max (pack + Presidio) | 40.0 % | 10.0 % [9.3–10.8] | 3.1 % | 5.6 % | 0.471 / 0.528 | 54.46 | 100.0 % |
| Pack + Presidio + spaCy | 39.9 % | 10.0 % [9.3–10.8] | 3.1 % | 5.6 % | 0.468 / 0.526 | 113.86 | 100.0 % |

### test (250 documents)

| System | Primary: span leak L (strict) | PHI characters left visible E [95% CI] | Direct-identifier characters left visible | Non-PHI text masked O | Span precision / F1 | ms/note | Exact restore (echo model) |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 / 0.000 | 0.0 | — |
| navajo-egp 0.1, regex | 68.6 % | 36.9 % [35.9–38.0] | 23.3 % | 1.5 % | 0.556 / 0.402 | 1.38 | 0.0 % |
| navajo-egp 0.1 + spaCy | 68.6 % | 33.8 % [32.7–34.9] | 19.6 % | 2.2 % | 0.483 / 0.381 | 31.73 | 1.6 % |
| Presidio (control) | 59.3 % | 32.4 % [31.3–33.7] | 28.9 % | 5.2 % | 0.385 / 0.396 | 50.36 | — |
| Shield default (health pack) | 31.3 % | 15.1 % [14.1–16.1] | 5.5 % | 1.2 % | 0.809 / 0.743 | 2.66 | 100.0 % |
| Health pack + spaCy | 29.6 % | 13.1 % [12.2–14.0] | 4.7 % | 4.4 % | 0.535 / 0.608 | 61.4 | 100.0 % |
| Shield max (pack + Presidio) | 39.1 % | 10.6 % [9.8–11.4] | 3.2 % | 5.6 % | 0.474 / 0.533 | 52.2 | 100.0 % |
| Pack + Presidio + spaCy | 39.1 % | 10.7 % [9.9–11.4] | 3.3 % | 5.7 % | 0.471 / 0.531 | 111.22 | 100.0 % |

## Pre-registered tests and ablations (paired document bootstrap)

| Comparison | Split | Metric | Difference (points) | 95% CI, seeds 0/1/2 | Reading |
|---|---|---|---|---|---|
| H1  NAVAJO 0.1 vs Presidio: navajo-egp 0.1 + spaCy − Presidio (control) | test | E_exposure | +1.39 | [+0.06, +2.65] / [+0.04, +2.80] / [+0.08, +2.80] | A higher (CI above 0) |
| H2  health pack vs 0.1 (exposure): Health pack + spaCy − navajo-egp 0.1 + spaCy | dev | E_exposure | -22.33 | [-23.49, -21.19] / [-23.48, -21.23] / [-23.52, -21.20] | A lower (CI below 0) |
| H2  health pack vs 0.1 (over-masking): Health pack + spaCy − navajo-egp 0.1 + spaCy | dev | O_overmask | +2.07 | [+1.90, +2.24] / [+1.90, +2.24] / [+1.89, +2.24] | A higher (CI above 0) |
| H3a hybrid vs NAVAJO health: Pack + Presidio + spaCy − Health pack + spaCy | test | E_exposure | -2.43 | [-2.93, -1.97] / [-2.94, -1.98] / [-2.92, -1.97] | A lower (CI below 0) |
| H3b hybrid vs Presidio: Pack + Presidio + spaCy − Presidio (control) | test | E_exposure | -21.79 | [-22.94, -20.78] / [-22.82, -20.80] / [-22.84, -20.77] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio: Health pack + spaCy − Presidio (control) | test | E_exposure | -19.37 | [-20.64, -18.10] / [-20.60, -18.13] / [-20.53, -18.13] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio (direct ids): Health pack + spaCy − Presidio (control) | test | DI_E_exposure | -24.24 | [-25.64, -22.90] / [-25.60, -22.93] / [-25.56, -22.84] | A lower (CI below 0) |
| Abl. hybrid vs Presidio (direct ids): Pack + Presidio + spaCy − Presidio (control) | test | DI_E_exposure | -25.64 | [-27.00, -24.41] / [-26.87, -24.40] / [-26.90, -24.40] | A lower (CI below 0) |
| Abl. hybrid over-masking vs Presidio: Pack + Presidio + spaCy − Presidio (control) | test | O_overmask | +0.50 | [+0.37, +0.65] / [+0.38, +0.66] / [+0.38, +0.66] | A higher (CI above 0) |
| Abl. spaCy inside hybrid: Pack + Presidio + spaCy − Shield max (pack + Presidio) | test | E_exposure | +0.08 | [+0.02, +0.13] / [+0.02, +0.13] / [+0.02, +0.14] | A higher (CI above 0) |
| Abl. NAVAJO inside hybrid, no spaCy: Shield max (pack + Presidio) − Presidio (control) | test | E_exposure | -21.87 | [-23.01, -20.87] / [-22.91, -20.87] / [-22.92, -20.83] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy: Shield max (pack + Presidio) − Shield default (health pack) | test | E_exposure | -4.50 | [-5.24, -3.82] / [-5.24, -3.79] / [-5.22, -3.78] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy (over-masking): Shield max (pack + Presidio) − Shield default (health pack) | test | O_overmask | +4.47 | [+4.24, +4.72] / [+4.24, +4.71] / [+4.23, +4.70] | A higher (CI above 0) |
| Abl. NAVAJO health no spaCy vs Presidio: Shield default (health pack) − Presidio (control) | test | E_exposure | -17.37 | [-18.79, -15.92] / [-18.78, -15.96] / [-18.74, -15.93] | A lower (CI below 0) |
| Abl. NAVAJO health no spaCy vs Presidio (over-masking): Shield default (health pack) − Presidio (control) | test | O_overmask | -4.02 | [-4.30, -3.74] / [-4.31, -3.74] / [-4.29, -3.75] | A lower (CI below 0) |

## Per-label character coverage (test)

| Gold label | n | navajo-egp 0.1, regex | navajo-egp 0.1 + spaCy | Presidio (control) | Health pack + spaCy | Pack + Presidio + spaCy |
|---|---|---|---|---|---|---|
| TERRITORIO | 956 | 47 % | 46 % | 66 % | 95 % | 98 % |
| FECHAS * | 611 | 79 % | 79 % | 80 % | 97 % | 97 % |
| EDAD_SUJETO_ASISTENCIA | 518 | 0 % | 0 % | 9 % | 3 % | 9 % |
| NOMBRE_SUJETO_ASISTENCIA * | 502 | 70 % | 94 % | 97 % | 100 % | 100 % |
| NOMBRE_PERSONAL_SANITARIO * | 501 | 95 % | 98 % | 98 % | 98 % | 100 % |
| SEXO_SUJETO_ASISTENCIA | 461 | 0 % | 4 % | 24 % | 8 % | 24 % |
| CALLE * | 413 | 69 % | 69 % | 57 % | 86 % | 89 % |
| PAIS | 363 | 8 % | 8 % | 98 % | 100 % | 100 % |
| ID_SUJETO_ASISTENCIA * | 283 | 16 % | 16 % | 3 % | 94 % | 94 % |
| CORREO_ELECTRONICO * | 249 | 97 % | 98 % | 99 % | 97 % | 100 % |
| ID_TITULACION_PERSONAL_SANITARIO * | 234 | 45 % | 44 % | 13 % | 100 % | 100 % |
| ID_ASEGURAMIENTO * | 198 | 78 % | 78 % | 8 % | 100 % | 100 % |
| HOSPITAL | 130 | 66 % | 71 % | 89 % | 95 % | 98 % |
| FAMILIARES_SUJETO_ASISTENCIA | 81 | 0 % | 2 % | 4 % | 4 % | 4 % |
| INSTITUCION | 67 | 44 % | 48 % | 84 % | 80 % | 93 % |
| ID_CONTACTO_ASISTENCIAL * | 39 | 43 % | 43 % | 17 % | 100 % | 100 % |
| NUMERO_TELEFONO * | 26 | 69 % | 69 % | 5 % | 98 % | 98 % |
| PROFESION | 9 | 0 % | 0 % | 0 % | 0 % | 0 % |
| OTROS_SUJETO_ASISTENCIA | 7 | 0 % | 0 % | 0 % | 0 % | 0 % |
| NUMERO_FAX * | 7 | 54 % | 54 % | 17 % | 100 % | 100 % |
| CENTRO_SALUD | 6 | 39 % | 39 % | 98 % | 100 % | 100 % |

Cells: share of the label's characters masked. * = direct identifier.

![exposure](fig_exposure_test.png)

Post-hoc analyses (no system changed): [POSTHOC.md](POSTHOC.md).

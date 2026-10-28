# Results — NAVAJO de-identification PoC on MEDDOCAN

Environment: `{"python": "3.13.5", "platform": "Linux-6.12.113+deb13-amd64-x86_64-with-glibc2.41", "numpy": "2.4.6", "spacy": "3.8.16", "presidio_analyzer": "?", "es_core_news_lg": "3.8.0", "build_seconds": 3.0, "presidio_recognizers_es": ["CreditCardRecognizer", "CryptoRecognizer", "DateRecognizer", "EmailRecognizer", "EsNieRecognizer", "EsNifRecognizer", "IbanRecognizer", "IpRecognizer", "MacAddressRecognizer", "MedicalLicenseRecognizer", "PhoneRecognizer", "SpacyRecognizer", "UrlRecognizer"], "presidio_added_for_es": []}`

### train (500 documents)

| System | Leak L (strict) | PHI chars exposed E [95% CI] | Direct ids exposed | Over-masking O | Precision | ms/doc | Round-trip exact |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 | 0.0 | — |
| NAVAJO 0.1 regex | 69.0 % | 34.4 % [33.6–35.2] | 21.1 % | 1.4 % | 0.543 | 1.39 | 0.0 % |
| NAVAJO 0.1 + spaCy | 68.7 % | 31.1 % [30.4–31.9] | 17.3 % | 2.2 % | 0.475 | 32.68 | 1.2 % |
| Presidio (control) | 61.2 % | 31.7 % [30.9–32.4] | 27.1 % | 5.1 % | 0.379 | 51.59 | — |
| NAVAJO health, no spaCy | 31.7 % | 14.2 % [13.5–14.9] | 5.0 % | 1.1 % | 0.819 | 2.67 | 100.0 % |
| NAVAJO health | 30.6 % | 12.6 % [12.0–13.3] | 4.2 % | 4.3 % | 0.537 | 61.2 | 100.0 % |
| Hybrid, no spaCy | 40.7 % | 10.7 % [10.1–11.3] | 2.9 % | 5.5 % | 0.473 | 52.01 | 100.0 % |
| Hybrid NAVAJO + Presidio | 40.6 % | 10.7 % [10.1–11.4] | 3.0 % | 5.6 % | 0.471 | 110.62 | 100.0 % |

### dev (250 documents)

| System | Leak L (strict) | PHI chars exposed E [95% CI] | Direct ids exposed | Over-masking O | Precision | ms/doc | Round-trip exact |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 | 0.01 | — |
| NAVAJO 0.1 regex | 69.1 % | 36.5 % [35.3–37.7] | 24.1 % | 1.5 % | 0.546 | 1.48 | 0.0 % |
| NAVAJO 0.1 + spaCy | 69.3 % | 33.3 % [32.1–34.5] | 19.9 % | 2.3 % | 0.472 | 33.52 | 0.8 % |
| Presidio (control) | 61.0 % | 32.0 % [30.8–33.3] | 29.5 % | 5.0 % | 0.379 | 52.96 | — |
| NAVAJO health, no spaCy | 31.8 % | 13.4 % [12.5–14.3] | 4.6 % | 1.2 % | 0.802 | 2.91 | 100.0 % |
| NAVAJO health | 30.5 % | 11.6 % [10.8–12.4] | 3.7 % | 4.3 % | 0.529 | 64.67 | 100.0 % |
| Hybrid, no spaCy | 40.0 % | 9.6 % [8.9–10.4] | 2.7 % | 5.6 % | 0.471 | 54.46 | 100.0 % |
| Hybrid NAVAJO + Presidio | 39.9 % | 9.6 % [8.9–10.4] | 2.8 % | 5.6 % | 0.468 | 113.86 | 100.0 % |

### test (250 documents)

| System | Leak L (strict) | PHI chars exposed E [95% CI] | Direct ids exposed | Over-masking O | Precision | ms/doc | Round-trip exact |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 | 0.0 | — |
| NAVAJO 0.1 regex | 68.6 % | 35.8 % [34.8–36.9] | 21.6 % | 1.5 % | 0.556 | 1.38 | 0.0 % |
| NAVAJO 0.1 + spaCy | 68.6 % | 32.7 % [31.6–33.7] | 17.7 % | 2.2 % | 0.483 | 31.73 | 1.6 % |
| Presidio (control) | 59.3 % | 31.0 % [29.8–32.2] | 27.0 % | 5.2 % | 0.385 | 50.36 | — |
| NAVAJO health, no spaCy | 31.3 % | 14.5 % [13.6–15.5] | 5.0 % | 1.2 % | 0.809 | 2.66 | 100.0 % |
| NAVAJO health | 29.6 % | 12.5 % [11.7–13.3] | 4.2 % | 4.4 % | 0.535 | 61.4 | 100.0 % |
| Hybrid, no spaCy | 39.1 % | 10.1 % [9.4–10.9] | 2.8 % | 5.6 % | 0.474 | 52.2 | 100.0 % |
| Hybrid NAVAJO + Presidio | 39.1 % | 10.2 % [9.4–10.9] | 2.9 % | 5.7 % | 0.471 | 111.22 | 100.0 % |

## Pre-registered tests and ablations (paired document bootstrap)

| Comparison | Split | Metric | Difference (points) | 95% CI, seeds 0/1/2 | Reading |
|---|---|---|---|---|---|
| H1  NAVAJO 0.1 vs Presidio: NAVAJO 0.1 + spaCy − Presidio (control) | test | E_exposure | +1.69 | [+0.37, +2.91] / [+0.35, +3.10] / [+0.39, +3.07] | A higher (CI above 0) |
| H2  health pack vs 0.1 (exposure): NAVAJO health − NAVAJO 0.1 + spaCy | dev | E_exposure | -21.69 | [-22.86, -20.56] / [-22.84, -20.58] / [-22.88, -20.56] | A lower (CI below 0) |
| H2  health pack vs 0.1 (over-masking): NAVAJO health − NAVAJO 0.1 + spaCy | dev | O_overmask | +2.07 | [+1.90, +2.24] / [+1.90, +2.24] / [+1.89, +2.24] | A higher (CI above 0) |
| H3a hybrid vs NAVAJO health: Hybrid NAVAJO + Presidio − NAVAJO health | test | E_exposure | -2.30 | [-2.79, -1.85] / [-2.78, -1.86] / [-2.77, -1.85] | A lower (CI below 0) |
| H3b hybrid vs Presidio: Hybrid NAVAJO + Presidio − Presidio (control) | test | E_exposure | -20.79 | [-21.86, -19.82] / [-21.79, -19.81] / [-21.79, -19.80] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio: NAVAJO health − Presidio (control) | test | E_exposure | -18.49 | [-19.67, -17.28] / [-19.65, -17.32] / [-19.62, -17.33] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio (direct ids): NAVAJO health − Presidio (control) | test | DI_E_exposure | -22.76 | [-24.14, -21.45] / [-24.04, -21.48] / [-24.03, -21.42] | A lower (CI below 0) |
| Abl. hybrid vs Presidio (direct ids): Hybrid NAVAJO + Presidio − Presidio (control) | test | DI_E_exposure | -24.07 | [-25.37, -22.90] / [-25.27, -22.89] / [-25.24, -22.90] | A lower (CI below 0) |
| Abl. hybrid over-masking vs Presidio: Hybrid NAVAJO + Presidio − Presidio (control) | test | O_overmask | +0.50 | [+0.37, +0.65] / [+0.38, +0.66] / [+0.38, +0.66] | A higher (CI above 0) |
| Abl. spaCy inside hybrid: Hybrid NAVAJO + Presidio − Hybrid, no spaCy | test | E_exposure | +0.06 | [+0.02, +0.10] / [+0.02, +0.10] / [+0.02, +0.10] | A higher (CI above 0) |
| Abl. NAVAJO inside hybrid, no spaCy: Hybrid, no spaCy − Presidio (control) | test | E_exposure | -20.85 | [-21.92, -19.88] / [-21.84, -19.89] / [-21.85, -19.86] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy: Hybrid, no spaCy − NAVAJO health, no spaCy | test | E_exposure | -4.40 | [-5.14, -3.73] / [-5.15, -3.68] / [-5.12, -3.68] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy (over-masking): Hybrid, no spaCy − NAVAJO health, no spaCy | test | O_overmask | +4.47 | [+4.24, +4.72] / [+4.24, +4.71] / [+4.23, +4.70] | A higher (CI above 0) |
| Abl. NAVAJO health no spaCy vs Presidio: NAVAJO health, no spaCy − Presidio (control) | test | E_exposure | -16.45 | [-17.79, -15.04] / [-17.81, -15.07] / [-17.77, -15.07] | A lower (CI below 0) |
| Abl. NAVAJO health no spaCy vs Presidio (over-masking): NAVAJO health, no spaCy − Presidio (control) | test | O_overmask | -4.02 | [-4.30, -3.74] / [-4.31, -3.74] / [-4.29, -3.75] | A lower (CI below 0) |

## Per-label character coverage (test)

| Gold label | n | NAVAJO 0.1 regex | NAVAJO 0.1 + spaCy | Presidio (control) | NAVAJO health | Hybrid NAVAJO + Presidio |
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

# Stress test E008 — MEDDOCAN test without the labelled header

Environment: `{"python": "3.13.7", "platform": "Windows-10-10.0.19045-SP0", "numpy": "2.4.6", "spacy": "3.8.16", "presidio_analyzer": "?", "es_core_news_lg": "3.8.0", "build_seconds": 3.7, "presidio_recognizers_es": ["CreditCardRecognizer", "CryptoRecognizer", "DateRecognizer", "EmailRecognizer", "EsNieRecognizer", "EsNifRecognizer", "IbanRecognizer", "IpRecognizer", "MacAddressRecognizer", "MedicalLicenseRecognizer", "PhoneRecognizer", "SpacyRecognizer", "UrlRecognizer"], "presidio_added_for_es": []}`

### test (250 documents)

| System | Leak L (strict) | PHI chars exposed E [95% CI] | Direct ids exposed | Over-masking O | Precision | ms/doc | Round-trip exact |
|---|---|---|---|---|---|---|---|
| Raw note (today) | 100.0 % | 100.0 % [100.0–100.0] | 100.0 % | 0.0 % | 0.000 | 0.0 | — |
| NAVAJO 0.1 regex | 76.5 % | 37.6 % [35.6–39.7] | 18.0 % | 1.3 % | 0.451 | 1.36 | 0.0 % |
| NAVAJO 0.1 + spaCy | 76.9 % | 36.2 % [34.1–38.2] | 16.9 % | 1.8 % | 0.366 | 36.35 | 2.4 % |
| Presidio (control) | 64.7 % | 27.5 % [25.6–29.6] | 16.5 % | 3.1 % | 0.278 | 53.67 | — |
| NAVAJO health, no spaCy | 53.7 % | 23.9 % [22.1–25.8] | 10.6 % | 0.9 % | 0.628 | 2.56 | 100.0 % |
| NAVAJO health | 49.7 % | 20.3 % [18.7–21.9] | 8.7 % | 2.8 % | 0.356 | 58.75 | 100.0 % |
| Hybrid, no spaCy | 57.5 % | 16.9 % [15.4–18.3] | 5.4 % | 3.5 % | 0.305 | 49.81 | 100.0 % |
| Hybrid NAVAJO + Presidio | 57.4 % | 17.0 % [15.5–18.4] | 5.6 % | 3.6 % | 0.304 | 105.76 | 100.0 % |

## Pre-registered tests and ablations (paired document bootstrap)

| Comparison | Split | Metric | Difference (points) | 95% CI, seeds 0/1/2 | Reading |
|---|---|---|---|---|---|
| H1  NAVAJO 0.1 vs Presidio: NAVAJO 0.1 + spaCy − Presidio (control) | test | E_exposure | +8.62 | [+6.58, +10.61] / [+6.61, +10.73] / [+6.54, +10.81] | A higher (CI above 0) |
| H3a hybrid vs NAVAJO health: Hybrid NAVAJO + Presidio − NAVAJO health | test | E_exposure | -3.31 | [-4.18, -2.50] / [-4.18, -2.51] / [-4.22, -2.50] | A lower (CI below 0) |
| H3b hybrid vs Presidio: Hybrid NAVAJO + Presidio − Presidio (control) | test | E_exposure | -10.57 | [-12.33, -8.91] / [-12.27, -8.97] / [-12.21, -9.00] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio: NAVAJO health − Presidio (control) | test | E_exposure | -7.26 | [-9.30, -5.24] / [-9.20, -5.29] / [-9.12, -5.33] | A lower (CI below 0) |
| Abl. NAVAJO health vs Presidio (direct ids): NAVAJO health − Presidio (control) | test | DI_E_exposure | -7.78 | [-10.77, -4.98] / [-10.54, -5.12] / [-10.51, -5.19] | A lower (CI below 0) |
| Abl. hybrid vs Presidio (direct ids): Hybrid NAVAJO + Presidio − Presidio (control) | test | DI_E_exposure | -10.86 | [-13.49, -8.56] / [-13.26, -8.63] / [-13.30, -8.62] | A lower (CI below 0) |
| Abl. hybrid over-masking vs Presidio: Hybrid NAVAJO + Presidio − Presidio (control) | test | O_overmask | +0.41 | [+0.28, +0.58] / [+0.28, +0.58] / [+0.28, +0.58] | A higher (CI above 0) |
| Abl. spaCy inside hybrid: Hybrid NAVAJO + Presidio − Hybrid, no spaCy | test | E_exposure | +0.11 | [+0.03, +0.20] / [+0.03, +0.20] / [+0.03, +0.21] | A higher (CI above 0) |
| Abl. NAVAJO inside hybrid, no spaCy: Hybrid, no spaCy − Presidio (control) | test | E_exposure | -10.68 | [-12.44, -9.00] / [-12.40, -9.06] / [-12.32, -9.11] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy: Hybrid, no spaCy − NAVAJO health, no spaCy | test | E_exposure | -7.03 | [-8.47, -5.74] / [-8.43, -5.64] / [-8.44, -5.67] | A lower (CI below 0) |
| Abl. Presidio inside hybrid, no spaCy (over-masking): Hybrid, no spaCy − NAVAJO health, no spaCy | test | O_overmask | +2.65 | [+2.44, +2.87] / [+2.45, +2.87] / [+2.45, +2.86] | A higher (CI above 0) |
| Abl. NAVAJO health no spaCy vs Presidio: NAVAJO health, no spaCy − Presidio (control) | test | E_exposure | -3.65 | [-6.08, -1.18] / [-6.00, -1.32] / [-5.92, -1.33] | A lower (CI below 0) |
| Abl. NAVAJO health no spaCy vs Presidio (over-masking): NAVAJO health, no spaCy − Presidio (control) | test | O_overmask | -2.24 | [-2.50, -1.98] / [-2.49, -1.98] / [-2.49, -1.99] | A lower (CI below 0) |

## Per-label character coverage (test)

| Gold label | n | NAVAJO 0.1 regex | NAVAJO 0.1 + spaCy | Presidio (control) | NAVAJO health | Hybrid NAVAJO + Presidio |
|---|---|---|---|---|---|---|
| TERRITORIO | 437 | 49 % | 49 % | 72 % | 91 % | 97 % |
| EDAD_SUJETO_ASISTENCIA | 269 | 0 % | 0 % | 1 % | 0 % | 1 % |
| NOMBRE_PERSONAL_SANITARIO * | 251 | 96 % | 99 % | 98 % | 97 % | 100 % |
| CORREO_ELECTRONICO * | 248 | 98 % | 98 % | 100 % | 97 % | 100 % |
| SEXO_SUJETO_ASISTENCIA | 218 | 0 % | 0 % | 1 % | 0 % | 1 % |
| CALLE * | 167 | 66 % | 67 % | 68 % | 77 % | 83 % |
| HOSPITAL | 130 | 66 % | 71 % | 89 % | 95 % | 98 % |
| PAIS | 116 | 26 % | 25 % | 96 % | 100 % | 100 % |
| FECHAS * | 113 | 4 % | 4 % | 8 % | 84 % | 84 % |
| FAMILIARES_SUJETO_ASISTENCIA | 80 | 0 % | 2 % | 4 % | 4 % | 4 % |
| INSTITUCION | 67 | 44 % | 48 % | 84 % | 80 % | 93 % |
| NUMERO_TELEFONO * | 24 | 66 % | 66 % | 5 % | 97 % | 97 % |
| ID_SUJETO_ASISTENCIA * | 13 | 0 % | 0 % | 0 % | 0 % | 0 % |
| PROFESION | 9 | 0 % | 0 % | 0 % | 0 % | 0 % |
| OTROS_SUJETO_ASISTENCIA | 7 | 0 % | 0 % | 0 % | 0 % | 0 % |
| NUMERO_FAX * | 7 | 54 % | 54 % | 17 % | 100 % | 100 % |
| CENTRO_SALUD | 6 | 39 % | 39 % | 98 % | 100 % | 100 % |
| NOMBRE_SUJETO_ASISTENCIA * | 2 | 0 % | 100 % | 100 % | 100 % | 100 % |

Cells: share of the label's characters masked. * = direct identifier.

![exposure](fig_exposure_test_noheader.png)

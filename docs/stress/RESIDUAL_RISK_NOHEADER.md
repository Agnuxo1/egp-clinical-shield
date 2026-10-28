# Per-note residual risk (test, header removed, 250 notes)

| System | Notes with ≥1 direct identifier fully visible | Notes with the patient's name fully visible | Notes with ≥1 direct-identifier character visible |
|---|---|---|---|
| NAVAJO 0.1 + spaCy | 10.4 % [6.8–14.4] | 0.0 % [0.0–0.0] | 67.6 % [61.6–73.2] |
| Presidio (control) | 10.8 % [7.2–14.8] | 0.0 % [0.0–0.0] | 72.4 % [66.8–77.6] |
| NAVAJO health, no spaCy | 13.2 % [9.2–17.2] | 0.8 % [0.0–2.0] | 58.8 % [52.8–65.2] |
| NAVAJO health | 11.6 % [7.6–15.6] | 0.0 % [0.0–0.0] | 55.6 % [49.2–62.0] |
| Hybrid NAVAJO + Presidio, no spaCy | 9.2 % [5.6–12.8] | 0.0 % [0.0–0.0] | 44.8 % [38.4–50.8] |

95 % bootstrap intervals over notes (2,000 resamples, seed 0). Direct identifiers as pre-registered (names, ID numbers, phone, fax, e-mail, street, URL, dates).

## Audit of 30 leaked direct identifiers (NAVAJO health, no spaCy, random sample of 197, seed 20261028)

Synthetic data from MEDDOCAN; no real person.

| Label | Gold text | Fully visible? | Left context |
|---|---|---|---|
| CALLE | `Avda. Pío XII, 36` | partly | …iología Clínica Universitaria  |
| CALLE | `Ofra s/n` | partly | …al Universitario de Canarias.  |
| CALLE | `Avda. Dr. Marañón s/n` | partly | …. Hospital Militar O'Donnell.  |
| CALLE | `Avda. Ramón y Cajal, 3` | partly | …ospital Clínico Universitario  |
| CALLE | `Ctra. De Colmenar Viejo, km. 9,100` | partly | …Alba. Hospital Ramón y Cajal.  |
| CALLE | `C. Lara Bohórquez San Andrés, 14 - Local 3` | partly | …o por: Sandra Bellorin Custo.  |
| CALLE | `Av. Travesía Choupana s/n` | partly | …io de Santiago de Compostela.  |
| CALLE | `Urbanización Montiboli, 188 A - 6` | partly | …: José Antonio Cánovas Ivorra  |
| CALLE | `C/Enrique Flórez 25` | partly | …  Dr. Alejandro Lorite Álvaro  |
| CALLE | `Ginzo de Limia 55, 9o C` | partly | …ogía, Hospital 12 de Octubre,  |
| CALLE | `Avda. San Juan Bosco, 15` | partly | … Universitario "Lozano Blesa"  |
| CALLE | `Teseo, 5 3-N` | partly | …Antonio Javier Márquez Moreno  |
| CALLE | `Pg Vall d'Hebron 119-129` | partly | …l Universitari Vall d'Hebron.  |
| CALLE | `Avda. Gaspar Aguilar, 90` | partly | …e Urología Hospital Dr. Peset  |
| CALLE | `C/ Pedro Rico, 19 - 10o D` | partly | …én Fernández García-Guilarte.  |
| CALLE | `Ctra. de Toledo, Km 12,5` | partly | …pital Universitario de Getafe  |
| CORREO_ELECTRONICO | `r_navarro_suay@yahoo.es` | yes | …por: Dr. Ricardo Navarro Suay  |
| FECHAS | `1997` | yes | …síndrome postlaminectomía. En  |
| FECHAS | `2004` | yes | … Crohn ileal diagnosticado en  |
| FECHAS | `febrero 2011` | partly | … valor TSH, y TC cervical. En  |
| FECHAS | `verano de 2003` | partly | …haber dormido muy poco) en el  |
| FECHAS | `2001` | yes | …tico. En la primera consulta ( |
| FECHAS | `2006` | yes | …ó con Nefrología a finales de  |
| FECHAS | `abril 2011` | partly | …e 850 mg/m2 cada 3 semanas en  |
| FECHAS | `1999` | yes | …ma izquierda diagnosticado en  |
| ID_SUJETO_ASISTENCIA | `soltero` | yes | …Varón de 44 años,  |
| NOMBRE_PERSONAL_SANITARIO | `Pere Huguet` | partly | …romosoma 22. Remitido por: Dr  |
| NOMBRE_PERSONAL_SANITARIO | `Eduardo Sánchez de Badia` | partly | …lta definitiva. Remitido por:  |
| NOMBRE_PERSONAL_SANITARIO | `Gabriel de Arriba` | partly | … de 24,6 mEq/l. Remitido por:  |
| NOMBRE_PERSONAL_SANITARIO | `Noemí Ruiz del Río` | partly | …íntomas. Responsable clínico:  |

All leaks by label (count, fully visible):

- CALLE: 108 (1 fully visible)
- FECHAS: 38 (20 fully visible)
- NOMBRE_PERSONAL_SANITARIO: 26 (0 fully visible)
- ID_SUJETO_ASISTENCIA: 13 (9 fully visible)
- CORREO_ELECTRONICO: 9 (9 fully visible)
- NOMBRE_SUJETO_ASISTENCIA: 2 (2 fully visible)
- NUMERO_TELEFONO: 1 (1 fully visible)

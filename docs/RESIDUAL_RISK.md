# Per-note residual risk (test, 250 notes)

| System | Notes with ≥1 direct identifier fully visible | Notes with the patient's name fully visible | Notes with ≥1 direct-identifier character visible |
|---|---|---|---|
| NAVAJO 0.1 + spaCy | 90.0 % [86.0–93.6] | 17.2 % [12.8–22.0] | 100.0 % [100.0–100.0] |
| Presidio (control) | 97.2 % [94.8–99.2] | 10.4 % [6.8–14.4] | 100.0 % [100.0–100.0] |
| NAVAJO health, no spaCy | 15.6 % [11.2–20.4] | 3.6 % [1.6–6.0] | 69.2 % [63.2–75.2] |
| NAVAJO health | 12.0 % [8.0–16.0] | 0.4 % [0.0–1.2] | 66.0 % [60.0–72.0] |
| Hybrid NAVAJO + Presidio, no spaCy | 9.6 % [6.0–13.2] | 0.4 % [0.0–1.2] | 54.4 % [48.0–60.8] |

95 % bootstrap intervals over notes (2,000 resamples, seed 0). Direct identifiers as pre-registered (names, ID numbers, phone, fax, e-mail, street, URL, dates).

## Audit of 30 leaked direct identifiers (NAVAJO health, no spaCy, random sample of 266, seed 20261028)

Synthetic data from MEDDOCAN; no real person.

| Label | Gold text | Fully visible? | Left context |
|---|---|---|---|
| CALLE | `Calle Strachan, 4 -2º piso` | partly | …por: Eduardo Sánchez de Badia  |
| CALLE | `Avda. Tres Cruces, s/n` | partly | …spital General Universitario.  |
| CALLE | `C/ Francisco Gourié, 28, 5.º E` | partly | …Dr. Jose Maria López Álvarez.  |
| CALLE | `Passeig de Sant Joan de Déu, 2` | partly | …ó. Hospital Sant Joan de Déu.  |
| CALLE | `Avda. Europa, 19` | partly | …S: 38 47563379 20. Domicilio:  |
| CALLE | `Teseo, 5 3-N` | partly | …Antonio Javier Márquez Moreno  |
| CALLE | `Av. del Rocío, 2` | partly | …S: 82 35613758 41. Domicilio:  |
| CALLE | `Avda. Menéndez Pidal, s/n` | partly | …cina. Universidad de Córdoba.  |
| CALLE | `Av. Beniarda, 13` | partly | …oza. NHC: 5467980. Domicilio:  |
| CALLE | `Ctra. Nacional IV, Km 665` | partly | …ología. Hospital Puerto Real.  |
| CALLE | `Ctra. Sant Boi, 59-61` | partly | …por la Imagen. CAP El Serral.  |
| CALLE | `Av. Cordoba, s/n` | partly | …l.com. Hospital 12 de octubre  |
| CALLE | `Pº de la Castellana, 261` | partly | …logía. Hospital Univ. La Paz.  |
| CALLE | `Av. Miguel de Cervantes, 25, 1H` | partly | …S: 56 89527056 79. Domicilio:  |
| CALLE | `Calle 64 # 52-59` | partly | …oquia Facultad de Odontología  |
| CALLE | `C/ S. Martín de Porres, 15 - 2º` | partly | … Marín. Unidad de Hematología  |
| CALLE | `Av. San Ignacio, 11` | partly | …S: 83 23783246 78. Domicilio:  |
| CALLE | `Av. Las Rozas, 34, 3, 1` | partly | …S: 79 83268953 05. Domicilio:  |
| CALLE | `Avda. de los Empresarios 15, 1F` | partly | …S: 15 50201565 22. Domicilio:  |
| CORREO_ELECTRONICO | `jesastur@hotmail.com` | yes | …iménez. Correos Electrónicos:  |
| FECHAS | `2001` | yes | …tico. En la primera consulta ( |
| ID_SUJETO_ASISTENCIA | `afgano` | yes | …, de 29 años (165 cm, 68 Kg),  |
| ID_SUJETO_ASISTENCIA | `caucásico` | yes | …e clínico del paciente: Varón  |
| ID_SUJETO_ASISTENCIA | `casado` | yes | …: Paciente varón, de 47 años,  |
| ID_SUJETO_ASISTENCIA | `raza negra` | partly | …aciente de sexo masculino, de  |
| NOMBRE_PERSONAL_SANITARIO | `Raquel Ridruejo Sáez` | partly | …cuadro séptico. Remitido por:  |
| NOMBRE_PERSONAL_SANITARIO | `Eduardo Sánchez de Badia` | partly | …lta definitiva. Remitido por:  |
| NOMBRE_PERSONAL_SANITARIO | `María del Rosario García Luzardo` | partly | …comotor normal. Remitido por:  |
| NOMBRE_SUJETO_ASISTENCIA | `Jorge` | yes | …﻿Nombre:  |
| NOMBRE_SUJETO_ASISTENCIA | `Joel` | yes | …﻿Nombre:  |

All leaks by label (count, fully visible):

- CALLE: 163 (1 fully visible)
- FECHAS: 38 (20 fully visible)
- NOMBRE_PERSONAL_SANITARIO: 30 (0 fully visible)
- ID_SUJETO_ASISTENCIA: 13 (9 fully visible)
- NOMBRE_SUJETO_ASISTENCIA: 10 (10 fully visible)
- CORREO_ELECTRONICO: 9 (9 fully visible)
- ID_TITULACION_PERSONAL_SANITARIO: 2 (0 fully visible)
- NUMERO_TELEFONO: 1 (1 fully visible)

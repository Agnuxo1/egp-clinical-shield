# EGP Clinical Shield

**Remove patient identities from a clinical note on the clinician's own computer, ask any AI assistant, and get the answer back with the real names restored.**

Built on [navajo-egp](poc/navajo_egp) (Project NAVAJO, MIT licence), with a new health pack for Spanish clinical documents and a pre-registered evaluation on 1,000 public synthetic clinical cases. Prepared for the MIT Solve 2027 Global Health Challenge.

> Status: **prototype**. No clinic uses it yet. All numbers below come from synthetic cases, not from real patient notes.

## The problem in one paragraph

Frontline clinicians already use AI assistants for letters, summaries and differential diagnoses, but those assistants run on third-party servers. Pasting a note sends the patient's name, record numbers, address and dates with it, which data-protection law treats as special-category data. Health services respond by banning AI for patient work, or staff use it anyway. Sources in [docs/SOURCES.md](docs/SOURCES.md).

## What it does

```
clinical note ──► mask on the PC (names, IDs, addresses, dates, institutions → ENTITY_A, ID_001 …)
                   │  ages, sex, symptoms, labs and drugs stay: the model needs them
                   ▼
              any AI assistant (OpenAI, Anthropic, a local model …) sees only placeholders
                   ▼
answer ◄── restore the real values from an in-memory mapping, then destroy the mapping
```

- Runs on a laptop CPU in milliseconds per note; no GPU, no account, no data leaves the machine except the masked text.
- One line wraps the OpenAI, Anthropic or LangChain client (`EGPMiddleware().wrap(client)`).
- Masking is reversible and exact: the health pack restores the original text byte for byte.

## Results

RESULTS_PLACEHOLDER

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash poc/run_server.sh          # downloads MEDDOCAN from Zenodo (md5 checked) and the official scorer, runs everything
python poc/make_report.py --results poc/results --out docs
```

The pre-registration is in [experiments/PREREGISTRO.md](experiments/PREREGISTRO.md) and every run, including the negative ones, is in [experiments/LOG.md](experiments/LOG.md).

## What is masked and what is kept

| Masked (direct identifiers and places) | Kept on purpose (clinically needed) |
|---|---|
| Patient, relative and clinician names; record, insurance, episode and licence numbers; phone, fax, e-mail, URLs; streets, postcodes, towns, provinces, countries; hospitals and institutions; dates | Age, sex, kinship words ("su madre"), symptoms, findings, lab values, drugs and doses |

Keeping age and sex follows NAVAJO's EGP design ("67 años → keep, needed for dosing"). MEDDOCAN counts them as PHI, so the all-PHI numbers above penalise this choice; the direct-identifier columns do not include them.

## Limitations

- Synthetic Spanish cases from one corpus with a uniform header template; real notes are messier. The health pack was developed on the training split only, and the test split was run once.
- Rule- and NER-based detection misses some entities; the evaluation reports what is missed by category.
- Placeholders protect identity, not every quasi-identifier: a rare disease plus a small town can still point to a person.
- Not a medical device and not legal advice. A clinic that deploys it still needs its own data-protection impact assessment.

## Licences

Code: MIT ([LICENSE](LICENSE)). MEDDOCAN data: CC BY 4.0, downloaded at run time, not redistributed. Official MEDDOCAN scorer: MIT. Presidio: MIT. spaCy `es_core_news_lg`: GPL-3.0, downloaded at run time, not redistributed.

## Citation

```bibtex
@software{angulo2026egpclinical,
  title  = {EGP Clinical Shield: reversible de-identification of clinical notes before AI assistants},
  author = {Angulo de Lafuente, Francisco},
  year   = {2026},
  url    = {https://github.com/Agnuxo1/egp-clinical-shield}
}
```

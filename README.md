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

Pre-registered evaluation on [MEDDOCAN](https://doi.org/10.5281/zenodo.4279323): 1,000 public synthetic Spanish clinical cases with gold annotations (500 train, 250 dev, 250 test), scored with the official MEDDOCAN scorer. The health pack was built on train only; **test was run once, for every system at the same time**. Lower is better everywhere.

![What reaches an external AI model](docs/fig_exposure_test.png)

| Test set, 250 notes | PHI characters left visible | Direct-identifier characters left visible | Clinical text masked by mistake | Notes with ≥1 direct identifier fully visible | ms per note (CPU) | Exact restore |
|---|---|---|---|---|---|---|
| Raw note (what happens today) | 100 % | 100 % | 0 % | 100 % | — | — |
| Microsoft Presidio (control) | 31.0 % | 27.0 % | 5.2 % | 97.2 % | 50 | — |
| navajo-egp 0.1 + spaCy (before this work) | 32.7 % | 17.7 % | 2.2 % | 90.0 % | 32 | 1.6 % |
| **Health pack, default mode** (no ML model) | **14.5 %** | **5.0 %** | **1.2 %** | **15.6 %** | **2.7** | **100 %** |
| **Health pack + Presidio, maximum protection** | **10.1 %** | **2.8 %** | 5.6 % | **9.6 %** | 52 | **100 %** |

Pre-registered hypotheses ([experiments/PREREGISTRO.md](experiments/PREREGISTRO.md)), with paired bootstrap intervals in [docs/RESULTS.md](docs/RESULTS.md):

- **H1, rejected.** navajo-egp 0.1 alone did not beat Presidio: +1.69 points of exposure, 95 % CI [+0.37, +2.91].
- **H2, rejected narrowly.** The health pack with spaCy cut exposure by 21.7 points on dev, but raised over-masking by 2.07 points; the pre-set limit was 2. The default mode (no spaCy) lowers over-masking instead.
- **H3, confirmed.** The hybrid exposes less than the health pack alone (−2.30 points) and than Presidio (−20.79 points).

Stress test without the form-like header (62 % of the PHI sits there; [docs/stress](docs/stress)): Presidio 27.5 %, default mode 23.9 % (difference −3.65, CI [−6.08, −1.18]), maximum protection 16.9 %. Much of the margin on full notes comes from the header. Per-note residual risk and an audit of 30 leaks: [docs/RESIDUAL_RISK.md](docs/RESIDUAL_RISK.md). Two bugs found in that audit are fixed in the next cycle (c3), checked on train and dev only; the test numbers above are from the frozen cycle c2.

## Reproduce

Linux or macOS with Python 3.13, about 15 minutes on 4 CPU cores:

```bash
bash poc/run_server.sh   # creates poc/.venv with the pinned versions, downloads MEDDOCAN (md5 checked) and the official scorer, runs all 8 systems
poc/.venv/bin/python poc/make_report.py --results poc/results --out docs
python -m pytest tests   # 42 tests; the core needs no extra packages
```

Stress test and residual risk: `poc/make_noheader.py`, then `poc/run_eval.py` on the new folder, and `poc/residual_risk.py`.

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

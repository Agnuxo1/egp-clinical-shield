# Post-hoc analyses after the pre-registered run

These used the test split after E007 without changing any system. Details and numbers in `experiments/LOG.md`.

- **E008, no header:** [docs/stress/RESULTS_NOHEADER.md](stress/RESULTS_NOHEADER.md).
- **E009/E011, per-note residual risk:** [docs/RESIDUAL_RISK.md](RESIDUAL_RISK.md).
- **E012, contribution of the navajo-egp core detectors inside the default mode** (default mode minus the health pack's own patterns alone, paired bootstrap, seed 0): PHI characters left visible −6.26 points [−7.05, −5.50] on full notes and −13.28 [−15.02, −11.62] without the header; direct identifiers −7.68 [−8.74, −6.68] and −20.30 [−23.21, −17.57]; non-PHI text masked +0.97 [+0.82, +1.14] and +0.77 [+0.61, +0.95]. Pack alone: 21.3 % / 13.2 % (full), 37.9 % / 31.8 % (no header).
- **E013, integrated shield (`deid/shield.py`, default mode, echo model):** 242 of 250 test notes restored exactly; 8 refused by the final hard-identifier check because an e-mail address was still visible (cause fixed in cycle c3, checked on train/dev only); 5.2 ms per note on the PC.

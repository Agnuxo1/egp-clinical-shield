#!/usr/bin/env bash
# Post-hoc analyses E008, E009/E011 and E012 on top of the pre-registered run in poc/results.
# None of them changes a system. PY, DATA and EV can point elsewhere (the defaults are what run_server.sh creates).
set -euo pipefail
export PYTHONUTF8=1 PYTHONHASHSEED=0
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
PY="${PY:-$HERE/.venv/bin/python}"
DATA="${DATA:-data/meddocan}"
EV="${EV:-data/ev}"
OUT=results_posthoc
NOHDR="${NOHDR:-data/meddocan_noheader}"
mkdir -p "$OUT"

"$PY" make_noheader.py --data "$DATA" --split test --out "$NOHDR"
cp "$NOHDR/test_noheader_stats.json" "$OUT/"
"$PY" run_eval.py --data "$NOHDR" --evaluator "$EV" --splits test --systems S0 S1 S2 C1 N3 N3r H4 H4r \
  --health c2 --out "$OUT/noheader" --boot 2000
"$PY" make_report.py --results "$OUT/noheader" --out "$OUT/noheader/report" --boot 2000 > /dev/null
"$PY" run_eval.py --data "$DATA" --evaluator "$EV" --splits test --systems N3r P3r --health c2 --out "$OUT/p3r_full" --boot 2000
"$PY" run_eval.py --data "$NOHDR" --evaluator "$EV" --splits test --systems N3r P3r --health c2 --out "$OUT/p3r_noheader" --boot 2000
"$PY" ablation_core.py --runs "$OUT/p3r_full" "$OUT/p3r_noheader" --out "$OUT/E012.json"
"$PY" residual_risk.py --data "$DATA" --results results --split test --out "$OUT/RESIDUAL_RISK.md"
"$PY" residual_risk.py --data "$NOHDR" --results "$OUT/noheader" --split test --title ", header removed" \
  --out "$OUT/RESIDUAL_RISK_NOHEADER.md"

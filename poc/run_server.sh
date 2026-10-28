#!/usr/bin/env bash
# E007: full pre-registered run on server-ia (CPU lane). Public inputs only; nothing secret in this folder.
set -euo pipefail
export LC_ALL=C.UTF-8 PYTHONUTF8=1 PYTHONHASHSEED=0
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
mkdir -p results data

VENV="${VENV:-$HERE/.venv}"  # E007 ran with VENV=/home/ai/venvs/mitsolve
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q "spacy==3.8.16" "presidio-analyzer==2.2.364" "matplotlib==3.11.2"
  "$VENV/bin/pip" install -q "https://github.com/explosion/spacy-models/releases/download/es_core_news_lg-3.8.0/es_core_news_lg-3.8.0-py3-none-any.whl"
fi
# refuse an existing environment with other versions
"$VENV/bin/python" - <<'PY'
from importlib.metadata import version
want = {"spacy": "3.8.16", "presidio-analyzer": "2.2.364", "es-core-news-lg": "3.8.0", "matplotlib": "3.11.2"}
bad = {k: version(k) for k in want if version(k) != want[k]}
assert not bad, f"version mismatch: {bad}"
PY
"$VENV/bin/pip" freeze > results/pip_freeze.txt

if [ ! -d data/meddocan ]; then
  curl -sSL -o data/meddocan.zip "https://zenodo.org/records/4279323/files/meddocan.zip?download=1"
  (cd data && echo "6a09eb975580fdf56bc7041eadc9c921  meddocan.zip" | md5sum -c -)
  "$VENV/bin/python" -c "import zipfile; zipfile.ZipFile('data/meddocan.zip').extractall('data')"
fi
if [ ! -d data/ev ]; then
  git clone -q https://github.com/PlanTL-SANIDAD/MEDDOCAN-Evaluation-Script.git data/ev
  git -C data/ev checkout -q 843152c475e7118171028badd16f6342c5560e0f
fi

{ nproc; lscpu | grep -m1 "Model name"; free -g | head -2; } > results/machine.txt
SECONDS=0
"$VENV/bin/python" run_eval.py --data data/meddocan --evaluator data/ev \
  --splits train dev test --systems S0 S1 S2 C1 N3 N3r H4 H4r --health c2 --out results --boot 2000 \
  2> results/stderr.txt | tee results/console.txt
echo "wall_seconds=$SECONDS" >> results/machine.txt
"$VENV/bin/python" make_report.py --results results --out results/report --boot 2000 > /dev/null

"""E011: recompute metrics from the saved brat predictions of a run_eval.py folder (systems are not re-run).

python recount.py --data <meddocan root> --results <run_eval out> [--boot 2000]
Writes summary.json (the previous one is kept as summary_before_E011.json) and *.counts.json.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from deid import metrics as M  # noqa: E402
from deid.data import load_split  # noqa: E402


def read_pred(path: str):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            _, info, _ = line.rstrip("\n").split("\t", 2)
            label, s, e = info.split()
            out.append((label, int(s), int(e)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    path = os.path.join(args.results, "summary.json")
    backup = os.path.join(args.results, "summary_before_E011.json")
    if not os.path.exists(backup):
        shutil.copy(path, backup)
    summary = json.load(open(backup, encoding="utf-8"))
    docs_by_split = {}
    for key, row in summary["results"].items():
        split, sid = key.split("/")
        docs = docs_by_split.setdefault(split, load_split(args.data, split))
        preds = {d.doc_id: read_pred(os.path.join(args.results, split, row["system"], d.doc_id + ".ann")) for d in docs}
        per_doc = [M.doc_counts(d.text, d.gold, preds[d.doc_id]) for d in docs]
        mat = M.count_matrix(per_doc)
        point = {k: float(v) for k, v in M.aggregate({k: mat[:, i].sum() for i, k in enumerate(M.COUNT_KEYS)}).items()}
        assert abs(point["R_strict"] - row["official"]["strict_R"]) < 1e-9 or sid == "S0", key
        row["point"] = point
        row["ci95"] = {f"seed{s}": M.bootstrap(mat, n=args.boot, seed=s) for s in (0, 1, 2)}
        row["per_label"] = M.per_label_recall(docs, preds)
        row["totals"] = {k: int(mat[:, i].sum()) for i, k in enumerate(M.COUNT_KEYS)}
        with open(os.path.join(args.results, split, row["system"] + ".counts.json"), "w", encoding="utf-8") as fh:
            json.dump(per_doc, fh)
        print(f"{key:10s} E={point['E_exposure']:.4f} DI_E={point['DI_E_exposure']:.4f} O={point['O_overmask']:.4f} "
              f"(before: E={summary_before(backup, key, 'E_exposure'):.4f})")
    summary["recount"] = "E011: E and DI_E count every character inside gold spans, as pre-registered"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)


def summary_before(backup, key, metric, _cache={}):
    if backup not in _cache:
        _cache[backup] = json.load(open(backup, encoding="utf-8"))
    return _cache[backup]["results"][key]["point"][metric]


if __name__ == "__main__":
    main()

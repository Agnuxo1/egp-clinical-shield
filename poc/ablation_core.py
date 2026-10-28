"""E012: contribution of the navajo-egp core detectors inside the default mode (N3r minus P3r, paired bootstrap).

python ablation_core.py --runs results_posthoc/p3r_full results_posthoc/p3r_noheader --out results_posthoc/E012.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deid import metrics as M  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    out = {}
    for run in args.runs:
        s = json.load(open(os.path.join(run, "summary.json"), encoding="utf-8"))["results"]
        mat = {sid: M.count_matrix(json.load(open(os.path.join(run, "test", s[f"test/{sid}"]["system"] + ".counts.json"))))
               for sid in ("N3r", "P3r")}
        res = {"pack_alone": {m: s["test/P3r"]["point"][m] for m in ("E_exposure", "DI_E_exposure", "O_overmask")}}
        for m in ("E_exposure", "DI_E_exposure", "O_overmask"):
            res[f"N3r_minus_P3r_{m}"] = M.paired_diff(mat["N3r"], mat["P3r"], m, n=args.boot, seed=0)
        out[os.path.basename(os.path.normpath(run))] = res
        print(run, {k: [round(100 * x, 2) for x in v] if isinstance(v, tuple) else
                    {kk: round(100 * vv, 1) for kk, vv in v.items()} for k, v in res.items()})
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()

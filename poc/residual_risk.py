"""E009: per-note residual risk and a sample of leaked direct identifiers.

python residual_risk.py --data <meddocan root> --results <run_eval out> --split test --out ../docs/RESIDUAL_RISK.md
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deid import metrics as M  # noqa: E402
from deid.data import load_split  # noqa: E402

SYSTEMS = ["S2", "C1", "N3r", "N3", "H4r"]
NAMES = {"S2": "navajo-egp 0.1 + spaCy", "C1": "Presidio (control)", "N3r": "Shield default (health pack)",
         "N3": "Health pack + spaCy", "H4r": "Shield max (pack + Presidio)"}


def read_pred(path: str):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            _, info, _ = line.rstrip("\n").split("\t", 2)
            _, s, e = info.split()
            out.append((int(s), int(e)))
    return out


def ci(flags, n=2000, seed=0):
    a = np.array(flags, dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(a), size=(n, len(a)))
    m = a[idx].mean(axis=1)
    return 100 * a.mean(), 100 * np.percentile(m, 2.5), 100 * np.percentile(m, 97.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--audit", default="N3r")
    ap.add_argument("--title", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    docs = load_split(args.data, args.split)
    summary = json.load(open(os.path.join(args.results, "summary.json"), encoding="utf-8"))["results"]
    rows, leaks = [], []
    for sid in SYSTEMS:
        name = summary[f"{args.split}/{sid}"]["system"]
        any_di, any_name, any_part = [], [], []
        for doc in docs:
            pred = read_pred(os.path.join(args.results, args.split, name, doc.doc_id + ".ann"))
            cov = np.zeros(len(doc.text), dtype=bool)
            for s, e in pred:
                cov[s:e] = True
            full = part = name_full = False
            for lab, s, e in doc.gold:
                if not M.is_direct(lab):
                    continue
                # fully visible: no character of the identifier is masked (E011: an earlier version
                # treated whitespace as masked, so multi-word identifiers never counted as fully visible)
                fully = not cov[s:e].any()
                seen = (~cov[s:e]) & np.array([not c.isspace() for c in doc.text[s:e]])
                if fully:
                    full = True
                    name_full |= lab == "NOMBRE_SUJETO_ASISTENCIA"
                if seen.any():
                    part = True
                    if sid == args.audit:
                        leaks.append((doc.doc_id, lab, doc.text[s:e], fully,
                                      doc.text[max(0, s - 30):s].replace("\n", " ")))
            any_di.append(full)
            any_name.append(name_full)
            any_part.append(part)
        rows.append((sid, ci(any_di), ci(any_name), ci(any_part)))
    md = [f"# Per-note residual risk ({args.split}{args.title}, {len(docs)} notes)", "",
          "| System | Notes with ≥1 direct identifier fully visible | Notes with the patient's name fully visible | Notes with ≥1 direct-identifier character visible |",
          "|---|---|---|---|"]
    f = lambda t: f"{t[0]:.1f} % [{t[1]:.1f}–{t[2]:.1f}]"
    for sid, a, b, c in rows:
        md.append(f"| {NAMES[sid]} | {f(a)} | {f(b)} | {f(c)} |")
    md += ["", "95 % bootstrap intervals over notes (2,000 resamples, seed 0). Direct identifiers as pre-registered "
           "(names, ID numbers, phone, fax, e-mail, street, URL, dates).", ""]
    random.seed(20261028)
    sample = random.sample(leaks, min(30, len(leaks)))
    md += [f"## Audit of 30 leaked direct identifiers ({NAMES[args.audit]}, random sample of {len(leaks)}, seed 20261028)", "",
           "Synthetic data from MEDDOCAN; no real person.", "",
           "| Label | Gold text | Fully visible? | Left context |", "|---|---|---|---|"]
    for doc_id, lab, txt, full, left in sorted(sample, key=lambda x: x[1]):
        md.append(f"| {lab} | `{txt}` | {'yes' if full else 'partly'} | …{left} |")
    by = {}
    for _, lab, _, full, _ in leaks:
        k = by.setdefault(lab, [0, 0])
        k[0] += 1
        k[1] += full
    md += ["", "All leaks by label (count, fully visible):", ""] + \
          [f"- {lab}: {n} ({fv} fully visible)" for lab, (n, fv) in sorted(by.items(), key=lambda kv: -kv[1][0])]
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()

"""Tables, pre-registered hypothesis tests, ablations and figures from a run_eval.py output folder.

python make_report.py --results results/ --out ../docs
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from deid import metrics as M  # noqa: E402

ORDER = ["S0", "S1", "S2", "C1", "N3r", "N3", "H4r", "H4"]
SHORT = {"S0": "Raw note (today)", "S1": "NAVAJO 0.1 regex", "S2": "NAVAJO 0.1 + spaCy",
         "C1": "Presidio (control)", "N3r": "NAVAJO health, no spaCy", "N3": "NAVAJO health",
         "H4r": "Hybrid, no spaCy", "H4": "Hybrid NAVAJO + Presidio"}
# (name, A, B, metric, split): metric(A) - metric(B); below 0 favours A
TESTS = [
    ("H1  NAVAJO 0.1 vs Presidio", "S2", "C1", "E_exposure", "test"),
    ("H2  health pack vs 0.1 (exposure)", "N3", "S2", "E_exposure", "dev"),
    ("H2  health pack vs 0.1 (over-masking)", "N3", "S2", "O_overmask", "dev"),
    ("H3a hybrid vs NAVAJO health", "H4", "N3", "E_exposure", "test"),
    ("H3b hybrid vs Presidio", "H4", "C1", "E_exposure", "test"),
    ("Abl. NAVAJO health vs Presidio", "N3", "C1", "E_exposure", "test"),
    ("Abl. NAVAJO health vs Presidio (direct ids)", "N3", "C1", "DI_E_exposure", "test"),
    ("Abl. hybrid vs Presidio (direct ids)", "H4", "C1", "DI_E_exposure", "test"),
    ("Abl. hybrid over-masking vs Presidio", "H4", "C1", "O_overmask", "test"),
    ("Abl. spaCy inside hybrid", "H4", "H4r", "E_exposure", "test"),
]


def load(results: str):
    s = json.load(open(os.path.join(results, "summary.json"), encoding="utf-8"))
    rows = s["results"]
    mats = {}
    for key, row in rows.items():
        split, sid = key.split("/")
        path = os.path.join(results, split, row["system"] + ".counts.json")
        mats[(split, sid)] = M.count_matrix(json.load(open(path, encoding="utf-8")))
    return s, rows, mats


def pct(x):
    return f"{100 * x:.1f}"


def table(rows, split):
    out = [f"### {split} ({next(r['n_docs'] for k, r in rows.items() if k.startswith(split + '/'))} documents)", "",
           "| System | Leak L (strict) | PHI chars exposed E [95% CI] | Direct ids exposed | Over-masking O | Precision | ms/doc | Round-trip exact |",
           "|---|---|---|---|---|---|---|---|"]
    for sid in ORDER:
        r = rows.get(f"{split}/{sid}")
        if not r:
            continue
        p, ci = r["point"], r["ci95"]["seed0"]
        rt = f"{100 * r['roundtrip_exact']:.1f} %" if "roundtrip_exact" in r else "—"
        out.append(f"| {SHORT[sid]} | {pct(p['L_leak'])} % | {pct(p['E_exposure'])} % [{pct(ci['E_exposure'][0])}–{pct(ci['E_exposure'][1])}] | "
                   f"{pct(p['DI_E_exposure'])} % | {pct(p['O_overmask'])} % | {p['P_strict']:.3f} | {r['ms_per_doc']} | {rt} |")
    return "\n".join(out)


def tests(mats, n):
    out = ["| Comparison | Split | Metric | Difference (points) | 95% CI, seeds 0/1/2 | Reading |", "|---|---|---|---|---|---|"]
    verdicts = {}
    for name, a, b, metric, split in TESTS:
        if (split, a) not in mats or (split, b) not in mats:
            continue
        res = [M.paired_diff(mats[(split, a)], mats[(split, b)], metric, n=n, seed=s) for s in (0, 1, 2)]
        point = res[0][0]
        cis = " / ".join(f"[{100 * lo:+.2f}, {100 * hi:+.2f}]" for _, lo, hi in res)
        below = all(hi < 0 for _, _, hi in res)
        above = all(lo > 0 for _, lo, _ in res)
        reading = "A lower (CI below 0)" if below else "A higher (CI above 0)" if above else "no clear difference"
        verdicts[name] = (point, below, above)
        out.append(f"| {name}: {SHORT[a]} − {SHORT[b]} | {split} | {metric} | {100 * point:+.2f} | {cis} | {reading} |")
    return "\n".join(out), verdicts


def per_label(rows, split, systems=("S1", "S2", "C1", "N3", "H4")):
    labels = list(rows[f"{split}/C1"]["per_label"].keys())
    out = ["| Gold label | n | " + " | ".join(SHORT[s] for s in systems) + " |", "|---|---|" + "---|" * len(systems)]
    for lab in labels:
        n = rows[f"{split}/C1"]["per_label"][lab]["n"]
        cells = []
        for s in systems:
            v = rows[f"{split}/{s}"]["per_label"].get(lab)
            cells.append(f"{100 * v['char_coverage']:.0f} %" if v else "—")
        out.append(f"| {lab}{' *' if M.is_direct(lab) else ''} | {n} | " + " | ".join(cells) + " |")
    out.append("\nCells: share of the label's characters masked. * = direct identifier.")
    return "\n".join(out)


def figures(rows, out_dir, split="test"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, surface = "#21211f", "#6b6a64", "#e6e5e0", "#fcfcfb"
    navajo, control, raw = "#2a78d6", "#eb6834", "#a3a29b"
    role = lambda s: raw if s == "S0" else control if s == "C1" else navajo
    sids = [s for s in ORDER if f"{split}/{s}" in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True, facecolor=surface)
    for ax, metric, title in [(axes[0], "E_exposure", "All PHI characters left visible"),
                              (axes[1], "DI_E_exposure", "Direct-identifier characters left visible")]:
        ax.set_facecolor(surface)
        vals = [rows[f"{split}/{s}"]["point"][metric] * 100 for s in sids]
        ci = [rows[f"{split}/{s}"]["ci95"]["seed0"][metric] for s in sids]
        y = np.arange(len(sids))[::-1]
        ax.barh(y, vals, height=0.62, color=[role(s) for s in sids], edgecolor=surface, linewidth=2)
        ax.errorbar(vals, y, xerr=[[v - 100 * c[0] for v, c in zip(vals, ci)], [100 * c[1] - v for v, c in zip(vals, ci)]],
                    fmt="none", ecolor=ink, elinewidth=1, capsize=3)
        for yi, v in zip(y, vals):
            ax.text(v + 1.5, yi, f"{v:.1f} %", va="center", fontsize=9, color=ink)
        ax.set_yticks(y, [SHORT[s] for s in sids], fontsize=9, color=ink)
        ax.set_xlim(0, 112)
        ax.set_title(title, fontsize=11, color=ink, loc="left")
        ax.set_xlabel("% of gold characters (lower is better)", fontsize=9, color=muted)
        ax.grid(axis="x", color=grid, linewidth=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(grid)
        ax.tick_params(colors=muted, length=0)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=raw, label="No protection"), Patch(color=control, label="Professional control"),
                        Patch(color=navajo, label="NAVAJO-based")], loc="lower center", ncol=3, frameon=False, fontsize=9)
    fig.suptitle(f"MEDDOCAN {split} set: what reaches an external AI model ({rows[f'{split}/S0']['n_docs']} Spanish clinical cases)",
                 fontsize=12, color=ink, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"fig_exposure_{split}.png")
    fig.savefig(path, dpi=160, facecolor=surface)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    s, rows, mats = load(args.results)
    splits = [sp for sp in ("train", "dev", "test") if any(k.startswith(sp + "/") for k in rows)]
    tests_md, verdicts = tests(mats, args.boot)
    md = ["# Results — NAVAJO de-identification PoC on MEDDOCAN", "",
          f"Environment: `{json.dumps(s['env'], ensure_ascii=False)}`", ""]
    for sp in splits:
        md += [table(rows, sp), ""]
    md += ["## Pre-registered tests and ablations (paired document bootstrap)", "", tests_md, ""]
    if "test" in splits and "test/C1" in rows:
        md += ["## Per-label character coverage (test)", "", per_label(rows, "test"), ""]
        md += [f"![exposure](fig_exposure_test.png)", ""]
        figures(rows, args.out, "test")
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    with open(os.path.join(args.out, "verdicts.json"), "w", encoding="utf-8") as fh:
        json.dump(verdicts, fh, indent=1)
    print("\n".join(md[:60]))


if __name__ == "__main__":
    main()

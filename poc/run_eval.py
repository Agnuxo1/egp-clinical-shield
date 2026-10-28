"""Run the pre-registered MEDDOCAN comparison.

python run_eval.py --data <meddocan root> --evaluator <MEDDOCAN-Evaluation-Script> \
    --splits train dev --systems S0 S1 S2 C1 --out results/
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from deid import metrics as M  # noqa: E402
from deid.data import load_split, write_brat  # noqa: E402
from deid import systems as S  # noqa: E402

NAVAJO_BASED = {"S1", "S2", "N3", "N3r", "H4", "H4r"}


def build(names: list[str], health_cycle: str):
    cache: dict[str, object] = {}

    def get(n: str):
        if n in cache:
            return cache[n]
        if n == "S0":
            obj = S.Raw()
        elif n == "S1":
            obj = S.Navajo(use_spacy=False)
        elif n == "S2":
            obj = S.Navajo(use_spacy=True)
        elif n == "C1":
            obj = S.Presidio()
        elif n in ("N3", "N3r"):
            from deid.health import HealthPatterns
            obj = S.Navajo(use_spacy=(n == "N3"), extra=HealthPatterns(health_cycle),
                           name=f"{n}_NAVAJO_HEALTH_{health_cycle}" + ("_NOSPACY" if n == "N3r" else ""))
        elif n == "P3r":
            obj = S.PackOnly(health_cycle)
        elif n == "H4":
            obj = S.Union([get("N3"), get("C1")], name=f"H4_HYBRID_{health_cycle}")
        elif n == "H4r":
            obj = S.Union([get("N3r"), get("C1")], name=f"H4r_HYBRID_{health_cycle}_NOSPACY")
        else:
            raise SystemExit(f"unknown system {n}")
        cache[n] = obj
        return obj

    return [(n, get(n)) for n in names]


def official_spans(evaluator_dir: str, gold_dir: str, sys_dir: str, report_path: str) -> dict:
    """Official MEDDOCAN SPAN subtrack (strict and merged), called as a library."""
    if evaluator_dir not in sys.path:
        sys.path.insert(0, evaluator_dir)
    import evaluate as ev  # noqa: PLC0415
    from classes import BratAnnotation, Span_Evaluation  # noqa: PLC0415

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = ev.evaluate(gold_dir, [sys_dir], BratAnnotation, Span_Evaluation, verbose=False)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    strict, merged = res.evaluations[0], res.evaluations[1]
    return {
        "strict_P": strict.micro_precision(), "strict_R": strict.micro_recall(),
        "merged_P": merged.micro_precision(), "merged_R": merged.micro_recall(),
        "n_docs": len(strict.doc_ids),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--evaluator", required=True)
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--systems", nargs="+", default=["S0", "S1", "S2", "C1"])
    ap.add_argument("--health", default="c1", help="health pattern cycle for N3/H4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    env = {"python": sys.version.split()[0], "platform": platform.platform()}
    for mod in ("numpy", "spacy", "presidio_analyzer", "es_core_news_lg"):
        try:
            m = __import__(mod)
            env[mod] = getattr(m, "__version__", "?")
        except Exception:  # noqa: BLE001
            env[mod] = None

    t0 = time.time()
    systems = build(args.systems, args.health)
    env["build_seconds"] = round(time.time() - t0, 1)
    for n, obj in systems:
        if isinstance(obj, S.Presidio):
            env["presidio_recognizers_es"] = obj.recognizers
            env["presidio_added_for_es"] = obj.added

    summary = {"env": env, "args": vars(args), "results": {}}
    for split in args.splits:
        docs = load_split(args.data, split)
        gold_dir = os.path.join(args.data, split, "brat")
        for n, obj in systems:
            t = time.time()
            preds = {d.doc_id: obj.spans(d.text) for d in docs}
            secs = time.time() - t
            sys_dir = os.path.join(args.out, split, obj.name)
            write_brat(docs, preds, sys_dir)
            per_doc = [M.doc_counts(d.text, d.gold, preds[d.doc_id]) for d in docs]
            mat = M.count_matrix(per_doc)
            point = {k: float(v) for k, v in M.aggregate({k: mat[:, i].sum() for i, k in enumerate(M.COUNT_KEYS)}).items()}
            boots = {f"seed{s}": M.bootstrap(mat, n=args.boot, seed=s) for s in (0, 1, 2)}
            off = official_spans(args.evaluator, gold_dir, sys_dir, os.path.join(args.out, split, obj.name + ".official.txt"))
            row = {
                "system": obj.name, "split": split, "n_docs": len(docs),
                "point": point, "ci95": boots, "official": off,
                "ms_per_doc": round(1000 * secs / len(docs), 2),
                "per_label": M.per_label_recall(docs, preds),
                "totals": {k: int(mat[:, i].sum()) for i, k in enumerate(M.COUNT_KEYS)},
            }
            # consistency: my strict recall must equal the official one
            assert abs(point["R_strict"] - off["strict_R"]) < 1e-9 or n == "S0", (point["R_strict"], off["strict_R"])
            if n in NAVAJO_BASED:
                rt = [S.roundtrip(d.text, preds[d.doc_id], lossless=n not in ("S1", "S2")) for d in docs]
                row["roundtrip_exact"] = sum(r[0] for r in rt) / len(rt)
                row["roundtrip_ws_normalised"] = sum(r[1] for r in rt) / len(rt)
            np_path = os.path.join(args.out, split, obj.name + ".counts.json")
            with open(np_path, "w", encoding="utf-8") as fh:
                json.dump(per_doc, fh)
            summary["results"][f"{split}/{n}"] = row
            print(f"{split:5s} {obj.name:28s} L={point['L_leak']:.3f} E={point['E_exposure']:.3f} "
                  f"O={point['O_overmask']:.3f} P={point['P_strict']:.3f} DI_E={point['DI_E_exposure']:.3f} "
                  f"off_R={off['strict_R']:.3f} {row['ms_per_doc']} ms/doc", flush=True)
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()

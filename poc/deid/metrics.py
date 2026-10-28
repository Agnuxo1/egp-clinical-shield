"""Pre-registered metrics: per-document counts, then aggregates and bootstrap intervals."""

from __future__ import annotations

import numpy as np

DI_PREFIXES = ("NOMBRE_", "ID_", "NUMERO_", "IDENTIF_")
DI_LABELS = {"CORREO_ELECTRONICO", "CALLE", "URL_WEB", "DIREC_PROT_INTERNET", "FECHAS"}

COUNT_KEYS = ["tp", "fn", "fp", "phi_chars", "phi_exposed", "nonphi_chars", "nonphi_masked",
              "di_tp", "di_fn", "di_chars", "di_exposed"]


def is_direct(label: str) -> bool:
    return label.startswith(DI_PREFIXES) or label in DI_LABELS


def doc_counts(text: str, gold, pred) -> dict:
    """gold: [(label, s, e)], pred: [(label, s, e)]. Strict span match as in the official SPAN subtrack."""
    gset = {(s, e) for _, s, e in gold}
    pset = {(s, e) for _, s, e in pred}
    covered = np.zeros(len(text), dtype=bool)
    for _, s, e in pred:
        covered[s:e] = True
    is_phi = np.zeros(len(text), dtype=bool)
    is_di = np.zeros(len(text), dtype=bool)
    for label, s, e in gold:
        is_phi[s:e] = True
        if is_direct(label):
            is_di[s:e] = True
    nonspace = np.array([not c.isspace() for c in text], dtype=bool) if text else np.zeros(0, bool)
    # E and DI_E count every character inside gold spans, as pre-registered (E011: an earlier version
    # skipped whitespace inside spans); O counts non-whitespace non-PHI characters, as pre-registered.
    phi = is_phi
    di = is_di
    nonphi = (~is_phi) & nonspace
    di_gold = {(s, e) for label, s, e in gold if is_direct(label)}
    return {
        "tp": len(gset & pset), "fn": len(gset - pset), "fp": len(pset - gset),
        "phi_chars": int(phi.sum()), "phi_exposed": int((phi & ~covered).sum()),
        "nonphi_chars": int(nonphi.sum()), "nonphi_masked": int((nonphi & covered).sum()),
        "di_tp": len(di_gold & pset), "di_fn": len(di_gold - pset),
        "di_chars": int(di.sum()), "di_exposed": int((di & ~covered).sum()),
    }


def aggregate(c: dict) -> dict:
    """c: summed counts (scalars or arrays over bootstrap replicates)."""
    c = {k: np.asarray(v, dtype=float) for k, v in c.items()}
    d = lambda a, b: np.divide(a, np.maximum(b, 1))
    recall = d(c["tp"], c["tp"] + c["fn"])
    precision = d(c["tp"], c["tp"] + c["fp"])
    pr = precision + recall
    f1 = np.divide(2 * precision * recall, pr, out=np.zeros_like(pr), where=pr > 0)
    return {
        "L_leak": 1 - recall,
        "E_exposure": d(c["phi_exposed"], c["phi_chars"]),
        "O_overmask": d(c["nonphi_masked"], c["nonphi_chars"]),
        "P_strict": precision,
        "R_strict": recall,
        "F1_strict": f1,
        "DI_L_leak": 1 - d(c["di_tp"], c["di_tp"] + c["di_fn"]),
        "DI_E_exposure": d(c["di_exposed"], c["di_chars"]),
    }


def count_matrix(per_doc: list[dict]) -> np.ndarray:
    return np.array([[pd[k] for k in COUNT_KEYS] for pd in per_doc], dtype=float)


def bootstrap(mat: np.ndarray, n: int = 2000, seed: int = 0) -> dict:
    """95 % percentile interval for every metric, resampling documents."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, mat.shape[0], size=(n, mat.shape[0]))
    sums = mat[idx].sum(axis=1)  # (n, k)
    reps = aggregate({k: sums[:, i] for i, k in enumerate(COUNT_KEYS)})
    return {m: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for m, v in reps.items()}


def paired_diff(mat_a: np.ndarray, mat_b: np.ndarray, metric: str, n: int = 2000, seed: int = 0):
    """Point estimate and 95 % interval of metric(A) - metric(B), same resampled documents."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, mat_a.shape[0], size=(n, mat_a.shape[0]))
    agg = lambda m: aggregate({k: m[idx].sum(axis=1)[:, i] for i, k in enumerate(COUNT_KEYS)})[metric]
    diff = agg(mat_a) - agg(mat_b)
    point = (aggregate({k: mat_a[:, i].sum() for i, k in enumerate(COUNT_KEYS)})[metric]
             - aggregate({k: mat_b[:, i].sum() for i, k in enumerate(COUNT_KEYS)})[metric])
    return float(point), float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))


def per_label_recall(docs, preds) -> dict:
    """Strict-span recall and character coverage per gold label."""
    out: dict[str, dict] = {}
    for doc in docs:
        pset = {(s, e) for _, s, e in preds[doc.doc_id]}
        covered = np.zeros(len(doc.text), dtype=bool)
        for _, s, e in preds[doc.doc_id]:
            covered[s:e] = True
        for label, s, e in doc.gold:
            r = out.setdefault(label, {"n": 0, "hit": 0, "chars": 0, "covered": 0})
            r["n"] += 1
            r["hit"] += (s, e) in pset
            r["chars"] += e - s
            r["covered"] += int(covered[s:e].sum())
    for r in out.values():
        r["recall"] = r["hit"] / r["n"]
        r["char_coverage"] = r["covered"] / max(r["chars"], 1)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["n"]))

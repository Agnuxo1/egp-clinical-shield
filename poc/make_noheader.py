"""E008 stress test: copy a MEDDOCAN split without the labelled header block.

The header is the run of lines at the top of a note that are section titles ("Datos del paciente.")
or "Key: value" fields ("NHC: 1234567."). It ends at the first line that is neither; if that line
starts with a label such as "Informe clínico del paciente:", the label is removed and the narrative
kept. Gold spans inside the removed text are dropped; the others are shifted.

python make_noheader.py --data <meddocan root> --split test --out <new root>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deid.data import Doc, load_split  # noqa: E402

TITLE = re.compile(r"(?i)^\s*datos (?:del paciente|asistenciales|cl[íi]nicos)\.?\s*$")
FIELD = re.compile(r"^\s*[^\s:][^:\n]{0,39}:\s*\S.{0,110}$")
LABEL = re.compile(r"^\s*[^\s:][^:\n]{0,39}:\s*")


def strip_header(doc: Doc) -> tuple[Doc, int]:
    pos, removed_lines = 0, 0
    for line in doc.text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if TITLE.match(body) or (FIELD.match(body) and len(body) <= 120):
            pos += len(line)
            removed_lines += 1
            continue
        if removed_lines:
            m = LABEL.match(body)
            if m and len(m.group(0)) <= 45:
                pos += m.end()
        break
    text = doc.text[pos:]
    gold = [(lab, s - pos, e - pos) for lab, s, e in doc.gold if s >= pos]
    for lab, s, e in gold:
        assert text[s:e] == doc.text[s + pos:e + pos]
    return Doc(doc.doc_id, text, gold), removed_lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    folder = os.path.join(args.out, args.split, "brat")
    os.makedirs(folder, exist_ok=True)
    stats = {"docs": 0, "docs_with_header": 0, "header_lines": 0, "gold_before": 0, "gold_after": 0}
    for doc in load_split(args.data, args.split):
        new, n = strip_header(doc)
        stats["docs"] += 1
        stats["docs_with_header"] += n > 0
        stats["header_lines"] += n
        stats["gold_before"] += len(doc.gold)
        stats["gold_after"] += len(new.gold)
        with open(os.path.join(folder, new.doc_id + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(new.text)
        with open(os.path.join(folder, new.doc_id + ".ann"), "w", encoding="utf-8", newline="") as fh:
            for i, (lab, s, e) in enumerate(new.gold, 1):
                fh.write(f"T{i}\t{lab} {s} {e}\t{new.text[s:e]}\n")
    with open(os.path.join(args.out, f"{args.split}_noheader_stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=1)
    print(stats)


if __name__ == "__main__":
    main()

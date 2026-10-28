"""Load MEDDOCAN brat files and write system output in brat format."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Doc:
    doc_id: str
    text: str
    gold: list[tuple[str, int, int]] = field(default_factory=list)  # (label, start, end)


def load_split(root: str, split: str) -> list[Doc]:
    """Read <root>/<split>/brat/*.txt|*.ann. Offsets are checked against the text."""
    folder = os.path.join(root, split, "brat")
    docs = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".txt"):
            continue
        doc_id = name[:-4]
        # newline="" keeps offsets identical to the ones in the .ann files
        with open(os.path.join(folder, name), encoding="utf-8", newline="") as fh:
            text = fh.read()
        gold = []
        ann_path = os.path.join(folder, doc_id + ".ann")
        with open(ann_path, encoding="utf-8", newline="") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line.startswith("T"):
                    continue
                _, info, surface = line.split("\t", 2)
                label, start, end = info.split()
                start, end = int(start), int(end)
                assert text[start:end] == surface, (doc_id, line)
                gold.append((label, start, end))
        docs.append(Doc(doc_id, text, sorted(gold, key=lambda g: (g[1], g[2]))))
    assert docs, f"no documents in {folder}"
    return docs


def write_brat(docs: list[Doc], spans: dict[str, list[tuple[str, int, int]]], out_dir: str) -> None:
    """One .ann (and a copy of the .txt, which the official script reads) per document."""
    os.makedirs(out_dir, exist_ok=True)
    for doc in docs:
        with open(os.path.join(out_dir, doc.doc_id + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(doc.text)
        with open(os.path.join(out_dir, doc.doc_id + ".ann"), "w", encoding="utf-8", newline="") as fh:
            for i, (label, start, end) in enumerate(spans.get(doc.doc_id, []), 1):
                surface = doc.text[start:end].replace("\n", " ")
                fh.write(f"T{i}\t{label} {start} {end}\t{surface}\n")

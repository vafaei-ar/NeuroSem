#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

KEYWORDS = [
    "overt", "covert", "inner", "aloud", "event", "marker", "trigger",
    "up1", "up2", "down1", "down2", "left1", "left2", "right1", "right2",
    "forward1", "forward2", "back1", "back2", "next1", "next2",
]


def collect(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in KEYWORDS):
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            hits.append({
                "line": i + 1,
                "context": "\n".join(f"{j+1}: {lines[j]}" for j in range(start, end)),
            })
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset_root")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    root = Path(args.dataset_root)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    candidates = []
    for name in ["README.md", "readme.md", "data_dictionary.md", "DATA_DICTIONARY.md"]:
        p = root / name
        if p.exists():
            candidates.append(p)

    result = {
        "purpose": "Model-blind documentation probe to resolve Nature event-label condition mapping.",
        "dataset_root": str(root),
        "model_blind": True,
        "neural_model_rsa_computed": False,
        "files": [],
    }
    for p in candidates:
        result["files"].append({
            "path": str(p.relative_to(root)),
            "hits": collect(p),
        })

    out_path = out / "summary.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()

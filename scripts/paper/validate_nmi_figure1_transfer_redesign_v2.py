#!/usr/bin/env python3
"""Validate provenance and displayed values for Figure 1 transfer-first redesign v2."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "nmi_figure1_transfer_redesign_v2" / "latest"
MANIFEST = OUT / "source_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(
            "Figure 1 manifest is missing. Run scripts/paper/build_nmi_figure1_transfer_redesign_v2.py first."
        )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "ok"
    assert manifest["scientific_values_changed"] is False

    for section in ("inputs", "source_data", "outputs"):
        for rel, expected in manifest[section].items():
            path = ROOT / rel
            assert path.exists(), f"Missing {section} file: {rel}"
            observed = sha256(path)
            assert observed == expected, f"SHA256 mismatch for {rel}: {observed} != {expected}"

    builder = ROOT / manifest["builder"]
    assert sha256(builder) == manifest["builder_sha256"], "Builder hash mismatch"

    transfer_path = OUT / "figure1_transfer_source.csv"
    rows = read_csv(transfer_path)
    for dataset, expected_n in (("zuco", 17), ("fmri", 12)):
        subset = [r for r in rows if r["dataset"] == dataset]
        assert len(subset) == expected_n
        a0 = np.asarray([float(r["text_only_residual_rsa"]) for r in subset], float)
        a1 = np.asarray([float(r["neural_guided_residual_rsa"]) for r in subset], float)
        delta = np.asarray([float(r["delta_rsa"]) for r in subset], float)
        assert np.allclose(a1 - a0, delta, atol=5e-12)
        summary = manifest["displayed_summary"][dataset]
        assert int(summary["n"]) == expected_n
        assert int(summary["positive_participants"]) == int(np.sum(delta > 0))
        assert np.isclose(float(summary["mean_delta_rsa"]), float(delta.mean()), atol=5e-12)
        lo, hi = [float(x) for x in summary["bootstrap_95ci"]]
        assert lo <= float(summary["mean_delta_rsa"]) <= hi

    seed_rows = read_csv(OUT / "figure1_seed_source.csv")
    for dataset, expected_n in (("zuco", 17), ("fmri", 12)):
        subset = [r for r in seed_rows if r["dataset"] == dataset]
        assert [r["training_run"] for r in subset] == ["Primary", "29", "30", "31"]
        assert all(int(r["n_participants"]) == expected_n for r in subset)
        assert all(float(r["mean_delta_rsa"]) > 0 for r in subset)
        assert all(0 <= int(r["positive_participants"]) <= expected_n for r in subset)

    result = {
        "status": "ok",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "figure_png_sha256": manifest["outputs"]["outputs/nmi_figure1_transfer_redesign_v2/latest/figure1.png"],
        "checked_inputs": len(manifest["inputs"]),
        "checked_source_tables": len(manifest["source_data"]),
        "checked_outputs": len(manifest["outputs"]),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

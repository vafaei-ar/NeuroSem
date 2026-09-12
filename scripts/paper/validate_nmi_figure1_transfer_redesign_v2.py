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

    for section in ("committed_inputs", "copied_source_data", "outputs"):
        for rel, expected in manifest[section].items():
            path = ROOT / rel
            assert path.exists(), f"Missing {section} file: {rel}"
            observed = sha256(path)
            assert observed == expected, f"SHA256 mismatch for {rel}: {observed} != {expected}"

    builder = ROOT / manifest["builder"]
    assert sha256(builder) == manifest["builder_sha256"], "Builder hash mismatch"

    source_job = manifest["source_runrelay_job"]
    assert source_job["job_id"] == "4N8R2K7C"
    assert source_job["exact_commit"] == "0ff001b37f17d91600035cab6c523676d3823d81"
    assert source_job["status"] == "completed"
    assert len(manifest["source_artifacts"]) == 4
    assert len(manifest["original_upstream_input_hashes"]) == 9

    reliability_rows = read_csv(OUT / "figure1_reliability_source.csv")
    transfer_rows = read_csv(OUT / "figure1_transfer_source.csv")
    seed_rows = read_csv(OUT / "figure1_seed_source.csv")

    for dataset, expected_n in (("zuco", 17), ("fmri", 12)):
        rr = [r for r in reliability_rows if r["dataset"] == dataset]
        tr = [r for r in transfer_rows if r["dataset"] == dataset]
        sr = [r for r in seed_rows if r["dataset"] == dataset]
        assert len(rr) == len(tr) == expected_n
        assert [int(r["participant_index"]) for r in rr] == list(range(1, expected_n + 1))
        assert [int(r["participant_index"]) for r in tr] == list(range(1, expected_n + 1))

        rel = np.asarray([float(r["residual_loo_reliability"]) for r in rr], float)
        a0 = np.asarray([float(r["text_only_residual_rsa"]) for r in tr], float)
        a1 = np.asarray([float(r["neural_guided_residual_rsa"]) for r in tr], float)
        delta = np.asarray([float(r["delta_rsa"]) for r in tr], float)
        assert np.allclose(a1 - a0, delta, atol=5e-12)
        assert np.all(delta > 0)

        summary = manifest["displayed_summary"][dataset]
        assert int(summary["n"]) == expected_n
        assert np.isclose(float(summary["reliability_mean"]), float(rel.mean()), atol=5e-12)
        assert int(summary["primary_positive"]) == int(np.sum(delta > 0)) == expected_n
        assert np.isclose(float(summary["primary_mean_delta"]), float(delta.mean()), atol=5e-12)
        lo, hi = [float(x) for x in summary["primary_bootstrap_95ci"]]
        assert lo <= float(summary["primary_mean_delta"]) <= hi

        assert [r["training_run"] for r in sr] == ["Primary", "29", "30", "31"]
        assert all(int(r["n_participants"]) == expected_n for r in sr)
        means = np.asarray([float(r["mean_delta_rsa"]) for r in sr], float)
        counts = [int(r["positive_participants"]) for r in sr]
        assert np.all(means > 0)
        assert np.allclose(means, np.asarray(summary["four_run_means"], float), atol=5e-12)
        assert counts == [int(x) for x in summary["four_run_positive_counts"]]
        assert sr[0]["evidence_status"] == "prospective primary"
        assert all(r["evidence_status"] == "post-confirmatory optimization robustness" for r in sr[1:])

    result = {
        "status": "ok",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "source_runrelay_job": source_job["job_id"],
        "figure_png_sha256": manifest["outputs"]["outputs/nmi_figure1_transfer_redesign_v2/latest/figure1.png"],
        "checked_committed_inputs": len(manifest["committed_inputs"]),
        "checked_source_artifacts": len(manifest["source_artifacts"]),
        "checked_upstream_hashes": len(manifest["original_upstream_input_hashes"]),
        "checked_outputs": len(manifest["outputs"]),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

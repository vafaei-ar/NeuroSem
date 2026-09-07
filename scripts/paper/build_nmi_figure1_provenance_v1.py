#!/usr/bin/env python3
"""Rebuild NeuroSem Figure 1 from traceable derived artifacts only.

Presentation-only. This wrapper performs no model fitting, representation selection,
hypothesis testing, or neural analysis. It binds the historical development summary,
the S0YJMCMF reliability replay, and the two frozen C-MTEB STS summaries to the Figure 1
builder, then records exact SHA256 provenance for every scientific input and output.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest"
BUILDER = ROOT / "scripts/paper/nmi_visualizations_v4/build_figure1_chineseeeg.py"
DEV = ROOT / "paper/figure_data/chineseeeg_development_v1.json"
RELIABILITY = ROOT / "outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/summary.json"
STS1 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1/20260823_122332/summary.json"
STS2 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1_seed2/20260823_123910/summary.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    required = [BUILDER, DEV, RELIABILITY, STS1, STS2]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing Figure 1 provenance inputs: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    out_prefix = OUT / "figure1"
    cmd = [
        str(ROOT / ".venv/bin/python"),
        str(BUILDER),
        "--development-json", str(DEV),
        "--reliability-summary", str(RELIABILITY),
        "--sts-seed1-summary", str(STS1),
        "--sts-seed2-summary", str(STS2),
        "--out-prefix", str(out_prefix),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    builder_payload = json.loads(proc.stdout)

    outputs = [OUT / "figure1.pdf", OUT / "figure1.svg", OUT / "figure1.png"]
    missing_outputs = [str(p) for p in outputs if not p.exists()]
    if missing_outputs:
        raise RuntimeError("Figure builder did not create expected outputs: " + ", ".join(missing_outputs))

    rel = read_json(RELIABILITY)
    sts_payloads = [read_json(STS1), read_json(STS2)]
    arm_map = {
        "Base": "base",
        "Text-only": "text_only",
        "Neural-guided": "neural",
        "Shuffled-neural": "shuffled_neural",
    }
    semantic = {
        display: [float(payload["results"][key]["mean_spearman"]) for payload in sts_payloads]
        for display, key in arm_map.items()
    }
    task_scores = {
        f"seed_{idx + 1}": {
            display: sts_payloads[idx]["results"][key]["task_scores"]
            for display, key in arm_map.items()
        }
        for idx in range(2)
    }

    manifest = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "presentation-only provenance-linked Figure 1 rebuild",
        "scientific_inputs": [
            {"role": "development_summary", "path": str(DEV.relative_to(ROOT)), "sha256": sha256(DEV)},
            {"role": "reliability_replay", "path": str(RELIABILITY.relative_to(ROOT)), "sha256": sha256(RELIABILITY), "job_id": "S0YJMCMF"},
            {"role": "sts_seed_1", "path": str(STS1.relative_to(ROOT)), "sha256": sha256(STS1)},
            {"role": "sts_seed_2", "path": str(STS2.relative_to(ROOT)), "sha256": sha256(STS2)},
        ],
        "builder": {"path": str(BUILDER.relative_to(ROOT)), "sha256": sha256(BUILDER)},
        "displayed_values": {
            "reliability": {
                "raw_loo": float(rel["raw_loo_mean"]),
                "residual_loo": float(rel["residual_loo_mean"]),
                "n_subjects": int(rel["n_subjects"]),
                "n_rows": int(rel["n_rows"]),
                "n_channels": int(rel["n_channels"]),
            },
            "semantic_mean_spearman": semantic,
            "semantic_task_scores": task_scores,
        },
        "builder_stdout": builder_payload,
        "outputs": [
            {"path": str(p.relative_to(ROOT)), "sha256": sha256(p), "size_bytes": p.stat().st_size}
            for p in outputs
        ],
        "guardrails": {
            "model_training_performed": False,
            "neural_analysis_performed": False,
            "representation_selection_performed": False,
            "semantic_values_hardcoded_in_non_demo_path": False,
            "reliability_values_hardcoded_in_non_demo_path": False,
        },
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "NeuroSem v1.18 Figure 1 provenance rebuild\n\n"
        f"Reliability replay: raw LOO {rel['raw_loo_mean']:.9f}; residual LOO {rel['residual_loo_mean']:.9f}\n"
        "STS panel: loaded from two frozen task-level C-MTEB summaries; no scientific values are hard-coded in the non-demo figure path.\n"
        "Terminology: reserved development test; fixed external transfer.\n"
        "Exact source and output hashes are recorded in source_manifest.json.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

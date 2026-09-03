#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "manuscript_reporting_values_v1" / "latest"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mean_col(rows: list[dict], name: str) -> float:
    return float(np.mean([float(r[name]) for r in rows]))


def primary_zuco() -> dict:
    root = ROOT / "outputs" / "zuco2_nr_e5_transfer_v1" / "latest"
    rows = read_csv(root / "subject_results.csv")
    a0 = mean_col(rows, "lambda_0_resid_rsa")
    a1 = mean_col(rows, "lambda_0p10_resid_rsa")
    delta = mean_col(rows, "delta_0p10_minus_0")
    return {
        "source": str((root / "subject_results.csv").relative_to(ROOT)),
        "n_participants": len(rows),
        "lambda_0_mean_rsa": a0,
        "lambda_0p10_mean_rsa": a1,
        "mean_delta": delta,
        "relative_delta_percent_of_text_only_mean": (100.0 * delta / a0) if a0 != 0 else None,
    }


def primary_fmri() -> dict:
    candidates = [
        ROOT / "outputs" / "smn4lang_fmri_e5_transfer_v1" / "latest" / "participant_results.csv",
        ROOT / "outputs" / "smn4lang_fmri_e5_transfer" / "latest" / "participant_results.csv",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        return {"available": False}
    rows = read_csv(p)
    keys = set(rows[0])
    a0_key = next(k for k in ["lambda_0_resid_rsa", "text_only_resid_rsa", "lambda_0_rsa"] if k in keys)
    a1_key = next(k for k in ["lambda_0p10_resid_rsa", "neural_guided_resid_rsa", "lambda_0p10_rsa"] if k in keys)
    delta_key = next(k for k in ["delta_0p10_minus_0", "delta_rsa", "delta"] if k in keys)
    a0, a1, delta = mean_col(rows, a0_key), mean_col(rows, a1_key), mean_col(rows, delta_key)
    return {
        "available": True,
        "source": str(p.relative_to(ROOT)),
        "n_participants": len(rows),
        "lambda_0_mean_rsa": a0,
        "lambda_0p10_mean_rsa": a1,
        "mean_delta": delta,
        "relative_delta_percent_of_text_only_mean": (100.0 * delta / a0) if a0 != 0 else None,
    }


def specificity_forward_seed_means() -> dict:
    p = ROOT / "outputs" / "nmi_reviewer_response_consolidated_v1" / "latest" / "summary.json"
    s = json.loads(p.read_text(encoding="utf-8"))
    seed_results = s["specificity_control"]["seed_results"]
    out = {}
    for dataset in ["zuco", "smn4lang_fmri"]:
        vals = []
        for rec in seed_results:
            t = rec["targets"][dataset]
            genuine_text = float(t["genuine_minus_shuffled"]["mean_delta"]) + float(t["shuffled_minus_text"]["mean_delta"])
            vals.append({"seed": int(rec["seed"]), "genuine_minus_text_mean_delta": genuine_text})
        out[dataset] = {
            "seed_values": vals,
            "mean_of_seed_means": float(np.mean([v["genuine_minus_text_mean_delta"] for v in vals])),
            "n_seed_means_positive": int(sum(v["genuine_minus_text_mean_delta"] > 0 for v in vals)),
        }
    return {"source": str(p.relative_to(ROOT)), "targets": out}


def reverse_lambda001_multiseed() -> dict:
    p = ROOT / "outputs" / "nmi_fmri_to_zuco_lambda001_multiseed_v1" / "latest" / "summary.json"
    s = json.loads(p.read_text(encoding="utf-8"))
    return {
        "source": str(p.relative_to(ROOT)),
        "new_seeds": s.get("new_seeds"),
        "seed_results": s.get("seed_results"),
        "aggregate": s.get("aggregate"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "presentation-only export of already-completed aggregate values for manuscript reporting",
        "primary_zuco": primary_zuco(),
        "primary_fmri": primary_fmri(),
        "forward_multiseed": specificity_forward_seed_means(),
        "reverse_lambda001_multiseed": reverse_lambda001_multiseed(),
        "guardrails": {
            "new_model_training": False,
            "new_model_evaluation": False,
            "new_neural_analysis": False,
            "new_hypothesis_test": False,
            "descriptive_aggregation_only": True,
        },
    }
    (OUT / "reporting_values.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    z = payload["primary_zuco"]
    lines = [
        "NeuroSem manuscript reporting values",
        "Status: ok",
        f"ZuCo text-only mean RSA: {z['lambda_0_mean_rsa']:.10f}",
        f"ZuCo neural-guided mean RSA: {z['lambda_0p10_mean_rsa']:.10f}",
        f"ZuCo mean delta: {z['mean_delta']:.10f}",
        f"ZuCo relative delta (% text-only mean): {z['relative_delta_percent_of_text_only_mean']:.6f}",
        "New analyses performed: 0",
    ]
    (OUT / "reporting_values.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

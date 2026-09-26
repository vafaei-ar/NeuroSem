#!/usr/bin/env python3
"""Read-only preflight for the NeuroSem target-compatibility project.

This script reads only already-completed outputs and filesystem metadata. It does not
load raw neural arrays, model weights, embeddings, or compute any new transfer,
compatibility, or mechanistic outcome.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "target_compatibility_preflight_v1" / "latest"

TARGETS = {
    "zuco": {
        "reliability": "outputs/zuco2_nr_primary_representation_reliability/latest/summary.json",
        "transfer": "outputs/zuco2_nr_e5_transfer_v1/latest/summary.json",
        "expected_role": "positive",
    },
    "smn4lang_fmri": {
        "reliability": "outputs/smn4lang_fmri_reliability/latest/summary.json",
        "transfer": "outputs/smn4lang_fmri_e5_transfer_v1/latest/summary.json",
        "expected_role": "positive",
    },
    "derco": {
        "reliability": "outputs/derco_eeg_reliability/latest/summary.json",
        "transfer": "outputs/derco_e5_transfer_v1/latest/summary.json",
        "expected_role": "negative",
    },
    "tmnred": {
        "reliability": "outputs/tmnred_primary_representation_reliability/latest/summary.json",
        "transfer": "outputs/tmnred_e5_transfer_v1/latest/summary.json",
        "expected_role": "null_or_inconclusive",
    },
    "garnett_dream": {
        "reliability": "outputs/garnett_dream_primary_reliability/latest/summary.json",
        "transfer": "outputs/garnett_dream_e5_transfer_v1/latest/summary.json",
        "expected_role": "null_or_inconclusive",
    },
    "nature_directional": {
        "reliability": None,
        "transfer": "outputs/nature_directional_neurosem_v1/latest/summary.json",
        "expected_role": "diagnostic_reliability_only",
    },
    "smn4lang_meg": {
        "reliability": "outputs/smn4lang_meg_primary_reliability/latest/summary.json",
        "transfer": None,
        "expected_role": "reliability_failure",
    },
}

DOSE_ADAPTERS = {
    "0.00": "outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter",
    "0.01": "outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural/20260823_192219/adapter",
    "0.03": "outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural/20260823_192323/adapter",
    "0.10": "outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/20260823_192425/adapter",
    "0.30": "outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural/20260823_192528/adapter",
    "1.00": "outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter",
}

LOCAL_TARGET_DIRS = {
    "derco_outputs": "outputs/derco_e5_transfer_v1",
    "derco_data": "data/raw/derco",
    "tmnred_outputs": "outputs/tmnred_e5_transfer_v1",
    "garnett_outputs": "outputs/garnett_dream_e5_transfer_v1",
    "nature_outputs": "outputs/nature_directional_neurosem_v1",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                rows.append((p, v))
            rows.extend(flatten(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{prefix}[{i}]"
            if isinstance(v, (str, int, float, bool)) or v is None:
                rows.append((p, v))
            rows.extend(flatten(v, p))
    return rows


def selected_fields(obj: Any) -> dict[str, Any]:
    keys = (
        "gate", "reliab", "mean_delta", "primary_mean_delta", "median_delta",
        "fraction", "positive", "bootstrap", "signflip", "p_one", "p_two",
        "primary_result", "primary_contrast", "analysis_status", "analysis_stage",
        "n_subject", "n_participant", "contrast",
    )
    out = {}
    for path, value in flatten(obj):
        low = path.lower()
        if any(k in low for k in keys):
            out[path] = value
    return out


def list_files(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    if path.is_file():
        return [{"relative_path": str(path.relative_to(ROOT)), "size_bytes": path.stat().st_size}]
    for p in sorted(path.rglob("*")):
        if p.is_file():
            rows.append({"relative_path": str(p.relative_to(ROOT)), "size_bytes": p.stat().st_size})
    return rows[:500]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    target_rows = []
    payloads = {}
    missing_required = []

    for key, spec in TARGETS.items():
        row = {"target": key, "expected_role_from_existing_results": spec["expected_role"]}
        for kind in ("reliability", "transfer"):
            rel = spec[kind]
            if rel is None:
                row[f"{kind}_path"] = None
                row[f"{kind}_exists"] = False
                continue
            p = ROOT / rel
            row[f"{kind}_path"] = rel
            row[f"{kind}_exists"] = p.is_file()
            if p.is_file():
                row[f"{kind}_sha256"] = sha256(p)
                obj = read_json(p)
                payloads[f"{key}:{kind}"] = obj
                row[f"{kind}_selected_fields"] = selected_fields(obj)
            else:
                row[f"{kind}_sha256"] = None
                if key in {"zuco", "smn4lang_fmri", "derco", "tmnred", "garnett_dream"}:
                    missing_required.append(rel)
        target_rows.append(row)

    adapter_rows = []
    for lam, rel in DOSE_ADAPTERS.items():
        p = ROOT / rel
        files = sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else []
        adapter_rows.append({
            "lambda": lam,
            "relative_path": rel,
            "exists": p.is_dir(),
            "n_files": len(files),
        })
        if not p.is_dir():
            missing_required.append(rel)

    inventories = {name: list_files(ROOT / rel) for name, rel in LOCAL_TARGET_DIRS.items()}

    with (OUT / "target_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["target", "expected_role_from_existing_results", "reliability_path", "reliability_exists",
                  "reliability_sha256", "transfer_path", "transfer_exists", "transfer_sha256"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in target_rows:
            w.writerow({k: r.get(k) for k in fields})

    with (OUT / "dose_adapter_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lambda", "relative_path", "exists", "n_files"])
        w.writeheader(); w.writerows(adapter_rows)

    summary = {
        "schema_version": 1,
        "status": "ok" if not missing_required else "incomplete",
        "analysis_stage": "read-only preflight before target-compatibility protocol freeze",
        "new_scientific_outcomes_computed": False,
        "raw_neural_arrays_loaded": False,
        "model_weights_loaded": False,
        "target_rows": target_rows,
        "dose_adapters": adapter_rows,
        "filesystem_inventories": inventories,
        "missing_required": sorted(set(missing_required)),
        "guardrails": [
            "Only already-completed result JSON and filesystem metadata are read.",
            "No target classification is changed from new mechanism outcomes.",
            "No model or neural arrays are loaded.",
            "No dose, gradient, fingerprint, Gromov-Wasserstein, or alternative-metric analysis is computed.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "existing_target_payloads.json").write_text(json.dumps(payloads, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "filesystem_inventory.json").write_text(json.dumps(inventories, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "NeuroSem target-compatibility preflight\n\n"
        f"Status: {summary['status']}\n"
        f"Missing required: {summary['missing_required']}\n"
        "No new scientific outcome was computed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": summary["status"], "missing_required": summary["missing_required"], "out": str(OUT)}, indent=2))
    return 0 if not missing_required else 2


if __name__ == "__main__":
    raise SystemExit(main())

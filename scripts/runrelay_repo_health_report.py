#!/usr/bin/env python3
"""Create a small safe derived health report from the public NeuroSem RunRelay config."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".runrelay" / "project.yaml"
AGENTS = ROOT / "AGENTS.md"
OUTPUT_DIR = ROOT / "outputs" / "runrelay_repo_health" / "latest"

REPORTING_INPUTS = [
    "outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv",
    "outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv",
    "outputs/smn4lang_fmri_e5_transfer/latest/participant_results.csv",
    "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json",
    "outputs/nmi_reviewer_response_scientific_v1/latest/summary.json",
    "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json",
]
for seed in [20260829, 20260830, 20260831]:
    for dataset, csv_name in [("zuco", "subject_results.csv"), ("smn4lang_fmri", "participant_results.csv")]:
        for comparison in ["shuffled_minus_text", "genuine_minus_shuffled"]:
            REPORTING_INPUTS.append(
                f"outputs/nmi_reviewer_response_scientific_v1/latest/seed_{seed}/{dataset}/{comparison}/{csv_name}"
            )

FORWARD_GRID = [0.00, 0.01, 0.03, 0.10, 0.30, 1.00]
FORWARD_LABELS = {
    0.00: "lambda_0",
    0.01: "lambda_0p01",
    0.03: "lambda_0p03",
    0.10: "lambda_0p10",
    0.30: "lambda_0p30",
    1.00: "lambda_1",
}

PRIMARY_PIPELINE_BLOBS = {
    "scripts/tuning/evaluate_zuco2_nr_e5_transfer_v1.py": {
        "expected_git_blob_sha1": "df140f62119a918a7f98351289ff5d8c4a39b3e0",
        "executed_commit": "edc52b1fc0621f3466bc48852317dfb658775fb0",
        "role": "ZuCo primary evaluator",
    },
    "scripts/analysis/run_zuco2_nr_primary_representation_reliability.py": {
        "expected_git_blob_sha1": "66f514a71521475b0ea506e9bab691ad2a0dde1e",
        "executed_commit": "edc52b1fc0621f3466bc48852317dfb658775fb0",
        "role": "ZuCo frozen representation/reliability helper",
    },
    "scripts/tuning/evaluate_tmnred_e5_transfer_v1.py": {
        "expected_git_blob_sha1": "5446c969b99b590f7011ed7bbe8de66332e62ef4",
        "executed_commit": "edc52b1fc0621f3466bc48852317dfb658775fb0",
        "role": "shared frozen E5 adapter/encoding helper",
    },
    "scripts/tuning/evaluate_smn4lang_fmri_e5_transfer_v1.py": {
        "expected_git_blob_sha1": "4d34c92425b1e6a0f4ce637c89de22957b07d11e",
        "executed_commit": "abfbac4d54269d96c52ac0cd61776cc2a0c2f892",
        "role": "SMN4Lang fMRI primary evaluator",
    },
    "scripts/analysis/run_smn4lang_fmri_reliability.py": {
        "expected_git_blob_sha1": "429bdbcd45511f8819b0f0842ca826664743d3ee",
        "executed_commit": "abfbac4d54269d96c52ac0cd61776cc2a0c2f892",
        "role": "SMN4Lang frozen representation/reliability helper",
    },
}


def inspect_reporting_input(rel: str) -> dict:
    p = ROOT / rel
    item = {"path": rel, "exists": p.exists(), "is_file": p.is_file()}
    if not p.is_file():
        return item
    item["size_bytes"] = p.stat().st_size
    if p.suffix.lower() == ".csv":
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                item["header"] = next(reader, [])
                item["n_rows"] = sum(1 for _ in reader)
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    elif p.suffix.lower() == ".json":
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            item["top_level_keys"] = sorted(obj.keys()) if isinstance(obj, dict) else []
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    return item


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path.resolve())


def latest_training_summary(root: Path) -> Path | None:
    candidates = sorted(root.glob("*/summary.json")) if root.exists() else []
    return candidates[-1] if candidates else None


def non_outcome_training_metadata(summary_path: Path | None) -> dict:
    if summary_path is None or not summary_path.is_file():
        return {}
    try:
        obj = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"read_error": type(e).__name__ + ": " + str(e)}
    out = {}
    for key in ["model_id", "model_revision", "arm", "seed", "neural_loss_weight"]:
        if key in obj and not isinstance(obj[key], (dict, list)):
            out[key] = obj[key]
    cfg = obj.get("config")
    if isinstance(cfg, dict):
        allowed = [
            "model_id", "model_revision", "arm", "seed", "neural_loss_weight",
            "epochs", "batch_size", "learning_rate", "weight_decay",
        ]
        out["config"] = {k: cfg[k] for k in allowed if k in cfg}
    return out


def forward_dose_preflight() -> dict:
    arms = []
    for lam in FORWARD_GRID:
        label = FORWARD_LABELS[lam]
        if lam == 0.0:
            summary = ROOT / "outputs/e5_neural_tuning_v1/text_only/20260823_181507/summary.json"
            adapter = ROOT / "outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter"
            provenance = "frozen original E5 text-only anchor"
        elif lam == 1.0:
            summary = ROOT / "outputs/e5_neural_tuning_v1/neural/20260823_181609/summary.json"
            adapter = ROOT / "outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter"
            provenance = "frozen original E5 genuine-neural anchor; reused by Pareto grid"
        else:
            training_root = ROOT / f"outputs/e5_neural_tuning_pareto_v1/{label}/neural"
            summary = latest_training_summary(training_root)
            adapter = summary.parent / "adapter" if summary is not None else training_root / "MISSING_ADAPTER"
            provenance = "Pareto-grid intermediate dose trained under frozen exploratory protocol"
        arms.append({
            "lambda": lam,
            "label": label,
            "provenance_class": provenance,
            "summary_path": relpath(summary) if summary is not None else None,
            "summary_exists": bool(summary is not None and summary.is_file()),
            "adapter_path": relpath(adapter),
            "adapter_exists": adapter.is_dir(),
            "training_metadata": non_outcome_training_metadata(summary),
        })

    pareto_summary = ROOT / "outputs/e5_pareto_v1/latest/combined_summary.json"
    pareto_csv = ROOT / "outputs/e5_pareto_v1/latest/pareto_points.csv"
    pareto_structure = {
        "summary_path": relpath(pareto_summary),
        "summary_exists": pareto_summary.is_file(),
        "csv_path": relpath(pareto_csv),
        "csv_exists": pareto_csv.is_file(),
    }
    if pareto_summary.is_file():
        try:
            obj = json.loads(pareto_summary.read_text(encoding="utf-8"))
            points = obj.get("points") if isinstance(obj, dict) else None
            points = points if isinstance(points, list) else []
            observed_lambdas = [float(p.get("lambda")) for p in points if isinstance(p, dict) and p.get("lambda") is not None]
            pareto_structure.update({
                "top_level_keys": sorted(obj.keys()) if isinstance(obj, dict) else [],
                "grid_declared": obj.get("grid") if isinstance(obj, dict) else None,
                "n_points": len(points),
                "observed_lambdas": observed_lambdas,
                "all_points_have_external_sts_mean": all(isinstance(p, dict) and "external_sts_mean" in p for p in points),
                "all_points_have_external_sts_task_scores": all(isinstance(p, dict) and "external_sts_task_scores" in p for p in points),
                "all_points_have_run07_neural_rsa_mean": all(isinstance(p, dict) and "run07_neural_rsa_mean" in p for p in points),
                "anchor_policy": obj.get("anchor_policy") if isinstance(obj, dict) else None,
                "run07_reuse_warning": obj.get("run07_reuse_warning") if isinstance(obj, dict) else None,
                "external_sts_reuse_warning": obj.get("external_sts_reuse_warning") if isinstance(obj, dict) else None,
                "sts_task_names": sorted((obj.get("dataset_provenance") or {}).keys()) if isinstance(obj, dict) else [],
            })
        except Exception as e:
            pareto_structure["read_error"] = type(e).__name__ + ": " + str(e)
    if pareto_csv.is_file():
        try:
            with pareto_csv.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                pareto_structure["csv_header"] = next(reader, [])
                pareto_structure["csv_n_rows"] = sum(1 for _ in reader)
        except Exception as e:
            pareto_structure["csv_read_error"] = type(e).__name__ + ": " + str(e)

    pipeline_hashes = []
    for rel, spec in PRIMARY_PIPELINE_BLOBS.items():
        p = ROOT / rel
        actual = git_blob_sha1(p) if p.is_file() else None
        pipeline_hashes.append({
            "path": rel,
            "role": spec["role"],
            "executed_primary_commit": spec["executed_commit"],
            "expected_git_blob_sha1": spec["expected_git_blob_sha1"],
            "actual_git_blob_sha1": actual,
            "matches_executed_primary_code": actual == spec["expected_git_blob_sha1"],
        })

    frozen_input_paths = [
        "outputs/zuco2_nr_input_materialization/latest/summary.json",
        "outputs/zuco2_nr_format_probe/latest/summary.json",
        "outputs/zuco2_nr_primary_representation_reliability/latest/summary.json",
        "outputs/smn4lang_fmri_reliability/latest/summary.json",
    ]
    input_presence = [{"path": rel, "exists": (ROOT / rel).is_file()} for rel in frozen_input_paths]

    all_arms_present = all(a["summary_exists"] and a["adapter_exists"] for a in arms)
    pareto_grid_complete = (
        pareto_structure.get("observed_lambdas") == FORWARD_GRID
        and pareto_structure.get("n_points") == len(FORWARD_GRID)
    )
    sts_grid_complete = bool(
        pareto_grid_complete
        and pareto_structure.get("all_points_have_external_sts_mean")
        and pareto_structure.get("all_points_have_external_sts_task_scores")
    )
    pipeline_invariant = all(x["matches_executed_primary_code"] for x in pipeline_hashes)
    frozen_inputs_present = all(x["exists"] for x in input_presence)

    return {
        "scope": "pre-outcome structural audit only; no external dose outcomes are reported",
        "prespecified_forward_grid": FORWARD_GRID,
        "arms": arms,
        "existing_pareto_output_structure": pareto_structure,
        "primary_pipeline_code_invariance": pipeline_hashes,
        "frozen_primary_input_presence": input_presence,
        "all_six_training_arms_present": all_arms_present,
        "existing_pareto_grid_complete": pareto_grid_complete,
        "matched_sts_measurements_exist_for_all_six_doses": sts_grid_complete,
        "primary_evaluation_code_matches_executed_commits": pipeline_invariant,
        "frozen_primary_inputs_present": frozen_inputs_present,
        "ready_to_freeze_forward_external_dose_characterization": bool(
            all_arms_present and sts_grid_complete and pipeline_invariant and frozen_inputs_present
        ),
    }


def main() -> None:
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    agents_text = AGENTS.read_text(encoding="utf-8")

    task_names = re.findall(r"^  ([A-Za-z0-9_]+):\s*$", manifest_text, flags=re.MULTILINE)
    machine_match = re.search(r"^  machine_id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    project_match = re.search(r"^  id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    script_paths = sorted(set(re.findall(r"^\s+-\s+(scripts/[A-Za-z0-9_./-]+\.py)\s*$", manifest_text, flags=re.MULTILINE)))

    script_checks = [
        {"path": rel, "exists": (ROOT / rel).is_file()}
        for rel in script_paths
    ]
    missing_scripts = [item["path"] for item in script_checks if not item["exists"]]
    dose_preflight = forward_dose_preflight()

    payload = {
        "schema_version": 1,
        "report": "neurosem_runrelay_repo_health",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": project_match.group(1) if project_match else None,
        "machine_id": machine_match.group(1) if machine_match else None,
        "task_count": len(task_names),
        "tasks": task_names,
        "referenced_python_script_count": len(script_checks),
        "missing_referenced_scripts": missing_scripts,
        "agents_declares_runrelay": "RunRelay" in agents_text,
        "reporting_input_diagnostic": {
            "scope": "existence, CSV headers/row counts, and JSON top-level keys only; no outcome values",
            "items": [inspect_reporting_input(rel) for rel in REPORTING_INPUTS],
        },
        "forward_dose_asset_preflight": dose_preflight,
        "status": "ok" if not missing_scripts and task_names and dose_preflight["ready_to_freeze_forward_external_dose_characterization"] else "attention",
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "health.txt").write_text(
        "\n".join(
            [
                "NeuroSem RunRelay repository health report",
                f"Status: {payload['status']}",
                f"Project: {payload['project_id']}",
                f"Machine: {payload['machine_id']}",
                f"Registered tasks: {payload['task_count']}",
                f"Referenced Python scripts checked: {payload['referenced_python_script_count']}",
                f"Missing referenced scripts: {len(missing_scripts)}",
                "Reporting input diagnostic: included in health.json",
                f"Forward dose arms present: {dose_preflight['all_six_training_arms_present']}",
                f"Matched STS grid present: {dose_preflight['matched_sts_measurements_exist_for_all_six_doses']}",
                f"Primary evaluation code invariant: {dose_preflight['primary_evaluation_code_matches_executed_commits']}",
                f"Forward dose preflight ready: {dose_preflight['ready_to_freeze_forward_external_dose_characterization']}",
                "Forward dose outcome values reported: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "manuscript_reporting_input_diagnostic_v1" / "latest"

PATHS = [
    "outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv",
    "outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv",
    "outputs/smn4lang_fmri_e5_transfer/latest/participant_results.csv",
    "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json",
    "outputs/nmi_reviewer_response_scientific_v1/latest/summary.json",
    "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json",
]

SEEDS = [20260829, 20260830, 20260831]
for seed in SEEDS:
    for dataset, csv_name in [("zuco", "subject_results.csv"), ("smn4lang_fmri", "participant_results.csv")]:
        for comparison in ["shuffled_minus_text", "genuine_minus_shuffled"]:
            PATHS.append(
                f"outputs/nmi_reviewer_response_scientific_v1/latest/seed_{seed}/{dataset}/{comparison}/{csv_name}"
            )


def inspect(rel: str) -> dict:
    p = ROOT / rel
    item = {"path": rel, "exists": p.exists(), "is_file": p.is_file()}
    if not p.is_file():
        return item
    item["size_bytes"] = p.stat().st_size
    if p.suffix.lower() == ".csv":
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                n_rows = sum(1 for _ in reader)
            item["header"] = header
            item["n_rows"] = n_rows
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    elif p.suffix.lower() == ".json":
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            item["top_level_keys"] = sorted(obj.keys()) if isinstance(obj, dict) else []
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    return item


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "model-blind diagnostic of manuscript reporting input availability and schemas",
        "items": [inspect(p) for p in PATHS],
        "guardrails": {
            "no_outcome_values_read_from_csv_rows": True,
            "csv_headers_and_row_counts_only": True,
            "json_top_level_keys_only": True,
            "no_model_training": True,
            "no_model_evaluation": True,
            "no_hypothesis_testing": True,
        },
    }
    out = OUT / "diagnostic.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "items": len(payload["items"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconcile key NMI v1.16 provenance disputes without new scientific analysis.

Read-only audit of already-completed derived outputs plus historical committed code.
No model training, model evaluation, neural analysis, hypothesis testing, or manuscript editing.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "nmi_v116_reconciliation_v1" / "latest"

DERCO_REL = ROOT / "outputs/derco_eeg_reliability/latest/summary.json"
DERCO_TRANSFER = ROOT / "outputs/derco_e5_transfer_v1/latest/summary.json"
MULTISEED = ROOT / "outputs/nmi_multiseed_e5_v1/latest/summary.json"
ZUCO_PRIMARY = ROOT / "outputs/zuco2_nr_e5_transfer_v1/latest/summary.json"
FMRI_PRIMARY = ROOT / "outputs/smn4lang_fmri_e5_transfer_v1/latest/summary.json"
MBERT_OLD = ROOT / "outputs/nmi_model_family_mbert_v1/latest/summary.json"
PANEL = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/summary.json"
PANEL_ROWS = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
PANEL_MODELS = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/resolved_models.json"
ZUCO_INPUT = ROOT / "outputs/zuco2_nr_input_materialization/latest/summary.json"

OLD_COMMIT = "ed9a2d089e3be028515cf16247cc0a5b1ccdff9a"
PANEL_COMMIT = "3aa4a6259f97fe72b3ae85f6c6c91c53a7eae219"
OLD_CONFIG_PATH = "configs/mbert_model_family_robustness_v1.json"
OLD_TRAIN_PATH = "scripts/tuning/train_bert_neurosem_lora.py"
PANEL_SCRIPT_PATH = "scripts/robustness/run_nmi_bidirectional_model_family_panel_v1.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(commit: str, path: str) -> str:
    cp = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return cp.stdout


def flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            rows.append((p, v))
            rows.extend(flatten(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{prefix}[{i}]"
            rows.append((p, v))
            rows.extend(flatten(v, p))
    return rows


def find_values(obj: Any, keywords: tuple[str, ...]) -> list[dict[str, Any]]:
    out = []
    for path, value in flatten(obj):
        low = path.lower()
        if any(k in low for k in keywords) and isinstance(value, (str, int, float, bool)):
            out.append({"path": path, "value": value})
    return out


def first_numeric(obj: Any, include: tuple[str, ...], exclude: tuple[str, ...] = ()) -> float | None:
    for path, value in flatten(obj):
        low = path.lower()
        if all(k in low for k in include) and not any(k in low for k in exclude) and isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()})


def multiseed_table(ms: Any, zuco: Any, fmri: Any) -> list[dict[str, Any]]:
    rows = []
    zprimary = first_numeric(zuco, ("mean", "delta"))
    fprimary = first_numeric(fmri, ("primary", "mean", "delta")) or first_numeric(fmri, ("mean", "delta"))
    rows.append({"run": "primary", "seed": "20260823 adapter", "zuco_mean_delta": zprimary, "fmri_mean_delta": fprimary})

    # nmi_multiseed_e5_v1 has varied slightly across implementation revisions; discover seed records structurally.
    candidate_lists = []
    if isinstance(ms, dict):
        for k, v in ms.items():
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                candidate_lists.append((k, v))
    seed_records = []
    for name, vals in candidate_lists:
        if any("seed" in str(k).lower() for x in vals for k in x.keys()):
            seed_records = vals
            break
    for rec in seed_records:
        seed = rec.get("seed") or rec.get("optimization_seed") or rec.get("train_seed")
        z = first_numeric(rec, ("zuco", "mean", "delta")) or first_numeric(rec, ("zuco", "delta"))
        f = first_numeric(rec, ("fmri", "mean", "delta")) or first_numeric(rec, ("smn4lang", "mean", "delta")) or first_numeric(rec, ("fmri", "delta"))
        zp = first_numeric(rec, ("zuco", "positive"))
        fp = first_numeric(rec, ("fmri", "positive")) or first_numeric(rec, ("smn4lang", "positive"))
        rows.append({"run": "additional_seed", "seed": seed, "zuco_mean_delta": z, "zuco_positive_field": zp, "fmri_mean_delta": f, "fmri_positive_field": fp})
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    required = [DERCO_REL, DERCO_TRANSFER, MULTISEED, ZUCO_PRIMARY, FMRI_PRIMARY, MBERT_OLD, PANEL, PANEL_ROWS, PANEL_MODELS, ZUCO_INPUT]
    missing = [rel(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing completed derived output(s): " + ", ".join(missing))

    payloads = {p.stem + "@" + p.parent.parent.name: read_json(p) for p in [DERCO_REL, DERCO_TRANSFER, MULTISEED, ZUCO_PRIMARY, FMRI_PRIMARY, MBERT_OLD, PANEL, PANEL_MODELS, ZUCO_INPUT]}
    derco_rel = read_json(DERCO_REL)
    derco_transfer = read_json(DERCO_TRANSFER)
    multiseed = read_json(MULTISEED)
    zuco = read_json(ZUCO_PRIMARY)
    fmri = read_json(FMRI_PRIMARY)
    mbert_old = read_json(MBERT_OLD)
    panel = read_json(PANEL)
    panel_models = read_json(PANEL_MODELS)
    panel_rows = read_csv(PANEL_ROWS)
    zuco_input = read_json(ZUCO_INPUT)

    old_cfg_text = git_show(OLD_COMMIT, OLD_CONFIG_PATH)
    old_cfg = json.loads(old_cfg_text)
    old_train = git_show(OLD_COMMIT, OLD_TRAIN_PATH)
    panel_script = git_show(PANEL_COMMIT, PANEL_SCRIPT_PATH)

    old_revision = old_cfg.get("model_revision")
    panel_mbert = panel_models.get("mbert", {}) if isinstance(panel_models, dict) else {}
    panel_revision = panel_mbert.get("revision") if isinstance(panel_mbert, dict) else None

    mbert_panel_rows = [r for r in panel_rows if r.get("model_key") == "mbert"]
    mbert_comparison = [
        {"feature": "model_id", "older_mbert_run": old_cfg.get("model_id"), "common_panel": panel_mbert.get("model_id") if isinstance(panel_mbert, dict) else None},
        {"feature": "model_revision", "older_mbert_run": old_revision, "common_panel": panel_revision},
        {"feature": "seeds", "older_mbert_run": old_cfg.get("prespecified_seeds"), "common_panel": sorted({r.get("seed") for r in mbert_panel_rows})},
        {"feature": "lambda", "older_mbert_run": old_cfg.get("neural_loss_weight"), "common_panel": sorted({r.get("lambda") for r in mbert_panel_rows})},
        {"feature": "text_objective", "older_mbert_run": "masked-language modelling (MLM)", "common_panel": "symmetric dropout-view InfoNCE, temperature 0.05"},
        {"feature": "base_model_class", "older_mbert_run": "AutoModelForMaskedLM", "common_panel": "AutoModel"},
        {"feature": "pooling", "older_mbert_run": "final hidden mean over non-special non-padding tokens", "common_panel": "attention-mask mean final hidden (special tokens not explicitly excluded)"},
        {"feature": "forward_external_target", "older_mbert_run": "ZuCo EEG and SMN4Lang fMRI", "common_panel": "SMN4Lang fMRI only for ChineseEEG-source direction"},
    ]

    protocol_checks = {
        "old_train_contains_mlm": "DataCollatorForLanguageModeling" in old_train and "AutoModelForMaskedLM" in old_train,
        "old_train_excludes_special_tokens_in_pooling": "~special.bool()" in old_train,
        "panel_contains_infonce": "symmetric dropout-view InfoNCE" in panel_script,
        "panel_uses_automodel": "AutoModel.from_pretrained" in panel_script,
        "panel_pooling_attention_mask_only": "attention-mask mean final hidden" in panel_script,
        "same_model_id": old_cfg.get("model_id") == (panel_mbert.get("model_id") if isinstance(panel_mbert, dict) else None),
        "same_revision": old_revision == panel_revision,
        "same_training_protocol": False,
    }

    seed_rows = multiseed_table(multiseed, zuco, fmri)

    key_rows = [
        {"issue": "DERCo reliability", "source": rel(DERCO_REL), "sha256": sha256(DERCO_REL), "selected_fields": find_values(derco_rel, ("reliab", "loo", "positive", "gate", "participant", "subject"))},
        {"issue": "DERCo transfer", "source": rel(DERCO_TRANSFER), "sha256": sha256(DERCO_TRANSFER), "selected_fields": find_values(derco_transfer, ("delta", "positive", "bootstrap", "one_sided", "p", "participant", "subject"))},
        {"issue": "Primary-seed robustness", "source": rel(MULTISEED), "sha256": sha256(MULTISEED), "selected_fields": seed_rows},
        {"issue": "Older mBERT robustness", "source": rel(MBERT_OLD), "sha256": sha256(MBERT_OLD), "selected_fields": find_values(mbert_old, ("seed", "zuco", "fmri", "delta", "revision", "model_id"))},
        {"issue": "Common bidirectional panel mBERT", "source": rel(PANEL_ROWS), "sha256": sha256(PANEL_ROWS), "selected_fields": mbert_panel_rows},
        {"issue": "ZuCo cohort/exclusion", "source": rel(ZUCO_INPUT), "sha256": sha256(ZUCO_INPUT), "selected_fields": find_values(zuco_input, ("ready_subject", "exclude", "ytl", "subject", "cohort"))},
    ]

    summary = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "read-only reconciliation of omitted DERCo and E5 multiseed evidence plus the two mBERT protocols",
        "guardrails": {
            "new_model_training": False,
            "new_model_evaluation": False,
            "new_neural_analysis": False,
            "new_hypothesis_test": False,
            "manuscript_editing": False,
        },
        "historical_job_commits": {"M7K2R9V4": OLD_COMMIT, "V8K3M6R2": PANEL_COMMIT},
        "protocol_checks": protocol_checks,
        "mbert_protocol_comparison": mbert_comparison,
        "mbert_common_panel_rows": mbert_panel_rows,
        "multiseed_table": seed_rows,
        "derco_reliability_fields": find_values(derco_rel, ("reliab", "loo", "positive", "gate", "participant", "subject")),
        "derco_transfer_fields": find_values(derco_transfer, ("delta", "positive", "bootstrap", "one_sided", "p", "participant", "subject")),
        "zuco_cohort_fields": find_values(zuco_input, ("ready_subject", "exclude", "ytl", "subject", "cohort")),
        "source_hashes": {rel(p): sha256(p) for p in required},
        "conclusions": {
            "derco_requires_manuscript_reconciliation": True,
            "multiseed_e5_requires_manuscript_reconciliation": True,
            "mbert_runs_are_not_same_training_protocol": True,
            "mbert_revision_is_same": old_revision == panel_revision,
            "common_panel_does_not_test_chineseeeg_to_zuco": True,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "source_summaries.json").write_text(json.dumps(payloads, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(OUT / "mbert_protocol_comparison.csv", mbert_comparison)
    write_csv(OUT / "key_reconciliation_rows.csv", key_rows)
    write_csv(OUT / "multiseed_primary_table.csv", seed_rows)

    report = [
        "NeuroSem NMI v1.16 key reconciliation audit",
        "",
        "Read-only audit; no new scientific analysis or manuscript editing.",
        "",
        "mBERT reconciliation",
        f"- Same model id: {protocol_checks['same_model_id']}",
        f"- Same immutable model revision: {protocol_checks['same_revision']}",
        "- Same training protocol: False",
        "- Older M7K2R9V4 protocol uses MLM / AutoModelForMaskedLM and excludes special tokens from pooling.",
        "- V8K3M6R2 common panel uses dropout-view InfoNCE / AutoModel and attention-mask mean pooling.",
        "- Therefore their mBERT seed results are not duplicate executions of one protocol and should not be treated as a numerical contradiction under identical conditions.",
        "- The common panel still does not test ChineseEEG-to-ZuCo, so it cannot establish backbone robustness for Primary Test 1.",
        "",
        "Manuscript reconciliation",
        "- DERCo is a completed high-reliability negative transfer boundary and must be represented or explicitly dispositioned.",
        "- nmi_multiseed_e5_v1 is a completed optimization-seed robustness result and must be represented or explicitly dispositioned.",
        "- See multiseed_primary_table.csv and key_reconciliation_rows.csv for machine-read values.",
    ]
    (OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": rel(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

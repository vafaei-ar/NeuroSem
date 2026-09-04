#!/usr/bin/env python3
"""Presentation-only NMI v4 figure rebuild from existing frozen NeuroSem outputs."""
from __future__ import annotations
import csv, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = REPO / "outputs/nmi_main_figures_v3/latest"
AUX_OUT = REPO / "outputs/nmi_visualizations_v4/latest"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def headers(path):
    with open(path, newline="", encoding="utf-8") as f:
        return set(next(csv.reader(f)))


def discover_csv(required, prefer):
    matches = []
    for p in (REPO / "outputs").rglob("*.csv"):
        try:
            if required.issubset(headers(p)):
                matches.append((int(prefer.lower() in str(p).lower()), p.stat().st_mtime, p))
        except Exception:
            pass
    if not matches:
        raise FileNotFoundError(f"No CSV with fields {sorted(required)}")
    matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
    if matches[0][0] != 1:
        raise FileNotFoundError(f"No preferred CSV containing {prefer!r}")
    return matches[0][2]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(script, *args):
    cmd = [sys.executable, str(HERE / script), *args]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=True)


def prepare_dose_json(path, reliability_csv, out):
    rows = read_csv(path)
    by = {(r["dataset"], float(r["lambda"])): r for r in rows}
    lam = [0.01, 0.03, 0.10, 0.30, 1.00]
    vals = lambda ds, f: [float(by[(ds, x)][f]) for x in lam]
    cis = lambda ds: [[float(by[(ds, x)]["bootstrap_95ci_low"]), float(by[(ds, x)]["bootstrap_95ci_high"])] for x in lam]
    rr = [r for r in read_csv(reliability_csv) if r.get("candidate") == "row_mean_all"]
    if len(rr) != 17:
        raise RuntimeError(f"Expected 17 ZuCo reliability rows, found {len(rr)}")
    payload = {
        "lambda": lam,
        "zuco_delta": vals("zuco", "mean_delta_rsa"),
        "zuco_ci": cis("zuco"),
        "fmri_delta": vals("smn4lang_fmri", "mean_delta_rsa"),
        "fmri_ci": cis("smn4lang_fmri"),
        "sts_delta": vals("zuco", "delta_external_sts_vs_lambda0_already_observed"),
        "zuco_baseline": float(by[("zuco", 0.0)]["lambda_0_mean_rsa"]),
        "fmri_baseline": float(by[("smn4lang_fmri", 0.0)]["lambda_0_mean_rsa"]),
        "zuco_reliability": sum(float(r["resid_loo"]) for r in rr) / len(rr),
        "prospective_lambda": 0.10,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def prepare_model_json(path, out):
    rows = read_csv(path)
    labels = {
        "e5_large": "E5-large",
        "e5_base": "E5-base",
        "multilingual_mpnet": "mMPNet",
        "multilingual_minilm": "mMiniLM",
        "xlmr_base": "XLM-R",
        "mbert": "mBERT",
    }
    payload = {"order": list(labels.values()), "eeg_to_fmri": {}, "fmri_to_eeg": {}}
    for direction in ("eeg_to_fmri", "fmri_to_eeg"):
        for key, label in labels.items():
            rr = sorted([r for r in rows if r["model_key"] == key and r["direction"] == direction], key=lambda r: int(r["seed"]))
            if len(rr) != 3:
                raise RuntimeError(f"Expected 3 seeds for {key}/{direction}, found {len(rr)}")
            payload[direction][label] = [float(r["external_mean_delta"]) for r in rr]
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    AUX_OUT.mkdir(parents=True, exist_ok=True)
    zuco_rel = discover_csv({"candidate", "resid_loo"}, "zuco2_nr_primary_representation_reliability")
    zuco_transfer = discover_csv({"lambda_0_resid_rsa", "lambda_0p10_resid_rsa", "delta_0p10_minus_0"}, "zuco2_nr_e5_transfer_v1")
    fmri_rel = discover_csv({"primary_residual_reliability"}, "smn4lang_fmri_reliability")
    fmri_transfer = discover_csv({"lambda_0_residual_rsa", "lambda_0p10_residual_rsa", "delta_0p10_minus_0"}, "smn4lang_fmri_e5_transfer_v1")
    dose_csv = REPO / "outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv"
    model_csv = REPO / "outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
    regional_csv = REPO / "outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv"
    dev_json = REPO / "paper/figure_data/chineseeeg_development_v1.json"
    inputs = [
        zuco_rel, zuco_rel.parent / "summary.json", zuco_transfer, zuco_transfer.parent / "summary.json",
        fmri_rel, fmri_rel.parent / "summary.json", fmri_transfer, fmri_transfer.parent / "summary.json",
        dose_csv, model_csv, regional_csv, dev_json,
    ]
    for p in inputs:
        if not p.exists():
            raise FileNotFoundError(p)
    with tempfile.TemporaryDirectory(prefix="neurosem_nmi_v4_") as td:
        td = Path(td)
        dose_json = td / "dose.json"
        model_json = td / "models.json"
        prepare_dose_json(dose_csv, zuco_rel, dose_json)
        prepare_model_json(model_csv, model_json)
        run("build_figure1_chineseeeg.py", "--development-json", str(dev_json), "--out-prefix", str(OUT / "figure1"))
        run("build_figure2_zuco.py", "--rel-subjects", str(zuco_rel), "--rel-summary", str(zuco_rel.parent / "summary.json"), "--transfer-subjects", str(zuco_transfer), "--transfer-summary", str(zuco_transfer.parent / "summary.json"), "--out-prefix", str(OUT / "figure2"))
        run("build_figure3_smn4lang.py", "--reliability-participants", str(fmri_rel), "--reliability-summary", str(fmri_rel.parent / "summary.json"), "--transfer-participants", str(fmri_transfer), "--transfer-summary", str(fmri_transfer.parent / "summary.json"), "--out-prefix", str(OUT / "figure3"))
        run("build_figure4_dose_models.py", "--dose-summary", str(dose_json), "--model-panel", str(model_json), "--out-prefix", str(OUT / "figure4"))
        run("build_extdata_regional.py", "--region-summary", str(regional_csv), "--out-prefix", str(AUX_OUT / "extdata_regional"))
    outputs = [OUT / f"{stem}.{ext}" for stem in ["figure1", "figure2", "figure3", "figure4"] for ext in ["pdf", "svg", "png"]]
    aux_outputs = [AUX_OUT / f"extdata_regional.{ext}" for ext in ["pdf", "svg", "png"]]
    manifest = {
        "schema_version": 2,
        "analysis": "NMI visualization v4 presentation-only rebuild",
        "guardrails": [
            "Uses already-completed frozen derived outputs only.",
            "No fitting, tuning, target selection, inference, or new hypothesis test is performed.",
            "Synthetic/demo paths are not used by this orchestrator.",
        ],
        "inputs": {str(p.relative_to(REPO)): sha256(p) for p in inputs},
        "outputs": {str(p.relative_to(REPO)): sha256(p) for p in outputs + aux_outputs},
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(OUT), "n_outputs": len(outputs), "aux_outputs": len(aux_outputs)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

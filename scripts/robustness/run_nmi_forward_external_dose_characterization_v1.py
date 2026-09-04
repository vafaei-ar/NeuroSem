#!/usr/bin/env python3
"""Frozen post-confirmatory forward external-dose characterization.

Evaluates the already-trained ChineseEEG multilingual-E5 dose grid on the unchanged
ZuCo and SMN4Lang primary pipelines. Lambda=.10 is reused from the completed
prospective primary outputs; the four previously unseen nonzero external doses are
evaluated exactly once per target through the shared external-evaluation wrapper.
"""
from __future__ import annotations

import csv
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analysis.run_zuco2_nr_primary_representation_reliability import boot_ci as zuco_boot_ci
from scripts.analysis.run_smn4lang_fmri_reliability import bootstrap_ci as fmri_boot_ci

PROTOCOL = "docs/31_NMI_FORWARD_EXTERNAL_DOSE_CHARACTERIZATION_V1.md"
ROOT = Path("outputs/nmi_forward_external_dose_characterization_v1/latest")
TEXT_ADAPTER = Path("outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter")
PRIMARY_ZUCO = Path("outputs/zuco2_nr_e5_transfer_v1/latest")
PRIMARY_FMRI = Path("outputs/smn4lang_fmri_e5_transfer_v1/latest")
PARETO_SUMMARY = Path("outputs/e5_pareto_v1/latest/combined_summary.json")

GRID = [0.00, 0.01, 0.03, 0.10, 0.30, 1.00]
NEW_DOSES = [0.01, 0.03, 0.30, 1.00]
LABEL = {
    0.00: "lambda_0",
    0.01: "lambda_0p01",
    0.03: "lambda_0p03",
    0.10: "lambda_0p10",
    0.30: "lambda_0p30",
    1.00: "lambda_1",
}
NEURAL_ROOT = {
    0.01: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural"),
    0.03: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural"),
    0.10: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural"),
    0.30: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural"),
    1.00: Path("outputs/e5_neural_tuning_v1/neural"),
}


def atomic_progress(current: int, total: int, phase: str, message: str = "") -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else None,
        "phase": phase,
        "message": message,
        "unit": "dose-target evaluations",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def exact_signflip(values: np.ndarray) -> dict:
    v = np.asarray(values, dtype=float)
    if not len(v) or len(v) > 20 or not np.isfinite(v).all():
        raise RuntimeError("Exact sign flip requires 1-20 finite participant deltas")
    obs = float(v.mean())
    one = 0
    two = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(v)):
        m = float(np.dot(v, np.asarray(signs, dtype=float)) / len(v))
        one += m >= obs - 1e-15
        two += abs(m) >= abs(obs) - 1e-15
        total += 1
    return {
        "one_sided_greater_p": one / total,
        "two_sided_p": two / total,
        "n_sign_patterns": total,
    }


def adapter_path_from_root(root: Path) -> Path:
    candidates = []
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and (d / "summary.json").is_file() and (d / "adapter").is_dir():
                candidates.append(d)
    if not candidates:
        raise FileNotFoundError(f"No completed adapter under {root}")
    return sorted(candidates)[-1] / "adapter"


def structural_preflight() -> dict:
    required = [TEXT_ADAPTER, PARETO_SUMMARY, PRIMARY_ZUCO / "summary.json", PRIMARY_ZUCO / "subject_results.csv",
                PRIMARY_FMRI / "summary.json", PRIMARY_FMRI / "participant_results.csv"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required frozen inputs: " + ", ".join(missing))
    resolved = {str(d): str(adapter_path_from_root(root)) for d, root in NEURAL_ROOT.items()}
    expected = {
        "0.01": "outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural/20260823_192219/adapter",
        "0.03": "outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural/20260823_192323/adapter",
        "0.1": "outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/20260823_192425/adapter",
        "0.3": "outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural/20260823_192528/adapter",
        "1.0": "outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter",
    }
    for key, rel in expected.items():
        got = Path(resolved[key]).resolve()
        want = (REPO_ROOT / rel).resolve()
        if got != want:
            raise RuntimeError(f"Adapter provenance mismatch for lambda={key}: {got} != {want}")
    return {"resolved_nonzero_adapters": resolved, "all_required_inputs_present": True}


def run_external(dataset: str, dose: float, done: int, total: int) -> Path:
    label = LABEL[dose]
    out = ROOT / dataset / label
    expected = out / ("subject_results.csv" if dataset == "zuco" else "participant_results.csv")
    summary = out / "summary.json"
    if expected.is_file() and summary.is_file():
        print(f"Reusing completed same-protocol output: {dataset} {label}", flush=True)
        atomic_progress(done + 1, total, "external-dose", f"reused {dataset} {label}")
        return out
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "scripts/robustness/evaluate_external_with_adapters_v1.py",
        "--dataset", dataset,
        "--text-adapter", str(TEXT_ADAPTER),
        "--neural-root", str(NEURAL_ROOT[dose]),
        "--output-dir", str(out),
    ]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    if not expected.is_file() or not summary.is_file():
        raise RuntimeError(f"Expected outputs missing after {dataset}/{label}")
    atomic_progress(done + 1, total, "external-dose", f"completed {dataset} {label}")
    return out


def sts_by_dose() -> dict[float, dict]:
    payload = json.loads(PARETO_SUMMARY.read_text(encoding="utf-8"))
    points = payload.get("points") or []
    out = {}
    for p in points:
        d = float(p["lambda"])
        out[d] = {
            "external_sts_mean": float(p["external_sts_mean"]),
            "delta_external_sts_vs_lambda0": float(p["delta_external_sts_vs_lambda0"]),
        }
    if sorted(out) != GRID:
        raise RuntimeError(f"Pareto STS grid mismatch: {sorted(out)}")
    return out


def standardized_rows(dataset: str, dose: float, source_dir: Path, status: str) -> tuple[list[dict], dict]:
    if dataset == "zuco":
        path = source_dir / "subject_results.csv"
        id_col = "subject"
        a0_col = "lambda_0_resid_rsa"
        a1_col = "lambda_0p10_resid_rsa"
        delta_col = "delta_0p10_minus_0"
        expected_n = 17
        ci_fn = zuco_boot_ci
    else:
        path = source_dir / "participant_results.csv"
        id_col = "subject"
        a0_col = "lambda_0_residual_rsa"
        a1_col = "lambda_0p10_residual_rsa"
        delta_col = "delta_0p10_minus_0"
        expected_n = 12
        ci_fn = fmri_boot_ci
    raw = read_csv(path)
    if len(raw) != expected_n:
        raise RuntimeError(f"{dataset}/{dose}: expected {expected_n} participant rows, got {len(raw)}")
    rows = []
    a0 = []
    a1 = []
    delta = []
    for r in raw:
        x0 = float(r[a0_col]); x1 = float(r[a1_col]); dx = float(r[delta_col])
        if not np.isclose(x1 - x0, dx, rtol=0, atol=1e-12):
            raise RuntimeError(f"{dataset}/{dose}/{r[id_col]} delta mismatch")
        rows.append({
            "dataset": dataset,
            "lambda": dose,
            "lambda_label": LABEL[dose],
            "subject": r[id_col],
            "lambda_0_rsa": x0,
            "dose_rsa": x1,
            "delta_rsa_vs_lambda0": dx,
            "outcome_status": status,
        })
        a0.append(x0); a1.append(x1); delta.append(dx)
    a0a = np.asarray(a0); a1a = np.asarray(a1); da = np.asarray(delta)
    ci = ci_fn(da)
    sf = exact_signflip(da)
    summary = {
        "dataset": dataset,
        "lambda": dose,
        "lambda_label": LABEL[dose],
        "outcome_status": status,
        "n_participants": expected_n,
        "lambda_0_mean_rsa": float(a0a.mean()),
        "dose_mean_rsa": float(a1a.mean()),
        "mean_delta_rsa": float(da.mean()),
        "median_delta_rsa": float(np.median(da)),
        "n_positive": int(np.sum(da > 0)),
        "fraction_positive": float(np.mean(da > 0)),
        "bootstrap_95ci_low": float(ci[0]),
        "bootstrap_95ci_high": float(ci[1]),
        "exact_two_sided_signflip_p": float(sf["two_sided_p"]),
        "exact_one_sided_greater_p": float(sf["one_sided_greater_p"]),
        "n_sign_patterns": int(sf["n_sign_patterns"]),
    }
    return rows, summary


def baseline_rows(dataset: str, primary_dir: Path) -> tuple[list[dict], dict]:
    if dataset == "zuco":
        raw = read_csv(primary_dir / "subject_results.csv")
        a0_col = "lambda_0_resid_rsa"
    else:
        raw = read_csv(primary_dir / "participant_results.csv")
        a0_col = "lambda_0_residual_rsa"
    rows = []
    vals = []
    for r in raw:
        x = float(r[a0_col]); vals.append(x)
        rows.append({
            "dataset": dataset,
            "lambda": 0.0,
            "lambda_label": LABEL[0.0],
            "subject": r["subject"],
            "lambda_0_rsa": x,
            "dose_rsa": x,
            "delta_rsa_vs_lambda0": 0.0,
            "outcome_status": "prospective primary baseline reused",
        })
    va = np.asarray(vals)
    summary = {
        "dataset": dataset,
        "lambda": 0.0,
        "lambda_label": LABEL[0.0],
        "outcome_status": "prospective primary baseline reused",
        "n_participants": len(vals),
        "lambda_0_mean_rsa": float(va.mean()),
        "dose_mean_rsa": float(va.mean()),
        "mean_delta_rsa": 0.0,
        "median_delta_rsa": 0.0,
        "n_positive": 0,
        "fraction_positive": 0.0,
        "bootstrap_95ci_low": 0.0,
        "bootstrap_95ci_high": 0.0,
        "exact_two_sided_signflip_p": 1.0,
        "exact_one_sided_greater_p": 1.0,
        "n_sign_patterns": 0,
    }
    return rows, summary


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    preflight = structural_preflight()
    total = len(NEW_DOSES) * 2
    atomic_progress(0, total, "preflight", "validated frozen adapters and primary inputs")

    done = 0
    for dataset in ["zuco", "smn4lang_fmri"]:
        for dose in NEW_DOSES:
            run_external(dataset, dose, done, total)
            done += 1

    sts = sts_by_dose()
    all_participant_rows = []
    dose_rows = []
    dataset_specs = {
        "zuco": PRIMARY_ZUCO,
        "smn4lang_fmri": PRIMARY_FMRI,
    }
    for dataset, primary in dataset_specs.items():
        base_rows, base_sum = baseline_rows(dataset, primary)
        all_participant_rows.extend(base_rows)
        dose_rows.append(base_sum)

        # The prospectively tested lambda=.10 point is reused, not recomputed.
        pr, ps = standardized_rows(dataset, 0.10, primary, "prospective primary lambda=.10 result reused")
        all_participant_rows.extend(pr); dose_rows.append(ps)

        for dose in [0.01, 0.03, 0.30, 1.00]:
            dr, ds = standardized_rows(dataset, dose, ROOT / dataset / LABEL[dose], "new post-confirmatory external-dose outcome")
            all_participant_rows.extend(dr); dose_rows.append(ds)

    dose_rows.sort(key=lambda r: (r["dataset"], float(r["lambda"])))
    for r in dose_rows:
        s = sts[float(r["lambda"])]
        r["external_sts_mean_already_observed"] = s["external_sts_mean"]
        r["delta_external_sts_vs_lambda0_already_observed"] = s["delta_external_sts_vs_lambda0"]

    write_csv(ROOT / "participant_dose_results.csv", all_participant_rows)
    write_csv(ROOT / "dose_summary.csv", dose_rows)
    write_csv(ROOT / "tradeoff_points.csv", [
        {
            "dataset": r["dataset"],
            "lambda": r["lambda"],
            "delta_external_sts_vs_lambda0_already_observed": r["delta_external_sts_vs_lambda0_already_observed"],
            "mean_external_delta_rsa_vs_lambda0": r["mean_delta_rsa"],
            "outcome_status": r["outcome_status"],
        }
        for r in dose_rows
    ])

    payload = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory forward external-dose characterization",
        "protocol": PROTOCOL,
        "grid": GRID,
        "newly_evaluated_doses": NEW_DOSES,
        "external_targets": ["zuco", "smn4lang_fmri"],
        "new_external_evaluation_count": total,
        "primary_lambda_0p10_reused_not_recomputed": True,
        "lambda_0_baseline_reused_from_primary_outputs": True,
        "outcome_status_asymmetry": {
            "already_observed_before_freeze": [
                "ChineseEEG run-07 six-dose outcomes",
                "eight-task Chinese STS outcomes for all six doses",
                "prospective ZuCo lambda=0 and lambda=.10 outcomes",
                "prospective SMN4Lang lambda=0 and lambda=.10 outcomes",
            ],
            "new_under_this_protocol": [
                "ZuCo lambda=.01,.03,.30,1.00 external outcomes",
                "SMN4Lang lambda=.01,.03,.30,1.00 external outcomes",
            ],
        },
        "adapter_preflight": preflight,
        "reporting_rule": "complete curves retained; no optimal dose, target-side selection, monotonicity test, or rescue tuning",
        "dose_summary": dose_rows,
    }
    (ROOT / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    atomic_progress(total, total, "complete", "consolidated complete frozen dose curves")
    print(json.dumps({"status": "ok", "output_dir": str(ROOT), "new_external_evaluations": total}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

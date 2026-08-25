#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
from pathlib import Path

from scipy.io import loadmat


def is_tracked(root: Path, rel: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", rel],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def annex_get(root: Path, rel: str) -> dict:
    p = root / rel
    rec = {"path": rel, "tracked": is_tracked(root, rel), "materialized_before": p.exists()}
    if not rec["tracked"]:
        rec["status"] = "not_tracked"
        return rec
    if not p.exists():
        cp = subprocess.run(
            ["git", "-C", str(root), "annex", "get", "--", rel],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        rec["annex_get_returncode"] = cp.returncode
        rec["annex_get_stdout_tail"] = cp.stdout[-1200:]
        rec["annex_get_stderr_tail"] = cp.stderr[-1200:]
    rec["materialized_after"] = p.exists()
    rec["size_bytes"] = p.stat().st_size if p.exists() else None
    rec["status"] = "materialized" if p.exists() else "not_materializable"
    return rec


def load_eeg_meta(set_path: Path) -> dict:
    d = loadmat(set_path, simplify_cells=True)
    eeg = d.get("EEG")
    if not isinstance(eeg, dict):
        raise RuntimeError(f"EEG structure missing in {set_path}")
    out = {}
    for k in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax", "data", "bepoch", "item", "bin"]:
        if k in eeg:
            v = eeg[k]
            if hasattr(v, "shape") and getattr(v, "size", 0) > 20:
                out[k] = {"shape": list(v.shape), "dtype": str(v.dtype)}
            elif hasattr(v, "tolist"):
                out[k] = v.tolist()
            else:
                out[k] = v
    return out


def data_companion(meta: dict, set_rel: str):
    data = meta.get("data")
    if isinstance(data, str) and data.strip():
        return str(Path(set_rel).parent / data.strip())
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_representation_input_materialization/latest")
    ap.add_argument("--min-retained-trials", type=int, default=30)
    args = ap.parse_args()

    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    failures = []
    subjects = [f"sub-{i:02d}" for i in range(1, 31)]
    sessions = [f"ses-{i}" for i in range(1, 9)]

    for subject in subjects:
        for session in sessions:
            set_rel = f"derivatives/preproc/{subject}/{session}/{subject}-{session}z.set"
            set_rec = annex_get(root, set_rel)
            row = {
                "subject": subject,
                "session": session,
                "set_path": set_rel,
                "set_status": set_rec.get("status"),
                "companion_path": "",
                "companion_status": "",
                "nbchan": "",
                "trials": "",
                "pnts": "",
                "srate": "",
                "xmin": "",
                "xmax": "",
                "passes_min_trials": False,
                "status": "",
            }
            if set_rec.get("status") != "materialized":
                row["status"] = "set_unavailable"
                failures.append(dict(row))
                rows.append(row)
                continue
            try:
                meta = load_eeg_meta(root / set_rel)
            except Exception as exc:
                row["status"] = f"metadata_error:{type(exc).__name__}"
                failures.append(dict(row))
                rows.append(row)
                continue

            for key in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax"]:
                row[key] = meta.get(key, "")

            companion_rel = data_companion(meta, set_rel)
            if companion_rel:
                comp_rec = annex_get(root, companion_rel)
                row["companion_path"] = companion_rel
                row["companion_status"] = comp_rec.get("status")
            else:
                row["companion_status"] = "embedded_or_not_required"

            trials = meta.get("trials")
            try:
                n_trials = int(trials)
            except Exception:
                n_trials = -1
            row["passes_min_trials"] = n_trials >= args.min_retained_trials

            structural_ok = (
                int(meta.get("nbchan", -1)) == 30
                and abs(float(meta.get("srate", -1)) - 200.0) < 1e-6
                and n_trials > 0
                and (not companion_rel or row["companion_status"] == "materialized")
            )
            if not structural_ok:
                row["status"] = "structural_failure"
                failures.append(dict(row))
            elif not row["passes_min_trials"]:
                row["status"] = "below_min_retained_trials"
                failures.append(dict(row))
            else:
                row["status"] = "ready"
            rows.append(row)

    csv_path = outdir / "session_inventory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ready_subjects = []
    for subject in subjects:
        sr = [r for r in rows if r["subject"] == subject]
        if len(sr) == 8 and all(r["status"] == "ready" for r in sr):
            ready_subjects.append(subject)

    payload = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "openneuro_accession": "ds005383",
        "published_snapshot": "1.0.0",
        "model_blind": True,
        "analysis_source": "published artifact-rejected epoched EEGLAB z.set derivative",
        "trial_identity_mapping": "EEGLAB bepoch -> original BIDS event row -> session-specific source-material row",
        "candidate_subjects": subjects,
        "sessions_per_subject": 8,
        "expected_sessions": 240,
        "min_retained_trials_per_session": args.min_retained_trials,
        "ready_subjects_all_8_sessions": ready_subjects,
        "n_ready_subjects_all_8_sessions": len(ready_subjects),
        "n_ready_sessions": sum(r["status"] == "ready" for r in rows),
        "n_failed_sessions": sum(r["status"] != "ready" for r in rows),
        "failures": failures,
        "notes": [
            "No EEG reliability, candidate ranking, language-model embedding, or neural-model RSA is computed.",
            "This step materializes only the prespecified artifact-rejected epoched derivatives and any exact external data companion referenced by each z.set file.",
            "Subject readiness is defined before representation outcomes: all eight sessions materializable and at least 30 retained trials per session.",
            "The later primary TMNRED RDM analysis will be within session to avoid conflating broad semantic category with session/block effects."
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failures:
        raise SystemExit(f"TMNRED representation input materialization had {len(failures)} non-ready sessions; inspect derived inventory before analysis.")
    print(json.dumps({"status": "ok", "n_ready_subjects": len(ready_subjects), "output_dir": str(outdir)}, indent=2))


if __name__ == "__main__":
    main()

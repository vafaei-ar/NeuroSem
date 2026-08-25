#!/usr/bin/env python3
import argparse
import csv
import json
import math
import subprocess
from collections import Counter
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


def _simplify_value(v):
    if hasattr(v, "shape") and getattr(v, "size", 0) > 20:
        return {"shape": list(v.shape), "dtype": str(v.dtype)}
    if hasattr(v, "tolist"):
        return v.tolist()
    return v


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if hasattr(value, "tolist"):
        value = value.tolist()
        return value if isinstance(value, list) else [value]
    return [value]


def _extract_bepoch_from_events(source: dict) -> list[int]:
    out = []
    seen = set()
    for event in _as_list(source.get("event")):
        if not isinstance(event, dict):
            continue
        try:
            value = int(event.get("bepoch"))
        except Exception:
            continue
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def load_eeg_meta(set_path: Path) -> dict:
    d = loadmat(set_path, simplify_cells=True)
    eeg = d.get("EEG")
    if isinstance(eeg, dict):
        source = eeg
        layout = "EEG_struct"
    elif all(k in d for k in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax", "data"]):
        source = d
        layout = "flat_top_level"
    else:
        raise RuntimeError(f"Recognized EEGLAB fields missing in {set_path}")

    out = {"layout": layout}
    for k in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax", "data", "item", "bin"]:
        if k in source:
            out[k] = _simplify_value(source[k])
    out["bepoch"] = _extract_bepoch_from_events(source)
    return out


def data_companion(root: Path, meta: dict, set_rel: str):
    data = meta.get("data")
    if isinstance(data, dict):
        return None
    canonical_rel = str(Path(set_rel).with_suffix(".fdt"))
    if is_tracked(root, canonical_rel):
        return canonical_rel
    if isinstance(data, str) and data.strip():
        legacy_rel = str(Path(set_rel).parent / data.strip())
        if is_tracked(root, legacy_rel):
            return legacy_rel
        raise RuntimeError(
            f"External EEG data referenced by {set_rel}, but neither canonical companion "
            f"{canonical_rel} nor legacy path {legacy_rel} is tracked"
        )
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_representation_input_materialization/latest")
    ap.add_argument("--min-retained-trials", type=int, default=30)
    ap.add_argument("--min-item-coverage-fraction", type=float, default=0.80)
    ap.add_argument("--min-subject-items", type=int, default=20)
    args = ap.parse_args()

    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    infrastructure_failures = []
    qc_exclusions = []
    subjects = [f"sub-{i:02d}" for i in range(1, 31)]
    sessions = [f"ses-{i}" for i in range(1, 9)]

    for subject in subjects:
        for session in sessions:
            set_rel = f"derivatives/preproc/{subject}/{session}/{subject}-{session}z.set"
            set_rec = annex_get(root, set_rel)
            row = {
                "subject": subject, "session": session, "set_path": set_rel,
                "set_status": set_rec.get("status"), "layout": "", "companion_path": "",
                "companion_status": "", "nbchan": "", "trials": "", "pnts": "",
                "srate": "", "xmin": "", "xmax": "", "requires_resampling_to_200hz": False,
                "passes_min_trials": False, "status": "",
            }
            if set_rec.get("status") != "materialized":
                row["status"] = "set_unavailable"
                infrastructure_failures.append(dict(row))
                rows.append(row)
                continue
            try:
                meta = load_eeg_meta(root / set_rel)
                row["layout"] = meta.get("layout", "")
            except Exception as exc:
                row["status"] = f"metadata_error:{type(exc).__name__}:{exc}"
                infrastructure_failures.append(dict(row))
                rows.append(row)
                continue
            for key in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax"]:
                row[key] = meta.get(key, "")
            try:
                companion_rel = data_companion(root, meta, set_rel)
            except Exception as exc:
                row["status"] = f"companion_resolution_error:{type(exc).__name__}:{exc}"
                infrastructure_failures.append(dict(row))
                rows.append(row)
                continue
            if companion_rel:
                comp_rec = annex_get(root, companion_rel)
                row["companion_path"] = companion_rel
                row["companion_status"] = comp_rec.get("status")
            else:
                row["companion_status"] = "embedded_or_not_required"
            try:
                n_trials = int(meta.get("trials", -1))
                nbchan = int(meta.get("nbchan", -1))
                srate = float(meta.get("srate", -1))
                xmin = float(meta.get("xmin", 999))
                xmax = float(meta.get("xmax", -999))
            except Exception:
                n_trials, nbchan, srate, xmin, xmax = -1, -1, -1.0, 999.0, -999.0
            row["passes_min_trials"] = n_trials >= args.min_retained_trials
            row["requires_resampling_to_200hz"] = abs(srate - 200.0) > 1e-6
            structural_ok = (
                nbchan == 30 and srate > 0 and n_trials > 0 and xmin <= -0.19 and xmax >= 1.99
                and (not companion_rel or row["companion_status"] == "materialized")
            )
            if not structural_ok:
                row["status"] = "structural_failure"
                infrastructure_failures.append(dict(row))
            elif not row["passes_min_trials"]:
                row["status"] = "qc_excluded_below_min_retained_trials"
                qc_exclusions.append(dict(row))
            elif row["requires_resampling_to_200hz"]:
                row["status"] = "ready_requires_resampling"
            else:
                row["status"] = "ready"
            rows.append(row)

    with (outdir / "session_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ready_statuses = {"ready", "ready_requires_resampling"}
    ready_subjects, excluded_subjects = [], []
    for subject in subjects:
        sr = [r for r in rows if r["subject"] == subject]
        if len(sr) == 8 and all(r["status"] in ready_statuses for r in sr):
            ready_subjects.append(subject)
        else:
            excluded_subjects.append(subject)

    item_cohort_failures = []
    item_coverage_by_session = {}
    if not infrastructure_failures:
        min_subjects_per_item = math.ceil(args.min_item_coverage_fraction * len(ready_subjects))
        for session in sessions:
            retained_by_subject = {}
            for subject in ready_subjects:
                set_rel = f"derivatives/preproc/{subject}/{session}/{subject}-{session}z.set"
                try:
                    meta = load_eeg_meta(root / set_rel)
                    b = meta.get("bepoch", [])
                    n_trials = int(meta.get("trials", -1))
                    if not b:
                        raise RuntimeError("missing bepoch values in EEGLAB event records")
                    if len(b) != len(set(b)):
                        raise RuntimeError("duplicate retained bepoch values after event deduplication")
                    if len(b) != n_trials:
                        raise RuntimeError(f"bepoch count {len(b)} does not match retained trial count {n_trials}")
                    retained_by_subject[subject] = set(b)
                except Exception as exc:
                    item_cohort_failures.append({
                        "subject": subject,
                        "session": session,
                        "error": f"{type(exc).__name__}:{exc}",
                    })

            if len(retained_by_subject) != len(ready_subjects):
                continue

            coverage = Counter()
            for values in retained_by_subject.values():
                coverage.update(values)
            core_items = sorted(item for item, count in coverage.items() if count >= min_subjects_per_item)
            exact_common = sorted(set.intersection(*retained_by_subject.values())) if retained_by_subject else []
            subject_core_counts = {
                subject: len(values.intersection(core_items))
                for subject, values in retained_by_subject.items()
            }
            low_subjects = {
                subject: count for subject, count in subject_core_counts.items()
                if count < args.min_subject_items
            }
            item_coverage_by_session[session] = {
                "n_ready_subjects": len(ready_subjects),
                "min_subjects_per_item": min_subjects_per_item,
                "coverage_fraction": args.min_item_coverage_fraction,
                "n_core_items": len(core_items),
                "core_bepoch": core_items,
                "exact_all_subject_intersection_n": len(exact_common),
                "exact_all_subject_intersection_bepoch": exact_common,
                "subject_core_item_counts": subject_core_counts,
                "item_retention_counts": {str(item): coverage[item] for item in sorted(coverage)},
            }
            if len(core_items) < args.min_subject_items:
                item_cohort_failures.append({
                    "session": session,
                    "error": f"80%-coverage item core below {args.min_subject_items}: {len(core_items)}",
                })
            if low_subjects:
                item_cohort_failures.append({
                    "session": session,
                    "error": "ready subject(s) retain fewer than minimum core items",
                    "subject_core_item_counts_below_min": low_subjects,
                })

    payload = {
        "schema_version": 5,
        "dataset": "TMNRED",
        "openneuro_accession": "ds005383",
        "published_snapshot": "1.0.0",
        "model_blind": True,
        "analysis_source": "published artifact-rejected epoched EEGLAB z.set derivative",
        "trial_identity_mapping": "unique EEGLAB event.bepoch values -> original BIDS event row -> session-specific source-material row",
        "candidate_subjects": subjects,
        "sessions_per_subject": 8,
        "expected_sessions": 240,
        "min_retained_trials_per_session": args.min_retained_trials,
        "ready_subjects_all_8_sessions": ready_subjects,
        "excluded_subjects": excluded_subjects,
        "n_ready_subjects_all_8_sessions": len(ready_subjects),
        "n_ready_sessions": sum(r["status"] in ready_statuses for r in rows),
        "n_qc_excluded_sessions": len(qc_exclusions),
        "n_infrastructure_failure_sessions": len(infrastructure_failures),
        "sessions_requiring_resampling_to_200hz": sum(
            bool(r["requires_resampling_to_200hz"]) and r["status"] in ready_statuses for r in rows
        ),
        "subjects_requiring_resampling_to_200hz": sorted({
            r["subject"] for r in rows if r["status"] == "ready_requires_resampling"
        }),
        "layout_counts": {
            layout: sum(r["layout"] == layout for r in rows)
            for layout in sorted({r["layout"] for r in rows if r["layout"]})
        },
        "sampling_rate_counts": {
            str(rate): sum(str(r["srate"]) == str(rate) for r in rows)
            for rate in sorted({r["srate"] for r in rows if r["srate"] != ""}, key=float)
        },
        "qc_exclusions": qc_exclusions,
        "infrastructure_failures": infrastructure_failures,
        "primary_item_cohort_rule": (
            "within each session, retain sentence items present in at least 80% of the frozen ready subjects; "
            "for each held-out subject, reliability uses the subset of that frozen high-coverage core retained by that subject"
        ),
        "min_item_coverage_fraction": args.min_item_coverage_fraction,
        "min_subjects_per_item": math.ceil(args.min_item_coverage_fraction * len(ready_subjects)) if ready_subjects else None,
        "min_subject_items": args.min_subject_items,
        "item_coverage_by_session": item_coverage_by_session,
        "item_cohort_failures": item_cohort_failures,
        "notes": [
            "No EEG reliability, candidate ranking, language-model embedding, or neural-model RSA is computed.",
            "Sampling-rate heterogeneity is harmonized by deterministic resampling during feature extraction rather than subject exclusion.",
            "The prospectively frozen subject QC remains every session >=30 retained artifact-rejected trials.",
            "Retained trial identity is read from unique EEGLAB event.bepoch values, as established prospectively by the event-alignment probe.",
            "The exact all-subject intersection is retained only as a descriptive sensitivity quantity because independent artifact rejection makes complete-case intersection increasingly sparse with 29 participants.",
            "The primary item rule is frozen model-blind at 80% participant coverage with at least 20 retained core items per subject/session before any EEG representation values are analyzed.",
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if infrastructure_failures:
        raise SystemExit(f"TMNRED input freeze had {len(infrastructure_failures)} infrastructure/structural failures")
    if item_cohort_failures:
        raise SystemExit(f"TMNRED robust item-cohort freeze had {len(item_cohort_failures)} failure(s)")
    print(json.dumps({
        "status": "ok",
        "n_ready_subjects": len(ready_subjects),
        "excluded_subjects": excluded_subjects,
        "subjects_requiring_resampling_to_200hz": payload["subjects_requiring_resampling_to_200hz"],
        "core_items": {k: v["n_core_items"] for k, v in item_coverage_by_session.items()},
        "output_dir": str(outdir),
    }, indent=2))


if __name__ == "__main__":
    main()

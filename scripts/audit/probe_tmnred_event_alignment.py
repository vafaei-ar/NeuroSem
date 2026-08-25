#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from scipy.io import loadmat


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def load_eeg_set(path: Path) -> dict:
    d = loadmat(path, simplify_cells=True)
    eeg = d.get("EEG")
    if not isinstance(eeg, dict):
        raise RuntimeError(f"EEG struct missing from {path}")
    return eeg


def read_events_tsv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def numeric_event_rows(eeg):
    rows = []
    for e in as_list(eeg.get("event")):
        if not isinstance(e, dict):
            continue
        typ = str(e.get("type", ""))
        if typ.lower() == "boundary":
            continue
        try:
            code = int(float(typ))
        except Exception:
            continue
        rows.append({
            "type": typ,
            "code": code,
            "latency": float(e.get("latency")),
        })
    return rows


def z_epoch_rows(eeg):
    rows = []
    for e in as_list(eeg.get("event")):
        if not isinstance(e, dict):
            continue
        try:
            bepoch = int(e.get("bepoch"))
        except Exception:
            continue
        rows.append({
            "epoch": int(e.get("epoch")) if e.get("epoch") is not None else None,
            "bepoch": bepoch,
            "item": int(e.get("item")) if e.get("item") is not None else None,
            "bini": int(e.get("bini")) if e.get("bini") is not None else None,
            "codelabel": str(e.get("codelabel", "")),
            "type": str(e.get("type", "")),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_event_alignment_probe/latest")
    args = ap.parse_args()

    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    bids_path = root / "sub-01/ses-1/eeg/sub-01_ses-1_task-fuzzysemanticrecognition_events.tsv"
    cont_path = root / "derivatives/preproc/sub-01/ses-1/sub-01-ses-1.set"
    z_path = root / "derivatives/preproc/sub-01/ses-1/sub-01-ses-1z.set"
    for p in (bids_path, cont_path, z_path):
        if not p.exists():
            raise SystemExit(f"Required representative file is not materialized: {p}")

    bids = read_events_tsv(bids_path)
    cont_eeg = load_eeg_set(cont_path)
    z_eeg = load_eeg_set(z_path)
    cont = numeric_event_rows(cont_eeg)
    zrows = z_epoch_rows(z_eeg)

    bids_codes = [int(float(r["value"])) for r in bids]
    cont_codes = [r["code"] for r in cont]
    direct_code_matches = sum(a == b for a, b in zip(bids_codes, cont_codes))

    # Compare temporal positions without assuming event-code identity. EEGLAB
    # latencies are 1-based sample positions; BIDS onset is seconds.
    srate = float(cont_eeg.get("srate", 200.0))
    n_pair = min(len(bids), len(cont))
    time_diffs = []
    for i in range(n_pair):
        bids_sec = float(bids[i]["onset"])
        cont_sec = (float(cont[i]["latency"]) - 1.0) / srate
        time_diffs.append(cont_sec - bids_sec)

    mapped = []
    for zr in zrows:
        idx = zr["bepoch"] - 1
        rec = dict(zr)
        if 0 <= idx < len(bids):
            br = bids[idx]
            rec.update({
                "mapped_trial_index_1based": idx + 1,
                "mapped_trial_type": br.get("trial_type"),
                "mapped_value": int(float(br.get("value"))),
                "mapped_onset": float(br.get("onset")),
                "mapped_is_target": str(br.get("trial_type", "")).startswith("target"),
            })
        else:
            rec["mapping_error"] = "bepoch_out_of_range"
        mapped.append(rec)

    by_bin = {}
    for r in mapped:
        key = str(r.get("bini"))
        d = by_bin.setdefault(key, {"n": 0, "target": 0, "nontarget": 0, "values": [], "trial_types": []})
        d["n"] += 1
        if r.get("mapped_is_target") is True:
            d["target"] += 1
        elif r.get("mapped_is_target") is False:
            d["nontarget"] += 1
        if "mapped_value" in r:
            d["values"].append(r["mapped_value"])
        if "mapped_trial_type" in r:
            d["trial_types"].append(r["mapped_trial_type"])
    for d in by_bin.values():
        d["values"] = sorted(set(d["values"]))
        d["trial_types"] = sorted(set(d["trial_types"]))

    payload = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "model_blind": True,
        "signal_loaded": False,
        "purpose": "Resolve event/trial identity alignment among BIDS events, continuous preprocessed EEGLAB metadata, and artifact-rejected epoched z.set metadata before freezing the full representation analysis.",
        "representative_subject": "sub-01",
        "representative_session": "ses-1",
        "counts": {"bids_events": len(bids), "continuous_numeric_events": len(cont), "zset_kept_epochs": len(zrows)},
        "continuous_vs_bids": {
            "direct_code_matches": direct_code_matches,
            "n_compared": n_pair,
            "direct_code_match_fraction": direct_code_matches / n_pair if n_pair else None,
            "time_difference_seconds_first_n": time_diffs[:50],
            "time_difference_abs_median_seconds": sorted(abs(x) for x in time_diffs)[len(time_diffs)//2] if time_diffs else None,
            "bids_codes_first_50": bids_codes[:50],
            "continuous_codes_first_50": cont_codes[:50],
        },
        "zset_bepoch_mapping": {
            "all_bepoch_in_range": all("mapping_error" not in r for r in mapped),
            "kept_bepoch_values": [r["bepoch"] for r in mapped],
            "rejected_trial_indices_1based": [i for i in range(1, len(bids)+1) if i not in {r["bepoch"] for r in mapped}],
            "bin_summary_under_bepoch_to_bids_mapping": by_bin,
            "mapped_rows": mapped,
        },
        "decision_guardrails": [
            "No EEG signal values are loaded.",
            "No representation reliability, RSA, model embeddings, or model alignment are computed.",
            "The probe only determines whether published artifact-rejected epochs can be mapped prospectively to BIDS stimulus identities."
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(outdir / "summary.json")}, indent=2))


if __name__ == "__main__":
    main()

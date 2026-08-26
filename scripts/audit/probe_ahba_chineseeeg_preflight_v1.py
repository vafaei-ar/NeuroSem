#!/usr/bin/env python3
"""Model-blind AHBA/ChineseEEG spatial-mapping preflight.

This audit does not open EEG signal samples and does not compute any NeuroSem RSA,
reliability, model embedding, or molecular outcome. It inventories the software and
spatial metadata needed for the separately frozen AHBA transcriptomic extension.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import re
import subprocess
from pathlib import Path


def pkg_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def git_lines(root: Path, *args: str) -> list[str]:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        return []
    return [x for x in cp.stdout.splitlines() if x.strip()]


def annex_get_small(root: Path, rel: str) -> bool:
    p = root / rel
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        return True
    cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True, check=False)
    return cp.returncode == 0 and p.exists() and p.is_file() and p.stat().st_size > 0


def sha_text(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def finite_float(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def brainvision_channel_names(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    in_channels = False
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_channels = s.lower() == "[channel infos]"
            continue
        if not in_channels or not s or s.startswith(";"):
            continue
        m = re.match(r"Ch\d+=(.*)$", s, flags=re.I)
        if not m:
            continue
        first = m.group(1).split(",", 1)[0].strip()
        if first:
            out.append(first)
    return out


def standard_montage_overlap(channel_names: list[str]) -> list[dict]:
    try:
        import mne
    except Exception:
        return []
    ch = set(channel_names)
    rows = []
    for name in mne.channels.get_builtin_montages():
        try:
            mont = mne.channels.make_standard_montage(name)
        except Exception:
            continue
        mset = set(mont.ch_names)
        overlap = len(ch & mset)
        if overlap:
            rows.append({
                "montage": name,
                "overlap": overlap,
                "n_input_channels": len(ch),
                "n_montage_channels": len(mset),
                "input_fraction_matched": overlap / max(1, len(ch)),
            })
    return sorted(rows, key=lambda r: (-r["overlap"], r["montage"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_chineseeeg_preflight_v1/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    tracked = git_lines(root, "ls-files")
    small_suffixes = ("_electrodes.tsv", "_coordsystem.json", "_channels.tsv", "_eeg.json", ".vhdr")
    candidates = [p for p in tracked if p.lower().endswith(small_suffixes)]

    # Restrict the primary inventory to ChineseEEG reading sessions; no signal payload is opened.
    reading_candidates = [p for p in candidates if ("littleprince" in p.lower() or "garnettdream" in p.lower() or "granett" in p.lower())]

    electrode_rows = []
    coords_rows = []
    channel_rows = []
    vhdr_rows = []
    representative_channels = None

    for rel in reading_candidates:
        low = rel.lower()
        if not annex_get_small(root, rel):
            continue
        p = root / rel
        if low.endswith("_electrodes.tsv"):
            rows = read_tsv(p)
            fields = list(rows[0].keys()) if rows else []
            xyz = [c for c in fields if c.lower() in {"x", "y", "z"}]
            n_xyz = 0
            if len(xyz) == 3:
                n_xyz = sum(all(finite_float(r.get(c)) for c in xyz) for r in rows)
            electrode_rows.append({
                "path": rel,
                "n_rows": len(rows),
                "columns": ",".join(fields),
                "n_rows_with_finite_xyz": n_xyz,
            })
        elif low.endswith("_coordsystem.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                d = {}
            coords_rows.append({
                "path": rel,
                "keys": ",".join(sorted(d.keys())),
                "eeg_coordinate_system": str(d.get("EEGCoordinateSystem", "")),
                "eeg_coordinate_units": str(d.get("EEGCoordinateUnits", "")),
            })
        elif low.endswith("_channels.tsv"):
            rows = read_tsv(p)
            names = [str(r.get("name", "")).strip() for r in rows if str(r.get("name", "")).strip()]
            types = [str(r.get("type", "")).strip().upper() for r in rows]
            eeg_names = [str(r.get("name", "")).strip() for r in rows if str(r.get("type", "")).strip().upper() == "EEG" and str(r.get("name", "")).strip()]
            if representative_channels is None and len(eeg_names) >= 100:
                representative_channels = eeg_names
            channel_rows.append({
                "path": rel,
                "n_channels": len(names),
                "n_eeg_channels": sum(t == "EEG" for t in types),
                "channel_name_sha256": sha_text(names),
                "eeg_channel_name_sha256": sha_text(eeg_names),
            })
        elif low.endswith(".vhdr"):
            names = brainvision_channel_names(p)
            if representative_channels is None and len(names) >= 100:
                representative_channels = names
            vhdr_rows.append({
                "path": rel,
                "n_header_channels": len(names),
                "channel_name_sha256": sha_text(names),
            })

    montage_overlaps = standard_montage_overlap(representative_channels or [])
    packages = {name: pkg_version(name) for name in ["abagen", "mne", "nibabel", "nilearn", "numpy", "scipy"]}

    exact_coords_files = [r for r in electrode_rows if int(r["n_rows_with_finite_xyz"]) >= 100]
    top_montage = montage_overlaps[0] if montage_overlaps else None

    with (out / "spatial_metadata_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["kind", "path", "n_rows", "columns", "n_rows_with_finite_xyz", "keys", "eeg_coordinate_system", "eeg_coordinate_units", "n_channels", "n_eeg_channels", "n_header_channels", "channel_name_sha256", "eeg_channel_name_sha256"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in electrode_rows:
            w.writerow({"kind": "electrodes", **r})
        for r in coords_rows:
            w.writerow({"kind": "coordsystem", **r})
        for r in channel_rows:
            w.writerow({"kind": "channels", **r})
        for r in vhdr_rows:
            w.writerow({"kind": "brainvision_header", **r})

    with (out / "montage_overlap.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["montage", "overlap", "n_input_channels", "n_montage_channels", "input_fraction_matched"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(montage_overlaps)

    summary = {
        "schema_version": 1,
        "analysis": "model-blind AHBA/ChineseEEG spatial-mapping preflight",
        "loads_eeg_samples": False,
        "computes_neurosem_outcomes": False,
        "computes_model_embeddings": False,
        "computes_gene_expression_outcomes": False,
        "data_root": str(root),
        "software": packages,
        "tracked_file_count": len(tracked),
        "reading_small_metadata_candidate_count": len(reading_candidates),
        "n_electrode_files": len(electrode_rows),
        "n_coordsystem_files": len(coords_rows),
        "n_channel_files": len(channel_rows),
        "n_brainvision_headers": len(vhdr_rows),
        "exact_sensor_coordinate_files_with_at_least_100_xyz": exact_coords_files,
        "representative_channel_count": len(representative_channels or []),
        "representative_channel_name_sha256": sha_text(representative_channels or []),
        "top_standard_montage_overlap": top_montage,
        "preflight_gate": {
            "abagen_available": packages["abagen"] is not None,
            "exact_sensor_coordinates_available": bool(exact_coords_files),
            "channel_identity_available": bool(representative_channels),
            "ready_to_freeze_forward_model": bool(exact_coords_files and representative_channels),
            "ready_for_next_model_blind_ahba_step": True,
        },
        "next_model_blind_steps": [
            "If abagen is unavailable, pin/install a project version before AHBA preprocessing.",
            "Freeze exact ChineseEEG montage coordinates/reference and forward/source model without NeuroSem outcome access.",
            "Download/process AHBA with ibf_threshold=0.5 and frozen donor/bilateral/normalization choices.",
            "Construct the 128 x G molecular-sensitivity matrix before any molecular RSA test.",
        ],
        "guardrails": [
            "No EEG signal sample is opened.",
            "No neural reliability, RSA, model adapter, or model embedding is loaded.",
            "No AHBA map is selected based on a NeuroSem outcome.",
            "Standard-montage overlaps are diagnostic only and do not select a montage automatically.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "preflight_gate": summary["preflight_gate"], "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

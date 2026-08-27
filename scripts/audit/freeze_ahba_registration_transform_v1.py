#!/usr/bin/env python3
"""Model-blind construction and validation of the ChineseEEG head-to-fsaverage transform.

Uses only measured electrode/fiducial geometry plus fsaverage anatomy. It never
opens EEG signal samples, downloads AHBA, or computes NeuroSem/model/gene outcomes.
"""
from __future__ import annotations

import argparse, csv, json, math, subprocess
from pathlib import Path


def annex_get(root: Path, rel: str) -> Path:
    p = root / rel
    if not p.exists() or p.stat().st_size == 0:
        cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True)
        if cp.returncode != 0:
            raise RuntimeError(f"could not materialize {rel}: {cp.stderr[-1000:]}")
    return p


def read_electrodes(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    ch_pos = {}
    for r in rows:
        try:
            xyz = tuple(float(r[k]) for k in ("x", "y", "z"))
        except Exception:
            continue
        if len(xyz) == 3 and all(math.isfinite(v) for v in xyz):
            ch_pos[str(r.get("name", "")).strip()] = xyz
    return ch_pos


def get_fids(d: dict):
    src = d.get("AnatomicalLandmarkCoordinates") or d.get("FiducialsCoordinates") or d.get("FiducialCoordinates") or {}
    aliases = {"nasion": ["nasion", "nas", "nz", "fidnz"], "lpa": ["lpa", "leftpreauricular", "leftauricular", "fidt9"], "rpa": ["rpa", "rightpreauricular", "rightauricular", "fidt10"]}
    norm = lambda s: "".join(c for c in str(s).lower() if c.isalnum())
    out = {}
    for canon, names in aliases.items():
        for k, v in src.items():
            if norm(k) in names and isinstance(v, (list, tuple)) and len(v) == 3:
                out[canon] = tuple(float(x) for x in v)
    return out


def stats_mm(x):
    import numpy as np
    a = np.asarray(x, float) * 1000.0
    return {"n": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)), "p95": float(np.percentile(a, 95)), "max": float(a.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--source-freeze", type=Path, default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_registration_transform_freeze_v1/latest"))
    args = ap.parse_args()
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    root = args.data_root.resolve()
    prev = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    if not prev.get("ready_for_registration_implementation"):
        raise SystemExit("registration/source-model freeze gate is not ready")

    e_rel = prev["representative_electrode_path"]
    c_rel = e_rel.replace("_electrodes.tsv", "_coordsystem.json")
    e_path = annex_get(root, e_rel); c_path = annex_get(root, c_rel)
    ch_pos = read_electrodes(e_path)
    fids = get_fids(json.loads(c_path.read_text(encoding="utf-8")))
    if len(ch_pos) != 128 or set(fids) != {"nasion", "lpa", "rpa"}:
        raise SystemExit("expected exact 128-position geometry plus NAS/LPA/RPA")

    import numpy as np
    import mne
    from scipy.spatial import cKDTree
    fs_dir = Path(prev["template_resources"]["fsaverage_dir"])
    subjects_dir = fs_dir.parent
    montage = mne.channels.make_dig_montage(ch_pos=ch_pos, nasion=fids["nasion"], lpa=fids["lpa"], rpa=fids["rpa"], coord_frame="head")
    info = mne.create_info(list(ch_pos), sfreq=1.0, ch_types="eeg")
    info.set_montage(montage, on_missing="raise")

    coreg = mne.coreg.Coregistration(info, subject="fsaverage", subjects_dir=subjects_dir, fiducials="auto")
    coreg.fit_fiducials(verbose=False)
    trans_fid = coreg.trans.copy()
    scalp = mne.get_head_surf("fsaverage", subjects_dir=subjects_dir, verbose=False)
    scalp_rr = np.asarray(scalp["rr"], float)
    tree = cKDTree(scalp_rr)
    pts = np.array([ch_pos[n] for n in info.ch_names])
    fid_mri = mne.transforms.apply_trans(trans_fid, pts)
    fid_dist = tree.query(fid_mri, k=1)[0]

    # Rigid ICP only. No MRI scaling is allowed because downstream source space/BEM are frozen fsaverage resources.
    coreg.set_scale_mode(None)
    coreg.fit_icp(n_iterations=20, lpa_weight=1.0, nasion_weight=2.0, rpa_weight=1.0, hsp_weight=0.0, eeg_weight=1.0, hpi_weight=0.0, verbose=False)
    trans_icp = coreg.trans.copy()
    icp_mri = mne.transforms.apply_trans(trans_icp, pts)
    icp_dist = tree.query(icp_mri, k=1)[0]
    sf, si = stats_mm(fid_dist), stats_mm(icp_dist)

    # Prespecified conservative acceptance: median <= 7 mm, p95 <= 15 mm, max <= 25 mm,
    # and ICP must not worsen the median relative to fiducial-only alignment.
    passes = si["median"] <= 7.0 and si["p95"] <= 15.0 and si["max"] <= 25.0 and si["median"] <= sf["median"] + 1e-9
    trans_path = out / "chineseeeg-head-fsaverage-trans.fif"
    if passes:
        mne.write_trans(trans_path, trans_icp, overwrite=True)

    # Headless 2D alignment diagnostic.
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    labels = [(0,1,"X","Y"),(0,2,"X","Z"),(1,2,"Y","Z")]
    ss = scalp_rr[::max(1, len(scalp_rr)//5000)]
    for ax, (a,b,la,lb) in zip(axes, labels):
        ax.scatter(ss[:,a]*1000, ss[:,b]*1000, s=1, alpha=.15)
        ax.scatter(icp_mri[:,a]*1000, icp_mri[:,b]*1000, s=10)
        ax.set_xlabel(la+" mm"); ax.set_ylabel(lb+" mm"); ax.set_aspect("equal", adjustable="box")
    fig.suptitle(f"ChineseEEG measured sensors to fsaverage scalp | median={si['median']:.2f} mm, p95={si['p95']:.2f} mm")
    fig.tight_layout(); fig.savefig(out / "alignment_diagnostic.png", dpi=180); plt.close(fig)

    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA registration transform freeze v1",
        "loads_eeg_samples": False, "downloads_ahba": False,
        "computes_neurosem_outcomes": False, "computes_model_quantities": False, "computes_gene_expression_outcomes": False,
        "representative_electrode_path": e_rel, "coordsystem_path": c_rel,
        "n_eeg_positions": len(ch_pos), "fiducials": {k:list(v) for k,v in fids.items()},
        "method": {"initialization":"measured NAS/LPA/RPA fiducials", "refinement":"rigid MNE ICP using EEG electrode positions against fsaverage scalp", "mri_scaling":"disabled", "icp_iterations":20},
        "distance_mm": {"fiducial_only": sf, "rigid_icp": si},
        "acceptance_thresholds_mm": {"median_max":7.0, "p95_max":15.0, "max_max":25.0, "icp_median_must_not_worsen":True},
        "registration_transform_frozen": bool(passes),
        "transform_path": str(trans_path) if passes else None,
        "source_space_path": prev["template_resources"]["source_space_path"],
        "bem_solution_path": prev["template_resources"]["bem_solution_path"],
        "frozen_conventions": prev["frozen_conventions"],
        "blockers": [] if passes else ["Rigid measured-head-to-fsaverage alignment did not meet the prespecified sensor-to-scalp distance gate."],
        "next_step_if_pass": "Run model-blind AHBA expression preprocessing under the already-frozen abagen settings, then construct the 128 x G molecular-sensitivity matrix using this frozen transform/source model.",
        "guardrails": prev["guardrails"],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status":"frozen" if passes else "blocked", "registration_transform_frozen":passes, "distance_mm":payload["distance_mm"]}, indent=2))
    return 0 if passes else 2

if __name__ == "__main__": raise SystemExit(main())

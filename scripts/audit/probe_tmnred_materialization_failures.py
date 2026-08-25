#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

from scipy.io import loadmat, whosmat

try:
    import h5py
except Exception:
    h5py = None


def tracked(root: Path, rel: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", rel],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def header(path: Path, n=128):
    try:
        return path.read_bytes()[:n].hex()
    except Exception as exc:
        return f"ERROR:{type(exc).__name__}:{exc}"


def inspect_set(root: Path, subject: str, session: str) -> dict:
    set_rel = f"derivatives/preproc/{subject}/{session}/{subject}-{session}z.set"
    set_path = root / set_rel
    canonical_fdt_rel = f"derivatives/preproc/{subject}/{session}/{subject}-{session}z.fdt"
    canonical_fdt_path = root / canonical_fdt_rel
    rec = {
        "subject": subject,
        "session": session,
        "set_rel": set_rel,
        "set_exists": set_path.exists(),
        "set_tracked": tracked(root, set_rel),
        "set_size_bytes": set_path.stat().st_size if set_path.exists() else None,
        "set_header_hex": header(set_path) if set_path.exists() else None,
        "canonical_fdt_rel": canonical_fdt_rel,
        "canonical_fdt_tracked": tracked(root, canonical_fdt_rel),
        "canonical_fdt_exists": canonical_fdt_path.exists(),
        "canonical_fdt_size_bytes": canonical_fdt_path.stat().st_size if canonical_fdt_path.exists() else None,
    }
    try:
        rec["whosmat"] = [
            {"name": name, "shape": list(shape), "class": cls}
            for name, shape, cls in whosmat(set_path)
        ]
    except Exception as exc:
        rec["whosmat_error"] = f"{type(exc).__name__}: {exc}"
    try:
        d = loadmat(set_path, simplify_cells=True)
        eeg = d.get("EEG")
        rec["loadmat_ok"] = isinstance(eeg, dict)
        if isinstance(eeg, dict):
            for key in ["nbchan", "trials", "pnts", "srate", "xmin", "xmax", "data"]:
                v = eeg.get(key)
                if hasattr(v, "tolist"):
                    v = v.tolist()
                if isinstance(v, (str, int, float, bool)) or v is None:
                    rec[f"EEG_{key}"] = v
                elif hasattr(v, "shape"):
                    rec[f"EEG_{key}"] = {"shape": list(v.shape), "dtype": str(v.dtype)}
    except Exception as exc:
        rec["loadmat_ok"] = False
        rec["loadmat_error"] = f"{type(exc).__name__}: {exc}"
    if h5py is not None:
        try:
            rec["h5py_is_hdf5"] = bool(h5py.is_hdf5(set_path))
            if rec["h5py_is_hdf5"]:
                with h5py.File(set_path, "r") as h5:
                    rec["h5py_top_keys"] = list(h5.keys())[:50]
        except Exception as exc:
            rec["h5py_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_materialization_failure_probe/latest")
    args = ap.parse_args()
    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # One representative metadata-error subject plus one ordinary subject.
    subjects = ["sub-02", "sub-20", "sub-23", "sub-26", "sub-28", "sub-01"]
    records = [inspect_set(root, s, "ses-1") for s in subjects]
    payload = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "model_blind": True,
        "purpose": "Diagnose structural input-materialization failures without computing EEG reliability or model alignment.",
        "records": records,
        "notes": [
            "This probe does not compute neural features, RDM reliability, embeddings, or model RSA.",
            "It checks whether the published z.set files are classic MATLAB or HDF5, records exact scipy errors, and checks the canonical neighboring renamed z.fdt companion path."
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(outdir / 'summary.json')}, indent=2))


if __name__ == "__main__":
    main()

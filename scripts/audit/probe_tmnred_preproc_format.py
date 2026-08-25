#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

try:
    from scipy.io import whosmat, loadmat
except Exception as exc:
    raise SystemExit(f"scipy is required for TMNRED format probe: {exc}")


def annex_get(root: Path, rel: str) -> dict:
    p = root / rel
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", rel],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    rec = {"path": rel, "tracked": tracked, "materialized_before": p.exists()}
    if not tracked:
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
        rec["annex_get_stdout_tail"] = cp.stdout[-2000:]
        rec["annex_get_stderr_tail"] = cp.stderr[-2000:]
    rec["materialized_after"] = p.exists()
    rec["size_bytes"] = p.stat().st_size if p.exists() else None
    rec["status"] = "materialized" if p.exists() else "not_materializable"
    return rec


def mat_inventory(path: Path) -> dict:
    out = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return out
    try:
        out["variables"] = [
            {"name": name, "shape": list(shape), "class": cls}
            for name, shape, cls in whosmat(path)
        ]
    except Exception as exc:
        out["whosmat_error"] = repr(exc)
    return out


def summarize_value(v, depth=0):
    if depth > 3:
        return {"type": type(v).__name__, "truncated": True}
    if isinstance(v, dict):
        return {str(k): summarize_value(val, depth + 1) for k, val in list(v.items())[:80]}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if hasattr(v, "shape"):
        shape = list(getattr(v, "shape", ()))
        dtype = str(getattr(v, "dtype", type(v).__name__))
        if getattr(v, "size", 0) <= 30:
            try:
                val = v.tolist()
                return {"type": type(v).__name__, "shape": shape, "dtype": dtype, "value": val}
            except Exception:
                pass
        return {"type": type(v).__name__, "shape": shape, "dtype": dtype}
    if isinstance(v, (list, tuple)):
        return [summarize_value(x, depth + 1) for x in list(v)[:30]]
    return {"type": type(v).__name__, "repr": repr(v)[:500]}


def set_metadata(path: Path) -> dict:
    out = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return out
    try:
        d = loadmat(path, simplify_cells=True)
        eeg = d.get("EEG")
        if isinstance(eeg, dict):
            keep = {}
            for key in [
                "setname", "filename", "filepath", "subject", "group", "condition", "session",
                "nbchan", "trials", "pnts", "srate", "xmin", "xmax", "times", "ref",
                "chanlocs", "event", "epoch", "urevent", "data", "icaweights", "icasphere",
                "icawinv", "icaact", "etc"
            ]:
                if key in eeg:
                    keep[key] = summarize_value(eeg[key])
            out["EEG"] = keep
        else:
            out["top_level"] = summarize_value(d)
    except Exception as exc:
        out["loadmat_error"] = repr(exc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_preproc_format_probe/latest")
    args = ap.parse_args()

    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rels = [
        "derivatives/preproc/sub-01/sub-01.mat",
        "derivatives/preproc/sub-01/ses-1/sub-01-ses-1.set",
        "derivatives/preproc/sub-01/ses-1/sub-01-ses-1.fdt",
        "derivatives/preproc/sub-01/ses-1/sub-01-ses-1z.set",
        "derivatives/preproc/sub-01/ses-1/sub-01-ses-1z.fdt",
        "derivatives/preproc/sub-01/ses-1/sub-01-ses-1.erp",
    ]
    materialization = [annex_get(root, rel) for rel in rels]
    failed = [r for r in materialization if r.get("status") != "materialized"]

    payload = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "model_blind": True,
        "purpose": "Resolve the published preprocessed file semantics from one representative subject/session before freezing full signal-level representation analysis.",
        "representative_subject": "sub-01",
        "representative_session": "ses-1",
        "materialization": materialization,
        "subject_mat_inventory": mat_inventory(root / rels[0]),
        "session_set_metadata": set_metadata(root / rels[1]),
        "session_zset_metadata": set_metadata(root / rels[3]),
        "session_erp_inventory": mat_inventory(root / rels[5]),
        "notes": [
            "No model embeddings, RSA scores, neural-representation reliability, or candidate selection are computed.",
            "The .fdt payloads are materialized only as companions for the representative EEGLAB metadata files and are not exported as artifacts.",
            "Only this small representative set is materialized; the full TMNRED signal cohort remains untouched until the analysis source is frozen."
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit(f"Representative TMNRED preprocessed files unavailable: {failed}")
    print(json.dumps({"status": "ok", "output": str(outdir / 'summary.json')}, indent=2))


if __name__ == "__main__":
    main()

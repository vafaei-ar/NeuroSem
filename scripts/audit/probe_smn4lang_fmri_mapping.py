#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

DATASET = "ds004078"
S3_BUCKET = "openneuro.org"


def run_capture(cmd: list[str], cwd: Path | None = None) -> dict:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def materialized(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    except OSError:
        return False


def direct_s3_get(root: Path, rel: str) -> dict:
    dest = root / rel
    if materialized(dest):
        return {"method": "already_materialized", "path": rel, "size_bytes": dest.stat().st_size}

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()

    attempts: list[dict] = []
    s3_uri = f"s3://{S3_BUCKET}/{DATASET}/{rel}"
    https_url = f"https://s3.amazonaws.com/{S3_BUCKET}/{DATASET}/{rel}"

    if shutil.which("aws"):
        attempt = run_capture(["aws", "s3", "cp", "--no-sign-request", s3_uri, str(dest)])
        attempts.append(attempt)
        if attempt["returncode"] == 0 and materialized(dest):
            return {"method": "aws_s3_public", "path": rel, "size_bytes": dest.stat().st_size, "attempts": attempts}
        if dest.exists() or dest.is_symlink():
            dest.unlink()

    if shutil.which("curl"):
        attempt = run_capture([
            "curl", "--fail", "--location", "--retry", "3", "--retry-delay", "2",
            "--output", str(dest), https_url,
        ])
        attempts.append(attempt)
        if attempt["returncode"] == 0 and materialized(dest):
            return {"method": "https_public_s3", "path": rel, "size_bytes": dest.stat().st_size, "attempts": attempts}
        if dest.exists() or dest.is_symlink():
            dest.unlink()

    raise RuntimeError(json.dumps({
        "path": rel,
        "s3_uri": s3_uri,
        "https_url": https_url,
        "attempts": attempts,
        "aws_available": bool(shutil.which("aws")),
        "curl_available": bool(shutil.which("curl")),
    }, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_fmri_mapping_probe/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    story = 1
    materialize = [
        f"derivatives/annotations/scripts/story_{story}.txt",
        f"derivatives/annotations/time_align/word-level/story_{story}_word_time.mat",
        f"derivatives/annotations/time_align/char-level/story_{story}_char_time.mat",
        f"derivatives/preprocessed_data/sub-01/CIFTI/sub-01_task-RDR_run-{story}_bold.dtseries.nii",
    ]

    downloads = {}
    try:
        for rel in materialize:
            downloads[rel] = direct_s3_get(root, rel)
    except Exception as exc:
        payload = {
            "schema_version": 4,
            "dataset": "SMN4Lang / OpenNeuro ds004078",
            "probe_subject": "sub-01",
            "probe_run_story": story,
            "status": "materialization_failed",
            "download_method": "public_openneuro_s3",
            "completed_downloads": downloads,
            "error": str(exc),
            "model_blind": True,
            "no_neural_model_outcomes": True,
        }
        (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": "materialization_failed", "error": str(exc)[:1000]}, indent=2))
        return 2

    try:
        import numpy as np
        import nibabel as nib
        from scipy.io import loadmat

        cifti_path = root / materialize[-1]
        img = nib.load(str(cifti_path))
        shape = list(img.shape)
        hdr = img.header
        axis0 = hdr.get_axis(0)
        axis1 = hdr.get_axis(1)
        series = axis0 if hasattr(axis0, "step") else axis1 if hasattr(axis1, "step") else None
        brain = axis1 if series is axis0 else axis0

        text = (root / materialize[0]).read_text(encoding="utf-8", errors="replace")
        word_mat = loadmat(root / materialize[1], simplify_cells=True)
        char_mat = loadmat(root / materialize[2], simplify_cells=True)

        raw_event_candidates = sorted(root.glob(f"sub-01/**/sub-01_task-RDR_run-{story}_events.tsv"))
        tracked_event_info = []
        for p in raw_event_candidates:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                tracked_event_info.append({"path": str(p.relative_to(root)), "head": txt.splitlines()[:8]})
            except Exception as exc:
                tracked_event_info.append({"path": str(p.relative_to(root)), "error": str(exc)})

        def mat_summary(d):
            outd = {}
            for k, v in d.items():
                if k.startswith("__"):
                    continue
                arr = np.asarray(v, dtype=object)
                outd[k] = {"type": type(v).__name__, "shape": list(arr.shape), "sample": repr(v)[:1000]}
            return outd

        payload = {
            "schema_version": 4,
            "dataset": "SMN4Lang / OpenNeuro ds004078",
            "probe_subject": "sub-01",
            "probe_run_story": story,
            "status": "ok",
            "download_method": "public_openneuro_s3",
            "downloads": downloads,
            "materialized_paths": materialize,
            "story_text_n_chars": len(text),
            "story_text_preview": text[:1000],
            "word_timing": mat_summary(word_mat),
            "char_timing": mat_summary(char_mat),
            "cifti_shape": shape,
            "cifti_dtype": str(img.get_data_dtype()),
            "cifti_series_start": None if series is None else float(series.start),
            "cifti_series_step": None if series is None else float(series.step),
            "cifti_series_unit": None if series is None else str(series.unit),
            "cifti_n_brainordinates": None if brain is None else int(len(brain)),
            "raw_event_candidates": tracked_event_info,
            "model_blind": True,
            "no_neural_model_outcomes": True,
        }
        (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ok", "shape": shape, "series_step": payload["cifti_series_step"]}, indent=2))
        return 0
    except Exception as exc:
        payload = {
            "schema_version": 4,
            "dataset": "SMN4Lang / OpenNeuro ds004078",
            "probe_subject": "sub-01",
            "probe_run_story": story,
            "status": "inspection_failed_after_materialization",
            "download_method": "public_openneuro_s3",
            "downloads": downloads,
            "error": repr(exc),
            "model_blind": True,
            "no_neural_model_outcomes": True,
        }
        (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": "inspection_failed_after_materialization", "error": repr(exc)}, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

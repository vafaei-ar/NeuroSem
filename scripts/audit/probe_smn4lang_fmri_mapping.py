#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, subprocess
from pathlib import Path


def run_capture(cmd: list[str], root: Path) -> dict:
    p = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-5000:],
        "stderr": p.stderr[-5000:],
    }


def ensure_annex_initialized(root: Path) -> dict:
    before = run_capture(["git", "annex", "info"], root)
    init = None
    if before["returncode"] != 0 and "First run: git-annex init" in before["stderr"]:
        init = run_capture(["git", "annex", "init", "neurosem-smn4lang-probe"], root)
        if init["returncode"] != 0:
            raise RuntimeError(json.dumps({"stage": "git_annex_init", "before": before, "init": init}, indent=2))
    enable_public = run_capture(["git", "annex", "enableremote", "s3-PUBLIC"], root)
    after = run_capture(["git", "annex", "info"], root)
    return {"before": before, "init": init, "enable_s3_public": enable_public, "after": after}


def annex_get(root: Path, rel: str) -> str:
    attempts = [
        ["git", "annex", "get", "--from", "s3-PUBLIC", rel],
        ["git", "annex", "get", rel],
    ]
    errors = []
    for cmd in attempts:
        p = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
        if p.returncode == 0:
            return " ".join(cmd)
        errors.append({"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]})
    whereis = run_capture(["git", "annex", "whereis", rel], root)
    remotes = run_capture(["git", "annex", "info"], root)
    raise RuntimeError(json.dumps({"path": rel, "attempts": errors, "whereis": whereis, "annex_info": remotes}, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_fmri_mapping_probe/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve(); out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)

    story = 1
    materialize = [
        f"derivatives/annotations/scripts/story_{story}.txt",
        f"derivatives/annotations/time_align/word-level/story_{story}_word_time.mat",
        f"derivatives/annotations/time_align/char-level/story_{story}_char_time.mat",
        f"derivatives/preprocessed_data/sub-01/CIFTI/sub-01_task-RDR_run-{story}_bold.dtseries.nii",
    ]

    try:
        annex_setup = ensure_annex_initialized(root)
        materialization_commands = {}
        for rel in materialize:
            materialization_commands[rel] = annex_get(root, rel)
    except Exception as exc:
        failure = {
            "schema_version": 3,
            "dataset": "SMN4Lang / OpenNeuro ds004078",
            "probe_subject": "sub-01",
            "probe_run_story": story,
            "status": "materialization_failed",
            "error": str(exc),
            "model_blind": True,
            "no_neural_model_outcomes": True,
        }
        (out / "summary.json").write_text(json.dumps(failure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": "materialization_failed"}, indent=2))
        return 2

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
        except Exception as e:
            tracked_event_info.append({"path": str(p.relative_to(root)), "error": str(e)})

    def mat_summary(d):
        outd = {}
        for k, v in d.items():
            if k.startswith("__"):
                continue
            arr = np.asarray(v, dtype=object)
            outd[k] = {"type": type(v).__name__, "shape": list(arr.shape), "sample": repr(v)[:1000]}
        return outd

    payload = {
        "schema_version": 3,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "probe_subject": "sub-01",
        "probe_run_story": story,
        "status": "ok",
        "annex_setup": annex_setup,
        "materialized_paths": materialize,
        "materialization_commands": materialization_commands,
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
    print(json.dumps({"status":"ok","shape":shape,"series_step":payload["cifti_series_step"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

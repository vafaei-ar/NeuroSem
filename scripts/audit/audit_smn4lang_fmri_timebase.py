#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import struct
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import loadmat

BASE = "https://s3.amazonaws.com/openneuro.org/ds004078"
SUBJECTS = [f"sub-{i:02d}" for i in range(1, 13)]
STORIES = list(range(1, 61))
N_BRAINORDINATES = 91282
TR = 0.71
REPRESENTATIVE_SIZE = 224_821_936
REPRESENTATIVE_N_TP = 614
HEADER_BYTES = REPRESENTATIVE_SIZE - REPRESENTATIVE_N_TP * N_BRAINORDINATES * 4


def get_bytes(rel: str) -> bytes:
    with urllib.request.urlopen(f"{BASE}/{rel}", timeout=120) as r:
        return r.read()


def head_size(rel: str) -> int:
    req = urllib.request.Request(f"{BASE}/{rel}", method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def parse_tsv(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def infer_n_tp(size: int) -> int | None:
    payload = size - HEADER_BYTES
    stride = N_BRAINORDINATES * 4
    if payload <= 0 or payload % stride != 0:
        return None
    return payload // stride


def mat_vec(d: dict, key: str) -> np.ndarray:
    return np.asarray(d[key]).reshape(-1)


def materialize_small_file(root: Path, rel: str) -> Path:
    local = root / rel
    local.parent.mkdir(parents=True, exist_ok=True)
    # The metadata checkout contains broken git-annex symlinks for files whose
    # payloads were not materialized. Path.exists() is false for those symlinks,
    # but write_bytes() would follow the dangling target and fail. Replace the
    # symlink with the public OpenNeuro S3 payload explicitly.
    if local.is_symlink():
        local.unlink()
    if not local.exists() or local.stat().st_size == 0:
        local.write_bytes(get_bytes(rel))
    return local


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_fmri_timebase_audit/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    story_rows = []
    timing_cache: dict[int, dict] = {}
    for story in STORIES:
        rel = f"derivatives/annotations/time_align/word-level/story_{story}_word_time.mat"
        local = materialize_small_file(root, rel)
        d = loadmat(local, simplify_cells=True)
        starts = mat_vec(d, "start").astype(float)
        ends = mat_vec(d, "end").astype(float)
        words = np.asarray(d["word"]).reshape(-1).astype(str)
        timing_cache[story] = {"start": starts, "end": ends, "word": words}
        story_rows.append({
            "story": story,
            "n_words": int(len(words)),
            "first_word_start": float(starts[0]),
            "last_word_end": float(ends[-1]),
            "monotonic_start": bool(np.all(np.diff(starts) >= 0)),
            "nonnegative_duration": bool(np.all(ends >= starts)),
        })

    run_rows = []
    failures = []
    for sub in SUBJECTS:
        for story in STORIES:
            cifti_rel = f"derivatives/preprocessed_data/{sub}/CIFTI/{sub}_task-RDR_run-{story}_bold.dtseries.nii"
            event_rel = f"{sub}/func/{sub}_task-RDR_run-{story}_events.tsv"
            try:
                size = head_size(cifti_rel)
                n_tp = infer_n_tp(size)
                events = parse_tsv(get_bytes(event_rel))
                audio_rows = [r for r in events if str(r.get("stim_file", "")).endswith(f"story_{story}.wav")]
                if len(audio_rows) != 1:
                    raise RuntimeError(f"expected one story audio event, got {len(audio_rows)}")
                ev = audio_rows[0]
                onset = float(ev["onset"])
                duration = float(ev["duration"])
                scan_end = (n_tp - 1) * TR if n_tp is not None else None
                wt = timing_cache[story]
                first_word = float(wt["start"][0])
                last_word = float(wt["end"][-1])
                run_rows.append({
                    "subject": sub,
                    "story": story,
                    "cifti_size_bytes": size,
                    "n_timepoints_inferred": n_tp,
                    "tr_seconds": TR,
                    "scan_last_sample_seconds": scan_end,
                    "audio_onset": onset,
                    "audio_duration": duration,
                    "audio_end": onset + duration,
                    "first_word_start": first_word,
                    "last_word_end": last_word,
                    "first_word_minus_audio_onset": first_word - onset,
                    "audio_end_minus_last_word": onset + duration - last_word,
                    "words_inside_audio_event": bool(first_word >= onset and last_word <= onset + duration + 1e-6),
                    "audio_inside_scan": bool(scan_end is not None and onset >= 0 and onset + duration <= scan_end + TR + 1e-6),
                })
            except Exception as e:
                failures.append({"subject": sub, "story": story, "error": repr(e)})

    def unique_vals(key: str):
        vals = sorted({r[key] for r in run_rows if r.get(key) is not None})
        return vals

    per_story_n_tp = {}
    per_story_onsets = {}
    per_story_durations = {}
    for story in STORIES:
        rr = [r for r in run_rows if r["story"] == story]
        per_story_n_tp[str(story)] = sorted({r["n_timepoints_inferred"] for r in rr})
        per_story_onsets[str(story)] = sorted({round(r["audio_onset"], 6) for r in rr})
        per_story_durations[str(story)] = sorted({round(r["audio_duration"], 6) for r in rr})

    all_story_timing_ok = all(r["monotonic_start"] and r["nonnegative_duration"] for r in story_rows)
    all_runs_present = len(run_rows) == len(SUBJECTS) * len(STORIES) and not failures
    all_n_tp_inferred = all(r["n_timepoints_inferred"] is not None for r in run_rows)
    within_story_tp_identical = all(len(v) == 1 for v in per_story_n_tp.values())
    within_story_onset_identical = all(len(v) == 1 for v in per_story_onsets.values())
    within_story_duration_identical = all(len(v) == 1 for v in per_story_durations.values())
    all_words_inside_audio = all(r["words_inside_audio_event"] for r in run_rows)
    all_audio_inside_scan = all(r["audio_inside_scan"] for r in run_rows)
    gate = all([
        all_story_timing_ok,
        all_runs_present,
        all_n_tp_inferred,
        within_story_tp_identical,
        within_story_onset_identical,
        within_story_duration_identical,
        all_words_inside_audio,
        all_audio_inside_scan,
    ])

    summary = {
        "schema_version": 2,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_subjects": len(SUBJECTS),
        "n_stories": len(STORIES),
        "expected_runs": len(SUBJECTS) * len(STORIES),
        "observed_runs": len(run_rows),
        "n_failures": len(failures),
        "timing_materialization": "public_openneuro_s3_replace_annex_symlink",
        "tr_seconds_locked_from_probe": TR,
        "n_brainordinates_locked_from_probe": N_BRAINORDINATES,
        "header_bytes_calibrated_from_probe": HEADER_BYTES,
        "checks": {
            "all_story_word_timings_monotonic_nonnegative": all_story_timing_ok,
            "all_720_runs_present": all_runs_present,
            "all_cifti_timepoints_inferred": all_n_tp_inferred,
            "within_story_timepoints_identical_across_12_subjects": within_story_tp_identical,
            "within_story_audio_onset_identical_across_12_subjects": within_story_onset_identical,
            "within_story_audio_duration_identical_across_12_subjects": within_story_duration_identical,
            "all_word_timings_inside_audio_event": all_words_inside_audio,
            "all_audio_events_inside_scan": all_audio_inside_scan,
        },
        "structural_timebase_gate": gate,
        "n_timepoints_unique_global": unique_vals("n_timepoints_inferred"),
        "per_story_n_timepoints": per_story_n_tp,
        "per_story_audio_onsets": per_story_onsets,
        "per_story_audio_durations": per_story_durations,
        "story_word_counts": {str(r["story"]): r["n_words"] for r in story_rows},
        "failures": failures[:50],
    }

    with (out / "run_timebase.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(run_rows[0].keys()) if run_rows else ["subject", "story"])
        w.writeheader(); w.writerows(run_rows)
    with (out / "story_timing.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(story_rows[0].keys()))
        w.writeheader(); w.writerows(story_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok" if gate else "structural_gate_failed", "observed_runs": len(run_rows), "failures": len(failures), "gate": gate}, indent=2))
    return 0 if gate else 2


if __name__ == "__main__":
    raise SystemExit(main())

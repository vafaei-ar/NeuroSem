#!/usr/bin/env python3
"""Materialize the frozen structured non-neural MPNet source targets, v2.

This implementation mirrors the neural-target builder's participant-specific nuisance
residualization. It uses source text and source metadata only, never EEG feature arrays,
neural target values, external targets, transfer outcomes, or manuscript results.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist

REPO_ROOT = Path(__file__).resolve().parents[2]
V1_PATH = REPO_ROOT / "scripts/robustness/materialize_nmi_alternative_signal_mpnet_v1.py"

spec = importlib.util.spec_from_file_location("mpnet_materializer_v1", V1_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load base materializer from {V1_PATH}")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)


def canonical_source_subjectwise(run_number: int) -> tuple[list[str], dict[str, list[dict[str, str]]], dict]:
    d = v1.latest_dir(v1.SOURCE_TARGET_ROOT / f"run-{run_number:02d}", "texts.json")
    texts = json.loads((d / "texts.json").read_text(encoding="utf-8"))
    summary = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    feature_dirs = summary.get("feature_dirs") or {}
    if not feature_dirs:
        raise RuntimeError(f"run {run_number}: source target summary lacks feature_dirs")

    reference_embedding_idx = None
    reference_chapters = None
    subject_rows: dict[str, list[dict[str, str]]] = {}
    checked = []

    for subject, raw_dir in sorted(feature_dirs.items()):
        fd = v1.resolve_feature_dir(str(raw_dir))
        rows = v1.read_csv(fd / "metadata.csv")
        row_texts = [r["text"] for r in rows]
        embedding_idx = [int(r["embedding_index"]) for r in rows]
        chapters = np.asarray(
            [int((r.get("chapter_marker_context") or "CH00")[2:]) for r in rows],
            dtype=int,
        )
        if row_texts != texts:
            raise RuntimeError(f"run {run_number}: text identity mismatch for {subject}")
        if reference_embedding_idx is None:
            reference_embedding_idx = embedding_idx
            reference_chapters = chapters
        elif embedding_idx != reference_embedding_idx or not np.array_equal(chapters, reference_chapters):
            raise RuntimeError(f"run {run_number}: canonical row identity mismatch for {subject}")

        subject_rows[subject] = rows
        checked.append({"subject": subject, "metadata_path": str(fd / "metadata.csv")})

    if len(subject_rows) < 3:
        raise RuntimeError(f"run {run_number}: need >=3 aligned source participants")

    provenance = {
        "source_target_dir": str(d),
        "source_target_summary_sha256": v1.sha256(d / "summary.json"),
        "source_texts_sha256": v1.sha256(d / "texts.json"),
        "metadata_subjects_checked": checked,
        "participant_specific_nuisance_residualization": True,
    }
    return texts, subject_rows, provenance


def main() -> int:
    import torch
    from transformers import AutoModel, AutoTokenizer

    v1.OUT.mkdir(parents=True, exist_ok=True)
    v1.atomic_progress(0, len(v1.RUNS), "load-model", "loading exact MPNet revision from prior model-family freeze")

    model_id, revision = v1.frozen_panel_revision()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True)
        model = AutoModel.from_pretrained(model_id, revision=revision, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            "Exact prior-panel MPNet revision is not available in the local Hugging Face cache; "
            "refusing to fall back to a mutable network revision"
        ) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    manifest_rows = []
    run_summaries = []
    for idx, run_number in enumerate(v1.RUNS, start=1):
        texts, subject_rows, source_provenance = canonical_source_subjectwise(run_number)
        emb = v1.encode(model, tokenizer, texts, device)
        if emb.shape[0] != len(texts) or not np.isfinite(emb).all():
            raise RuntimeError(f"run {run_number}: invalid MPNet embedding matrix")

        model_rdm = pdist(emb, metric="cosine")
        participant_residuals = []
        for subject, rows in subject_rows.items():
            nuisances = v1.nuisances_from_metadata(texts, rows)
            residual = v1.residualize_ranked(model_rdm, nuisances)
            participant_residuals.append(residual)

        target = np.mean(np.stack(participant_residuals, axis=0), axis=0)
        target -= target.mean()
        sd = target.std()
        if sd == 0:
            raise RuntimeError(f"run {run_number}: zero-variance averaged residual target")
        target /= sd
        if not np.isfinite(target).all() or abs(float(target.mean())) > 1e-10 or not np.isclose(float(target.std()), 1.0, atol=1e-8):
            raise RuntimeError(f"run {run_number}: target standardization invariant failed")

        run_dir = v1.OUT / f"run_{run_number:02d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        target_path = run_dir / "structured_nonneural_target.npy"
        texts_path = run_dir / "texts.json"
        np.save(target_path, target.astype(np.float32))
        texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2), encoding="utf-8")

        run_summary = {
            "run_number": run_number,
            "n_rows": len(texts),
            "n_edges": int(len(target)),
            "n_source_participants": len(subject_rows),
            "source_participants": sorted(subject_rows),
            "alternative_target_model_id": model_id,
            "alternative_target_model_revision": revision,
            "revision_source": str(v1.PANEL_RESOLVED_MODELS),
            "pooling": "attention-mask mean final hidden state; L2-normalized",
            "max_length": v1.MAX_LENGTH,
            "model_rdm": "cosine distance",
            "target_transform": (
                "same MPNet rank-z RDM residualized separately against each source participant's six nuisance RDMs; "
                "participant residuals averaged; run-level mean z-standardized"
            ),
            "nuisances": v1.NUISANCE_LABELS,
            "target_mean_float64_before_float32_save": float(target.mean()),
            "target_std_float64_before_float32_save": float(target.std()),
            "source_provenance": source_provenance,
        }
        summary_path = run_dir / "summary.json"
        summary_path.write_text(json.dumps(run_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        run_summary["target_sha256"] = v1.sha256(target_path)
        run_summary["texts_sha256"] = v1.sha256(texts_path)
        run_summaries.append(run_summary)
        manifest_rows.append({
            "run": run_number,
            "n_rows": len(texts),
            "n_edges": len(target),
            "n_source_participants": len(subject_rows),
            "model_revision": revision,
            "target_sha256": v1.sha256(target_path),
            "texts_sha256": v1.sha256(texts_path),
        })
        v1.atomic_progress(idx, len(v1.RUNS), "materialize-targets", f"completed source run {run_number:02d}")

    summary = {
        "schema_version": 2,
        "status": "ok",
        "analysis_stage": "post-confirmatory alternative-signal target materialization",
        "protocol": v1.PROTOCOL,
        "alternative_signal_type": "structured item-linked non-neural multilingual-MPNet geometry",
        "model_id": model_id,
        "model_revision": revision,
        "revision_source": str(v1.PANEL_RESOLVED_MODELS),
        "runs": v1.RUNS,
        "participant_specific_nuisance_residualization": True,
        "guardrails": {
            "eeg_feature_arrays_read": False,
            "neural_target_values_read": False,
            "external_target_data_read": False,
            "transfer_outcomes_read": False,
            "e5_training_performed": False,
            "external_evaluation_performed": False,
        },
        "run_summaries": run_summaries,
    }
    (v1.OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    v1.write_csv(v1.OUT / "target_manifest.csv", manifest_rows)
    (v1.OUT / "report.txt").write_text(
        "NeuroSem alternative-signal MPNet target materialization v2\n\n"
        f"Model: {model_id}\nRevision: {revision}\n"
        f"Revision source: {v1.PANEL_RESOLVED_MODELS}\n"
        "Runs: 01-06\n"
        "Target: item-linked MPNet geometry residualized separately against each contributing source participant's six nuisance RDMs, then averaged and z-standardized.\n"
        "This mirrors the participant-specific nuisance procedure used by the neural target builder.\n"
        "No EEG feature arrays, neural target values, external outcomes, E5 training or external evaluation were read/performed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "model_revision": revision, "runs": v1.RUNS}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

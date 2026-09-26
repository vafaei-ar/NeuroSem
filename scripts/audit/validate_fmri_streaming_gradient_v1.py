#!/usr/bin/env python3
"""Numerically validate the memory-efficient fMRI gradient factorization.

This is an engineering equivalence test, not a scientific compatibility analysis.
It compares the original one-pass parameter gradient with the new two-pass chain-rule
VJP on one already-frozen fMRI story and one participant. No ChineseEEG source gradient
or source-target compatibility cosine is computed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.robustness.target_gradient_common_v1 import (
    load_reference_model,
    loss_from_model_edges,
    standard_design_from_columns,
)
from scripts.robustness.run_target_gradient_compatibility_v1 import (
    accumulate_embedding_vjps,
    fmri_embedding_gradients,
    torch_fmri_edges_fullgraph,
)
from scripts.analysis.run_smn4lang_fmri_reliability import (
    SUBJECTS,
    STORIES,
    TR,
    canonical_hrf,
)
from scripts.tuning import evaluate_smn4lang_fmri_e5_transfer_v1 as fmri_eval
from scripts.robustness import run_nmi_bidirectional_model_family_panel_v1 as family_panel

OUT = ROOT / "outputs/fmri_streaming_gradient_validation_v1/latest"


def flatten(grads):
    import torch
    return torch.cat([g.detach().reshape(-1).float().cpu() for g in grads])


def main() -> int:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required for fMRI gradient validation")
    device = "cuda"
    OUT.mkdir(parents=True, exist_ok=True)

    story = int(STORIES[0])
    subject = str(SUBJECTS[0])
    hrf = canonical_hrf(TR)
    ctx = fmri_eval.story_context((ROOT / "data/raw/smn4lang").resolve(), story, hrf)
    A = standard_design_from_columns(list(ctx["nuisance"]))

    cache = ROOT / family_panel.FMRI_CACHE
    done = cache / "_COMPLETE.json"
    if not done.is_file():
        raise RuntimeError("fMRI cache is not materialized")
    npz = np.load(cache / f"story_{story:02d}.npz")
    neural = np.asarray(npz[subject.replace("-", "_")], dtype=np.float64)
    npz.close()

    tok, model, named = load_reference_model(device)
    params = [p for _, p in named]

    # Original one-pass gradient.
    edges, emb = torch_fmri_edges_fullgraph(model, tok, ctx, hrf, device)
    loss, _ = loss_from_model_edges(edges, neural, A)
    g_full = flatten(torch.autograd.grad(loss, params, retain_graph=False, create_graph=False, allow_unused=False))
    del loss, edges, emb
    torch.cuda.empty_cache()

    # New two-pass chain-rule gradient.
    n_params = int(sum(p.numel() for p in params))
    accum = {subject: torch.zeros(n_params, dtype=torch.float32, device="cpu")}
    emb_grads = fmri_embedding_gradients(model, tok, ctx, hrf, A, {subject: neural}, device)
    accumulate_embedding_vjps(
        model,
        tok,
        list(ctx["prefixes"]),
        named,
        emb_grads,
        accum,
        device,
        batch_size=8,
    )
    g_stream = accum[subject]

    diff = g_stream.double() - g_full.double()
    full_norm = float(torch.linalg.vector_norm(g_full.double()))
    stream_norm = float(torch.linalg.vector_norm(g_stream.double()))
    diff_norm = float(torch.linalg.vector_norm(diff))
    rel_l2 = diff_norm / full_norm
    cosine = float(torch.dot(g_full.double(), g_stream.double()) / (full_norm * stream_norm))
    max_abs = float(torch.max(torch.abs(diff)))

    # Tolerance is much tighter than needed for sign/direction equivalence while
    # allowing small deterministic floating-point differences from recomputation.
    passed = bool(cosine > 0.999999 and rel_l2 < 5e-4)

    payload = {
        "schema_version": 1,
        "status": "ok" if passed else "failed",
        "analysis_type": "engineering gradient-equivalence validation only",
        "story": story,
        "subject": subject,
        "n_prefixes": len(ctx["prefixes"]),
        "one_pass_norm": full_norm,
        "streamed_norm": stream_norm,
        "difference_norm": diff_norm,
        "relative_l2_error": rel_l2,
        "cosine_similarity": cosine,
        "max_absolute_parameter_error": max_abs,
        "acceptance_rule": "cosine > 0.999999 and relative_l2_error < 5e-4",
        "passed": passed,
        "scientific_compatibility_outcome_computed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "fMRI streamed-gradient engineering validation\n"
        f"story={story} subject={subject}\n"
        f"cosine={cosine:.12g}\n"
        f"relative_l2_error={rel_l2:.12g}\n"
        f"max_abs={max_abs:.12g}\n"
        f"passed={passed}\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

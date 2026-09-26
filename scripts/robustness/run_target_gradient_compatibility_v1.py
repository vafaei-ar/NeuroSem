#!/usr/bin/env python3
"""Stage 2 target-gradient compatibility for one frozen NeuroSem target.

The target class and gradient definition were frozen in
docs/TARGET_COMPATIBILITY_MECHANISM_V1.md before any values from this script are
computed. Each invocation evaluates exactly one member of the five-target primary
mechanism set.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.robustness.target_gradient_common_v1 import (
    BOOTSTRAP_N,
    BOOTSTRAP_SEED,
    accumulate_autograd_loss,
    bootstrap_mean_ci,
    compute_source_gradient,
    encode_grad,
    load_reference_model,
    loss_from_model_edges,
    pairwise_cosine_distance_torch,
    parameter_manifest,
    ranked_design_from_columns,
    residualize_np,
    standard_design_from_columns,
)
from scripts.analysis import run_zuco2_nr_primary_representation_reliability as zuco
from scripts.tuning import evaluate_tmnred_e5_transfer_v1 as tmn
from scripts.tuning import evaluate_garnett_dream_e5_transfer_v1 as gar
from scripts.analysis import run_garnett_dream_primary_reliability as garrel
from scripts.analysis.run_smn4lang_fmri_reliability import (
    SUBJECTS as FMRI_SUBJECTS,
    STORIES as FMRI_STORIES,
    TR as FMRI_TR,
    canonical_hrf,
)
from scripts.tuning import evaluate_smn4lang_fmri_e5_transfer_v1 as fmri_eval
from scripts.robustness import run_nmi_bidirectional_model_family_panel_v1 as family_panel

PROTOCOL = "docs/TARGET_COMPATIBILITY_MECHANISM_V1.md"
TARGET_CLASS = {
    "zuco": "reliable-positive",
    "smn4lang_fmri": "reliable-positive",
    "derco": "reliable-negative",
    "tmnred": "reliable-null/inconclusive",
    "garnett_dream": "reliable-null/inconclusive",
}
DERCO_EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")


def write_progress(current: int, total: int, target: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    d = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else 0.0,
        "phase": f"gradient-{target}",
        "message": message,
        "unit": "target units",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(d) + "\n", encoding="utf-8")
    tmp.replace(p)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def new_accumulators(participants: list[str], n_params: int):
    import torch
    return {s: torch.zeros(n_params, dtype=torch.float32, device="cpu") for s in participants}


def finalize(source, accum, unit_counts: dict[str, int]) -> tuple[list[dict], dict]:
    import torch
    rows = []
    src = source.double()
    src_norm = float(torch.linalg.vector_norm(src))
    for sub in sorted(accum):
        g = accum[sub].double()
        gn = float(torch.linalg.vector_norm(g))
        if gn <= 0 or not np.isfinite(gn):
            raise RuntimeError(f"{sub}: degenerate target gradient")
        dot = float(torch.dot(src, g))
        cos = dot / (src_norm * gn)
        rows.append({
            "participant": sub,
            "n_units": int(unit_counts[sub]),
            "source_dot_target": dot,
            "target_gradient_norm": gn,
            "gradient_cosine": cos,
        })
    vals = [float(r["gradient_cosine"]) for r in rows]
    summary = {
        "n_participants": len(vals),
        "mean_gradient_cosine": float(np.mean(vals)),
        "median_gradient_cosine": float(np.median(vals)),
        "n_positive": int(np.sum(np.asarray(vals) > 0)),
        "fraction_positive": float(np.mean(np.asarray(vals) > 0)),
        "participant_bootstrap_95ci_mean": bootstrap_mean_ci(vals),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
    return rows, summary


def run_losses_for_unit(active: list[str], loss_builder, named_params, accum, unit_counts):
    for i, sub in enumerate(active):
        loss, _ = loss_builder(sub)
        accumulate_autograd_loss(loss, named_params, accum[sub], retain_graph=(i < len(active) - 1))
        unit_counts[sub] += 1
        del loss


# -------------------- ZuCo --------------------
def target_zuco(model, tok, named_params, source, device):
    import torch
    cohort = json.loads((ROOT / "outputs/zuco2_nr_input_materialization/latest/summary.json").read_text())
    mapping = json.loads((ROOT / "outputs/zuco2_nr_format_probe/latest/summary.json").read_text())
    participants = list(cohort.get("ready_subjects_all_7_runs") or [])
    if len(participants) != 17 or "YTL" in participants:
        raise RuntimeError("unexpected frozen ZuCo cohort")
    maps = {r["run"]: r for r in mapping["wordcount_mapping_diagnostics"]}
    inv = zuco.load_inventory(ROOT / "outputs/zuco2_nr_input_materialization/latest/session_inventory.csv")
    path_by = {}
    for r in inv:
        if r.get("subject") in participants and str(r.get("ready", "")).lower() == "true":
            path_by[(r["subject"], int(r["run"]))] = ROOT / "data/raw/zuco2_nr" / r["osf_path"]
    if len(path_by) != 17 * 7:
        raise RuntimeError("ZuCo frozen EEG file inventory mismatch")

    specs = {}
    for run in range(1, 8):
        rows = zuco.load_material_rows(ROOT / f"data/raw/zuco2_probe/task_materials/nr_{run}.csv")
        selected = maps[f"NR{run}"]["selected_material_rows_1based"]
        texts = [str(rows[i - 1][2]).strip() for i in selected]
        if len(texts) != zuco.EXPECTED[run]:
            raise RuntimeError("ZuCo text count mismatch")
        X = zuco.nuisance_matrix(texts)
        A = np.column_stack([np.ones(X.shape[0]), X])
        neural = {}
        for sub in participants:
            feats, _ = zuco.load_run_features(path_by[(sub, run)], zuco.EXPECTED[run])
            neural[sub] = zuco.residualize(zuco.rdm_edges(feats["row_mean_all"]), X)
        specs[run] = {"texts": texts, "design": A, "neural": neural}

    n_params = sum(p.numel() for _, p in named_params)
    accum = new_accumulators(participants, n_params)
    counts = {s: 0 for s in participants}
    for k, run in enumerate(range(1, 8), 1):
        spec = specs[run]
        emb = encode_grad(model, tok, spec["texts"], device, max_length=128, batch_size=16)
        edges = pairwise_cosine_distance_torch(emb)
        def build(sub):
            return loss_from_model_edges(edges, spec["neural"][sub], spec["design"])
        run_losses_for_unit(participants, build, named_params, accum, counts)
        del emb, edges
        torch.cuda.empty_cache()
        write_progress(k, 7, "zuco", f"completed NR{run}")
    return finalize(source, accum, counts), {"n_units": 7}


# -------------------- fMRI --------------------
def torch_fmri_edges(model, tok, ctx: dict, hrf: np.ndarray, device: str):
    import torch
    import torch.nn.functional as F
    emb = encode_grad(model, tok, list(ctx["prefixes"]), device, max_length=128, batch_size=8)
    idx = np.asarray([int(math.floor(float(s) / FMRI_TR)) for s in ctx["starts"]], dtype=int)
    keep = (idx >= 0) & (idx < int(ctx["n_tp"]))
    idx_t = torch.as_tensor(idx[keep], dtype=torch.long, device=device)
    src = emb[torch.as_tensor(np.where(keep)[0], dtype=torch.long, device=device)]
    events = torch.zeros((int(ctx["n_tp"]), emb.shape[1]), dtype=emb.dtype, device=device)
    events = events.index_add(0, idx_t, src)
    h = torch.as_tensor(np.asarray(hrf, dtype=np.float32), dtype=emb.dtype, device=device)
    kernel = h.flip(0).view(1, 1, -1).expand(emb.shape[1], 1, -1)
    drive = F.conv1d(events.T.unsqueeze(0), kernel, padding=len(hrf) - 1, groups=emb.shape[1])
    drive = drive[0, :, : int(ctx["n_tp"])].T
    valid = torch.as_tensor(np.asarray(ctx["valid_idx"], dtype=int), dtype=torch.long, device=device)
    x = drive[valid]
    return pairwise_cosine_distance_torch(x), emb


def target_fmri(model, tok, named_params, source, device):
    import torch
    cache = ROOT / family_panel.FMRI_CACHE
    done = cache / "_COMPLETE.json"
    if not done.is_file():
        family_panel.build_fmri_cache()
    meta = json.loads(done.read_text())
    if int(meta.get("n_subjects", -1)) != 12 or int(meta.get("n_stories", -1)) != 60:
        raise RuntimeError("fMRI cache completeness mismatch")

    root = (ROOT / "data/raw/smn4lang").resolve()
    hrf = canonical_hrf(FMRI_TR)
    participants = list(FMRI_SUBJECTS)
    contexts = {story: fmri_eval.story_context(root, story, hrf) for story in FMRI_STORIES}
    n_params = sum(p.numel() for _, p in named_params)
    accum = new_accumulators(participants, n_params)
    counts = {s: 0 for s in participants}

    for k, story in enumerate(FMRI_STORIES, 1):
        ctx = contexts[story]
        edges, emb = torch_fmri_edges(model, tok, ctx, hrf, device)
        A = standard_design_from_columns(list(ctx["nuisance"]))
        npz = np.load(cache / f"story_{story:02d}.npz")
        neural = {s: np.asarray(npz[s.replace("-", "_")], dtype=np.float64) for s in participants}
        def build(sub):
            return loss_from_model_edges(edges, neural[sub], A)
        run_losses_for_unit(participants, build, named_params, accum, counts)
        npz.close()
        del edges, emb
        torch.cuda.empty_cache()
        write_progress(k, len(FMRI_STORIES), "smn4lang_fmri", f"completed story {story:02d}")
    return finalize(source, accum, counts), {"n_units": len(FMRI_STORIES), "neural_cache": str(cache.relative_to(ROOT))}


# -------------------- DERCo --------------------
def derco_parse(ep, article: int):
    inv = {int(code): label for label, code in ep.event_id.items()}
    out = []
    for row_i, code in enumerate(ep.events[:, 2].tolist()):
        m = DERCO_EVENT_RE.match(inv[int(code)])
        if not m or int(m.group("article")) != article:
            raise RuntimeError("unexpected DERCo event label")
        out.append((int(m.group("stim_index")), m.group("word"), row_i))
    idx = [x[0] for x in out]
    if len(set(idx)) != len(idx) or any(b <= a for a, b in zip(idx, idx[1:])):
        raise RuntimeError("DERCo item identity/order mismatch")
    return out


def derco_zscore_features(x):
    mu = np.nanmean(x, axis=0, keepdims=True)
    sd = np.nanstd(x, axis=0, ddof=0, keepdims=True)
    sd = np.where((~np.isfinite(sd)) | (sd == 0), 1.0, sd)
    return (x - mu) / sd


def target_derco(model, tok, named_params, source, device):
    import mne
    import torch
    root = ROOT / "data/raw/derco"
    participants = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    if len(participants) != 22:
        raise RuntimeError("DERCo participant count mismatch")
    articles = list(range(5))

    words = {a: {} for a in articles}
    raw_items = {}
    for a in articles:
        for sub in participants:
            ep = mne.read_epochs(root / sub / f"article_{a}/preprocessed_epoch.fif", preload=False, verbose="ERROR")
            items = derco_parse(ep, a)
            raw_items[(sub, a)] = items
            for idx, word, _ in items:
                prev = words[a].get(idx)
                if prev is not None and prev.casefold() != word.casefold():
                    raise RuntimeError("DERCo canonical word conflict")
                words[a][idx] = word
    canonical = {a: [(idx, words[a][idx]) for idx in sorted(words[a])] for a in articles}
    posmap = {a: {idx: i for i, (idx, _) in enumerate(canonical[a])} for a in articles}

    neural_specs = {}
    for a in articles:
        for sub in participants:
            ep = mne.read_epochs(root / sub / f"article_{a}/preprocessed_epoch.fif", preload=False, verbose="ERROR")
            items = raw_items[(sub, a)]
            indices = [x[0] for x in items]
            words_i = [x[1] for x in items]
            rows = [x[2] for x in items]
            data = ep.get_data(picks="eeg")[rows]
            feat = derco_zscore_features(np.mean(data, axis=2))
            neural = pdist(feat, metric="correlation")
            positions = np.asarray(indices, dtype=float)
            lengths = np.asarray([len(w) for w in words_i], dtype=float)
            cols = [
                pdist(positions[:, None], metric="cityblock"),
                pdist(lengths[:, None], metric="cityblock"),
            ]
            A = np.column_stack([np.ones(len(neural)), *cols])
            neural_specs[(sub, a)] = {
                "indices": np.asarray([posmap[a][idx] for idx in indices], dtype=int),
                "neural": residualize_np(neural, A),
                "design": A,
            }

    n_params = sum(p.numel() for _, p in named_params)
    accum = new_accumulators(participants, n_params)
    counts = {s: 0 for s in participants}
    for k, a in enumerate(articles, 1):
        texts = [w for _, w in canonical[a]]
        emb = encode_grad(model, tok, texts, device, max_length=128, batch_size=16)
        def build(sub):
            spec = neural_specs[(sub, a)]
            ix = torch.as_tensor(spec["indices"], dtype=torch.long, device=device)
            edges = pairwise_cosine_distance_torch(emb[ix])
            return loss_from_model_edges(edges, spec["neural"], spec["design"])
        run_losses_for_unit(participants, build, named_params, accum, counts)
        del emb
        torch.cuda.empty_cache()
        write_progress(k, len(articles), "derco", f"completed article {a}")
    return finalize(source, accum, counts), {"n_units": 5}


# -------------------- TMNRED --------------------
def target_tmnred(model, tok, named_params, source, device):
    import torch
    root = ROOT / "data/raw/tmnred"
    freeze = json.loads((ROOT / "outputs/tmnred_representation_input_materialization/latest/summary.json").read_text())
    participants = list(tmn.READY_SUBJECTS)
    if freeze.get("ready_subjects_all_8_sessions") != participants:
        raise RuntimeError("TMNRED cohort mismatch")
    blocks = tmn.stimulus_blocks(root / "derivatives/source material/source material.xlsx")
    specs = {}
    for ses in tmn.SESSIONS:
        for sub in participants:
            arr, emap = tmn.load_signal(root, sub, ses)
            items = sorted(emap)
            epidx = [emap[i] - 1 for i in items]
            feat = tmn.zscore_cols(tmn.row_mean_features(arr)[epidx, :])
            neural = pdist(feat, metric="correlation")
            X = tmn.nuisance_for_items(items, blocks[ses])
            specs[(sub, ses)] = {
                "ix": np.asarray(items, dtype=int) - 1,
                "neural": tmn.residualize(neural, X),
                "design": np.column_stack([np.ones(len(neural)), X]),
            }

    n_params = sum(p.numel() for _, p in named_params)
    accum = new_accumulators(participants, n_params)
    counts = {s: 0 for s in participants}
    for k, ses in enumerate(tmn.SESSIONS, 1):
        emb = encode_grad(model, tok, blocks[ses], device, max_length=128, batch_size=16)
        def build(sub):
            spec = specs[(sub, ses)]
            ix = torch.as_tensor(spec["ix"], dtype=torch.long, device=device)
            edges = pairwise_cosine_distance_torch(emb[ix])
            return loss_from_model_edges(edges, spec["neural"], spec["design"])
        run_losses_for_unit(participants, build, named_params, accum, counts)
        del emb
        torch.cuda.empty_cache()
        write_progress(k, len(tmn.SESSIONS), "tmnred", f"completed {ses}")
    return finalize(source, accum, counts), {"n_units": len(tmn.SESSIONS)}


# -------------------- Garnett Dream --------------------
def target_garnett(model, tok, named_params, source, device):
    import torch
    data_root = (ROOT / "data/raw/chineseeeg").resolve()
    freeze = json.loads((ROOT / "outputs/garnett_dream_input_materialization/latest/summary.json").read_text())
    expected = {int(k): int(v) for k, v in freeze.get("chapter_item_counts", {}).items()}
    mapping = json.loads((ROOT / "outputs/garnett_dream_segmented_xlsx_mapping_probe_v1/latest/summary.json").read_text())
    texts_by_chapter, _ = gar.load_frozen_texts(mapping, data_root, expected)
    text_nuis = {ch: gar.text_nuisance_edges(texts_by_chapter[ch]) for ch in range(1, 19)}

    inventory = garrel.read_csv(ROOT / "outputs/garnett_dream_input_materialization/latest/session_inventory.csv")
    items = garrel.read_csv(ROOT / "outputs/garnett_dream_input_materialization/latest/item_identity.csv")
    vhdrs = garrel.companion_vhdr_by_run(inventory)
    items_by_key = defaultdict(list)
    for r in items:
        items_by_key[(str(r["subject"]), int(r["run"]), int(r["chapter"]))].append(r)

    specs = {}
    by_chapter = defaultdict(list)
    participants = set()
    for key, vhdr_rel in sorted(vhdrs.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        sub, _, ch = key
        participants.add(sub)
        feats, durations, _ = garrel.features_for_run(data_root, vhdr_rel, items_by_key[key])
        neural = garrel.rdm_from_features(feats["row_mean_all"])
        tn = text_nuis[ch]
        nuis = [
            tn["order"],
            pdist(np.asarray(durations, dtype=float)[:, None], metric="cityblock"),
            tn["character_count"],
            tn["punctuation_count"],
            tn["character_set_jaccard"],
        ]
        specs[(sub, ch)] = {
            "neural": garrel.residualize(neural, nuis),
            "design": ranked_design_from_columns(nuis),
        }
        by_chapter[ch].append(sub)
    participants = sorted(participants)
    if len(participants) != 10:
        raise RuntimeError("Garnett participant count mismatch")

    n_params = sum(p.numel() for _, p in named_params)
    accum = new_accumulators(participants, n_params)
    counts = {s: 0 for s in participants}
    for k, ch in enumerate(range(1, 19), 1):
        active = sorted(by_chapter[ch])
        emb = encode_grad(model, tok, texts_by_chapter[ch], device, max_length=128, batch_size=8)
        edges = pairwise_cosine_distance_torch(emb)
        def build(sub):
            spec = specs[(sub, ch)]
            return loss_from_model_edges(edges, spec["neural"], spec["design"])
        run_losses_for_unit(active, build, named_params, accum, counts)
        del emb, edges
        torch.cuda.empty_cache()
        write_progress(k, 18, "garnett_dream", f"completed chapter {ch}")
    return finalize(source, accum, counts), {"n_units": 18, "n_subject_runs": len(vhdrs)}


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, choices=sorted(TARGET_CLASS))
    args = ap.parse_args()
    target = args.target
    stage1_path = ROOT / "outputs/target_compatibility_dose_v1/latest/summary.json"
    if not stage1_path.is_file():
        raise RuntimeError("Stage-1 target dose characterization has not completed")
    stage1 = json.loads(stage1_path.read_text(encoding="utf-8"))
    if stage1.get("status") != "ok" or stage1.get("all_reproduction_gates_passed") is not True:
        raise RuntimeError("Stage-1 target dose characterization/reproduction gate is not clean")
    if not torch.cuda.is_available():
        raise RuntimeError("Stage-2 gradient compatibility requires CUDA")
    device = "cuda"
    out = ROOT / "outputs/target_gradient_compatibility_v1" / target / "latest"
    out.mkdir(parents=True, exist_ok=True)

    tok, model, named_params = load_reference_model(device)
    pmanifest = parameter_manifest(named_params)
    source, source_meta = compute_source_gradient(model, tok, named_params, device)

    dispatch = {
        "zuco": target_zuco,
        "smn4lang_fmri": target_fmri,
        "derco": target_derco,
        "tmnred": target_tmnred,
        "garnett_dream": target_garnett,
    }
    (rows, summary), target_meta = dispatch[target](model, tok, named_params, source, device)

    write_csv(out / "participant_cosines.csv", rows)
    (out / "parameter_manifest.json").write_text(json.dumps(pmanifest, indent=2) + "\n", encoding="utf-8")
    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory target-gradient compatibility",
        "protocol": PROTOCOL,
        "target": target,
        "historical_target_class": TARGET_CLASS[target],
        "reference_model": "primary seed-20260823 lambda=0 text-only multilingual-E5 adapter",
        "trainable_subspace": "LoRA query/value parameters only",
        "source_gradient": source_meta,
        "parameter_manifest": {
            "n_tensors": pmanifest["n_tensors"],
            "n_parameters": pmanifest["n_parameters"],
            "sha256": pmanifest["sha256"],
        },
        "target_metadata": target_meta,
        "result": summary,
        "interpretation_guardrail": (
            "Positive cosine means local first-order alignment between the ChineseEEG source objective "
            "and this participant target objective at the fixed text-only reference; negative means local "
            "conflict. Historical transfer classes were known before this post-confirmatory mechanism analysis."
        ),
        "guardrails": [
            "No target, participant, unit, representation, nuisance set, layer or parameter subset is selected from compatibility outcomes.",
            "The same frozen source gradient definition and ordered LoRA q/v parameter coordinates are used for every target.",
            "No alternative differentiable ranking surrogate is searched.",
            "Participant is the reporting/resampling unit.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "report.txt").write_text(
        f"Target-gradient compatibility: {target}\n"
        f"historical_class={TARGET_CLASS[target]}\n"
        f"mean_cosine={summary['mean_gradient_cosine']:.10g}\n"
        f"median_cosine={summary['median_gradient_cosine']:.10g}\n"
        f"positive={summary['n_positive']}/{summary['n_participants']}\n"
        f"bootstrap95={summary['participant_bootstrap_95ci_mean']}\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "target": target, "result": summary, "out": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

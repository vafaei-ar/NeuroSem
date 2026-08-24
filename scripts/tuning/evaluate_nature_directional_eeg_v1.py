#!/usr/bin/env python3
"""Frozen external Nature directional-word EEG validation for NeuroSem E5.

Primary confirmatory contrast: lambda=0.10 versus lambda=0.00 text-only.
Protocol: docs/nature_directional_validation_protocol_v2.md
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

MODEL_ID = "intfloat/multilingual-e5-large"
MODEL_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
PREFIX = "query: "
CONCEPTS = ["UP", "DOWN", "LEFT", "RIGHT", "FORWARD", "BACK"]
WORDS = {
    "russian": ["вверх", "вниз", "влево", "вправо", "вперёд", "назад"],
    "spanish": ["arriba", "abajo", "izquierda", "derecha", "adelante", "atrás"],
}
PRIMARY_SUBJECTS = {
    "russian": ["sub2", "sub4", "sub6", "sub7", "sub8", "sub9", "sub11", "sub12"],
    "spanish": [f"sub{i}" for i in range(10)],
}
ADAPTER_0 = Path("outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter")
ADAPTER_1 = Path("outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter")
LAMBDA_010_ROOT = Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural")


def latest_completed_adapter(root: Path) -> Path:
    candidates = []
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and (d / "summary.json").exists() and (d / "adapter").is_dir():
                candidates.append(d)
    if not candidates:
        raise FileNotFoundError(f"No completed adapter under {root}")
    return sorted(candidates)[-1] / "adapter"


def masked_mean(hidden, mask):
    mask = mask.to(hidden.dtype).unsqueeze(-1)
    return (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)


def encode_words(model, tokenizer, words, device):
    import torch

    batch = [PREFIX + w for w in words]
    enc = tokenizer(batch, padding=True, truncation=True, max_length=32, return_tensors="pt")
    attention = enc["attention_mask"].to(device)
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.inference_mode():
        out = model(**enc, return_dict=True)
        pooled = masked_mean(out.last_hidden_state, attention.bool())
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
    return pooled.cpu().numpy().astype(np.float64)


def load_base(device):
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model.eval().to(device)
    return tokenizer, model


def load_adapter(adapter: Path, device):
    from peft import PeftModel
    from transformers import AutoModel, AutoTokenizer

    if not adapter.is_dir():
        raise FileNotFoundError(adapter)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    base = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = PeftModel.from_pretrained(base, adapter)
    model.eval().to(device)
    return tokenizer, model


def model_rdms(device):
    import torch

    adapter_010 = latest_completed_adapter(LAMBDA_010_ROOT)
    specs = {
        "base": None,
        "lambda_0": ADAPTER_0,
        "lambda_0p10": adapter_010,
        "lambda_1": ADAPTER_1,
    }
    out = {}
    provenance = {}
    for label, adapter in specs.items():
        print(f"Loading model arm: {label}", flush=True)
        if adapter is None:
            tokenizer, model = load_base(device)
        else:
            tokenizer, model = load_adapter(adapter, device)
        out[label] = {}
        for language, words in WORDS.items():
            emb = encode_words(model, tokenizer, words, device)
            out[label][language] = pdist(emb, metric="cosine")
        provenance[label] = None if adapter is None else str(adapter.resolve())
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return out, provenance


def zscore_features(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    mean = x.mean(axis=0, keepdims=True)
    sd = x.std(axis=0, keepdims=True)
    z = x - mean
    nz = sd[0] > 0
    z[:, nz] /= sd[:, nz]
    z[:, ~nz] = 0.0
    return z


def neural_rdm_from_concept_vectors(vectors: list[np.ndarray]) -> np.ndarray:
    x = np.stack(vectors, axis=0)
    z = zscore_features(x)
    rdm = pdist(z, metric="correlation")
    if not np.isfinite(rdm).all():
        raise RuntimeError("Non-finite neural RDM")
    return rdm


def event_samples_for_label(epochs, label: str) -> np.ndarray:
    if label not in epochs.event_id:
        raise RuntimeError(f"Missing event label {label}")
    code = epochs.event_id[label]
    return epochs.events[epochs.events[:, 2] == code, 0]


def assert_condition_order(epochs, subject: str):
    checks = {}
    for concept in CONCEPTS:
        a = event_samples_for_label(epochs, concept + "1")
        b = event_samples_for_label(epochs, concept + "2")
        if len(a) == 0 or len(b) == 0:
            raise RuntimeError(f"{subject}: empty event set for {concept}")
        med1 = float(np.median(a))
        med2 = float(np.median(b))
        ok = med1 < med2
        checks[concept] = {"median_suffix1_sample": med1, "median_suffix2_sample": med2, "suffix1_precedes_suffix2": ok}
        if not ok:
            raise RuntimeError(
                f"{subject}: condition-order assertion failed for {concept}; refusing to infer covert mapping"
            )
    return checks


def scalp_picks(epochs):
    import mne

    picks = mne.pick_types(epochs.info, eeg=True, meg=False, eog=False, emg=False, exclude=[])
    names = [epochs.ch_names[p] for p in picks]
    keep = [p for p, name in zip(picks, names) if name.upper() not in {"A1", "A2"}]
    if not keep:
        raise RuntimeError("No scalp EEG channels after excluding A1/A2")
    return keep


def prepare_condition_data(epochs, concept: str, picks):
    sel = epochs[concept + "2"].copy().pick(picks)
    if len(sel) < 2:
        raise RuntimeError(f"Too few covert trials for {concept}: {len(sel)}")
    sel.apply_baseline((-0.20, 0.00), verbose="ERROR")
    sel.crop(tmin=0.20, tmax=0.80, include_tmax=True)
    data = sel.get_data(copy=True)
    if not np.isfinite(data).all():
        raise RuntimeError(f"Non-finite EEG data for {concept}")
    return data


def subject_neural_rdms(fif: Path, subject: str):
    import mne

    epochs = mne.read_epochs(fif, preload=True, verbose="ERROR")
    order_checks = assert_condition_order(epochs, subject)
    picks = scalp_picks(epochs)

    full_vectors = []
    odd_vectors = []
    even_vectors = []
    counts = {}
    for concept in CONCEPTS:
        data = prepare_condition_data(epochs, concept, picks)
        n = data.shape[0]
        counts[concept] = int(n)
        full_vectors.append(data.mean(axis=0).reshape(-1))
        odd = data[::2]
        even = data[1::2]
        if len(odd) == 0 or len(even) == 0:
            raise RuntimeError(f"{subject}: insufficient trials for split-half reliability/{concept}")
        odd_vectors.append(odd.mean(axis=0).reshape(-1))
        even_vectors.append(even.mean(axis=0).reshape(-1))

    full = neural_rdm_from_concept_vectors(full_vectors)
    odd = neural_rdm_from_concept_vectors(odd_vectors)
    even = neural_rdm_from_concept_vectors(even_vectors)
    reliability = float(spearmanr(odd, even).statistic)
    return full, reliability, counts, order_checks, [epochs.ch_names[p] for p in picks]


def exact_signflip(values: np.ndarray):
    values = np.asarray(values, dtype=np.float64)
    n = len(values)
    observed = float(values.mean())
    ge = 0
    total = 1 << n
    for bits in range(total):
        s = np.ones(n, dtype=np.float64)
        for i in range(n):
            if bits & (1 << i):
                s[i] = -1.0
        if float(np.mean(values * s)) >= observed - 1e-15:
            ge += 1
    return {"n": n, "observed_mean": observed, "p_one_sided_ge": ge / total, "sign_configurations": total}


def safe_rho(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise RuntimeError("Non-finite Spearman RSA")
    return rho


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset_root", type=Path, nargs="?", default=Path("data/raw/nature_directional_eeg/extracted/inner_speech_v2"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/nature_directional_neurosem_v1/latest"))
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    import torch

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    root = args.dataset_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    rdms, model_provenance = model_rdms(device)
    subject_rows = []
    neural_rdms = {}
    order_audit = {}
    trial_counts = {}
    channel_inventory = {}

    for language, subjects in PRIMARY_SUBJECTS.items():
        for subject in subjects:
            fif = root / "preprocessed" / language / subject / f"{subject}_epochs.fif"
            if not fif.exists():
                raise FileNotFoundError(fif)
            print(f"Evaluating {language}/{subject}", flush=True)
            neural, reliability, counts, checks, channels = subject_neural_rdms(fif, subject)
            neural_rdms[f"{language}/{subject}"] = neural
            order_audit[f"{language}/{subject}"] = checks
            trial_counts[f"{language}/{subject}"] = counts
            channel_inventory[f"{language}/{subject}"] = channels

            rhos = {label: safe_rho(neural, by_lang[language]) for label, by_lang in rdms.items()}
            row = {
                "language": language,
                "subject": subject,
                "split_half_rdm_spearman": reliability,
                "rho_base": rhos["base"],
                "rho_lambda_0": rhos["lambda_0"],
                "rho_lambda_0p10": rhos["lambda_0p10"],
                "rho_lambda_1": rhos["lambda_1"],
                "delta_0p10_vs_0": rhos["lambda_0p10"] - rhos["lambda_0"],
                "delta_1_vs_0": rhos["lambda_1"] - rhos["lambda_0"],
            }
            for concept in CONCEPTS:
                row[f"n_{concept.lower()}_covert"] = counts[concept]
            subject_rows.append(row)

    all_delta = np.array([r["delta_0p10_vs_0"] for r in subject_rows], dtype=np.float64)
    primary_test = exact_signflip(all_delta)
    language_tests = {}
    for language in PRIMARY_SUBJECTS:
        vals = np.array([r["delta_0p10_vs_0"] for r in subject_rows if r["language"] == language], dtype=np.float64)
        language_tests[language] = exact_signflip(vals)

    secondary_delta_1 = np.array([r["delta_1_vs_0"] for r in subject_rows], dtype=np.float64)
    secondary_test_1 = exact_signflip(secondary_delta_1)

    # Write compact model RDM tables in canonical concept-pair order.
    iu = np.triu_indices(len(CONCEPTS), 1)
    pair_rows = []
    for i, j in zip(*iu):
        row = {"concept_a": CONCEPTS[i].lower(), "concept_b": CONCEPTS[j].lower()}
        edge_index = len(pair_rows)
        for label, by_lang in rdms.items():
            for language, rdm in by_lang.items():
                row[f"{label}_{language}"] = float(rdm[edge_index])
        pair_rows.append(row)

    write_csv(out / "subject_results.csv", subject_rows)
    write_csv(out / "model_rdm_edges.csv", pair_rows)

    np.savez_compressed(
        out / "neural_rdms.npz",
        **{k.replace("/", "__"): v for k, v in neural_rdms.items()},
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/nature_directional_validation_protocol_v2.md",
        "analysis_status": "prospective external neural validation",
        "dataset_root": str(root),
        "publication_doi": "10.1038/s41597-026-07809-9",
        "data_doi": "10.5281/zenodo.20374418",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_provenance": model_provenance,
        "device": device,
        "concept_order": [c.lower() for c in CONCEPTS],
        "words": WORDS,
        "primary_condition": "covert/inner speech; event suffix 2 after within-subject structural order assertion",
        "primary_subjects": PRIMARY_SUBJECTS,
        "n_primary_subjects": len(subject_rows),
        "eeg_representation": {
            "input": "distributed preprocessed MNE Epochs",
            "channels": "EEG channels excluding A1/A2 if present",
            "baseline_sec": [-0.20, 0.00],
            "primary_window_sec": [0.20, 0.80],
            "trial_aggregation": "mean within participant x covert concept",
            "feature_transform": "flatten channels x time, featurewise z-score across six concepts",
            "neural_rdm": "correlation distance",
        },
        "model_representation": {
            "prefix": PREFIX,
            "pooling": "attention-mask mean of final hidden state",
            "normalization": "L2",
            "model_rdm": "cosine distance",
        },
        "rsa": "Spearman correlation across 15 unique six-concept RDM edges",
        "primary_contrast": "lambda_0p10 minus lambda_0",
        "primary_test": primary_test,
        "language_tests": language_tests,
        "cross_language_same_direction": bool(
            language_tests["russian"]["observed_mean"] > 0 and language_tests["spanish"]["observed_mean"] > 0
        ),
        "secondary_lambda1_vs_lambda0_test": secondary_test_1,
        "subject_results": subject_rows,
        "trial_counts": trial_counts,
        "event_order_assertions": order_audit,
        "channel_inventory": channel_inventory,
        "reliability_policy": "split-half RDM reliability is diagnostic only and never used for exclusion or feature selection",
        "no_posthoc_rescue": True,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "primary_mean_delta": primary_test["observed_mean"],
        "primary_p_one_sided": primary_test["p_one_sided_ge"],
        "russian_mean_delta": language_tests["russian"]["observed_mean"],
        "spanish_mean_delta": language_tests["spanish"]["observed_mean"],
        "cross_language_same_direction": summary["cross_language_same_direction"],
        "output": str(out),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

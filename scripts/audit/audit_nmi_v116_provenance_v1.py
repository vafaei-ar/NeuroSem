#!/usr/bin/env python3
"""Audit NMI v1.16 STS provenance and manuscript-relevant derived outputs.

Read-only audit. No model fitting, neural analysis, inference, or manuscript editing.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "nmi_v116_provenance_audit_v1" / "latest"
FIG_BUILDER = ROOT / "scripts" / "paper" / "build_nmi_submission_figures_v1.py"
DOSE_SCRIPT = ROOT / "scripts" / "robustness" / "run_nmi_forward_external_dose_characterization_v1.py"
PARETO_SUMMARY = ROOT / "outputs" / "e5_pareto_v1" / "latest" / "combined_summary.json"
DOSE_SUMMARY = ROOT / "outputs" / "nmi_forward_external_dose_characterization_v1" / "latest" / "dose_summary.csv"
DEV_JSON = ROOT / "paper" / "figure_data" / "chineseeeg_development_v1.json"
RESULTS_MD = ROOT / "docs" / "3_RESULTS_AND_COMPARISONS.md"

FIG1_SEMANTIC = {
    "Base": [0.283464, 0.283464],
    "Text-only": [0.308486, 0.305020],
    "Neural-guided": [0.308575, 0.301607],
    "Shuffled-neural": [0.307943, 0.305266],
}
EXPECTED_STS_DELTA = {
    0.01: -0.000088,
    0.03: -0.000418,
    0.10: -0.001655,
    0.30: -0.007936,
    1.00: -0.034533,
}
SOURCE_DIRS = [ROOT / "scripts", ROOT / "docs", ROOT / "paper"]
TEXT_SUFFIXES = {".py", ".json", ".csv", ".tsv", ".txt", ".md", ".yaml", ".yml"}
KEYWORDS = ("sts", "semantic", "pareto", "benchmark", "task")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def read_text(path: Path, max_bytes: int = 5_000_000) -> str | None:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def iter_source_text_files() -> Iterable[Path]:
    for base in SOURCE_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and p.stat().st_size <= 5_000_000:
                yield p


def iter_output_candidate_text_files() -> Iterable[Path]:
    base = ROOT / "outputs"
    if not base.exists():
        return
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        low = rel(p).lower()
        name = p.name.lower()
        metadata_like = any(tok in name for tok in ("summary", "manifest", "report", "index"))
        keyword_like = any(tok in low for tok in KEYWORDS)
        if (metadata_like or keyword_like) and p.stat().st_size <= 5_000_000:
            yield p


def numeric_variants(x: float) -> set[str]:
    return {
        f"{x:.6f}", f"{x:.5f}", f"{x:.4f}",
        f"{x:.6e}", f"{x:.5e}", f"{x:.4e}", repr(float(x)),
    }


def find_numeric_hits(values: dict[str, float], paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cache: dict[Path, str | None] = {}
    for label, value in values.items():
        variants = numeric_variants(value)
        hits = []
        for p in paths:
            if p not in cache:
                cache[p] = read_text(p)
            text = cache[p]
            if text and any(v in text for v in variants):
                hits.append(rel(p))
        rows.append({"label": label, "value": value, "hit_count": len(hits), "hits": hits})
    return rows


def recursive_keys(obj: Any, prefix: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.append(p)
            out.extend(recursive_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:50]):
            out.extend(recursive_keys(v, f"{prefix}[{i}]"))
    return out


def inspect_pareto() -> dict[str, Any]:
    if not PARETO_SUMMARY.is_file():
        return {"exists": False, "path": rel(PARETO_SUMMARY)}
    payload = json.loads(PARETO_SUMMARY.read_text(encoding="utf-8"))
    points = payload.get("points") if isinstance(payload, dict) else None
    keys = recursive_keys(payload)
    task_markers = [
        k for k in keys
        if any(tok in k.lower() for tok in ("task_scores", "tasks", "per_task", "benchmark_scores", "normalization"))
    ]
    point_summary = []
    if isinstance(points, list):
        for p in points:
            if isinstance(p, dict):
                point_summary.append({
                    "lambda": p.get("lambda"),
                    "external_sts_mean": p.get("external_sts_mean"),
                    "delta_external_sts_vs_lambda0": p.get("delta_external_sts_vs_lambda0"),
                    "keys": sorted(p.keys()),
                })
    return {
        "exists": True,
        "path": rel(PARETO_SUMMARY),
        "sha256": sha256(PARETO_SUMMARY),
        "top_level_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
        "n_points": len(points) if isinstance(points, list) else None,
        "points": point_summary,
        "task_level_markers": task_markers,
        "has_task_level_or_normalization_metadata": bool(task_markers),
        "keys_containing_sts_or_task": [k for k in keys if "sts" in k.lower() or "task" in k.lower()][:100],
    }


def inspect_dose_summary() -> dict[str, Any]:
    if not DOSE_SUMMARY.is_file():
        return {"exists": False, "path": rel(DOSE_SUMMARY)}
    rows = list(csv.DictReader(DOSE_SUMMARY.open("r", encoding="utf-8", newline="")))
    subset = []
    for r in rows:
        try:
            lam = float(r["lambda"])
        except Exception:
            continue
        if r.get("dataset") == "zuco":
            subset.append({
                "lambda": lam,
                "external_sts_mean_already_observed": r.get("external_sts_mean_already_observed"),
                "delta_external_sts_vs_lambda0_already_observed": r.get("delta_external_sts_vs_lambda0_already_observed"),
            })
    return {"exists": True, "path": rel(DOSE_SUMMARY), "sha256": sha256(DOSE_SUMMARY), "zuco_rows": sorted(subset, key=lambda r: r["lambda"])}


def candidate_sts_files() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for p in sorted(set(iter_output_candidate_text_files()), key=lambda x: rel(x)):
        low = rel(p).lower()
        if not any(tok in low for tok in KEYWORDS):
            continue
        text = read_text(p)
        markers = []
        if text:
            for tok in ("task_scores", "per_task", "normalization", "benchmark", "external_sts_mean", "spearman"):
                if tok.lower() in text.lower():
                    markers.append(tok)
        candidates.append({"path": rel(p), "size_bytes": p.stat().st_size, "sha256": sha256(p), "content_markers": markers})
    return candidates[:1000]


def output_inventory() -> list[dict[str, Any]]:
    base = ROOT / "outputs"
    rows: list[dict[str, Any]] = []
    if not base.exists():
        return rows
    focus = (
        "derco", "multiseed", "model_family", "bidirectional", "reviewer", "pareto", "dose",
        "regional", "spatial", "reliability", "transfer", "zuco", "smn4lang", "chineseeeg",
        "sts", "semantic", "model_space",
    )
    for d in sorted([x for x in base.iterdir() if x.is_dir()], key=lambda p: p.name.lower()):
        if not any(tok in d.name.lower() for tok in focus):
            continue
        root = d / "latest" if (d / "latest").is_dir() else d
        summary = root / "summary.json"
        status = None
        stage = None
        summary_sha = None
        if summary.is_file() and summary.stat().st_size <= 5_000_000:
            summary_sha = sha256(summary)
            try:
                obj = json.loads(summary.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    status = obj.get("status")
                    stage = obj.get("analysis_stage") or obj.get("analysis") or obj.get("stage")
            except Exception:
                status = "unparsed"
        rows.append({
            "output_family": d.name,
            "root": rel(root),
            "summary_exists": summary.is_file(),
            "summary_sha256": summary_sha,
            "status": status,
            "analysis_stage": stage,
            "file_count_top_level": sum(1 for p in root.iterdir()) if root.is_dir() else 0,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    required = [FIG_BUILDER, DOSE_SCRIPT, DEV_JSON, RESULTS_MD]
    missing = [rel(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing committed audit input(s): " + ", ".join(missing))

    source_files = list(iter_source_text_files())
    output_candidates = list(iter_output_candidate_text_files())
    search_files = sorted(set(source_files + output_candidates), key=lambda p: rel(p))

    fig1_values = {
        f"figure1e.{arm}.{i+1}": v
        for arm, vals in FIG1_SEMANTIC.items()
        for i, v in enumerate(vals)
    }
    fig1_hits = find_numeric_hits(fig1_values, search_files)
    sts_hits = find_numeric_hits({f"sts_delta.lambda_{lam:g}": v for lam, v in EXPECTED_STS_DELTA.items()}, search_files)

    pareto = inspect_pareto()
    dose = inspect_dose_summary()
    candidates = candidate_sts_files()
    inventory = output_inventory()

    builder_text = FIG_BUILDER.read_text(encoding="utf-8")
    fig1_hardcoded = all(any(v in builder_text for v in numeric_variants(x)) for x in fig1_values.values())
    machine_hits = []
    for rec in fig1_hits:
        mh = [
            h for h in rec["hits"]
            if h != rel(FIG_BUILDER) and (h.startswith("outputs/") or h.startswith("paper/figure_data/"))
        ]
        machine_hits.append({"label": rec["label"], "machine_hits": mh})
    fig1_machine_source_for_all = all(x["machine_hits"] for x in machine_hits)

    task_files = [
        c for c in candidates
        if any(m in c.get("content_markers", []) for m in ("task_scores", "per_task", "normalization", "benchmark"))
    ]
    pareto_points = bool(pareto.get("exists") and pareto.get("n_points") == 6)
    dose_sts = bool(dose.get("exists") and len(dose.get("zuco_rows", [])) >= 6)
    task_trace = bool(pareto.get("has_task_level_or_normalization_metadata")) or bool(task_files)

    conclusions = {
        "figure1e_eight_task_semantic_panel": {
            "literal_values_present_in_figure_builder": fig1_hardcoded,
            "machine_readable_producing_source_found_for_all_displayed_values": fig1_machine_source_for_all,
            "status": "reconstructible" if fig1_machine_source_for_all else "not_reconstructible_from_current_machine_readable_sources",
            "reason": "Displayed values are literal constants in the figure builder and at least one lacks a separate machine-readable producing source." if not fig1_machine_source_for_all else "All displayed values have non-builder machine-readable source hits.",
        },
        "figure3b_sts_cost_axis": {
            "panel_values_rebuildable_from_existing_aggregate_summary": pareto_points and dose_sts,
            "task_level_eight_benchmark_recomputation_trace_found": task_trace,
            "status": "fully_reconstructible_to_task_level" if (pareto_points and dose_sts and task_trace) else "aggregate_panel_rebuildable_but_task_level_provenance_unresolved" if (pareto_points and dose_sts) else "not_reconstructible_from_current_sources",
            "reason": "The panel consumes aggregate STS values copied from e5_pareto_v1; task-level benchmark scores and normalization must be separately traceable for scientific recomputation.",
        },
    }

    summary = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "read-only NMI v1.16 provenance audit prioritizing STS reconstructibility and manuscript-relevant output inventory",
        "guardrails": {
            "new_model_training": False,
            "new_model_evaluation": False,
            "new_neural_analysis": False,
            "new_hypothesis_test": False,
            "manuscript_editing": False,
            "raw_sensitive_data_exported": False,
        },
        "inputs": {
            "figure_builder": {"path": rel(FIG_BUILDER), "sha256": sha256(FIG_BUILDER)},
            "dose_script": {"path": rel(DOSE_SCRIPT), "sha256": sha256(DOSE_SCRIPT)},
            "development_json": {"path": rel(DEV_JSON), "sha256": sha256(DEV_JSON)},
            "results_summary": {"path": rel(RESULTS_MD), "sha256": sha256(RESULTS_MD)},
            "pareto_summary": pareto,
            "dose_summary": dose,
        },
        "conclusions": conclusions,
        "figure1_numeric_hits": fig1_hits,
        "sts_delta_numeric_hits": sts_hits,
        "candidate_sts_task_files": candidates,
        "candidate_task_level_files": task_files,
        "output_inventory_count": len(inventory),
        "output_inventory_focus_matches": [r["output_family"] for r in inventory],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(OUT / "sts_source_hits.csv", fig1_hits + sts_hits)
    write_csv(OUT / "output_inventory.csv", inventory)
    write_csv(OUT / "candidate_sts_files.csv", candidates)

    report = [
        "NeuroSem NMI v1.16 provenance audit v1",
        "",
        "Read-only provenance audit; no scientific analysis or manuscript editing.",
        "",
        "STS reconstructibility",
        f"- Figure 1e: {conclusions['figure1e_eight_task_semantic_panel']['status']}",
        f"  {conclusions['figure1e_eight_task_semantic_panel']['reason']}",
        f"- Figure 3b STS cost axis: {conclusions['figure3b_sts_cost_axis']['status']}",
        f"  {conclusions['figure3b_sts_cost_axis']['reason']}",
        "",
        "Inventory",
        f"- Manuscript-relevant derived output families found: {len(inventory)}",
        f"- STS/semantic/benchmark candidate metadata files found: {len(candidates)}",
        f"- Candidate task-level/normalization files: {len(task_files)}",
        "",
        "Next audit actions",
        "1. If Figure 1e is not reconstructible, replace or remove it rather than treating hard-coded display values as canonical evidence.",
        "2. If Figure 3b is only aggregate-rebuildable, recover the task-level STS producing path or rebuild the panel from fully traceable quantities.",
        "3. Use output_inventory.csv for the reverse output-to-manuscript audit, including DERCo and multiseed E5 outputs.",
    ]
    (OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "output_dir": str(OUT),
        "figure1e_status": conclusions["figure1e_eight_task_semantic_panel"]["status"],
        "figure3b_status": conclusions["figure3b_sts_cost_axis"]["status"],
        "output_inventory_count": len(inventory),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

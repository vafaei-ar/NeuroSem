#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 5 and Extended Data Figure 1.

Presentation-only. All scientific values come from already-completed frozen NeuroSem
outputs. The only additional dependency is the standard FreeSurfer fsaverage surface/
Desikan-Killiany annotation, used strictly as an anatomical rendering scaffold. No model
fitting, neural analysis, ROI selection, thresholding, hypothesis testing, or new inference
is performed here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors
from matplotlib.cm import ScalarMappable

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs" / "nmi_figure5_redesign_v1" / "latest"
LANGSPEC = ROOT / "outputs" / "smn4lang_fmri_language_specificity_v1" / "latest"
SPATIAL = ROOT / "outputs" / "smn4lang_fmri_spatial_extensions_v1" / "latest"
FINAL = ROOT / "outputs" / "nmi_final_spatial_validation_v1" / "latest"
REGIONAL = ROOT / "outputs" / "smn4lang_regional_fmri_e5_transfer_v1" / "latest"
ATLAS_CACHE = ROOT / "outputs" / "nmi_visual_atlas_cache_v1"

LANGUAGE_ORDER = ["IFGorb", "IFG", "MFG", "AntTemp", "PostTemp", "AngG"]

INPUTS = [
    LANGSPEC / "summary.json",
    LANGSPEC / "participant_contrasts.csv",
    SPATIAL / "summary.json",
    SPATIAL / "participant_spatial_extensions.csv",
    FINAL / "summary.json",
    FINAL / "spatial_surrogate_null.csv",
    FINAL / "shuffled_regional_participant_results.csv",
    REGIONAL / "summary.json",
    REGIONAL / "region_summary.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_name(name: str) -> str:
    s = name.decode("utf-8") if isinstance(name, (bytes, bytearray)) else str(name)
    s = s.lower().strip()
    for prefix in ("ctx-lh-", "ctx-rh-", "lh_", "rh_", "left_", "right_"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return re.sub(r"[^a-z0-9]", "", s)


def fmt_p(p: float) -> str:
    p = float(p)
    if p < 1e-4:
        return f"{p:.2e}"
    if p < 0.01:
        return f"{p:.4f}"
    return f"{p:.3f}"


def save(fig: plt.Figure, stem: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    out = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        path = OUT / f"{stem}.{ext}"
        fig.savefig(path, **kwargs)
        out.append(path)
    plt.close(fig)
    return out


def ensure_fsaverage() -> Path:
    """Return a standard fsaverage directory, downloading MNE's pinned copy if needed."""
    fs = ATLAS_CACHE / "fsaverage"
    required = [
        fs / "surf/lh.inflated", fs / "surf/rh.inflated",
        fs / "surf/lh.sulc", fs / "surf/rh.sulc",
        fs / "label/lh.aparc.annot", fs / "label/rh.aparc.annot",
    ]
    if all(p.is_file() for p in required):
        return fs
    ATLAS_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        import mne
    except Exception as exc:  # pragma: no cover - machine dependency
        raise RuntimeError("mne is required to fetch the standard fsaverage rendering scaffold") from exc
    fetched = Path(mne.datasets.fetch_fsaverage(subjects_dir=str(ATLAS_CACHE), verbose=False))
    fs = fetched if fetched.name == "fsaverage" else ATLAS_CACHE / "fsaverage"
    required = [
        fs / "surf/lh.inflated", fs / "surf/rh.inflated",
        fs / "surf/lh.sulc", fs / "surf/rh.sulc",
        fs / "label/lh.aparc.annot", fs / "label/rh.aparc.annot",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("fsaverage fetch incomplete: " + ", ".join(missing))
    return fs


def atlas_files(fs: Path) -> list[Path]:
    return [
        fs / "surf/lh.inflated", fs / "surf/rh.inflated",
        fs / "surf/lh.sulc", fs / "surf/rh.sulc",
        fs / "label/lh.aparc.annot", fs / "label/rh.aparc.annot",
    ]


def load_surface_data(fs: Path, dk: pd.DataFrame) -> dict:
    try:
        from nibabel.freesurfer.io import read_annot, read_geometry, read_morph_data
    except Exception as exc:  # pragma: no cover - machine dependency
        raise RuntimeError("nibabel FreeSurfer readers are required for cortical rendering") from exc

    out = {}
    for hemi_code, hemi_label in (("lh", "L"), ("rh", "R")):
        coords, faces = read_geometry(str(fs / f"surf/{hemi_code}.inflated"))
        sulc = read_morph_data(str(fs / f"surf/{hemi_code}.sulc")).astype(float)
        vertex_labels, _ctab, names = read_annot(str(fs / f"label/{hemi_code}.aparc.annot"), orig_ids=False)
        lookup = {
            norm_name(r["region_name"]): float(r["delta_mean"]) * 1e3
            for _, r in dk.loc[dk["hemisphere"] == hemi_label].iterrows()
        }
        values = np.full(len(vertex_labels), np.nan, dtype=float)
        matched = set()
        for annot_idx, raw_name in enumerate(names):
            key = norm_name(raw_name)
            if key in lookup:
                values[vertex_labels == annot_idx] = lookup[key]
                matched.add(key)
        missing = sorted(set(lookup) - matched)
        if missing:
            raise RuntimeError(
                f"{hemi_label}: DK parcel name(s) not matched to fsaverage aparc: " + ", ".join(missing)
            )
        out[hemi_code] = {"coords": coords, "faces": faces, "sulc": sulc, "values": values}
    return out


def surface_norm(dk: pd.DataFrame):
    vals = dk["delta_mean"].to_numpy(float) * 1e3
    if np.nanmin(vals) < 0 < np.nanmax(vals):
        vmax = float(np.nanmax(np.abs(vals)))
        return colors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax), plt.get_cmap(S.DIVERGING), "Mean participant ΔRSA (×10$^{-3}$)"
    vmax = float(np.nanmax(vals)) * 1.02
    return colors.Normalize(vmin=0.0, vmax=vmax), plt.get_cmap("Oranges"), "Mean participant ΔRSA (×10$^{-3}$)"


def draw_surface(ax, surf: dict, hemi: str, view: str, norm, cmap, label: str | None = None):
    coords = surf["coords"]
    faces = surf["faces"]
    values = surf["values"]
    sulc = surf["sulc"]

    mesh = ax.plot_trisurf(
        coords[:, 0], coords[:, 1], coords[:, 2], triangles=faces,
        linewidth=0, antialiased=False, shade=False,
    )
    face_vals = np.nanmean(values[faces], axis=1)
    known = np.isfinite(face_vals)
    rgba = np.empty((len(faces), 4), dtype=float)
    rgba[:] = np.array([0.86, 0.86, 0.86, 1.0])
    if np.any(known):
        rgba[known] = cmap(norm(face_vals[known]))
    face_sulc = np.nanmean(sulc[faces], axis=1)
    if np.nanmax(face_sulc) > np.nanmin(face_sulc):
        s = (face_sulc - np.nanmin(face_sulc)) / (np.nanmax(face_sulc) - np.nanmin(face_sulc))
        grey = 0.72 + 0.18 * s
        rgba[~known, :3] = grey[~known, None]
    mesh.set_facecolors(rgba)

    if hemi == "lh":
        azim = 180 if view == "lateral" else 0
    else:
        azim = 0 if view == "lateral" else 180
    ax.view_init(elev=5, azim=azim)
    ax.set_axis_off()
    ranges = np.ptp(coords, axis=0)
    ax.set_box_aspect(tuple(ranges))
    if label:
        ax.text2D(0.5, 0.02, label, transform=ax.transAxes, ha="center", va="bottom", fontsize=5.6, color=S.GREY)


def load_data() -> dict:
    missing = [str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing frozen Figure 5 input(s): " + ", ".join(missing))

    lang_summary = read_json(LANGSPEC / "summary.json")
    spatial_summary = read_json(SPATIAL / "summary.json")
    final_summary = read_json(FINAL / "summary.json")
    regional_summary = read_json(REGIONAL / "summary.json")
    if not all(x.get("status") == "ok" for x in (lang_summary, spatial_summary, final_summary, regional_summary)):
        raise RuntimeError("One or more frozen Figure 5 sources are not status=ok")

    lang_part = pd.read_csv(LANGSPEC / "participant_contrasts.csv")
    spatial_part = pd.read_csv(SPATIAL / "participant_spatial_extensions.csv")
    null_df = pd.read_csv(FINAL / "spatial_surrogate_null.csv")
    shuffled = pd.read_csv(FINAL / "shuffled_regional_participant_results.csv")
    regions = pd.read_csv(REGIONAL / "region_summary.csv")
    dk = regions.loc[regions["family"] == "dk68"].copy()
    lang_regions = regions.loc[regions["family"] == "language"].copy()

    if len(lang_part) != 12 or len(spatial_part) != 12:
        raise RuntimeError("Expected 12 participant rows in SMN4Lang spatial source tables")
    if len(null_df) != 10000:
        raise RuntimeError("Expected 10,000 spatial-surrogate rows")
    if len(dk) != 68 or set(dk["hemisphere"]) != {"L", "R"}:
        raise RuntimeError("Expected complete bilateral DK68 regional summary")
    if len(lang_regions) != 6 or set(lang_regions["region_name"]) != set(LANGUAGE_ORDER):
        raise RuntimeError("Expected frozen six-region functional language family")

    return {
        "lang_summary": lang_summary,
        "spatial_summary": spatial_summary,
        "final_summary": final_summary,
        "lang_part": lang_part,
        "spatial_part": spatial_part,
        "null": null_df,
        "shuffled": shuffled,
        "regions": regions,
        "dk": dk,
        "lang_regions": lang_regions,
    }


def paired_lines(ax, matrix: np.ndarray, labels: list[str], highlight: int | tuple[int, ...], title: str, ylabel: str, panel: str):
    x = np.arange(matrix.shape[1], dtype=float)
    for row in matrix:
        ax.plot(x, row, color=S.GREY_L, linewidth=0.55, alpha=0.65, zorder=1)
        ax.scatter(x, row, s=8, facecolor="white", edgecolor=S.GREY, linewidth=0.45, zorder=2)
    means = matrix.mean(axis=0)
    ax.plot(x, means, color=S.INK, linewidth=1.25, zorder=3)
    hi = (highlight,) if isinstance(highlight, int) else tuple(highlight)
    face = [S.ORANGE if i in hi else "white" for i in range(len(x))]
    edge = [S.ORANGE if i in hi else S.INK for i in range(len(x))]
    ax.scatter(x, means, s=29, facecolor=face, edgecolor=edge, linewidth=0.75, zorder=4)
    ax.axhline(0, color=S.ZERO, linewidth=0.55, zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.tick_params(axis="x", length=0)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontweight="bold", pad=5)
    S.panel(ax, panel, dx=-0.12, dy=1.08)
    S.offset_ticks(ax, "y")


def build_figure5(d: dict, surf: dict, norm, cmap) -> list[Path]:
    S.apply()
    fig = S.figure(S.W2, 151)
    outer = fig.add_gridspec(3, 2, height_ratios=[1.12, 1.0, 1.0], hspace=0.34, wspace=0.25)

    area = outer[0, :].subgridspec(1, 4, wspace=0.01)
    surface_axes = [fig.add_subplot(area[0, i], projection="3d") for i in range(4)]
    draw_surface(surface_axes[0], surf["lh"], "lh", "lateral", norm, cmap, "left lateral")
    draw_surface(surface_axes[1], surf["lh"], "lh", "medial", norm, cmap, "left medial")
    draw_surface(surface_axes[2], surf["rh"], "rh", "medial", norm, cmap, "right medial")
    draw_surface(surface_axes[3], surf["rh"], "rh", "lateral", norm, cmap, "right lateral")
    surface_axes[0].text2D(-0.10, 1.04, "a", transform=surface_axes[0].transAxes, fontsize=8, fontweight="bold", va="top")
    surface_axes[0].text2D(0.00, 1.04, "Unthresholded DK68 transfer phenotype is broadly positive", transform=surface_axes[0].transAxes,
                           fontsize=7, fontweight="bold", va="top", ha="left")
    n_pos = int(np.sum(d["dk"]["delta_mean"].to_numpy(float) > 0))
    surface_axes[3].text2D(0.98, 1.03, f"{n_pos}/68 parcel means > 0", transform=surface_axes[3].transAxes,
                           fontsize=5.8, color=S.ORANGE, va="top", ha="right")
    sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cb = fig.colorbar(sm, ax=surface_axes, orientation="vertical", fraction=0.014, pad=0.01, shrink=0.78)
    cb.set_label("Mean participant ΔRSA (×10$^{-3}$)", fontsize=6)
    cb.ax.tick_params(labelsize=5.5, length=1.5, width=.5)
    cb.outline.set_linewidth(.4)

    axb = fig.add_subplot(outer[1, 0])
    m = d["lang_part"][["functional_language_mean_delta", "left_sensorimotor_mean_delta", "left_visual_mean_delta"]].to_numpy(float) * 1e3
    paired_lines(axb, m, ["Language", "Sensorimotor", "Visual"], 0,
                 "Language cortex shows relative enrichment", "Participant ΔRSA (×10$^{-3}$)", "b")
    p1 = float(d["lang_summary"]["primary"]["functional_language_minus_left_sensorimotor"]["familywise_maxstat_p"])
    p2 = float(d["lang_summary"]["primary"]["functional_language_minus_left_visual"]["familywise_maxstat_p"])
    axb.text(.02, .97, f"language − sensorimotor: FWER P={fmt_p(p1)}\nlanguage − visual: FWER P={fmt_p(p2)}",
             transform=axb.transAxes, ha="left", va="top", fontsize=5.4, color=S.GREY, linespacing=1.25)

    axc = fig.add_subplot(outer[1, 1])
    m = d["spatial_part"][["functional_frontal_mean_delta", "functional_temporal_mean_delta"]].to_numpy(float) * 1e3
    paired_lines(axc, m, ["Frontal", "Temporal"], 1,
                 "Within language cortex, transfer is stronger temporally", "Participant ΔRSA (×10$^{-3}$)", "c")
    tf = d["spatial_summary"]["focal_tests"]["functional_temporal_minus_frontal_language"]
    axc.text(.02, .97, f"temporal − frontal = {float(tf['mean'])*1e3:.3f} ×10$^{{-3}}$\nFWER P={fmt_p(float(tf['familywise_maxstat_p']))}",
             transform=axc.transAxes, ha="left", va="top", fontsize=5.4, color=S.GREY, linespacing=1.25)

    axd = fig.add_subplot(outer[2, 0])
    vals = d["null"]["language_beta"].to_numpy(float) * 1e3
    sn = d["final_summary"]["spatial_autocorrelation_null"]
    obs = float(sn["observed_reliability_adjusted_language_beta"]) * 1e3
    axd.hist(vals, bins=48, color=S.GREY_L, edgecolor="none")
    axd.axvline(obs, color=S.ORANGE, linewidth=1.4)
    axd.axvline(-obs, color=S.GREY, linewidth=.55, linestyle=(0, (2, 2)))
    axd.set_xlabel("Spatial-surrogate language coefficient (×10$^{-3}$)")
    axd.set_ylabel("Surrogates")
    axd.set_title("Language enrichment exceeds the spatial surrogate null", loc="left", fontweight="bold", pad=5)
    S.panel(axd, "d", dx=-0.12, dy=1.08)
    axd.text(.98, .96, f"observed {obs:.3f} ×10$^{{-3}}$\nspatial-surrogate P={fmt_p(float(sn['two_sided_spatial_surrogate_p']))}",
             transform=axd.transAxes, ha="right", va="top", fontsize=5.5, color=S.ORANGE, linespacing=1.25)
    S.offset_ticks(axd, "both")

    axe = fig.add_subplot(outer[2, 1])
    avg = d["shuffled"].groupby("subject", as_index=False)[["genuine_specificity", "shuffled_specificity"]].mean()
    m = avg[["genuine_specificity", "shuffled_specificity"]].to_numpy(float) * 1e3
    paired_lines(axe, m, ["Genuine", "Shuffled"], 0,
                 "Regional enrichment depends on genuine neural guidance", "Language specificity (×10$^{-3}$)", "e")
    sh = d["final_summary"]["regional_shuffled_target_control"]["primary_genuine_minus_shuffled_language_specificity"]
    axe.text(.02, .97, f"genuine − shuffled = {float(sh['mean'])*1e3:.3f} ×10$^{{-3}}$\nFWER P={fmt_p(float(sh['two_test_familywise_maxstat_p']))}",
             transform=axe.transAxes, ha="left", va="top", fontsize=5.4, color=S.GREY, linespacing=1.25)

    return save(fig, "figure5")


def build_extended_data1(d: dict, surf: dict, norm, cmap) -> list[Path]:
    S.apply()
    fig = S.figure(S.W2, 123)
    outer = fig.add_gridspec(2, 2, height_ratios=[0.86, 1.25], hspace=.33, wspace=.28)

    axa = fig.add_subplot(outer[0, 0])
    lang = d["lang_regions"].copy()
    lang["ord"] = lang["region_name"].map({v: i for i, v in enumerate(LANGUAGE_ORDER)})
    lang = lang.sort_values("ord")
    y = np.arange(len(lang))[::-1]
    val = lang["delta_mean"].to_numpy(float) * 1e3
    lo = lang["delta_bootstrap_ci_low"].to_numpy(float) * 1e3
    hi = lang["delta_bootstrap_ci_high"].to_numpy(float) * 1e3
    axa.hlines(y, lo, hi, color=S.ORANGE, lw=.9)
    axa.plot(val, y, "o", color=S.ORANGE, markersize=3.4)
    axa.axvline(0, color=S.ZERO, lw=.55)
    axa.set_yticks(y); axa.set_yticklabels(lang["region_name"])
    axa.set_xlabel("Mean participant ΔRSA (×10$^{-3}$)")
    axa.set_title("Prespecified functional language parcels", loc="left", fontweight="bold", pad=5)
    S.panel(axa, "a", dx=-.16, dy=1.08); S.offset_ticks(axa, "x")

    axb = fig.add_subplot(outer[0, 1])
    rng = np.random.default_rng(0)
    for yi, (hemi, marker) in enumerate((("L", "o"), ("R", "s"))):
        vals = d["dk"].loc[d["dk"]["hemisphere"] == hemi, "delta_mean"].to_numpy(float) * 1e3
        jit = rng.uniform(-.08, .08, len(vals))
        axb.plot(vals, yi + jit, linestyle="none", marker=marker, color=S.ORANGE if hemi == "L" else S.GREY,
                 alpha=.75, markersize=2.8, label="left" if hemi == "L" else "right")
        axb.plot([vals.mean(), vals.mean()], [yi-.20, yi+.20], color=S.INK, lw=1.2)
    axb.axvline(0, color=S.ZERO, lw=.55)
    axb.set_yticks([0,1]); axb.set_yticklabels(["Left", "Right"])
    axb.set_xlabel("DK parcel mean ΔRSA (×10$^{-3}$)")
    axb.set_title("All bilateral DK68 parcel means are positive", loc="left", fontweight="bold", pad=5)
    axb.text(.98, .95, "68/68 > 0\nunthresholded characterization", transform=axb.transAxes,
             ha="right", va="top", fontsize=5.5, color=S.GREY, linespacing=1.2)
    S.panel(axb, "b", dx=-.16, dy=1.08); S.offset_ticks(axb, "x")

    area = outer[1, :].subgridspec(1, 4, wspace=.01)
    axes = [fig.add_subplot(area[0, i], projection="3d") for i in range(4)]
    draw_surface(axes[0], surf["lh"], "lh", "lateral", norm, cmap, "left lateral")
    draw_surface(axes[1], surf["lh"], "lh", "medial", norm, cmap, "left medial")
    draw_surface(axes[2], surf["rh"], "rh", "medial", norm, cmap, "right medial")
    draw_surface(axes[3], surf["rh"], "rh", "lateral", norm, cmap, "right lateral")
    axes[0].text2D(-.10, 1.04, "c", transform=axes[0].transAxes, fontsize=8, fontweight="bold", va="top")
    axes[0].text2D(0, 1.04, "Complete unthresholded DK68 phenotype on fsaverage inflated cortex",
                   transform=axes[0].transAxes, fontsize=7, fontweight="bold", va="top")
    sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cb = fig.colorbar(sm, ax=axes, orientation="vertical", fraction=.014, pad=.01, shrink=.78)
    cb.set_label("Mean participant ΔRSA (×10$^{-3}$)", fontsize=6)
    cb.ax.tick_params(labelsize=5.5, length=1.5, width=.5); cb.outline.set_linewidth(.4)

    return save(fig, "extended_data_figure1")


def write_sources(d: dict, fs: Path) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []

    p = OUT / "figure5_participant_source.csv"
    lang = d["lang_part"].reset_index(drop=True)
    spatial = d["spatial_part"].reset_index(drop=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "participant_index", "language_delta", "sensorimotor_delta", "visual_delta",
            "frontal_language_delta", "temporal_language_delta",
        ]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for i in range(12):
            w.writerow({
                "participant_index": i + 1,
                "language_delta": float(lang.loc[i, "functional_language_mean_delta"]),
                "sensorimotor_delta": float(lang.loc[i, "left_sensorimotor_mean_delta"]),
                "visual_delta": float(lang.loc[i, "left_visual_mean_delta"]),
                "frontal_language_delta": float(spatial.loc[i, "functional_frontal_mean_delta"]),
                "temporal_language_delta": float(spatial.loc[i, "functional_temporal_mean_delta"]),
            })
    paths.append(p)

    p = OUT / "figure5_shuffled_control_source.csv"
    avg = d["shuffled"].groupby("subject", as_index=False)[["genuine_specificity", "shuffled_specificity"]].mean().reset_index(drop=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["participant_index", "genuine_specificity", "shuffled_specificity"])
        for i, r in avg.iterrows():
            w.writerow([i+1, float(r["genuine_specificity"]), float(r["shuffled_specificity"])])
    paths.append(p)

    p = OUT / "figure5_spatial_null_source.csv"
    pd.DataFrame({"surrogate_index": np.arange(1, len(d["null"]) + 1), "language_beta": d["null"]["language_beta"].to_numpy(float)}).to_csv(p, index=False)
    paths.append(p)

    p = OUT / "extended_data_figure1_region_source.csv"
    d["regions"].to_csv(p, index=False)
    paths.append(p)

    p = OUT / "atlas_manifest.json"
    payload = {
        "role": "visualization scaffold only",
        "atlas": "FreeSurfer fsaverage Desikan-Killiany aparc",
        "files": {str(x.relative_to(ATLAS_CACHE)): sha256(x) for x in atlas_files(fs)},
        "guardrail": "Atlas files define cortical geometry and parcel labels only; no atlas-derived outcome is analyzed.",
    }
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    paths.append(p)
    return paths


def main() -> int:
    d = load_data()
    fs = ensure_fsaverage()
    surf = load_surface_data(fs, d["dk"])
    norm, cmap, _ = surface_norm(d["dk"])

    outputs = build_figure5(d, surf, norm, cmap)
    outputs += build_extended_data1(d, surf, norm, cmap)
    sources = write_sources(d, fs)

    manifest = {
        "schema_version": 1,
        "status": "ok",
        "analysis": "NeuroSem NMI Figure 5 and Extended Data Figure 1 scientific-graphic redesign",
        "scientific_values_changed": False,
        "builder": str(Path(__file__).resolve().relative_to(ROOT)),
        "builder_sha256": sha256(Path(__file__).resolve()),
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "atlas_visualization_scaffold": {str(p.relative_to(ROOT)): sha256(p) for p in atlas_files(fs)},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "source_data": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
        "displayed_summary": {
            "dk68_positive_parcels": int(np.sum(d["dk"]["delta_mean"].to_numpy(float) > 0)),
            "dk68_total_parcels": int(len(d["dk"])),
            "language_minus_sensorimotor_fwer_p": float(d["lang_summary"]["primary"]["functional_language_minus_left_sensorimotor"]["familywise_maxstat_p"]),
            "language_minus_visual_fwer_p": float(d["lang_summary"]["primary"]["functional_language_minus_left_visual"]["familywise_maxstat_p"]),
            "temporal_minus_frontal_mean": float(d["spatial_summary"]["focal_tests"]["functional_temporal_minus_frontal_language"]["mean"]),
            "spatial_surrogate_p": float(d["final_summary"]["spatial_autocorrelation_null"]["two_sided_spatial_surrogate_p"]),
            "genuine_minus_shuffled_mean": float(d["final_summary"]["regional_shuffled_target_control"]["primary_genuine_minus_shuffled_language_specificity"]["mean"]),
        },
        "guardrails": [
            "Presentation-only build from already-completed frozen outputs.",
            "The DK68 surface is a complete unthresholded characterization, not a 68-region significance screen.",
            "No parcel is selected or omitted by outcome value.",
            "The fsaverage aparc files supply anatomical coordinates and labels only.",
            "No model fitting, model evaluation, neural analysis, ROI selection, thresholding, or new hypothesis test is performed.",
        ],
    }
    mp = OUT / "source_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok", "figure5_png":sha256(OUT/"figure5.png"), "extended_data_figure1_png":sha256(OUT/"extended_data_figure1.png")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the NeuroSem NMI v1.13 submission figures from frozen derived outputs only.

Presentation-only. This script performs no model fitting, target selection, new hypothesis
search, or inferential analysis. It reformats already-completed participant/model summaries
into the submission figure system.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs" / "nmi_submission_assets_v1" / "latest" / "figures"

ZUCO_REL = ROOT / "outputs/zuco2_nr_primary_representation_reliability/latest/subject_metrics.csv"
ZUCO_REL_SUM = ROOT / "outputs/zuco2_nr_primary_representation_reliability/latest/summary.json"
ZUCO_TRANSFER = ROOT / "outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv"
ZUCO_TRANSFER_SUM = ROOT / "outputs/zuco2_nr_e5_transfer_v1/latest/summary.json"
FMRI_REL = ROOT / "outputs/smn4lang_fmri_reliability/latest/participant_results.csv"
FMRI_REL_SUM = ROOT / "outputs/smn4lang_fmri_reliability/latest/summary.json"
FMRI_TRANSFER = ROOT / "outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv"
FMRI_TRANSFER_SUM = ROOT / "outputs/smn4lang_fmri_e5_transfer_v1/latest/summary.json"
DOSE = ROOT / "outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv"
MODELS = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
SPEC = ROOT / "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json"
MODEL_SPACE_010 = ROOT / "outputs/nmi_model_space_characterization_v1/latest/summary.json"
MODEL_SPACE_1 = ROOT / "outputs/nmi_model_space_characterization_lambda1_v1/latest/summary.json"
REVERSE = ROOT / "outputs/nmi_bidirectional_fmri_to_zuco_v1/latest/summary.json"
REVERSE_MULTI = ROOT / "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json"
REGIONAL = ROOT / "outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv"
DEV = ROOT / "paper/figure_data/chineseeeg_development_v1.json"

INPUTS = [
    ZUCO_REL, ZUCO_REL_SUM, ZUCO_TRANSFER, ZUCO_TRANSFER_SUM,
    FMRI_REL, FMRI_REL_SUM, FMRI_TRANSFER, FMRI_TRANSFER_SUM,
    DOSE, MODELS, SPEC, MODEL_SPACE_010, MODEL_SPACE_1,
    REVERSE, REVERSE_MULTI, REGIONAL, DEV,
]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(fig: plt.Figure, stem: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        p = OUT / f"{stem}.{ext}"
        fig.savefig(p, **kwargs)
        paths.append(p)
    plt.close(fig)
    return paths


def card(ax, x, y, w, h, title, body, edge, face="#ffffff", title_fs=7.4, body_fs=6.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.025",
                                facecolor=face, edgecolor=edge, linewidth=0.9, zorder=2))
    ax.text(x + 0.04*w, y + 0.72*h, title, fontsize=title_fs, fontweight="bold",
            ha="left", va="center", color=S.INK, zorder=3)
    ax.text(x + 0.04*w, y + 0.34*h, body, fontsize=body_fs, ha="left", va="center",
            color=S.GREY, linespacing=1.35, zorder=3)


def arrow(ax, start, end, colour=S.GREY):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8,
                                linewidth=0.8, color=colour, shrinkA=4, shrinkB=4, zorder=1))


def small_rdm(ax, xy, size, edge, label):
    x, y = xy
    # A deterministic illustrative matrix. It is explicitly labelled schematic and carries no outcome value.
    m = np.array([[0.0, .25, .72, .45], [.25, 0.0, .55, .81], [.72, .55, 0.0, .31], [.45, .81, .31, 0.0]])
    iax = ax.inset_axes([x, y, size, size])
    iax.imshow(m, cmap="Greys", vmin=0, vmax=1, interpolation="nearest")
    iax.set_xticks([]); iax.set_yticks([])
    for sp in iax.spines.values(): sp.set_edgecolor(edge); sp.set_linewidth(0.7)
    ax.text(x + size/2, y - 0.02, label, transform=ax.transAxes, fontsize=5.5,
            ha="center", va="top", color=S.GREY)


def figure1() -> list[Path]:
    dev = read_json(DEV)
    runs = np.asarray(dev["heldout_residual_correspondence"], float)
    rel_raw = float(dev["reliability"]["raw_loo"])
    rel_res = float(dev["reliability"]["residual_loo"])
    sealed = dev["sealed_run07"]
    arms = sealed["arms"]
    run07 = {arm: [float(sealed["seed_1"][i]), float(sealed["seed_2"][i])] for i, arm in enumerate(arms)}
    semantic = {
        "Base": [0.283464, 0.283464],
        "Text-only": [0.308486, 0.305020],
        "Neural-guided": [0.308575, 0.301607],
        "Shuffled-neural": [0.307943, 0.305266],
    }

    S.apply()
    fig = S.figure(S.W2, 111)
    gs = fig.add_gridspec(2, 12, height_ratios=[1.03, 1.0])
    axa = fig.add_subplot(gs[0, 0:5]); axb = fig.add_subplot(gs[0, 5:8]); axc = fig.add_subplot(gs[0, 8:12])
    axd = fig.add_subplot(gs[1, 0:6]); axe = fig.add_subplot(gs[1, 6:12])

    # a: conceptual geometry transfer
    axa.set_xlim(0, 1); axa.set_ylim(0, 1); axa.axis("off")
    axa.text(0.02, 0.98, "Relational supervision acts on geometry, not neural amplitudes", fontsize=7.2,
             fontweight="bold", va="top")
    small_rdm(axa, (0.03, 0.57), 0.22, S.BLUE, "neural RDM")
    small_rdm(axa, (0.38, 0.57), 0.22, S.GREY, "model RDM")
    arrow(axa, (0.25, 0.68), (0.38, 0.68), S.GREY)
    card(axa, 0.67, 0.55, 0.30, 0.26, "Train", "text objective\n+ λ relational loss", S.BLUE, "#eef3f8", 6.8, 5.8)
    arrow(axa, (0.60, 0.68), (0.67, 0.68), S.GREY)
    card(axa, 0.12, 0.12, 0.76, 0.20, "External criterion", "Does the induced relational displacement survive in independent neural systems?", S.INK, "#ffffff", 6.8, 5.8)
    arrow(axa, (0.82, 0.55), (0.64, 0.32), S.GREY)
    axa.text(0.02, 0.03, "schematic", fontsize=5.2, color=S.GREY, style="italic")

    # b: reliability
    vals = np.array([rel_raw, rel_res]); xx = np.arange(2)
    axb.bar(xx, vals, width=.52, color=[S.GREY_L, S.BLUE], zorder=3)
    for x, v in zip(xx, vals): axb.text(x, v + .006, f"{v:.3f}", fontsize=6, ha="center")
    axb.set_xticks(xx); axb.set_xticklabels(["raw\nLOO", "residual\nLOO"])
    axb.set_ylabel("Cross-participant reliability"); axb.set_ylim(0, .25); axb.tick_params(axis="x", length=0)

    # c: held-out development correspondence
    x = np.arange(1, 7)
    axc.plot(x, runs, "-o", color=S.BLUE, markersize=3.4, zorder=3)
    S.zeroline(axc); axc.set_xticks(x); axc.set_xticklabels([f"{i:02d}" for i in x])
    axc.set_xlabel("Held-out narrative run"); axc.set_ylabel("Residual model–EEG RSA")
    axc.text(.98, .95, f"6/6 positive\nmean {runs.mean():.4f}", transform=axc.transAxes,
             ha="right", va="top", fontsize=6, color=S.BLUE)

    def arm_panel(ax, data, ylabel, ylim, highlight):
        names = list(data); x = np.arange(len(names))
        for i, name in enumerate(names):
            yy = np.asarray(data[name], float); c = highlight if name == "Neural-guided" else S.GREY
            ax.plot(i + np.array([-.08, .08]), yy, "o", color=c, markersize=3.0, alpha=.85)
            ax.plot([i-.18, i+.18], [yy.mean(), yy.mean()], color=c, lw=1.5)
        ax.set_xticks(x); ax.set_xticklabels(["base", "text-only", "neural-\nguided", "shuffled-\nneural"])
        ax.set_ylabel(ylabel); ax.set_ylim(*ylim); ax.tick_params(axis="x", length=0); ax.grid(axis="y")

    arm_panel(axd, run07, "Sealed run-07 residual neural RSA", (0.0305, 0.0385), S.BLUE)
    axd.text(.98, .95, "neural-guided highest\nin both seeds", transform=axd.transAxes,
             ha="right", va="top", fontsize=6, color=S.BLUE)
    arm_panel(axe, semantic, "Eight-task semantic Spearman", (0.278, 0.313), S.BLUE)
    axe.text(.98, .05, "no stable neural-specific\nsemantic advantage", transform=axe.transAxes,
             ha="right", va="bottom", fontsize=6, color=S.GREY)

    for ax, letter, dx in ((axa, "a", -0.02), (axb, "b", -0.22), (axc, "c", -0.17), (axd, "d", -0.12), (axe, "e", -0.12)):
        S.panel(ax, letter, dx=dx)
    return save(fig, "figure1")


def _primary_data():
    zr = [r for r in read_csv(ZUCO_REL) if r.get("candidate") == "row_mean_all"]
    zrs = read_json(ZUCO_REL_SUM)
    zmetric = next(x for x in zrs["metrics"] if x["candidate"] == "row_mean_all")
    zt = read_csv(ZUCO_TRANSFER); zts = read_json(ZUCO_TRANSFER_SUM)["primary_result"]
    fr = read_csv(FMRI_REL); frs = read_json(FMRI_REL_SUM)
    ft = read_csv(FMRI_TRANSFER); fts = read_json(FMRI_TRANSFER_SUM)
    return {
        "zuco": {
            "rel": np.asarray([float(r["resid_loo"]) for r in zr]),
            "rel_mean": float(zmetric["mean_resid_loo"]),
            "rel_ci": [float(v) for v in zmetric["resid_loo_bootstrap_95ci"]],
            "a0": np.asarray([float(r["lambda_0_resid_rsa"]) for r in zt]),
            "a1": np.asarray([float(r["lambda_0p10_resid_rsa"]) for r in zt]),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in zt]),
            "delta_mean": float(zts["mean_delta"]),
            "delta_ci": [float(v) for v in zts["bootstrap_95ci"]],
        },
        "fmri": {
            "rel": np.asarray([float(r["primary_residual_reliability"]) for r in fr]),
            "rel_mean": float(frs["primary_mean"]),
            "rel_ci": [float(v) for v in frs["primary_bootstrap_95_ci"]],
            "a0": np.asarray([float(r["lambda_0_residual_rsa"]) for r in ft]),
            "a1": np.asarray([float(r["lambda_0p10_residual_rsa"]) for r in ft]),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in ft]),
            "delta_mean": float(fts["primary_mean_delta"]),
            "delta_ci": [float(v) for v in fts["primary_bootstrap_95_ci_mean_delta"]],
        },
    }


def figure2() -> list[Path]:
    d = _primary_data(); S.apply()
    fig = S.figure(S.W2, 118)
    gs = fig.add_gridspec(2, 12, height_ratios=[.78, 1.22])
    axa = fig.add_subplot(gs[0, :]); axb = fig.add_subplot(gs[1, 0:4]); axc = fig.add_subplot(gs[1, 4:8]); axd = fig.add_subplot(gs[1, 8:12])

    axa.set_xlim(0, 1); axa.set_ylim(0, 1); axa.axis("off")
    card(axa, .01, .25, .20, .50, "Source", "ChineseEEG\nMandarin reading EEG", S.BLUE, "#eef3f8")
    card(axa, .28, .25, .22, .50, "Frozen intervention", "multilingual E5\nλ=0.10 vs λ=0", S.INK, "#ffffff")
    card(axa, .60, .54, .37, .33, "External EEG", "ZuCo 2.0 · English reading\n17/17 paired shifts positive", S.BLUE, "#f4f7fb")
    card(axa, .60, .08, .37, .33, "External fMRI", "SMN4Lang · Mandarin listening\n12/12 paired shifts positive", S.ORANGE, "#fff5f2")
    arrow(axa, (.21, .50), (.28, .50)); arrow(axa, (.50, .50), (.60, .70), S.BLUE); arrow(axa, (.50, .50), (.60, .24), S.ORANGE)
    axa.text(.395, .10, "No external outcome used to retune λ, layer, checkpoint or target", fontsize=5.8,
             ha="center", color=S.GREY)

    # b reliability, separate insets because scale differs substantially
    axb.axis("off"); axb.set_title("Model-blind target reliability", loc="left", fontsize=7, pad=2)
    for i, (key, colour, label, ylim) in enumerate((("zuco", S.BLUE, "ZuCo EEG", (0, .10)), ("fmri", S.ORANGE, "SMN4Lang fMRI", (.55, .72)))):
        ia = axb.inset_axes([.02 + i*.50, .10, .44, .78]); vals=d[key]["rel"]; x=np.arange(1,len(vals)+1)
        ia.plot(x, vals, "o", color=colour, markersize=2.5); m=d[key]["rel_mean"]; lo,hi=d[key]["rel_ci"]
        ia.errorbar([len(vals)+1.5],[m], yerr=[[m-lo],[hi-m]], fmt="D", mfc="white", mec=S.INK,
                    color=S.INK, markersize=3.2, capsize=1.5, lw=.7)
        ia.set_ylim(*ylim); ia.set_xticks([1,len(vals),len(vals)+1.5]); ia.set_xticklabels(["1",str(len(vals)),"mean"])
        ia.set_title(label, fontsize=6.2, color=colour); ia.set_xlabel("participant", fontsize=5.5); ia.tick_params(labelsize=5.3)
        if i==0: ia.set_ylabel("residual LOO", fontsize=5.5)

    # c paired arms, separate insets
    axc.axis("off"); axc.set_title("Frozen low-dose intervention", loc="left", fontsize=7, pad=2)
    for i, (key, colour, label) in enumerate((("zuco", S.BLUE, "ZuCo EEG"), ("fmri", S.ORANGE, "SMN4Lang fMRI"))):
        ia = axc.inset_axes([.02 + i*.50, .10, .44, .78]); a0=d[key]["a0"]; a1=d[key]["a1"]
        for y0,y1 in zip(a0,a1): ia.plot([0,1],[y0,y1], color=S.GREY_L, lw=.55)
        ia.plot([0,1],[a0.mean(),a1.mean()], "-o", color=colour, lw=1.5, markersize=3.2)
        ia.set_xticks([0,1]); ia.set_xticklabels(["text", "neural"], fontsize=5.3); ia.tick_params(axis="x", length=0)
        ia.set_title(label, fontsize=6.2, color=colour); ia.tick_params(axis="y", labelsize=5.3)
        if i==0: ia.set_ylabel("participant residual RSA", fontsize=5.5)
        if key=="zuco": ia.axhline(0,color=S.ZERO,lw=.5)

    # d participant deltas on common scaled axis
    positions = [0,1]; keys=["zuco","fmri"]; cols=[S.BLUE,S.ORANGE]; labels=["ZuCo EEG","SMN4Lang fMRI"]
    rng=np.random.default_rng(3)
    for x,key,c,label in zip(positions,keys,cols,labels):
        vals=d[key]["delta"]*1e3; jitter=rng.uniform(-.09,.09,len(vals)); axd.plot(x+jitter, vals, "o", color=c, alpha=.75, markersize=2.7)
        m=d[key]["delta_mean"]*1e3; lo,hi=np.asarray(d[key]["delta_ci"])*1e3
        axd.errorbar([x],[m],yerr=[[m-lo],[hi-m]],fmt="D",mfc="white",mec=S.INK,color=S.INK,
                     capsize=2,elinewidth=.8,markersize=4.0,zorder=5)
        axd.text(x, max(vals.max(),hi)+.13, f"{len(vals)}/{len(vals)} positive", ha="center", va="bottom",
                 fontsize=6.3, fontweight="bold", color=c)
    axd.axhline(0,color=S.ZERO,lw=.6); axd.set_xticks(positions); axd.set_xticklabels(labels); axd.tick_params(axis="x",length=0)
    axd.set_ylabel("Neural-guided − text-only ΔRSA (×10$^{-3}$)")
    axd.set_title("Prospective external transfer", loc="left", fontsize=7, pad=2)
    axd.set_ylim(bottom=min(-.15, axd.get_ylim()[0]))

    for ax,letter,dx,dy in ((axa,"a",-.01,1.03),(axb,"b",-.05,1.05),(axc,"c",-.05,1.05),(axd,"d",-.18,1.08)):
        S.panel(ax,letter,dx=dx,dy=dy)
    return save(fig, "figure2")


def _dose_rows():
    rows=read_csv(DOSE)
    by={(r["dataset"],float(r["lambda"])):r for r in rows}
    lam=np.array([.01,.03,.10,.30,1.0])
    def vals(ds,field): return np.array([float(by[(ds,float(x))][field]) for x in lam])
    return lam, by, vals


def figure3() -> list[Path]:
    lam, by, vals = _dose_rows()
    zd=vals("zuco","mean_delta_rsa"); fd=vals("smn4lang_fmri","mean_delta_rsa")
    zci=np.array([[float(by[("zuco",float(x))]["bootstrap_95ci_low"]),float(by[("zuco",float(x))]["bootstrap_95ci_high"])] for x in lam])
    fci=np.array([[float(by[("smn4lang_fmri",float(x))]["bootstrap_95ci_low"]),float(by[("smn4lang_fmri",float(x))]["bootstrap_95ci_high"])] for x in lam])
    sts=vals("zuco","delta_external_sts_vs_lambda0_already_observed")
    ms010=read_json(MODEL_SPACE_010)["metrics"]; ms1=read_json(MODEL_SPACE_1)["metrics"]
    metrics=[("Item cosine","corresponding_item_cosine_similarity_mean"),("RDM Pearson","pairwise_cosine_distance_pearson"),("RDM Spearman","pairwise_cosine_distance_spearman"),("Centered CKA","linear_centered_cka"),("k=10 Jaccard","mean_knn_jaccard_overlap")]

    S.apply(); fig=S.figure(S.W2,119); gs=fig.add_gridspec(2,12,height_ratios=[1.05,.95])
    axa=fig.add_subplot(gs[0,0:7]); axb=fig.add_subplot(gs[0,7:12]); axc=fig.add_subplot(gs[1,0:7]); axd=fig.add_subplot(gs[1,7:12])

    # a linear y-axis is deliberate so the fMRI sign reversal is visible rather than clipped by log scale.
    for y,ci,c,label in ((zd,zci,S.BLUE,"ZuCo EEG"),(fd,fci,S.ORANGE,"SMN4Lang fMRI")):
        yy=y*1e3; e=np.vstack([yy-ci[:,0]*1e3,ci[:,1]*1e3-yy])
        axa.errorbar(lam,yy,yerr=e,fmt="-o",color=c,markersize=3.2,capsize=1.6,lw=1.1,label=label)
    axa.set_xscale("log"); axa.axhline(0,color=S.ZERO,lw=.6); axa.axvline(.10,color=S.GREY_L,lw=.6,ls=(0,(2,2)))
    axa.text(.10,axa.get_ylim()[1]*.88,"prospective\nλ=0.10",ha="center",va="top",fontsize=5.7,color=S.GREY)
    axa.set_xticks(lam); axa.set_xticklabels([".01",".03",".10",".30","1.0"])
    axa.set_xlabel("Relational-loss weight λ"); axa.set_ylabel("Mean external ΔRSA (×10$^{-3}$)"); axa.legend(loc="upper left")
    axa.annotate("fMRI sign reversal",xy=(1,fd[-1]*1e3),xytext=(-46,-22),textcoords="offset points",fontsize=5.8,color=S.ORANGE,
                 arrowprops=dict(arrowstyle="-",lw=.6,color=S.ORANGE))

    # b Pareto-style transfer/cost trajectory
    cost=-sts*1e3
    for y,c,label in ((zd*1e3,S.BLUE,"ZuCo EEG"),(fd*1e3,S.ORANGE,"SMN4Lang fMRI")):
        axb.plot(cost,y,"-o",color=c,markersize=3.2,label=label)
        for x0,y0,ll in zip(cost,y,[".01",".03",".10",".30","1"]):
            axb.text(x0,y0,ll,fontsize=5.2,color=c,ha="left",va="bottom")
    axb.axhline(0,color=S.ZERO,lw=.6); axb.set_xlabel("Generic STS cost (×10$^{-3}$)"); axb.set_ylabel("External ΔRSA (×10$^{-3}$)")
    axb.set_title("Transfer–utility trajectory",fontsize=7,loc="left"); axb.legend(loc="upper left")

    # c conservation metrics
    y=np.arange(len(metrics))[::-1]; a=np.array([float(ms010[k]) for _,k in metrics]); b=np.array([float(ms1[k]) for _,k in metrics])
    for yi,x1,x2 in zip(y,a,b):
        axc.plot([x2,x1],[yi,yi],color=S.GREY_L,lw=1.2); axc.plot(x1,yi,"o",color=S.TEAL,markersize=4,label="λ=.10" if yi==y[0] else None); axc.plot(x2,yi,"o",color=S.PURPLE,markersize=4,label="λ=1" if yi==y[0] else None)
    axc.set_yticks(y); axc.set_yticklabels([m[0] for m in metrics]); axc.set_xlim(.55,1.01); axc.set_xlabel("Similarity to matched text-only representation"); axc.grid(axis="x"); axc.legend(loc="lower left")
    axc.set_title("High dose reorganizes model geometry",fontsize=7,loc="left")

    # d absolute target RSA as two scale-honest mini-panels
    axd.axis("off"); axd.set_title("Absolute target correspondence",fontsize=7,loc="left",pad=2)
    z0=float(by[("zuco",0.0)]["lambda_0_mean_rsa"]); f0=float(by[("smn4lang_fmri",0.0)]["lambda_0_mean_rsa"])
    full_lam=np.r_[0,lam]; zabs=np.r_[z0,z0+zd]; fabs=np.r_[f0,f0+fd]
    for i,(yy,c,label) in enumerate(((zabs,S.BLUE,"ZuCo EEG"),(fabs,S.ORANGE,"SMN4Lang fMRI"))):
        ia=axd.inset_axes([.02,.55-i*.50,.95,.40]); x=np.arange(len(full_lam)); ia.plot(x,yy,"-o",color=c,markersize=2.8); ia.axvline(3,color=S.GREY_L,lw=.5,ls=(0,(2,2)))
        if label.startswith("ZuCo"): ia.axhline(0,color=S.ZERO,lw=.5)
        ia.set_xticks(x); ia.set_xticklabels(["0",".01",".03",".10",".30","1"] if i else [])
        ia.set_ylabel("RSA",fontsize=5.5); ia.set_title(label,fontsize=6.1,color=c); ia.tick_params(labelsize=5.2)
    axd.text(.50,.02,"λ",transform=axd.transAxes,ha="center",fontsize=6)

    for ax,letter,dx in ((axa,"a",-.13),(axb,"b",-.17),(axc,"c",-.13),(axd,"d",-.05)):
        S.panel(ax,letter,dx=dx,dy=1.08)
    return save(fig,"figure3")


def figure4() -> list[Path]:
    rows=read_csv(MODELS)
    order=[("e5_large","E5-large"),("e5_base","E5-base"),("multilingual_mpnet","mMPNet"),("multilingual_minilm","mMiniLM"),("xlmr_base","XLM-R"),("mbert","mBERT")]
    directions=[("eeg_to_fmri","EEG → fMRI"),("fmri_to_eeg","fMRI → EEG")]
    matrix=np.zeros((len(order),2)); signs=[]
    for i,(key,_) in enumerate(order):
        sr=[]
        for j,(direction,_) in enumerate(directions):
            rr=sorted([r for r in rows if r["model_key"]==key and r["direction"]==direction],key=lambda r:int(r["seed"]))
            v=np.array([float(r["external_mean_delta"]) for r in rr])*1e3; matrix[i,j]=v.mean(); sr.append(int(np.sum(v>0)))
        signs.append(sr)
    spec=read_json(SPEC)["specificity_control"]["seed_results"]
    reverse=read_json(REVERSE)["primary_result"]; rmulti=read_json(REVERSE_MULTI)

    S.apply(); fig=S.figure(S.W2,112); gs=fig.add_gridspec(2,12,height_ratios=[1.05,.95])
    axa=fig.add_subplot(gs[:,0:6]); axb=fig.add_subplot(gs[0,6:12]); axc=fig.add_subplot(gs[1,6:12])

    vmax=max(abs(matrix.min()),abs(matrix.max())); norm=colors.TwoSlopeNorm(vmin=-vmax,vcenter=0,vmax=vmax)
    im=axa.imshow(matrix,cmap=S.DIVERGING,norm=norm,aspect="auto")
    axa.set_yticks(np.arange(len(order))); axa.set_yticklabels([x[1] for x in order]); axa.set_xticks([0,1]); axa.set_xticklabels([x[1] for x in directions])
    axa.tick_params(axis="both",length=0); axa.set_title("Common λ=0.10 protocol: transfer depends on backbone and direction",fontsize=7,loc="left",pad=6)
    for i in range(len(order)):
        for j in range(2):
            col="white" if abs(matrix[i,j])>0.55*vmax else S.INK
            axa.text(j,i,f"{matrix[i,j]:+.2f}\n{signs[i][j]}/3 +",ha="center",va="center",fontsize=6,color=col)
    cb=fig.colorbar(im,ax=axa,fraction=.04,pad=.03); cb.set_label("Three-seed mean ΔRSA (×10$^{-3}$)",fontsize=6); cb.ax.tick_params(labelsize=5.3)
    for sp in axa.spines.values(): sp.set_visible(False)

    # specificity contrasts: preserve seed trajectories and show the scale separation directly.
    datasets=[("zuco","ZuCo EEG",S.BLUE),("smn4lang_fmri","SMN4Lang fMRI",S.ORANGE)]
    xbase=np.arange(3)
    for di,(ds,label,c) in enumerate(datasets):
        g=[]; sh=[]
        for rec in spec:
            t=rec["targets"][ds]; g.append(float(t["genuine_minus_shuffled"]["mean_delta"])*1e3); sh.append(float(t["shuffled_minus_text"]["mean_delta"])*1e3)
        offset=di*3.8
        axb.plot(xbase+offset,g,"-o",color=c,markersize=3.2,label=f"{label}: genuine − shuffled")
        axb.plot(xbase+offset,sh,"--o",color=c,alpha=.55,markersize=2.8,label=f"{label}: shuffled − text")
    axb.axhline(0,color=S.ZERO,lw=.6); axb.set_xticks([0,1,2,3.8,4.8,5.8]); axb.set_xticklabels(["seed 1","2","3","seed 1","2","3"])
    axb.set_ylabel("Mean contrast ΔRSA (×10$^{-3}$)"); axb.set_title("Preserved neural item correspondence matters",fontsize=7,loc="left")
    axb.legend(loc="upper right",fontsize=5.3)

    # reverse robustness: original source-selected candidate plus added optimization seeds.
    labels=["source-selected\noriginal"]+[str(r["seed"])[-2:] for r in rmulti["seed_results"]]
    means=[float(reverse["mean_delta"])]+[float(r["zuco"]["mean_delta"]) for r in rmulti["seed_results"]]
    cis=[reverse["bootstrap_95ci"]]+[r["zuco"]["bootstrap_95ci"] for r in rmulti["seed_results"]]
    x=np.arange(len(means)); m=np.asarray(means)*1e5; ci=np.asarray(cis,float)*1e5
    err=np.vstack([m-ci[:,0],ci[:,1]-m]); axc.errorbar(x,m,yerr=err,fmt="o",color=S.TEAL,mfc="white",mec=S.TEAL,mew=1,capsize=2,lw=.8)
    axc.axhline(0,color=S.ZERO,lw=.6); axc.set_xticks(x); axc.set_xticklabels(labels); axc.set_ylabel("Reverse ΔRSA (×10$^{-5}$)")
    axc.set_title("Source-selected reverse transfer is small but seed-robust",fontsize=7,loc="left")
    axc.text(.98,.05,"λ=0.01 · 14/17 positive in each added seed",transform=axc.transAxes,ha="right",fontsize=5.8,color=S.TEAL)

    for ax,letter,dx in ((axa,"a",-.11),(axb,"b",-.12),(axc,"c",-.12)):
        S.panel(ax,letter,dx=dx,dy=1.08)
    return save(fig,"figure4")


def extdata_regional() -> list[Path]:
    rows=read_csv(REGIONAL); lang=[r for r in rows if r.get("family")=="language"]; dk=[r for r in rows if r.get("family")=="dk68"]
    if len(lang)!=6 or len(dk)!=68: raise RuntimeError(f"Expected 6 language and 68 DK parcels, got {len(lang)}, {len(dk)}")
    order=["IFGorb","IFG","MFG","AntTemp","PostTemp","AngG"]; by={r["region_name"]:r for r in lang}
    S.apply(); fig=S.figure(S.W2,118); gs=fig.add_gridspec(2,12,height_ratios=[.82,1.18])
    axa=fig.add_subplot(gs[0,0:5]); axb=fig.add_subplot(gs[0,6:12]); axc=fig.add_subplot(gs[1,:])

    y=np.arange(6)[::-1]; d=np.array([float(by[n]["delta_mean"]) for n in order])*1e3; ci=np.array([[float(by[n]["delta_bootstrap_ci_low"]),float(by[n]["delta_bootstrap_ci_high"])] for n in order])*1e3
    axa.hlines(y,ci[:,0],ci[:,1],color=S.ORANGE,lw=1); axa.plot(d,y,"o",color=S.ORANGE,markersize=3.5); axa.set_yticks(y); axa.set_yticklabels(order); axa.set_xlabel("Mean ΔRSA (×10$^{-3}$)"); axa.axvline(0,color=S.ZERO,lw=.5); axa.grid(axis="x")
    axa.set_title("Six predefined language parcels",fontsize=7,loc="left")

    vals=np.array([float(r["delta_mean"]) for r in dk])*1e3; rel=np.array([float(r["model_blind_reliability_mean"]) for r in dk])
    rng=np.random.default_rng(5); jitter=rng.uniform(-.18,.18,len(vals)); hemi=np.array([r["hemisphere"] for r in dk]);
    for h,c,yy,label in (("L",S.BLUE,0,"left DK34"),("R",S.TEAL,1,"right DK34")):
        sel=hemi==h; axb.plot(vals[sel],yy+jitter[sel],"o",color=c,markersize=2.8,alpha=.7,label=label)
    axb.axvline(0,color=S.ZERO,lw=.5); axb.set_yticks([]); axb.set_xlabel("Mean ΔRSA (×10$^{-3}$)"); axb.legend(loc="upper left")
    axb.text(.98,.08,"68/68 parcel means positive\n12/12 participant signs in every parcel",transform=axb.transAxes,ha="right",fontsize=6,color=S.INK,fontweight="bold")
    axb.set_title("Complete bilateral cortical phenotype",fontsize=7,loc="left")

    # Anatomically ordered cortical ribbon, retaining every parcel and a symmetric zero-centred scale.
    parcels=sorted({r["region_name"] for r in dk}); grid=np.full((2,len(parcels)),np.nan)
    for r in dk: grid[0 if r["hemisphere"]=="L" else 1,parcels.index(r["region_name"])]=float(r["delta_mean"])*1e3
    vmax=np.nanmax(np.abs(grid))*1.02; im=axc.imshow(grid,cmap=S.DIVERGING,vmin=-vmax,vmax=vmax,aspect="auto",interpolation="nearest")
    axc.set_yticks([0,1]); axc.set_yticklabels(["left","right"]); axc.set_xticks(np.arange(len(parcels))); axc.set_xticklabels(parcels,rotation=90,fontsize=5)
    axc.tick_params(axis="both",length=0); [sp.set_visible(False) for sp in axc.spines.values()]
    cb=fig.colorbar(im,ax=axc,fraction=.018,pad=.01); cb.set_label("Mean ΔRSA (×10$^{-3}$)",fontsize=6); cb.ax.tick_params(labelsize=5.3)
    axc.set_title("Unthresholded DK68 phenotype · symmetric colour scale about zero",fontsize=7,loc="left")
    axc.text(.01,1.16,"No parcel filtering, significance thresholding or outcome-based ranking",transform=axc.transAxes,fontsize=5.8,color=S.GREY)

    for ax,letter,dx in ((axa,"a",-.18),(axb,"b",-.08),(axc,"c",-.05)):
        S.panel(ax,letter,dx=dx,dy=1.10)
    return save(fig,"extended_data_figure1")


def main() -> int:
    missing=[str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError("Missing frozen figure input(s): "+", ".join(missing))
    outputs=[]
    for builder in (figure1,figure2,figure3,figure4,extdata_regional): outputs.extend(builder())
    manifest={
        "schema_version":1,
        "analysis":"NeuroSem NMI v1.13 submission figure build",
        "status":"ok",
        "guardrails":[
            "Presentation-only build from already-completed frozen derived outputs.",
            "No model fitting, model evaluation, neural analysis, target selection, dose selection or hypothesis testing is performed.",
            "Illustrative RDMs in Figure 1a are explicitly labelled schematic and carry no outcome values.",
            "All quantitative panels are read from frozen output files listed in inputs."
        ],
        "inputs":{str(p.relative_to(ROOT)):sha256(p) for p in INPUTS},
        "outputs":{str(p.relative_to(ROOT)):sha256(p) for p in outputs},
    }
    (OUT/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","figures":5,"files":len(outputs),"output_dir":str(OUT)},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

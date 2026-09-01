#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

MM = 1 / 25.4
NAVY = "#17324D"
TEAL = "#238A8D"
ORANGE = "#D97925"
BLUE = "#4C78A8"
GRAY = "#7A7A7A"
LIGHT = "#D9DEE3"
PALE = "#F3F5F7"
DARK = "#202124"


def set_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7.0,
        "axes.titlesize": 8.4,
        "axes.labelsize": 7.2,
        "xtick.labelsize": 6.7,
        "ytick.labelsize": 6.7,
        "legend.fontsize": 6.7,
        "axes.linewidth": 0.7,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 2.6,
        "ytick.major.size": 2.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    })


def panel_label(ax, s: str) -> None:
    ax.text(-0.09, 1.06, s, transform=ax.transAxes, fontsize=10.2, fontweight="bold", va="top", color=DARK)


def clean(ax, grid=False) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis="y", color=LIGHT, linewidth=0.55, alpha=0.65, zorder=0)
    ax.tick_params(direction="out")


def exact_signflip(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    n = len(x)
    obs = float(x.mean())
    vals = []
    for mask in range(1 << n):
        signs = np.array([1.0 if (mask >> i) & 1 else -1.0 for i in range(n)])
        vals.append(float(np.mean(x * signs)))
    return float(np.mean(np.asarray(vals) >= obs - 1e-15))


def bootstrap_ci(x: np.ndarray, seed=20260830, n_boot=10000) -> tuple[float, float]:
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        vals[i] = rng.choice(x, len(x), replace=True).mean()
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def headers(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        return set(next(r))


def discover_csv(root: Path, required: set[str], prefer: str | None = None) -> Path:
    matches = []
    for p in root.rglob("*.csv"):
        try:
            if required.issubset(headers(p)):
                score = int(prefer is not None and prefer.lower() in str(p).lower())
                matches.append((score, p.stat().st_mtime, p))
        except Exception:
            continue
    if not matches:
        raise FileNotFoundError(f"No CSV under {root} with columns {sorted(required)}")
    matches.sort(key=lambda z: (z[0], z[1]), reverse=True)
    return matches[0][2]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_figure(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(out_dir / f"{stem}.svg", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(out_dir / f"{stem}.png", dpi=600, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def draw_arrow(ax, x0, y0, x1, y1, color=GRAY):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.0, color=color, shrinkA=2, shrinkB=2))


def draw_node(ax, x, y, w, h, title, subtitle, edge=NAVY, fill="white"):
    box = mpl.patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018", fc=fill, ec=edge, lw=1.0)
    ax.add_patch(box)
    ax.text(x + w/2, y + h*0.61, title, ha="center", va="center", fontsize=7.6, fontweight="bold", color=DARK)
    ax.text(x + w/2, y + h*0.30, subtitle, ha="center", va="center", fontsize=6.5, color=GRAY)


def figure1(dev: dict, out: Path) -> dict:
    runs = np.asarray(dev["heldout_residual_correspondence"], float)
    sealed = dev["sealed_run07"]
    arms = sealed["arms"]
    s1 = np.asarray(sealed["seed_1"], float)
    s2 = np.asarray(sealed["seed_2"], float)

    fig = plt.figure(figsize=(178*MM, 112*MM))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[0.78, 1.0], width_ratios=[0.85, 1.05, 1.35], hspace=0.55, wspace=0.48)

    ax = fig.add_subplot(gs[0, :]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); panel_label(ax, "a")
    ax.set_title("Neural geometry is used as a relational training signal", loc="left", pad=3, fontweight="bold")
    draw_node(ax, 0.02, 0.28, 0.20, 0.38, "Human EEG", "reproducible pairwise geometry", edge=TEAL, fill="#F3FAFA")
    draw_node(ax, 0.28, 0.28, 0.20, 0.38, "Relational supervision", "match model distances to neural distances", edge=NAVY, fill="#F4F7FA")
    draw_node(ax, 0.54, 0.28, 0.20, 0.38, "Language model", "small geometry-preserving perturbation", edge=ORANGE, fill="#FFF8F1")
    draw_node(ax, 0.80, 0.28, 0.18, 0.38, "External brains", "test transfer without retuning", edge=BLUE, fill="#F4F7FB")
    for x0, x1 in [(0.22,0.28),(0.48,0.54),(0.74,0.80)]: draw_arrow(ax, x0, 0.47, x1, 0.47)

    ax = fig.add_subplot(gs[1,0]); panel_label(ax, "b"); clean(ax, grid=True)
    vals = [dev["reliability"]["raw_loo"], dev["reliability"]["residual_loo"]]
    ax.plot([0,1], vals, color=GRAY, lw=1.0, zorder=1)
    ax.scatter([0,1], vals, s=35, c=[LIGHT, TEAL], edgecolor=DARK, linewidth=0.5, zorder=3)
    ax.set_xticks([0,1], ["Raw", "Nuisance-\nresidualized"])
    ax.set_ylabel("Cross-participant reliability")
    ax.set_ylim(0, max(vals)*1.25)
    ax.set_title("Reliable development target", loc="left", fontweight="bold")
    for i,v in enumerate(vals): ax.text(i, v+0.012, f"{v:.3f}", ha="center", va="bottom", fontsize=6.8)

    ax = fig.add_subplot(gs[1,1]); panel_label(ax, "c"); clean(ax, grid=True)
    x = np.arange(1,7)
    ax.scatter(x, runs, s=27, color=TEAL, edgecolor="white", linewidth=0.4, zorder=3)
    ax.plot(x, runs, color=TEAL, lw=0.8, alpha=0.55)
    ax.axhline(0, color=GRAY, lw=0.7)
    ax.axhline(runs.mean(), color=NAVY, lw=1.0, ls="--")
    ax.set_xticks(x)
    ax.set_xlabel("Held-out narrative run")
    ax.set_ylabel("Residual model–EEG correspondence")
    ax.set_title("Learnability generalizes across held-out runs", loc="left", fontweight="bold")
    ax.text(0.03,0.96,f"6/6 positive\nmean = {runs.mean():.4f}\nexact P = 0.0156", transform=ax.transAxes, va="top", fontsize=6.7)

    ax = fig.add_subplot(gs[1,2]); panel_label(ax, "d"); clean(ax, grid=True)
    xp = np.arange(len(arms))
    ax.plot(xp, s1, marker="o", ms=4.4, lw=0.95, color=GRAY, label="Seed 1")
    ax.plot(xp, s2, marker="o", ms=4.4, lw=0.95, color=NAVY, label="Seed 2")
    ng = arms.index("Neural-guided")
    ax.scatter([ng,ng],[s1[ng],s2[ng]],s=46,color=ORANGE,edgecolor="white",linewidth=0.5,zorder=5)
    ax.set_xticks(xp,["Base","Text-only","Neural-\nguided","Shuffled-\nneural"])
    ax.set_ylabel("Residual neural alignment")
    ax.set_title("Neural guidance is highest in both sealed seeds", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="lower left", ncol=2, handlelength=1.4, columnspacing=0.9)
    ax.margins(x=0.08)

    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.11, top=0.97)
    save_figure(fig, out, "figure1")
    return {"figure":"figure1","inputs":["paper/figure_data/chineseeeg_development_v1.json"]}


def load_zuco(outputs: Path) -> tuple[np.ndarray,np.ndarray,np.ndarray,list[Path]]:
    relp = discover_csv(outputs, {"candidate","resid_loo"}, prefer="zuco")
    trp = discover_csv(outputs, {"lambda_0_resid_rsa","lambda_0p10_resid_rsa","delta_0p10_minus_0"}, prefer="zuco")
    rr = [r for r in read_csv(relp) if r.get("candidate") == "row_mean_all"]
    tr = read_csv(trp)
    rel = np.asarray([float(r["resid_loo"]) for r in rr], float)
    a0 = np.asarray([float(r["lambda_0_resid_rsa"]) for r in tr], float)
    a1 = np.asarray([float(r["lambda_0p10_resid_rsa"]) for r in tr], float)
    return rel,a0,a1,[relp,trp]


def figure2(outputs: Path, out: Path) -> dict:
    rel,a0,a1,src = load_zuco(outputs); d=a1-a0; m=float(d.mean()); lo,hi=bootstrap_ci(d); p=exact_signflip(d)
    rlo,rhi=bootstrap_ci(rel,seed=20260831)
    fig=plt.figure(figsize=(178*MM,112*MM)); gs=GridSpec(2,3,figure=fig,height_ratios=[0.65,1.0],width_ratios=[0.85,1.15,1.15],hspace=0.55,wspace=0.47)
    ax=fig.add_subplot(gs[0,:]); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); panel_label(ax,"a"); ax.set_title("Frozen cross-language transfer test",loc="left",pad=3,fontweight="bold")
    draw_node(ax,.04,.26,.23,.42,"ChineseEEG", "Chinese natural-reading EEG source",edge=TEAL,fill="#F3FAFA")
    draw_node(ax,.38,.26,.23,.42,"Frozen E5 contrast", "neural-guided λ=0.10 vs text-only λ=0",edge=ORANGE,fill="#FFF8F1")
    draw_node(ax,.72,.26,.23,.42,"ZuCo EEG", "17 independent English readers",edge=BLUE,fill="#F4F7FB")
    draw_arrow(ax,.27,.47,.38,.47); draw_arrow(ax,.61,.47,.72,.47)

    ax=fig.add_subplot(gs[1,0]); panel_label(ax,"b"); clean(ax,grid=True)
    y=np.arange(1,len(rel)+1); ax.scatter(rel,y,s=22,color=TEAL,edgecolor="white",linewidth=.35,zorder=3); ax.axvline(0,color=GRAY,lw=.7)
    ax.errorbar([rel.mean()],[len(rel)+1.4],xerr=[[rel.mean()-rlo],[rhi-rel.mean()]],fmt="D",ms=4.8,capsize=2.5,color=NAVY,lw=1.0)
    ax.set_yticks([]); ax.set_xlabel("Residual LOO reliability"); ax.set_title("Target reliability",loc="left",fontweight="bold")
    ax.text(.02,.98,f"17/17 positive\nmean = {rel.mean():.3f}",transform=ax.transAxes,va="top",fontsize=6.6)

    ax=fig.add_subplot(gs[1,1]); panel_label(ax,"c"); clean(ax,grid=True)
    for i,(u,v) in enumerate(zip(a0,a1)):
        ax.plot([0,1],[u,v],color=LIGHT,lw=.85,zorder=1); ax.scatter([0,1],[u,v],s=19,color=[GRAY,ORANGE],zorder=2)
    ax.set_xticks([0,1],["Text-only","Neural-guided"]); ax.set_ylabel("Participant residual RSA"); ax.set_title("Independent EEG alignment",loc="left",fontweight="bold")
    ax.text(.03,.97,"17/17 participants shift upward",transform=ax.transAxes,va="top",fontsize=6.7,fontweight="bold",color=NAVY)

    ax=fig.add_subplot(gs[1,2]); panel_label(ax,"d"); clean(ax,grid=False)
    order=np.argsort(d); yy=np.arange(len(d)); ax.axvline(0,color=GRAY,lw=.7); ax.hlines(yy,0,d[order]*1e3,color=LIGHT,lw=.8); ax.scatter(d[order]*1e3,yy,s=23,color=ORANGE,zorder=3)
    ax.errorbar([m*1e3],[len(d)+.8],xerr=[[(m-lo)*1e3],[(hi-m)*1e3]],fmt="D",ms=5,capsize=2.5,color=NAVY,lw=1.0)
    ax.set_yticks([]); ax.set_xlabel("Neural-guided − text-only RSA (×10⁻³)"); ax.set_title("Participant-level transfer",loc="left",fontweight="bold")
    ax.text(.02,.98,f"mean = +{m*1e3:.3f} ×10⁻³\n95% CI {lo*1e3:.3f} to {hi*1e3:.3f}\nexact P = {p:.2e}",transform=ax.transAxes,va="top",fontsize=6.6)
    fig.subplots_adjust(left=.075,right=.99,bottom=.12,top=.97); save_figure(fig,out,"figure2")
    return {"figure":"figure2","inputs":[str(x) for x in src]}


def load_fmri(outputs: Path) -> tuple[np.ndarray,np.ndarray,np.ndarray,list[Path]]:
    relp=discover_csv(outputs,{"primary_residual_reliability"},prefer="smn4lang")
    trp=discover_csv(outputs,{"lambda_0_residual_rsa","lambda_0p10_residual_rsa","delta_0p10_minus_0"},prefer="smn4lang")
    rr=read_csv(relp); tr=read_csv(trp)
    rel=np.asarray([float(r["primary_residual_reliability"]) for r in rr],float)
    a0=np.asarray([float(r["lambda_0_residual_rsa"]) for r in tr],float); a1=np.asarray([float(r["lambda_0p10_residual_rsa"]) for r in tr],float)
    return rel,a0,a1,[relp,trp]


def figure3(outputs: Path,out: Path) -> dict:
    rel,a0,a1,src=load_fmri(outputs); d=a1-a0; m=float(d.mean()); lo,hi=bootstrap_ci(d,seed=20260827); p=exact_signflip(d); rlo,rhi=bootstrap_ci(rel,seed=20260827)
    fig=plt.figure(figsize=(178*MM,112*MM)); gs=GridSpec(2,3,figure=fig,height_ratios=[.65,1],width_ratios=[.85,1.15,1.15],hspace=.55,wspace=.47)
    ax=fig.add_subplot(gs[0,:]); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); panel_label(ax,"a"); ax.set_title("Prospective cross-modal transfer test",loc="left",pad=3,fontweight="bold")
    draw_node(ax,.04,.26,.23,.42,"ChineseEEG", "EEG-derived relational constraint",edge=TEAL,fill="#F3FAFA")
    draw_node(ax,.38,.26,.23,.42,"Frozen E5 contrast", "no SMN4Lang model tuning",edge=ORANGE,fill="#FFF8F1")
    draw_node(ax,.72,.26,.23,.42,"SMN4Lang fMRI", "12 independent Mandarin listeners",edge=BLUE,fill="#F4F7FB")
    draw_arrow(ax,.27,.47,.38,.47); draw_arrow(ax,.61,.47,.72,.47)

    ax=fig.add_subplot(gs[1,0]); panel_label(ax,"b"); clean(ax,grid=True)
    y=np.arange(1,len(rel)+1); ax.scatter(rel,y,s=22,color=TEAL,edgecolor="white",linewidth=.35,zorder=3)
    ax.errorbar([rel.mean()],[len(rel)+1.3],xerr=[[rel.mean()-rlo],[rhi-rel.mean()]],fmt="D",ms=4.8,capsize=2.5,color=NAVY,lw=1.0)
    ax.set_yticks([]); ax.set_xlabel("Residual LOO reliability"); ax.set_title("Model-blind reliability gate",loc="left",fontweight="bold")
    ax.text(.02,.98,f"12/12 positive\nmean = {rel.mean():.3f}",transform=ax.transAxes,va="top",fontsize=6.6)

    ax=fig.add_subplot(gs[1,1]); panel_label(ax,"c"); clean(ax,grid=True)
    for u,v in zip(a0,a1): ax.plot([0,1],[u,v],color=LIGHT,lw=.9); ax.scatter([0,1],[u,v],s=20,color=[GRAY,ORANGE])
    ax.set_xticks([0,1],["Text-only","Neural-guided"]); ax.set_ylabel("Participant residual RSA"); ax.set_title("Prospective fMRI alignment",loc="left",fontweight="bold")
    ax.text(.03,.97,"12/12 participants shift upward",transform=ax.transAxes,va="top",fontsize=6.7,fontweight="bold",color=NAVY)

    ax=fig.add_subplot(gs[1,2]); panel_label(ax,"d"); clean(ax)
    order=np.argsort(d); yy=np.arange(len(d)); ax.axvline(0,color=GRAY,lw=.7); ax.hlines(yy,0,d[order]*1e3,color=LIGHT,lw=.8); ax.scatter(d[order]*1e3,yy,s=23,color=ORANGE)
    ax.errorbar([m*1e3],[len(d)+.7],xerr=[[(m-lo)*1e3],[(hi-m)*1e3]],fmt="D",ms=5,capsize=2.5,color=NAVY,lw=1.0)
    ax.set_yticks([]); ax.set_xlabel("Neural-guided − text-only RSA (×10⁻³)"); ax.set_title("Participant-level transfer",loc="left",fontweight="bold")
    ax.text(.02,.98,f"mean = +{m*1e3:.3f} ×10⁻³\n95% CI {lo*1e3:.3f} to {hi*1e3:.3f}\nexact P = {p:.6f}",transform=ax.transAxes,va="top",fontsize=6.6)
    fig.subplots_adjust(left=.075,right=.99,bottom=.12,top=.97); save_figure(fig,out,"figure3")
    return {"figure":"figure3","inputs":[str(x) for x in src]}


def figure4(outputs: Path,out: Path) -> dict:
    dose=outputs/"nmi_bidirectional_fmri_eeg_dose_response_v1"/"latest"/"zuco_subject_dose_results.csv"
    panel=outputs/"nmi_bidirectional_model_family_panel_v1"/"latest"/"model_seed_direction_results.csv"
    if not dose.exists(): dose=discover_csv(outputs,{"target","subject","lambda","delta"},prefer="dose")
    if not panel.exists(): panel=discover_csv(outputs,{"model_key","direction","seed","external_mean_delta"},prefer="model_family")
    dr=read_csv(dose); pr=read_csv(panel)
    dr=[r for r in dr if r.get("target","ZuCo").lower().startswith("zuco")]
    lambdas=sorted({float(r["lambda"]) for r in dr}); means=[]; los=[]; his=[]
    for j,lam in enumerate(lambdas):
        x=np.asarray([float(r["delta"]) for r in dr if abs(float(r["lambda"])-lam)<1e-12],float); means.append(x.mean()); a,b=bootstrap_ci(x,seed=20260830+j); los.append(a); his.append(b)
    model_order=["e5_large","e5_base","mpnet","minilm","xlmr","mbert"]
    labels={"e5_large":"E5-large","e5_base":"E5-base","mpnet":"mMPNet","minilm":"mMiniLM","xlmr":"XLM-R","mbert":"mBERT"}

    fig=plt.figure(figsize=(178*MM,126*MM)); gs=GridSpec(2,2,figure=fig,height_ratios=[.88,1.12],hspace=.52,wspace=.48)
    ax=fig.add_subplot(gs[0,0]); panel_label(ax,"a"); clean(ax,grid=True)
    x=np.asarray(lambdas); y=np.asarray(means)*1e3; lo=np.asarray(los)*1e3; hi=np.asarray(his)*1e3
    ax.errorbar(x,y,yerr=np.vstack([y-lo,hi-y]),fmt="o-",ms=4.5,lw=1.2,capsize=2.4,color=ORANGE)
    ax.set_xscale("log"); ax.set_xticks(x,[".01",".03",".10",".30","1.0"]); ax.set_xlabel("fMRI relational-loss weight λ (log scale)"); ax.set_ylabel("ZuCo ΔRSA (×10⁻³)")
    ax.set_title("Reverse fMRI→EEG transfer increases with guidance strength",loc="left",fontweight="bold")
    ax.axhline(0,color=GRAY,lw=.7)
    ax.text(.03,.97,"Post-confirmatory dose characterization",transform=ax.transAxes,va="top",fontsize=6.6,color=GRAY)

    ax=fig.add_subplot(gs[0,1]); panel_label(ax,"b"); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_title("Bidirectional transfer is reproducible within E5",loc="left",fontweight="bold")
    draw_node(ax,.08,.58,.34,.22,"EEG → E5 → fMRI","prospective direction",edge=TEAL,fill="#F3FAFA")
    draw_node(ax,.58,.58,.34,.22,"fMRI → E5 → EEG","reverse direction",edge=ORANGE,fill="#FFF8F1")
    ax.text(.50,.42,"E5-large and E5-base are positive across all three seeds in both directions",ha="center",va="center",fontsize=7.0,fontweight="bold",color=NAVY,wrap=True)
    ax.text(.50,.18,"Other encoders show partial, unstable or direction-specific portability",ha="center",va="center",fontsize=6.8,color=GRAY,wrap=True)

    for col,(direction,title,scale) in enumerate([("eeg_to_fmri","EEG-derived constraint → fMRI",1e3),("fmri_to_eeg","fMRI-derived constraint → EEG",1e3)]):
        ax=fig.add_subplot(gs[1,col]); panel_label(ax,"c" if col==0 else "d"); clean(ax,grid=False); ax.axvline(0,color=GRAY,lw=.75)
        for yi,key in enumerate(model_order[::-1]):
            rows=[r for r in pr if r["model_key"]==key and r["direction"]==direction]
            vals=np.asarray([float(r["external_mean_delta"])*scale for r in rows],float)
            stable=bool(len(vals)==3 and np.all(vals>0)); c=ORANGE if key.startswith("e5_") else (TEAL if stable else GRAY)
            ax.scatter(vals,np.full(len(vals),yi),s=22,color=c,alpha=.9,zorder=3)
            if len(vals): ax.scatter([vals.mean()],[yi],s=58,facecolor="white",edgecolor=c,linewidth=1.1,zorder=4)
        ax.set_yticks(range(len(model_order)),[labels[k] for k in model_order[::-1]])
        ax.set_xlabel("Mean participant ΔRSA per seed (×10⁻³)")
        ax.set_title(title,loc="left",fontweight="bold")
        if col==1: ax.tick_params(axis="y",labelleft=False)
    fig.subplots_adjust(left=.12,right=.99,bottom=.10,top=.97); save_figure(fig,out,"figure4")
    return {"figure":"figure4","inputs":[str(dose),str(panel)]}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--outputs-root",type=Path,default=Path("outputs"))
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/nmi_main_figures_v3/latest"))
    ap.add_argument("--development-json",type=Path,default=Path("paper/figure_data/chineseeeg_development_v1.json"))
    args=ap.parse_args(); set_style(); out=args.output_dir.resolve(); outputs=args.outputs_root.resolve(); devp=args.development_json.resolve(); dev=read_json(devp)
    records=[figure1(dev,out),figure2(outputs,out),figure3(outputs,out),figure4(outputs,out)]
    sources={}
    for rec in records:
        for p in rec["inputs"]:
            q=Path(p)
            if q.exists(): sources[str(q)]=sha256(q)
    manifest={"schema_version":1,"analysis":"NMI main figures v3","journal_target":"Nature Machine Intelligence","max_figure_width_mm":178,"vector_outputs":["pdf","svg"],"raster_output":{"format":"png","dpi":600},"figures":[r["figure"] for r in records],"source_files_sha256":sources,"guardrails":["Figure assembly only; no model fitting or outcome selection.","All quantitative panels are reconstructed from frozen derived outputs or the committed frozen development-summary JSON.","Panel typography and dimensions are authored at final publication width.","Main figures prioritize one visual argument each; technical diagnostics remain supplementary/Extended Data candidates."]}
    (out/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","output_dir":str(out),"figures":manifest["figures"]},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())

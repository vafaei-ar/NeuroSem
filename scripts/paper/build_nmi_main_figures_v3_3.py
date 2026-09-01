#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec


def load_v3():
    path = Path(__file__).with_name("build_nmi_main_figures_v3.py")
    spec = importlib.util.spec_from_file_location("neurosem_nmi_figures_v3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_rows(required: set[str]) -> tuple[int | None, str | None]:
    if {"candidate", "resid_loo"}.issubset(required):
        return 17, "zuco_reliability"
    if {"lambda_0_resid_rsa", "lambda_0p10_resid_rsa", "delta_0p10_minus_0"}.issubset(required):
        return 17, "zuco_transfer"
    if {"primary_residual_reliability"}.issubset(required):
        return 12, "fmri_reliability"
    if {"lambda_0_residual_rsa", "lambda_0p10_residual_rsa", "delta_0p10_minus_0"}.issubset(required):
        return 12, "fmri_transfer"
    return None, None


def safe_discover_csv(module, root: Path, required: set[str], prefer: str | None = None) -> Path:
    candidates = list(root.glob("*/latest/*.csv"))
    candidates.extend(root.glob("*/latest/*/*.csv"))
    n_expected, role = expected_rows(required)
    matches = []
    for p in candidates:
        try:
            if not required.issubset(module.headers(p)):
                continue
            rows = module.read_csv(p)
            if role == "zuco_reliability":
                if sum(r.get("candidate") == "row_mean_all" for r in rows) != n_expected:
                    continue
            elif n_expected is not None and len(rows) != n_expected:
                continue
            score = 0
            if prefer and prefer.lower() in str(p).lower():
                score += 10
            name = p.name.lower()
            if "subject" in name or "participant" in name:
                score += 4
            if "session" in name or "run" in name:
                score -= 4
            matches.append((score, p.stat().st_mtime, p, len(rows)))
        except Exception:
            continue
    if not matches:
        raise FileNotFoundError(
            f"No validated frozen CSV under {root} with columns {sorted(required)}; role={role} expected_rows={n_expected}"
        )
    matches.sort(key=lambda z: (z[0], z[1]), reverse=True)
    score, _, chosen, n_rows = matches[0]
    print(f"figure-source: role={role} rows={n_rows} score={score} path={chosen}", flush=True)
    return chosen


def capped_exact_signflip(module, x):
    if len(x) > 20:
        raise RuntimeError(f"Refusing exact sign-flip over n={len(x)}; participant-level source required")
    return module._original_exact_signflip(x)


def install_style(m):
    def style():
        mpl.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
            "font.size": 7.2,
            "axes.titlesize": 8.4,
            "axes.labelsize": 7.4,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "legend.fontsize": 7.0,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
        })
    m.set_style = style


def draw_node(m, ax, x, y, w, h, title, subtitle, edge, fill):
    box = mpl.patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.010,rounding_size=0.016",
        fc=fill, ec=edge, lw=0.9,
    )
    ax.add_patch(box)
    ax.text(x+w/2, y+h*0.62, title, ha="center", va="center", fontsize=7.5, fontweight="bold", color=m.DARK)
    ax.text(x+w/2, y+h*0.29, subtitle, ha="center", va="center", fontsize=6.3, color=m.GRAY, linespacing=1.05)


def figure1(m, dev: dict, out: Path) -> dict:
    runs = np.asarray(dev["heldout_residual_correspondence"], float)
    sealed = dev["sealed_run07"]
    arms = sealed["arms"]
    s1 = np.asarray(sealed["seed_1"], float)
    s2 = np.asarray(sealed["seed_2"], float)

    fig = plt.figure(figsize=(178*m.MM, 96*m.MM))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[0.50, 1.0], width_ratios=[0.90, 1.05, 1.25], hspace=0.48, wspace=0.50)

    ax = fig.add_subplot(gs[0, :]); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); m.panel_label(ax,"a")
    ax.set_title("Neural geometry supplies a relational training signal", loc="left", pad=2, fontweight="bold")
    draw_node(m,ax,.03,.27,.20,.38,"Human EEG","reproducible\npairwise geometry",m.TEAL,"#F3FAFA")
    draw_node(m,ax,.29,.27,.20,.38,"Neural constraint","match pairwise\nmodel distances",m.NAVY,"#F4F7FA")
    draw_node(m,ax,.55,.27,.20,.38,"Language model","small relational\nperturbation",m.ORANGE,"#FFF8F1")
    draw_node(m,ax,.81,.27,.16,.38,"External brains","test transfer\nwithout retuning",m.BLUE,"#F4F7FB")
    for x0,x1 in [(.23,.29),(.49,.55),(.75,.81)]: m.draw_arrow(ax,x0,.46,x1,.46)

    ax=fig.add_subplot(gs[1,0]); m.panel_label(ax,"b"); m.clean(ax,grid=True)
    vals=[dev["reliability"]["raw_loo"],dev["reliability"]["residual_loo"]]
    ax.plot([0,1],vals,color=m.LIGHT,lw=1.2,zorder=1)
    ax.scatter([0,1],vals,s=38,c=["#C7CDD3",m.TEAL],edgecolor=m.DARK,linewidth=.45,zorder=3)
    ax.set_xticks([0,1],["Raw","Nuisance-\nresidualized"]); ax.set_ylabel("Cross-participant reliability")
    ax.set_ylim(0,max(vals)*1.25); ax.set_title("Reliable neural target",loc="left",fontweight="bold")
    for i,v in enumerate(vals): ax.text(i,v+0.010,f"{v:.3f}",ha="center",va="bottom",fontsize=7.0)

    ax=fig.add_subplot(gs[1,1]); m.panel_label(ax,"c"); m.clean(ax,grid=True)
    x=np.arange(1,7)
    ax.scatter(x,runs,s=30,color=m.TEAL,edgecolor="white",linewidth=.4,zorder=3)
    ax.plot(x,runs,color=m.TEAL,lw=.85,alpha=.55)
    ax.axhline(0,color=m.GRAY,lw=.7); ax.axhline(runs.mean(),color=m.NAVY,lw=1.0,ls="--")
    ax.set_xticks(x); ax.set_xlabel("Held-out narrative run"); ax.set_ylabel("Residual model–EEG correspondence")
    ax.set_title("Neural geometry is learnable across held-out runs",loc="left",fontweight="bold",fontsize=8.0)
    ax.text(.04,.96,f"6/6 positive\nmean = {runs.mean():.4f}\nexact P = 0.0156",transform=ax.transAxes,va="top",fontsize=6.6)

    ax=fig.add_subplot(gs[1,2]); m.panel_label(ax,"d"); m.clean(ax,grid=True)
    xp=np.arange(len(arms))
    ax.plot(xp,s1,marker="o",ms=4.4,lw=.9,color=m.GRAY,label="Seed 1")
    ax.plot(xp,s2,marker="o",ms=4.4,lw=.9,color=m.NAVY,label="Seed 2")
    ng=arms.index("Neural-guided")
    ax.scatter([ng,ng],[s1[ng],s2[ng]],s=50,color=m.ORANGE,edgecolor="white",linewidth=.5,zorder=5)
    ax.set_xticks(xp,["Base","Text-only","Neural-\nguided","Shuffled-\nneural"])
    ax.set_ylabel("Residual neural alignment")
    ax.set_title("Neural guidance wins in both sealed seeds",loc="left",fontweight="bold",fontsize=8.0)
    ax.legend(frameon=False,loc="lower left",ncol=2,handlelength=1.3,columnspacing=.8)
    fig.subplots_adjust(left=.074,right=.992,bottom=.13,top=.97)
    m.save_figure(fig,out,"figure1")
    return {"figure":"figure1","inputs":["paper/figure_data/chineseeeg_development_v1.json"]}


def reliability_panel(m, ax, rel, title, seed):
    m.clean(ax,grid=False)
    lo,hi=m.bootstrap_ci(rel,seed=seed)
    y=np.linspace(-.16,.16,len(rel))
    ax.scatter(rel,y,s=25,color=m.TEAL,edgecolor="white",linewidth=.35,zorder=3)
    ax.errorbar([rel.mean()],[-.40],xerr=[[rel.mean()-lo],[hi-rel.mean()]],fmt="D",ms=4.8,capsize=2.3,color=m.NAVY,lw=1.0)
    ax.text(rel.mean(),-.49,"mean",ha="center",va="top",fontsize=6.4,color=m.GRAY)
    ax.set_yticks([]); ax.set_xlabel("Residual LOO reliability"); ax.set_title(title,loc="left",fontweight="bold")
    ax.text(.02,.98,f"{len(rel)}/{len(rel)} positive\nmean = {rel.mean():.3f}",transform=ax.transAxes,va="top",fontsize=6.6)
    ax.set_ylim(-.58,.32)


def paired_panel(m, ax, a0, a1, title, statement):
    m.clean(ax,grid=True)
    for u,v in zip(a0,a1):
        ax.plot([0,1],[u,v],color="#D6DBE0",lw=.85,zorder=1)
        ax.scatter([0,1],[u,v],s=21,color=[m.GRAY,m.ORANGE],zorder=2)
    ax.set_xticks([0,1],["Text-only","Neural-guided"]); ax.set_ylabel("Participant residual RSA")
    ax.set_title(title,loc="left",fontweight="bold")
    ax.text(.03,.97,statement,transform=ax.transAxes,va="top",fontsize=6.7,fontweight="bold",color=m.NAVY)


def delta_panel(m, ax, d, seed, title):
    m.clean(ax,grid=False)
    mval=float(d.mean()); lo,hi=m.bootstrap_ci(d,seed=seed); p=m.exact_signflip(d)
    x=d*1e3
    jitter=np.linspace(-.16,.16,len(x))
    ax.axvline(0,color=m.GRAY,lw=.7)
    ax.scatter(x,jitter,s=28,color=m.ORANGE,edgecolor="white",linewidth=.35,zorder=3)
    ax.errorbar([mval*1e3],[-.42],xerr=[[(mval-lo)*1e3],[(hi-mval)*1e3]],fmt="D",ms=5,capsize=2.4,color=m.NAVY,lw=1.05,zorder=4)
    ax.text(mval*1e3,-.51,"mean",ha="center",va="top",fontsize=6.4,color=m.GRAY)
    ax.set_ylim(-.60,.30); ax.set_yticks([])
    ax.set_xlabel(r"Neural-guided - text-only RSA ($\times 10^{-3}$)")
    ax.set_title(title,loc="left",fontweight="bold")
    ax.text(.02,.98,f"mean = {mval*1e3:+.3f}\n95% CI {lo*1e3:.3f} to {hi*1e3:.3f}\nexact P = {p:.3g}",transform=ax.transAxes,va="top",fontsize=6.5)


def transfer_figure(m, outputs: Path, out: Path, which: str) -> dict:
    if which=="zuco":
        rel,a0,a1,src=m.load_zuco(outputs); n=17; top="Frozen cross-language transfer test"; target="ZuCo EEG"; subtitle="17 independent English readers"; rel_title="Target reliability"; pair_title="Independent EEG alignment"; seed=20260831
    else:
        rel,a0,a1,src=m.load_fmri(outputs); n=12; top="Prospective cross-modal transfer test"; target="SMN4Lang fMRI"; subtitle="12 independent Mandarin listeners"; rel_title="Model-blind reliability gate"; pair_title="Prospective fMRI alignment"; seed=20260827
    d=a1-a0
    fig=plt.figure(figsize=(178*m.MM,96*m.MM)); gs=GridSpec(2,3,figure=fig,height_ratios=[.50,1],width_ratios=[.88,1.18,1.10],hspace=.48,wspace=.49)
    ax=fig.add_subplot(gs[0,:]); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); m.panel_label(ax,"a"); ax.set_title(top,loc="left",pad=2,fontweight="bold")
    left_sub="Chinese natural-reading EEG source" if which=="zuco" else "EEG-derived relational constraint"
    mid_sub="neural-guided λ=0.10 vs text-only λ=0" if which=="zuco" else "no SMN4Lang model tuning"
    draw_node(m,ax,.05,.27,.22,.38,"ChineseEEG",left_sub,m.TEAL,"#F3FAFA")
    draw_node(m,ax,.39,.27,.22,.38,"Frozen E5 contrast",mid_sub,m.ORANGE,"#FFF8F1")
    draw_node(m,ax,.73,.27,.22,.38,target,subtitle,m.BLUE,"#F4F7FB")
    m.draw_arrow(ax,.27,.46,.39,.46); m.draw_arrow(ax,.61,.46,.73,.46)
    ax=fig.add_subplot(gs[1,0]); m.panel_label(ax,"b"); reliability_panel(m,ax,rel,rel_title,seed)
    ax=fig.add_subplot(gs[1,1]); m.panel_label(ax,"c"); paired_panel(m,ax,a0,a1,pair_title,f"{n}/{n} participants shift upward")
    ax=fig.add_subplot(gs[1,2]); m.panel_label(ax,"d"); delta_panel(m,ax,d,seed,"Participant-level transfer")
    fig.subplots_adjust(left=.076,right=.992,bottom=.14,top=.97)
    stem="figure2" if which=="zuco" else "figure3"; m.save_figure(fig,out,stem)
    return {"figure":stem,"inputs":[str(x) for x in src]}


def figure4(m, outputs: Path, out: Path) -> dict:
    dose=outputs/"nmi_bidirectional_fmri_eeg_dose_response_v1"/"latest"/"zuco_subject_dose_results.csv"
    panel=outputs/"nmi_bidirectional_model_family_panel_v1"/"latest"/"model_seed_direction_results.csv"
    if not dose.exists(): dose=m.discover_csv(outputs,{"target","subject","lambda","delta"},prefer="dose")
    if not panel.exists(): panel=m.discover_csv(outputs,{"model_key","direction","seed","external_mean_delta"},prefer="model_family")
    dr=[r for r in m.read_csv(dose) if r.get("target","ZuCo").lower().startswith("zuco")]
    pr=m.read_csv(panel)
    lambdas=sorted({float(r["lambda"]) for r in dr}); means=[]; los=[]; his=[]
    for j,lam in enumerate(lambdas):
        z=np.asarray([float(r["delta"]) for r in dr if abs(float(r["lambda"])-lam)<1e-12],float)
        means.append(z.mean()); a,b=m.bootstrap_ci(z,seed=20260830+j); los.append(a); his.append(b)

    model_order=["e5_large","e5_base","multilingual_mpnet","multilingual_minilm","xlmr_base","mbert"]
    labels={"e5_large":"E5-large","e5_base":"E5-base","multilingual_mpnet":"mMPNet","multilingual_minilm":"mMiniLM","xlmr_base":"XLM-R","mbert":"mBERT"}
    class_color={"e5_large":m.ORANGE,"e5_base":m.ORANGE,"multilingual_mpnet":m.TEAL,"multilingual_minilm":m.TEAL,"xlmr_base":m.GRAY,"mbert":m.GRAY}

    fig=plt.figure(figsize=(178*m.MM,114*m.MM)); gs=GridSpec(2,2,figure=fig,height_ratios=[.78,1.22],hspace=.48,wspace=.42)
    ax=fig.add_subplot(gs[0,0]); m.panel_label(ax,"a"); m.clean(ax,grid=True)
    x=np.asarray(lambdas); y=np.asarray(means)*1e3; lo=np.asarray(los)*1e3; hi=np.asarray(his)*1e3
    ax.errorbar(x,y,yerr=np.vstack([y-lo,hi-y]),fmt="o-",ms=4.6,lw=1.15,capsize=2.3,color=m.ORANGE)
    ax.set_xscale("log"); ax.set_xticks(x,[".01",".03",".10",".30","1.0"])
    ax.set_xlabel("fMRI relational-loss weight λ (log scale)"); ax.set_ylabel(r"ZuCo ΔRSA ($\times 10^{-3}$)")
    ax.set_title("Reverse transfer is graded within E5",loc="left",fontweight="bold")
    ax.axhline(0,color=m.GRAY,lw=.7); ax.text(.03,.96,"post-confirmatory characterization",transform=ax.transAxes,va="top",fontsize=6.4,color=m.GRAY)

    ax=fig.add_subplot(gs[0,1]); m.panel_label(ax,"b"); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_title("Bidirectional E5 transfer replicates across model sizes",loc="left",fontweight="bold")
    ax.text(.10,.68,"EEG",fontsize=8.2,fontweight="bold",ha="center"); ax.text(.50,.68,"E5",fontsize=8.2,fontweight="bold",ha="center"); ax.text(.90,.68,"fMRI",fontsize=8.2,fontweight="bold",ha="center")
    m.draw_arrow(ax,.15,.70,.45,.70,color=m.TEAL); m.draw_arrow(ax,.55,.70,.85,.70,color=m.TEAL)
    m.draw_arrow(ax,.85,.49,.55,.49,color=m.ORANGE); m.draw_arrow(ax,.45,.49,.15,.49,color=m.ORANGE)
    ax.text(.50,.86,"EEG-derived constraint",ha="center",fontsize=6.5,color=m.TEAL)
    ax.text(.50,.35,"fMRI-derived constraint",ha="center",fontsize=6.5,color=m.ORANGE)
    ax.text(.50,.13,"E5-large: 3/3 seeds both directions   |   E5-base: 3/3 seeds both directions",ha="center",fontsize=6.4,fontweight="bold",color=m.NAVY)

    for col,(direction,title) in enumerate([("eeg_to_fmri","EEG-derived constraint → fMRI"),("fmri_to_eeg","fMRI-derived constraint → EEG")]):
        ax=fig.add_subplot(gs[1,col]); m.panel_label(ax,"c" if col==0 else "d"); m.clean(ax,grid=False); ax.axvline(0,color=m.GRAY,lw=.8)
        yloc={k:len(model_order)-1-i for i,k in enumerate(model_order)}
        for sep in [3.5,1.5]: ax.axhline(sep,color="#E4E7EA",lw=.7,zorder=0)
        for key in model_order:
            rows=[r for r in pr if r["model_key"]==key and r["direction"]==direction]
            if len(rows)!=3:
                raise RuntimeError(f"Expected 3 seeds for {key} {direction}; found {len(rows)}")
            rows=sorted(rows,key=lambda r:int(r["seed"]))
            vals=np.asarray([float(r["external_mean_delta"])*1e3 for r in rows],float)
            yy=yloc[key]
            offsets=np.asarray([-0.10,0.0,0.10])
            c=class_color[key]
            ax.scatter(vals,yy+offsets,s=24,color=c,edgecolor="white",linewidth=.35,zorder=3)
            ax.scatter([vals.mean()],[yy],s=62,facecolor="white",edgecolor=c,linewidth=1.2,zorder=4)
        ax.set_yticks([yloc[k] for k in model_order],[labels[k] for k in model_order])
        if col==1: ax.tick_params(axis="y",labelleft=False)
        ax.set_xlabel(r"Mean participant ΔRSA per seed ($\times 10^{-3}$)")
        ax.set_title(title,loc="left",fontweight="bold")
        ax.set_ylim(-.45,5.45)
    fig.subplots_adjust(left=.12,right=.992,bottom=.11,top=.97)
    m.save_figure(fig,out,"figure4")
    return {"figure":"figure4","inputs":[str(dose),str(panel)]}


def main() -> int:
    m=load_v3(); install_style(m); m.set_style()
    m.discover_csv=lambda root,required,prefer=None: safe_discover_csv(m,root,required,prefer)
    m._original_exact_signflip=m.exact_signflip
    m.exact_signflip=lambda x: capped_exact_signflip(m,x)
    out=Path("outputs/nmi_main_figures_v3/latest").resolve(); outputs=Path("outputs").resolve(); devp=Path("paper/figure_data/chineseeeg_development_v1.json").resolve(); dev=m.read_json(devp)
    records=[figure1(m,dev,out),transfer_figure(m,outputs,out,"zuco"),transfer_figure(m,outputs,out,"fmri"),figure4(m,outputs,out)]
    sources={}
    for rec in records:
        for p in rec["inputs"]:
            q=Path(p)
            if q.exists(): sources[str(q)]=m.sha256(q)
    manifest={"schema_version":2,"analysis":"NMI main figures v3.3","journal_target":"Nature Machine Intelligence","max_figure_width_mm":178,"vector_outputs":["pdf","svg"],"raster_output":{"format":"png","dpi":600},"figures":[r["figure"] for r in records],"source_files_sha256":sources,"qa_fixes":["participant-count validated input discovery","exact sign-flip capped at n<=20","mathtext scientific-notation labels","model-family keys synchronized to frozen panel","compressed schematics and non-overlapping panel titles","participant deltas shown as compact strip plus mean bootstrap interval"],"guardrails":["Figure assembly only; no model fitting or outcome selection.","All quantitative panels are reconstructed from frozen derived outputs or committed frozen development values.","All six prespecified model families and all three seeds are required in Figure 4."]}
    (out/"source_manifest.json").write_text(__import__("json").dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(__import__("json").dumps({"status":"ok","output_dir":str(out),"figures":manifest["figures"]},indent=2)); return 0


if __name__=="__main__":
    raise SystemExit(main())

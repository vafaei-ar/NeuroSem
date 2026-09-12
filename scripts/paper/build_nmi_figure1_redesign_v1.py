#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 1 from frozen development artifacts.

Presentation-only. No model fitting, representation selection, neural analysis or
hypothesis testing is performed. All displayed scientific values are loaded from
provenance-linked derived artifacts.
"""
from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts/paper/nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs/nmi_figure1_redesign_v1/latest"
DEV = ROOT / "paper/figure_data/chineseeeg_development_v1.json"
REL_SUM = ROOT / "outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/summary.json"
REL_SUB = ROOT / "outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/subject_summary.csv"
STS1 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1/20260823_122332/summary.json"
STS2 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1_seed2/20260823_123910/summary.json"
INPUTS = [DEV, REL_SUM, REL_SUB, STS1, STS2]

ARM_MAP = {
    "Base": "base",
    "Text-only": "text_only",
    "Neural-guided": "neural",
    "Shuffled-neural": "shuffled_neural",
}
ARM_STYLE = {
    "Base": (S.GREY_L, "o"),
    "Text-only": (S.GREY, "s"),
    "Neural-guided": (S.BLUE, "D"),
    "Shuffled-neural": ("#8f8f8f", "^")
}


def read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def read_csv(p: Path) -> list[dict]:
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def box(ax, x, y, w, h, text, edge=S.INK, face="white", fs=6.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=0.75))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs, linespacing=1.25)


def arrow(ax, start, end, color=S.GREY):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7,
        linewidth=0.7, color=color, shrinkA=3, shrinkB=3))


def load_data() -> dict:
    dev = read_json(DEV)
    rel_sum = read_json(REL_SUM)
    rel_rows = read_csv(REL_SUB)
    sts_payloads = [read_json(STS1), read_json(STS2)]

    raw = np.asarray([float(r["raw_loo"]) for r in rel_rows])
    resid = np.asarray([float(r["residual_loo"]) for r in rel_rows])
    assert len(raw) == int(rel_sum["n_subjects"]) == 9
    assert np.isclose(raw.mean(), float(rel_sum["raw_loo_mean"]), atol=5e-12)
    assert np.isclose(resid.mean(), float(rel_sum["residual_loo_mean"]), atol=5e-12)

    runs = np.asarray(dev["heldout_residual_correspondence"], float)
    assert len(runs) == 6 and np.all(runs > 0)
    sealed = dev["sealed_run07"]
    run07 = {
        arm: np.asarray([float(sealed["seed_1"][i]), float(sealed["seed_2"][i])])
        for i, arm in enumerate(sealed["arms"])
    }
    semantic = {}
    for display, key in ARM_MAP.items():
        vals = []
        for payload in sts_payloads:
            result = payload["results"][key]
            task_scores = result["task_scores"]
            assert len(task_scores) == 8
            task_mean = float(np.mean([float(v) for v in task_scores.values()]))
            reported = float(result["mean_spearman"])
            assert np.isclose(task_mean, reported, atol=5e-13)
            vals.append(reported)
        semantic[display] = np.asarray(vals)
    return {"raw": raw, "resid": resid, "runs": runs, "run07": run07, "semantic": semantic}


def panel_a(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(-0.05, 1.04, "a", transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    ax.text(0.00, 1.00, "From reproducible neural geometry to a frozen intervention",
            transform=ax.transAxes, fontsize=7, fontweight="bold", va="top")
    box(ax, .02, .57, .30, .25, "Natural-reading EEG\nitem geometry", S.BLUE, "#f4f7fb")
    box(ax, .37, .57, .25, .25, "Neural RDM", S.BLUE, "#f4f7fb")
    box(ax, .68, .57, .30, .25, "Relational loss\n+ matched text loss", S.INK)
    box(ax, .37, .16, .25, .23, "Model update", S.INK)
    box(ax, .68, .16, .30, .23, "Freeze intervention\nfor external tests", S.ORANGE, "#fff6f2")
    arrow(ax, (.32,.695), (.37,.695), S.BLUE); arrow(ax, (.62,.695), (.68,.695), S.BLUE)
    arrow(ax, (.83,.57), (.55,.39), S.GREY); arrow(ax, (.62,.275), (.68,.275), S.ORANGE)
    ax.text(.02,.10,"Development establishes measurability and learnability;\nexternal transfer remains the primary claim.",
            fontsize=5.5, color=S.GREY, ha="left", va="bottom")


def panel_b(ax, d):
    ax.text(-0.17, 1.05, "b", transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    ax.set_title("Source reliability survives nuisance adjustment", loc="left", fontweight="bold", pad=5)
    for r0, r1 in zip(d["raw"], d["resid"]):
        ax.plot([0,1], [r0,r1], color=S.GREY_L, lw=0.65, zorder=1)
        ax.scatter([0],[r0], s=12, facecolor="white", edgecolor=S.GREY, linewidth=0.55, zorder=2)
        ax.scatter([1],[r1], s=12, facecolor="white", edgecolor=S.BLUE, linewidth=0.65, zorder=2)
    means = [d["raw"].mean(), d["resid"].mean()]
    ax.plot([0,1], means, color=S.INK, lw=1.4, zorder=3)
    ax.scatter([0,1], means, s=28, facecolor=[S.GREY_L,S.BLUE], edgecolor=S.INK, linewidth=.55, zorder=4)
    ax.set_xticks([0,1]); ax.set_xticklabels(["Raw LOO", "Residual LOO"]); ax.tick_params(axis="x", length=0)
    ax.set_xlim(-.25,1.25); ax.set_ylim(0, max(.28, d["raw"].max()*1.15))
    ax.set_ylabel("Cross-participant reliability")
    ax.text(.02,.94,f"mean {means[0]:.3f}",transform=ax.transAxes,fontsize=5.6,color=S.GREY,va="top")
    ax.text(.98,.94,f"mean {means[1]:.3f}",transform=ax.transAxes,fontsize=5.6,color=S.BLUE,ha="right",va="top")
    S.offset_ticks(ax, "y")


def panel_c(ax, d):
    ax.text(-0.17, 1.05, "c", transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    ax.set_title("Held-out source correspondence is positive across runs", loc="left", fontweight="bold", pad=5)
    x = np.arange(1,7)
    ax.axhline(0, color=S.ZERO, lw=.55)
    ax.scatter(x, d["runs"], s=18, facecolor="white", edgecolor=S.BLUE, linewidth=.75, zorder=3)
    ax.plot([.65,6.35], [d["runs"].mean()]*2, color=S.BLUE, lw=1.1, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels([f"{i:02d}" for i in x])
    ax.set_xlabel("Held-out narrative run"); ax.set_ylabel("Residual model–EEG RSA")
    ax.set_xlim(.5,6.5); ax.set_ylim(0, d["runs"].max()*1.25)
    ax.text(.98,.95,f"6/6 positive\nmean {d['runs'].mean():.4f}\nexact one-sided P=0.0156",
            transform=ax.transAxes,ha="right",va="top",fontsize=5.5,color=S.BLUE,linespacing=1.25)
    S.offset_ticks(ax, "y")


def panel_d(ax, d):
    ax.text(-0.17, 1.05, "d", transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    ax.set_title("Development trade-off: neural alignment vs generic semantics", loc="left", fontweight="bold", pad=5)
    for arm in ARM_MAP:
        color, marker = ARM_STYLE[arm]
        xs = d["semantic"][arm]; ys = d["run07"][arm]
        ax.scatter(xs, ys, s=26 if arm=="Neural-guided" else 20, marker=marker,
                   facecolor=color if arm=="Neural-guided" else "white", edgecolor=color,
                   linewidth=.8, zorder=4)
        cx, cy = float(xs.mean()), float(ys.mean())
        dx, dy = {
            "Base": (-.0007,-.00028), "Text-only": (.0005,.00018),
            "Neural-guided": (.0004,.00020), "Shuffled-neural": (.0004,-.00035),
        }[arm]
        ax.text(cx+dx, cy+dy, arm, fontsize=5.5, color=color, ha="left", va="center")
    ax.set_xlabel("Eight-task semantic mean Spearman")
    ax.set_ylabel("Reserved run-07 residual neural RSA")
    ax.set_xlim(.281,.311); ax.set_ylim(.0310,.0382)
    ax.text(.98,.05,"Neural-guided is highest neurally in both seeds,\nwithout a stable semantic advantage.",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=5.4,color=S.GREY,linespacing=1.25)
    S.offset_ticks(ax, "both")


def write_source(d) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True); paths=[]
    p=OUT/"figure1_reliability_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["participant_index","raw_loo","residual_loo"])
        for i,(a,b) in enumerate(zip(d["raw"],d["resid"]),1): w.writerow([i,f"{a:.12g}",f"{b:.12g}"])
    paths.append(p)
    p=OUT/"figure1_development_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["record_type","label","seed","neural_metric","semantic_metric"])
        for i,v in enumerate(d["runs"],1): w.writerow(["heldout_run",f"run_{i:02d}","",f"{v:.12g}",""])
        for arm in ARM_MAP:
            for seed,(y,x) in enumerate(zip(d["run07"][arm],d["semantic"][arm]),1):
                w.writerow(["development_arm",arm,seed,f"{y:.12g}",f"{x:.12g}"])
    paths.append(p)
    return paths


def main() -> int:
    missing=[str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError("Missing frozen Figure 1 input(s): "+", ".join(missing))
    d=load_data(); S.apply(); fig=S.figure(S.W2,108); gs=fig.add_gridspec(2,2,hspace=.34,wspace=.28)
    a,b,c,e=[fig.add_subplot(gs[i,j]) for i,j in ((0,0),(0,1),(1,0),(1,1))]
    panel_a(a); panel_b(b,d); panel_c(c,d); panel_d(e,d)
    OUT.mkdir(parents=True,exist_ok=True); outputs=[]
    for ext,kw in (("pdf",{}),("svg",{}),("png",{"dpi":600})):
        p=OUT/f"figure1.{ext}"; fig.savefig(p,**kw); outputs.append(p)
    plt.close(fig); source=write_source(d)
    svg=OUT/"figure1.svg"
    transport=base64.b64encode(gzip.compress(svg.read_bytes(),compresslevel=9,mtime=0)).decode("ascii")
    manifest={
        "schema_version":1,"status":"ok","analysis":"NeuroSem NMI Figure 1 scientific-graphic redesign",
        "scientific_values_changed":False,
        "guardrails":["Presentation-only build from frozen provenance-linked outputs.","No model fitting, neural analysis, representation selection or hypothesis testing.","Participant identifiers are not exported."],
        "builder":str(Path(__file__).relative_to(ROOT)),"builder_sha256":sha256(Path(__file__)),
        "inputs":{str(p.relative_to(ROOT)):sha256(p) for p in INPUTS},
        "outputs":{str(p.relative_to(ROOT)):sha256(p) for p in outputs},
        "source_data":{str(p.relative_to(ROOT)):sha256(p) for p in source},
        "displayed_summary":{"raw_loo_mean":float(d["raw"].mean()),"residual_loo_mean":float(d["resid"].mean()),"heldout_run_mean":float(d["runs"].mean()),"heldout_runs_positive":int(np.sum(d["runs"]>0))},
        "svg_transport":{"encoding":"gzip+base64","decoded_sha256":sha256(svg),"base64":transport}
    }
    (OUT/"source_manifest.json").write_text(json.dumps(manifest,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","png_sha256":sha256(OUT/"figure1.png"),"svg_sha256":sha256(svg)},indent=2))
    return 0


if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 3 from frozen dose/model-space outputs only."""
from __future__ import annotations
import base64,csv,gzip,hashlib,json,sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
STYLE_DIR=ROOT/"scripts/paper/nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:sys.path.insert(0,str(STYLE_DIR))
import nmi_style as S  # noqa: E402
OUT=ROOT/"outputs/nmi_figure3_redesign_v1/latest"
DOSE=ROOT/"outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv"
MS010=ROOT/"outputs/nmi_model_space_characterization_v1/latest/summary.json"
MS1=ROOT/"outputs/nmi_model_space_characterization_lambda1_v1/latest/summary.json"
INPUTS=[DOSE,MS010,MS1];LAM=np.array([.01,.03,.10,.30,1.0])

def rc(p):
    with p.open("r",encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def rj(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def load():
    rows=rc(DOSE);by={(r["dataset"],float(r["lambda"])):r for r in rows};out={}
    for key,label,color in (("zuco","ZuCo EEG",S.BLUE),("smn4lang_fmri","SMN4Lang fMRI",S.ORANGE)):
        rr=[by[(key,float(x))] for x in LAM]
        out[key]={"label":label,"color":color,
            "delta":np.array([float(r["mean_delta_rsa"]) for r in rr]),
            "lo":np.array([float(r["bootstrap_95ci_low"]) for r in rr]),
            "hi":np.array([float(r["bootstrap_95ci_high"]) for r in rr]),
            "sts":np.array([float(r["delta_external_sts_vs_lambda0_already_observed"]) for r in rr])}
    a=rj(MS010)["metrics"];b=rj(MS1)["metrics"]
    metrics=[("Item cosine","corresponding_item_cosine_similarity_mean"),("RDM Pearson","pairwise_cosine_distance_pearson"),("RDM Spearman","pairwise_cosine_distance_spearman"),("Centered CKA","linear_centered_cka"),("k=10 Jaccard","mean_knn_jaccard_overlap")]
    return out,metrics,a,b
def hdr(ax,l,t):
    ax.text(-.10,1.08,l,transform=ax.transAxes,fontsize=8,fontweight="bold",va="bottom")
    ax.text(.02,1.08,t,transform=ax.transAxes,fontsize=7,fontweight="bold",va="bottom")
def panel_a(ax,d):
    hdr(ax,"a","Dose reveals target-dependent transfer")
    for key in ("zuco","smn4lang_fmri"):
        q=d[key];y=q["delta"]*1e3;lo=q["lo"]*1e3;hi=q["hi"]*1e3;e=np.vstack([y-lo,hi-y])
        ax.errorbar(LAM,y,yerr=e,fmt="-o",color=q["color"],mfc="white",mec=q["color"],mew=.8,ms=4,capsize=2,lw=1.05,label=q["label"])
    ax.axhline(0,color=S.ZERO,lw=.55);ax.axvline(.10,color=S.GREY_L,lw=.55,ls=(0,(2,2)))
    ax.set_xscale("log");ax.set_xticks(LAM);ax.set_xticklabels([".01",".03",".10",".30","1.0"])
    ax.set_xlabel("Relational-loss weight λ");ax.set_ylabel("Mean external ΔRSA (×10$^{-3}$)");ax.legend(loc="upper left",fontsize=5.7)
    ax.text(.10,.04,"prospective dose",transform=ax.get_xaxis_transform(),ha="center",va="bottom",rotation=90,fontsize=5.0,color=S.GREY)
    fy=d["smn4lang_fmri"]["delta"][-1]*1e3
    ax.annotate("fMRI reverses",xy=(1,fy),xytext=(-54,13),textcoords="offset points",fontsize=5.4,color=S.ORANGE,arrowprops=dict(arrowstyle="-",lw=.55,color=S.ORANGE))
    S.offset_ticks(ax,"y")
def panel_b(ax,d):
    hdr(ax,"b","Transfer–utility frontier")
    for key in ("zuco","smn4lang_fmri"):
        q=d[key];x=-q["sts"]*1e3;y=q["delta"]*1e3
        ax.scatter(x,y,s=26,facecolor="white",edgecolor=q["color"],linewidth=.85,label=q["label"],zorder=3)
        for xx,yy,ll in zip(x,y,[".01",".03",".10",".30","1"]):ax.text(xx,yy,ll,fontsize=5.2,color=q["color"],ha="left",va="bottom")
    ax.axhline(0,color=S.ZERO,lw=.55);ax.set_xlabel("Generic STS cost (×10$^{-3}$)");ax.set_ylabel("External ΔRSA (×10$^{-3}$)");ax.legend(loc="upper left",fontsize=5.7)
    ax.text(.98,.05,"Each label is λ; STS outcomes were already observed.",transform=ax.transAxes,ha="right",va="bottom",fontsize=5.1,color=S.GREY)
    S.offset_ticks(ax,"both")
def panel_c(ax,metrics,a,b):
    hdr(ax,"c","Model displacement grows at high dose")
    y=np.arange(len(metrics))[::-1];v10=np.array([float(a[k]) for _,k in metrics]);v1=np.array([float(b[k]) for _,k in metrics])
    for yi,x1,x2 in zip(y,v10,v1):ax.plot([x2,x1],[yi,yi],color=S.GREY_L,lw=1.15,zorder=1)
    ax.scatter(v10,y,s=30,facecolor=S.TEAL,edgecolor="white",linewidth=.4,label="λ=.10",zorder=3)
    ax.scatter(v1,y,s=30,facecolor=S.PURPLE,edgecolor="white",linewidth=.4,label="λ=1.0",zorder=3)
    ax.set_yticks(y);ax.set_yticklabels([m[0] for m in metrics]);ax.set_xlabel("Similarity to matched text-only representation");ax.set_xlim(.55,1.005);ax.axvline(1,color=S.GREY_XL,lw=.55)
    ax.legend(loc="upper left",fontsize=5.7,ncol=2,frameon=False);S.offset_ticks(ax,"x")
def write_source(d,metrics,a,b):
    OUT.mkdir(parents=True,exist_ok=True);ps=[];p=OUT/"figure3_dose_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["dataset","lambda","mean_delta_rsa","ci_low","ci_high","sts_delta_vs_lambda0"])
        for key in ("zuco","smn4lang_fmri"):
            q=d[key]
            for i,l in enumerate(LAM):w.writerow([key,l,q["delta"][i],q["lo"][i],q["hi"][i],q["sts"][i]])
    ps.append(p);p=OUT/"figure3_model_space_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["metric","lambda_0p10","lambda_1p0"])
        for name,k in metrics:w.writerow([name,float(a[k]),float(b[k])])
    ps.append(p);return ps
def main():
    miss=[str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if miss:raise FileNotFoundError("Missing Figure 3 input(s): "+", ".join(miss))
    d,metrics,a,b=load();S.apply();fig=S.figure(S.W2,102);gs=fig.add_gridspec(2,12,wspace=.42,hspace=.42);aa=fig.add_subplot(gs[0,0:8]);bb=fig.add_subplot(gs[1,0:8]);cc=fig.add_subplot(gs[:,8:12])
    panel_a(aa,d);panel_b(bb,d);panel_c(cc,metrics,a,b);OUT.mkdir(parents=True,exist_ok=True);outs=[]
    for ext,kw in (("pdf",{}),("svg",{}),("png",{"dpi":600})):
        p=OUT/f"figure3.{ext}";fig.savefig(p,**kw);outs.append(p)
    plt.close(fig);src=write_source(d,metrics,a,b);svg=OUT/"figure3.svg";transport=base64.b64encode(gzip.compress(svg.read_bytes(),9,mtime=0)).decode("ascii")
    man={"schema_version":2,"status":"ok","analysis":"NeuroSem NMI Figure 3 scientific-graphic redesign","scientific_values_changed":False,"guardrails":["Presentation-only build from frozen dose and model-space outputs.","No new dose, model evaluation, neural analysis or inference."],"builder":str(Path(__file__).relative_to(ROOT)),"builder_sha256":sha(Path(__file__)),"inputs":{str(p.relative_to(ROOT)):sha(p) for p in INPUTS},"outputs":{str(p.relative_to(ROOT)):sha(p) for p in outs},"source_data":{str(p.relative_to(ROOT)):sha(p) for p in src},"svg_transport":{"encoding":"gzip+base64","decoded_sha256":sha(svg),"base64":transport}}
    (OUT/"source_manifest.json").write_text(json.dumps(man,separators=(",",":"))+"\n",encoding="utf-8");print(json.dumps({"status":"ok","png_sha256":sha(OUT/"figure3.png"),"svg_sha256":sha(svg)},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 4 from frozen scope/specificity outputs."""
from __future__ import annotations
import base64,csv,gzip,hashlib,json,sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
STYLE_DIR=ROOT/"scripts/paper/nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:sys.path.insert(0,str(STYLE_DIR))
import nmi_style as S  # noqa: E402
OUT=ROOT/"outputs/nmi_figure4_redesign_v1/latest"
MODELS=ROOT/"outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
SPEC=ROOT/"outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json"
MULTI=ROOT/"outputs/nmi_multiseed_e5_v1/latest/summary.json"
ALT=ROOT/"outputs/nmi_alternative_signal_e5_v1/latest/seed_target_results.csv"
MP_SPACE=ROOT/"outputs/nmi_mpnet_model_space_comparison_v1/latest/seed_comparison_metrics.csv"
REVERSE=ROOT/"outputs/nmi_bidirectional_fmri_to_zuco_v1/latest/summary.json"
REVERSE_MULTI=ROOT/"outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json"
INPUTS=[MODELS,SPEC,MULTI,ALT,MP_SPACE,REVERSE,REVERSE_MULTI]

def rc(p):
    with p.open("r",encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def rj(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def hdr(ax,l,t,dx=-.10):
    ax.text(dx,1.09,l,transform=ax.transAxes,fontsize=8,fontweight="bold",va="bottom")
    ax.text(.02,1.09,t,transform=ax.transAxes,fontsize=7,fontweight="bold",va="bottom")
def model_panel(ax,rows,direction,power,title,show_y=True,header=False):
    order=[("e5_large","E5-large"),("e5_base","E5-base"),("multilingual_mpnet","mMPNet"),("multilingual_minilm","mMiniLM"),("xlmr_base","XLM-R"),("mbert","mBERT")]
    sc=10.0**(-power);ys=np.arange(len(order))[::-1];col=S.BLUE if direction=="eeg_to_fmri" else S.TEAL
    ax.axvline(0,color=S.ZERO,lw=.55)
    for yi,(key,label) in zip(ys,order):
        rr=sorted([r for r in rows if r["model_key"]==key and r["direction"]==direction],key=lambda r:int(r["seed"]));vals=np.array([float(r["external_mean_delta"]) for r in rr])*sc
        ax.plot([vals.min(),vals.max()],[yi,yi],color=S.GREY_L,lw=1.0,zorder=1);ax.scatter(vals,np.full(3,yi),s=15,facecolor="white",edgecolor=col,linewidth=.7,zorder=2);ax.scatter([vals.mean()],[yi],s=26,marker="D",facecolor=col,edgecolor="white",linewidth=.4,zorder=3)
    ax.set_yticks(ys);ax.set_yticklabels([x[1] for x in order] if show_y else []);ax.set_xlabel(f"Seed mean ΔRSA (×10$^{{{power}}}$)");ax.text(.02,.96,title,transform=ax.transAxes,ha="left",va="top",fontsize=6.2,fontweight="bold")
    if header:hdr(ax,"a","Backbone and direction shape transfer",dx=-.16)
    S.offset_ticks(ax,"x")
def signal_values():
    spec=rj(SPEC)["specificity_control"]["seed_results"];multi=rj(MULTI)["results"];alt=rc(ALT);out={}
    for target,spec_key,multi_key,alt_key in (("zuco","zuco","zuco_mean_delta","zuco"),("fmri","smn4lang_fmri","smn4lang_fmri_mean_delta","smn4lang_fmri")):
        shuffled=np.array([float(r["targets"][spec_key]["shuffled_minus_text"]["mean_delta"]) for r in spec]);genuine=np.array([float(r[multi_key]) for r in multi]);ar=sorted([r for r in alt if r["target"]==alt_key],key=lambda r:int(r["seed"]));mpnet=np.array([float(r["surrogate_minus_text_mean_delta"]) for r in ar]);out[target]={"shuffled":shuffled,"genuine":genuine,"mpnet":mpnet}
    return out
def signal_panel(ax,v,target,power,color,header=False):
    sc=10.0**(-power);cats=[("Shuffled",v["shuffled"]),("Genuine",v["genuine"]),("MPNet",v["mpnet"])]
    ax.axhline(0,color=S.ZERO,lw=.55)
    for i,(lab,vals0) in enumerate(cats):
        vals=vals0*sc;j=np.array([-.08,0,.08]);ax.scatter(i+j,vals,s=18,facecolor="white",edgecolor=color,linewidth=.75,zorder=3);ax.plot([i-.17,i+.17],[vals.mean(),vals.mean()],color=color,lw=1.35,zorder=2)
    ax.set_xticks(range(3));ax.set_xticklabels([x[0] for x in cats]);ax.tick_params(axis="x",length=0);ax.set_ylabel(f"Transfer vs text (×10$^{{{power}}}$)");ax.text(.02,.95,target,transform=ax.transAxes,ha="left",va="top",fontsize=6.1,fontweight="bold")
    if header:hdr(ax,"b","Target structure constrains transfer",dx=-.16)
    S.offset_ticks(ax,"y")
def space_panel(ax):
    hdr(ax,"c","Alternative signal induces larger displacement",dx=-.10);rows=rc(MP_SPACE);metrics=[("Item cosine","corresponding_item_cosine_similarity_mean"),("RDM Pearson","pairwise_cosine_distance_pearson"),("RDM Spearman","pairwise_cosine_distance_spearman"),("Centered CKA","linear_centered_cka"),("k=10 Jaccard","mean_knn_jaccard_overlap")];ys=np.arange(5)[::-1]
    for yi,(name,k) in zip(ys,metrics):
        g=np.array([float(r[k]) for r in rows if r["comparison"]=="genuine_neural_vs_text_only"]);m=np.array([float(r[k]) for r in rows if r["comparison"]=="mpnet_surrogate_vs_text_only"])
        ax.plot([m.mean(),g.mean()],[yi,yi],color=S.GREY_L,lw=1.05);ax.scatter(g,np.full(3,yi+.07),s=12,facecolor="white",edgecolor=S.TEAL,linewidth=.6);ax.scatter(m,np.full(3,yi-.07),s=12,facecolor="white",edgecolor=S.PURPLE,linewidth=.6);ax.scatter([g.mean()],[yi+.07],s=23,facecolor=S.TEAL,edgecolor="white",linewidth=.35);ax.scatter([m.mean()],[yi-.07],s=23,facecolor=S.PURPLE,edgecolor="white",linewidth=.35)
    ax.set_yticks(ys);ax.set_yticklabels([x[0] for x in metrics]);ax.set_xlabel("Similarity to seed-matched text-only representation");ax.set_xlim(.78,1.005);ax.axvline(1,color=S.GREY_XL,lw=.55)
    ax.scatter([],[],s=20,color=S.TEAL,label="genuine neural");ax.scatter([],[],s=20,color=S.PURPLE,label="MPNet surrogate");ax.legend(loc="lower right",fontsize=5.4,frameon=False);S.offset_ticks(ax,"x")
def reverse_panel(ax):
    hdr(ax,"d","Reverse transfer remains small",dx=-.10);pr=rj(REVERSE)["primary_result"];mr=rj(REVERSE_MULTI)["seed_results"]
    means=[float(pr["mean_delta"])]+[float(r["zuco"]["mean_delta"]) for r in mr];cis=[pr["bootstrap_95ci"]]+[r["zuco"]["bootstrap_95ci"] for r in mr];labels=["Primary"]+[str(r["seed"])[-2:] for r in mr];x=np.arange(4);y=np.array(means)*1e5;ci=np.array(cis,float)*1e5;err=np.vstack([y-ci[:,0],ci[:,1]-y])
    ax.axhline(0,color=S.ZERO,lw=.55);ax.axvline(.5,color=S.GREY_L,lw=.55,ls="--");ax.errorbar([0],[y[0]],yerr=err[:,[0]],fmt="D",color=S.TEAL,mfc=S.TEAL,mec="white",mew=.4,capsize=2,lw=.8,ms=4.2);ax.errorbar(x[1:],y[1:],yerr=err[:,1:],fmt="o",color=S.TEAL,mfc="white",mec=S.TEAL,mew=.8,capsize=2,lw=.8,ms=4)
    ax.set_xticks(x);ax.set_xticklabels(labels);ax.tick_params(axis="x",length=0);ax.set_ylabel("Reverse ΔRSA (×10$^{-5}$)");ax.text(.98,.93,"14/17 positive in each added seed",transform=ax.transAxes,ha="right",va="top",fontsize=5.4,color=S.TEAL);S.offset_ticks(ax,"y")
def write_source(models,signals):
    OUT.mkdir(parents=True,exist_ok=True);ps=[];p=OUT/"figure4_model_family_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=models[0].keys());w.writeheader();w.writerows(models)
    ps.append(p);p=OUT/"figure4_signal_source.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["target","signal","seed_index","mean_delta_vs_text"])
        for t in signals:
            for sig in signals[t]:
                for i,v in enumerate(signals[t][sig],1):w.writerow([t,sig,i,v])
    ps.append(p);return ps
def main():
    miss=[str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if miss:raise FileNotFoundError("Missing Figure 4 input(s): "+", ".join(miss))
    models=rc(MODELS);signals=signal_values();S.apply();fig=S.figure(S.W2,120);gs=fig.add_gridspec(2,12,wspace=.55,hspace=.42)
    a1=fig.add_subplot(gs[0,0:4]);a2=fig.add_subplot(gs[0,4:8]);gb=gs[0,8:12].subgridspec(2,1,hspace=.34);b1=fig.add_subplot(gb[0]);b2=fig.add_subplot(gb[1]);c=fig.add_subplot(gs[1,0:6]);d=fig.add_subplot(gs[1,6:12])
    model_panel(a1,models,"eeg_to_fmri",-3,"ChineseEEG → fMRI",True,True);model_panel(a2,models,"fmri_to_eeg",-4,"fMRI → ZuCo",False,False);signal_panel(b1,signals["zuco"],"ZuCo EEG",-3,S.BLUE,True);signal_panel(b2,signals["fmri"],"SMN4Lang fMRI",-3,S.ORANGE,False);space_panel(c);reverse_panel(d)
    OUT.mkdir(parents=True,exist_ok=True);outs=[]
    for ext,kw in (("pdf",{}),("svg",{}),("png",{"dpi":600})):
        p=OUT/f"figure4.{ext}";fig.savefig(p,**kw);outs.append(p)
    plt.close(fig);src=write_source(models,signals);svg=OUT/"figure4.svg";transport=base64.b64encode(gzip.compress(svg.read_bytes(),9,mtime=0)).decode("ascii")
    man={"schema_version":2,"status":"ok","analysis":"NeuroSem NMI Figure 4 scientific-graphic redesign","scientific_values_changed":False,"guardrails":["Presentation-only build from frozen model-family, specificity, surrogate, model-space and reverse-transfer outputs.","No training, neural analysis or new inference."],"builder":str(Path(__file__).relative_to(ROOT)),"builder_sha256":sha(Path(__file__)),"inputs":{str(p.relative_to(ROOT)):sha(p) for p in INPUTS},"outputs":{str(p.relative_to(ROOT)):sha(p) for p in outs},"source_data":{str(p.relative_to(ROOT)):sha(p) for p in src},"svg_transport":{"encoding":"gzip+base64","decoded_sha256":sha(svg),"base64":transport}}
    (OUT/"source_manifest.json").write_text(json.dumps(man,separators=(",",":"))+"\n",encoding="utf-8");print(json.dumps({"status":"ok","png_sha256":sha(OUT/"figure4.png"),"svg_sha256":sha(svg)},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())

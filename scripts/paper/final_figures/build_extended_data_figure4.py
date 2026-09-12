#!/usr/bin/env python3
"""Extended Data Figure 4: dose- and architecture-dependent cortical specificity."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]; PAPER_SCRIPTS=ROOT/"scripts"/"paper"
if str(PAPER_SCRIPTS) not in sys.path: sys.path.insert(0,str(PAPER_SCRIPTS))
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import nmi_mockup_style_v3 as ns
from common import OUT, read_json, save_three, write_manifest

REMAINING=ROOT/"outputs"/"nmi_remaining_regional_ideas_v1"/"latest"; FINAL=ROOT/"outputs"/"nmi_final_spatial_validation_v1"/"latest"; FORWARD=ROOT/"outputs"/"nmi_forward_external_dose_characterization_v1"/"latest"
INPUTS=[REMAINING/"summary.json",REMAINING/"dose_system_summary.csv",REMAINING/"model_backbone_enrichment_summary.csv",FINAL/"summary.json",FORWARD/"dose_summary.csv"]
MODEL_LABELS={"e5_large":"E5-large","e5_base":"E5-base","multilingual_mpnet":"mMPNet","multilingual_minilm":"mMiniLM","xlmr_base":"XLM-R","mbert":"mBERT"}


def ed_title(fig,number,text):
    fig.text(.5,.978,f"Extended Data Figure {number}. {text}",ha="center",va="top",family="serif",fontweight="bold",fontsize=13.5,color=ns.INK)

def fmt_p(value):
    v=float(value)
    return f"{v:.2e}" if v<1e-4 else f"{v:.4f}" if v<.01 else f"{v:.3f}"

def panel_a(fig,dose,final):
    ax=fig.add_axes([.075,.555,.390,.285]); x=np.arange(len(dose)); styles=[("language_mean_delta","Language",ns.ORANGE,"o"),("sensorimotor_mean_delta","Sensorimotor",ns.BLUE,"s"),("visual_mean_delta","Visual",ns.GREY,"^")]
    for col,label,color,marker in styles:
        y=dose[col].to_numpy(float)*1e3; ax.plot(x,y,color=color,lw=1.4,marker=marker,ms=5.5,mec="white",mew=.5,label=label)
    ns.zero_line(ax); ax.axvline(2,color=ns.RULE,lw=.9,ls=(0,(4,3))); ax.text(2,1.02,"prospective dose",transform=ax.get_xaxis_transform(),ha="center",va="bottom",fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels([f"{float(v):g}" for v in dose["lambda"]]); ax.set_xlabel("Neural-supervision dose (lambda)"); ax.set_ylabel("Mean participant DeltaRSA (x10^-3)"); ax.legend(loc="upper left",fontsize=7)
    hs=final["hierarchical_synthesis"]["dose_by_system"]; ax.text(.98,.05,f"dose x system omnibus P = {fmt_p(hs['interaction_wald_p'])}\nHolm P = {fmt_p(hs['two_model_holm_p'])}",transform=ax.transAxes,ha="right",va="bottom",fontsize=6.8,color=ns.GREY,linespacing=1.25)
    ns.panel_letter(fig,.018,.905,"a",13); ns.panel_title(fig,.048,.899,"Dose changes the cortical transfer profile",9.5)

def panel_b(fig,backbone,final):
    ax=fig.add_axes([.585,.555,.335,.285]); b=backbone.copy(); b["label"]=b["model_key"].map(MODEL_LABELS).fillna(b["model_key"]); y=np.arange(len(b))[::-1]
    val=b["mean_language_specificity_across_seeds"].to_numpy(float)*1e3; lo=b["participant_avg_specificity_ci_low"].to_numpy(float)*1e3; hi=b["participant_avg_specificity_ci_high"].to_numpy(float)*1e3
    ax.axvline(0,color=ns.RULE,lw=.9,ls=(0,(4,3)))
    span=max(np.ptp(np.r_[lo,hi]),1e-6)
    for yi,v,l,h,p in zip(y,val,lo,hi,b["specificity_fwer_p_across_6_models"].to_numpy(float)):
        color=ns.ORANGE if v>0 else ns.BLUE; ax.plot([l,h],[yi,yi],color=color,lw=1.6,alpha=.65); ax.plot(v,yi,"o",color=color,ms=7,mec="white",mew=.6,zorder=4)
        if p<.05: ax.text(h+.03*span,yi,"*",va="center",ha="left",fontsize=11,color=color)
    ax.set_yticks(y); ax.set_yticklabels(b["label"]); ax.set_xlabel("Language specificity (x10^-3)")
    hs=final["hierarchical_synthesis"]["backbone_by_system"]; ax.text(.98,.05,f"backbone x system omnibus P = {fmt_p(hs['interaction_wald_p'])}\nHolm P = {fmt_p(hs['two_model_holm_p'])}",transform=ax.transAxes,ha="right",va="bottom",fontsize=6.8,color=ns.GREY,linespacing=1.25)
    ax.text(.02,.95,"* six-model max-stat FWER P < 0.05",transform=ax.transAxes,ha="left",va="top",fontsize=6.4,color=ns.GREY)
    ns.panel_letter(fig,.505,.905,"b",13); ns.panel_title(fig,.535,.899,"Architecture strongly shapes cortical specificity",9.5)

def dose_join(dose,forward):
    f=forward.loc[forward["dataset"]=="zuco",["lambda","mean_delta_rsa","delta_external_sts_vs_lambda0_already_observed"]].copy(); f=f.rename(columns={"mean_delta_rsa":"zuco_mean_delta","delta_external_sts_vs_lambda0_already_observed":"sts_delta"}); return dose.merge(f,on="lambda",how="inner",validate="one_to_one")

def trajectory(ax,x,y,color,labels):
    for i in range(len(x)-1): ax.annotate("",xy=(x[i+1],y[i+1]),xytext=(x[i],y[i]),arrowprops=dict(arrowstyle="-|>",color=color,lw=1.2,mutation_scale=9,shrinkA=5,shrinkB=5))
    ax.scatter(x,y,s=52,c=color,edgecolors="white",linewidth=.7,zorder=4)
    for xx,yy,lab in zip(x,y,labels): ax.text(xx,yy,lab,fontsize=7,color=color,ha="left",va="bottom")

def panel_c(fig,joined):
    ax=fig.add_axes([.075,.100,.390,.295]); x=joined["zuco_mean_delta"].to_numpy(float)*1e3; y=joined["language_specificity_mean"].to_numpy(float)*1e3; labs=[f"{float(v):g}" for v in joined["lambda"]]
    trajectory(ax,x,y,ns.BLUE,labs); ns.zero_line(ax); ax.set_xlabel("ZuCo external DeltaRSA (x10^-3)"); ax.set_ylabel("fMRI language specificity (x10^-3)")
    ax.text(.02,.95,"labels show lambda; trajectory follows increasing dose",transform=ax.transAxes,ha="left",va="top",fontsize=6.6,color=ns.GREY)
    ns.panel_letter(fig,.018,.455,"c",13); ns.panel_title(fig,.048,.449,"Cross-modal transfer and cortical specificity diverge across dose",9.5)

def panel_d(fig,joined):
    ax=fig.add_axes([.585,.100,.335,.295]); x=-joined["sts_delta"].to_numpy(float)*1e3; y=joined["language_specificity_mean"].to_numpy(float)*1e3; labs=[f"{float(v):g}" for v in joined["lambda"]]
    trajectory(ax,x,y,ns.ORANGE,labs); ns.zero_line(ax); ax.set_xlabel("Generic semantic cost (-DeltaSTS, x10^-3)"); ax.set_ylabel("fMRI language specificity (x10^-3)")
    ax.text(.02,.95,"descriptive condition-level relationship; no dose is selected here",transform=ax.transAxes,ha="left",va="top",fontsize=6.6,color=ns.GREY)
    ns.panel_letter(fig,.505,.455,"d",13); ns.panel_title(fig,.535,.449,"Semantic cost does not map monotonically onto cortical specificity",9.5)

def main()->int:
    missing=[p for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError("Missing frozen Extended Data Figure 4 source(s): "+", ".join(str(p) for p in missing))
    remaining=read_json(REMAINING/"summary.json"); final=read_json(FINAL/"summary.json")
    if remaining.get("status","ok")!="ok" or final.get("status","ok")!="ok": raise RuntimeError("One or more frozen regional source analyses are not status=ok")
    dose=pd.read_csv(REMAINING/"dose_system_summary.csv").sort_values("lambda").reset_index(drop=True); backbone=pd.read_csv(REMAINING/"model_backbone_enrichment_summary.csv").reset_index(drop=True); forward=pd.read_csv(FORWARD/"dose_summary.csv")
    if len(dose)!=5 or len(backbone)!=6: raise RuntimeError("Expected five doses and six model backbones")
    joined=dose_join(dose,forward)
    if len(joined)!=5: raise RuntimeError("Could not align all five frozen doses to forward external characterization")
    ns.use(); fig=plt.figure(figsize=(10.4,7.35),dpi=200); ed_title(fig,4,"Dose and architecture reshape cortical specificity")
    panel_a(fig,dose,final); panel_b(fig,backbone,final); panel_c(fig,joined); panel_d(fig,joined)
    paths=save_three(fig,"extended_data_figure4"); plt.close(fig)
    write_manifest("extended_data_figure4",Path(__file__),INPUTS,paths,{"role":"dose- and architecture-dependent cortical specificity","guardrail":"Post-confirmatory presentation only; no new model fitting, ROI search, dose search, or inference."})
    print(f"wrote {OUT / 'extended_data_figure4.png'}"); return 0


if __name__=="__main__": raise SystemExit(main())

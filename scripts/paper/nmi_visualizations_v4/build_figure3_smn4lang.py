#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import nmi_style as S

def read_csv(path):
    with open(path,newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
def read_json(path):
    with open(path,encoding="utf-8") as f: return json.load(f)
DEMO_SUMMARY={"reliability_mean":0.65327,"reliability_ci":[0.639,0.668],"arm0_mean":0.12092,"arm1_mean":0.12178,"delta_mean":0.00085250,"delta_ci":[0.0007897,0.0009140]}
def demo_data(n=12,seed=7):
    rng=np.random.default_rng(seed); rel=np.clip(rng.normal(0.653,0.026,n),0.55,0.78); a0=rng.normal(0.12092,0.0072,n); d=np.abs(rng.normal(0.0008525,0.00013,n)); a0=a0-a0.mean()+DEMO_SUMMARY["arm0_mean"]; d=d-d.mean()+DEMO_SUMMARY["delta_mean"]; return rel,a0,a0+d,d

def panel_a(ax):
    S.schematic(ax); S.flowbox(ax,0.02,0.76,0.44,0.18,"ChineseEEG natural-reading\nneural-guided training target"); S.flowbox(ax,0.54,0.76,0.44,0.18,"Frozen E5 contrast\n$\\lambda$=0.10 vs $\\lambda$=0",fc="#fbeeec"); S.arrow(ax,(0.46,0.85),(0.54,0.85)); S.flowbox(ax,0.12,0.38,0.76,0.22,"SMN4Lang / OpenNeuro ds004078\n12 Mandarin participants, 60 spoken stories\nprespecified LanA language-network fMRI"); S.arrow(ax,(0.76,0.76),(0.55,0.60)); ax.text(0.5,0.24,"Model-blind reliability gate completed before E5 evaluation",ha="center",va="center",fontsize=6,color=S.GREY); ax.text(0.5,0.09,"LanA was a precommitted reliable target,\nnot a test of language-network selectivity",ha="center",va="center",fontsize=6,color=S.GREY,linespacing=1.4)

def panel_b(ax,rel,summ):
    n=len(rel); x=np.arange(1,n+1); ax.plot(x,rel,"o",color=S.ORANGE,markersize=2.8,zorder=3); m=summ["reliability_mean"]; lo,hi=summ["reliability_ci"]; ax.errorbar([n+1.4],[m],yerr=[[m-lo],[hi-m]],fmt="D",color=S.INK,mfc="white",mec=S.INK,mew=0.9,capsize=1.8,elinewidth=0.7,markersize=3.6,zorder=4); ax.set_xticks([1,4,8,12,n+1.4]); ax.set_xticklabels(["1","4","8","12","mean"]); ax.set_xlim(0.2,n+2.4); ax.set_xlabel("Participant"); ax.set_ylabel("Residual LOO reliability"); ax.set_ylim(0.55,0.78); S.offset_ticks(ax,"y")

def panel_c(ax,a0,a1,summ):
    for y0,y1 in zip(a0,a1): ax.plot([0,1],[y0,y1],"-",color=S.GREY_L,lw=0.5,zorder=2); ax.plot([0,1],[y0,y1],"o",color=S.GREY,markersize=1.9,zorder=3)
    ax.plot([0,1],[summ["arm0_mean"],summ["arm1_mean"]],"-o",color=S.ORANGE,lw=1.3,markersize=3.4,zorder=5); ax.annotate("arm means",xy=(1,summ["arm1_mean"]),xytext=(5,0),textcoords="offset points",fontsize=6,color=S.ORANGE,va="center"); ax.set_xlim(-0.22,1.42); ax.set_xticks([0,1]); ax.set_xticklabels(["text-only\n$\\lambda$=0","neural-guided\n$\\lambda$=0.10"]); ax.set_ylabel("Participant residual RSA"); ax.tick_params(axis="x",length=0); S.offset_ticks(ax,"y")

def panel_d(ax,d,summ):
    order=np.argsort(d); y=np.arange(1,len(d)+1); ax.plot(d[order]*1e3,y,"o",color=S.ORANGE,markersize=2.8,zorder=3); m=summ["delta_mean"]*1e3; lo,hi=[v*1e3 for v in summ["delta_ci"]]; ax.errorbar([m],[len(d)+1.5],xerr=[[m-lo],[hi-m]],fmt="D",color=S.INK,mfc="white",mec=S.INK,mew=0.9,capsize=1.8,elinewidth=0.7,markersize=3.6,zorder=4); S.zeroline(ax,"v"); ax.set_ylim(0,len(d)+2.6); ax.set_yticks([1,len(d),len(d)+1.5]); ax.set_yticklabels(["lowest","highest","mean"]); ax.set_ylabel("Participants, sorted by $\\Delta$RSA"); ax.set_xlabel("Neural-guided $-$ text-only RSA ($\\times10^{-3}$)"); ax.set_xlim(0,max(d.max()*1e3,hi)*1.10); S.offset_ticks(ax,"x")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--reliability-participants",type=Path); ap.add_argument("--reliability-summary",type=Path); ap.add_argument("--transfer-participants",type=Path); ap.add_argument("--transfer-summary",type=Path); ap.add_argument("--out-prefix",type=Path,required=True); ap.add_argument("--demo",action="store_true"); args=ap.parse_args()
    if args.demo: rel,a0,a1,d=demo_data(); summ=DEMO_SUMMARY
    else:
        for req in ("reliability_participants","reliability_summary","transfer_participants","transfer_summary"):
            if getattr(args,req) is None: ap.error(f"--{req.replace('_','-')} required unless --demo")
        rel_rows=read_csv(args.reliability_participants); rel_sum=read_json(args.reliability_summary); tr_rows=read_csv(args.transfer_participants); tr_sum=read_json(args.transfer_summary); rel=np.array([float(r["primary_residual_reliability"]) for r in rel_rows]); a0=np.array([float(r["lambda_0_residual_rsa"]) for r in tr_rows]); a1=np.array([float(r["lambda_0p10_residual_rsa"]) for r in tr_rows]); d=np.array([float(r["delta_0p10_minus_0"]) for r in tr_rows]); summ={"reliability_mean":float(rel_sum["primary_mean"]),"reliability_ci":rel_sum["primary_bootstrap_95_ci"],"arm0_mean":float(tr_sum["lambda_0_mean_participant_rsa"]),"arm1_mean":float(tr_sum["lambda_0p10_mean_participant_rsa"]),"delta_mean":tr_sum["primary_mean_delta"],"delta_ci":tr_sum["primary_bootstrap_95_ci_mean_delta"]}
    S.apply(); fig=S.figure(S.W2,96); gs=fig.add_gridspec(2,2); ax_a=fig.add_subplot(gs[0,0]); ax_b=fig.add_subplot(gs[0,1]); ax_c=fig.add_subplot(gs[1,0]); ax_d=fig.add_subplot(gs[1,1]); panel_a(ax_a); panel_b(ax_b,rel,summ); panel_c(ax_c,a0,a1,summ); panel_d(ax_d,d,summ); S.panel(ax_a,"a",dx=-0.06)
    for ax,letter in ((ax_b,"b"),(ax_c,"c"),(ax_d,"d")): S.panel(ax,letter,dx=-0.18)
    written=S.save(fig,args.out_prefix); print(json.dumps({"status":"ok","n":int(len(d)),**written},indent=2))
if __name__=="__main__": main()

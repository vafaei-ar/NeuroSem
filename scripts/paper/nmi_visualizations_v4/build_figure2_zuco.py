#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import nmi_style as S

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def read_json(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

DEMO_SUMMARY={"reliability_mean":0.06742,"reliability_ci":[0.05831,0.07687],"arm0_mean":-0.00796,"arm1_mean":-0.00630,"delta_mean":0.0016637,"delta_ci":[0.0012294,0.0021452]}
def demo_data(n=17,seed=11):
    rng=np.random.default_rng(seed); rel=np.clip(rng.normal(0.0674,0.017,n),0.02,None); a0=rng.normal(-0.00796,0.0105,n); d=np.abs(rng.normal(0.0016637,0.0009,n)); a0=a0-a0.mean()+DEMO_SUMMARY["arm0_mean"]; d=d-d.mean()+DEMO_SUMMARY["delta_mean"]; return rel,a0,a0+d,d

def panel_a(ax):
    S.schematic(ax); S.flowbox(ax,0.02,0.74,0.44,0.20,"ChineseEEG\nChinese natural-reading EEG\nneural-guided training"); S.flowbox(ax,0.54,0.74,0.44,0.20,"Frozen E5 contrast\n$\\lambda$=0.10 neural-guided\nvs $\\lambda$=0 text-only",fc="#eef3f8"); S.arrow(ax,(0.46,0.84),(0.54,0.84)); S.flowbox(ax,0.16,0.34,0.68,0.20,"ZuCo 2.0 Task 1\n17 independent readers, English\nnatural-reading EEG"); S.arrow(ax,(0.76,0.74),(0.55,0.54)); ax.text(0.5,0.16,"No ZuCo outcome used for model retuning",ha="center",va="center",fontsize=6,color=S.GREY)

def panel_b(ax,rel,summ):
    n=len(rel); x=np.arange(1,n+1); ax.plot(x,rel,"o",color=S.BLUE,markersize=2.8,zorder=3); m=summ["reliability_mean"]; lo,hi=summ["reliability_ci"]; ax.errorbar([n+1.6],[m],yerr=[[m-lo],[hi-m]],fmt="D",color=S.INK,mfc="white",mec=S.INK,mew=0.9,capsize=1.8,elinewidth=0.7,markersize=3.6,zorder=4); S.zeroline(ax); ax.set_xticks([1,5,9,13,17,n+1.6]); ax.set_xticklabels(["1","5","9","13","17","mean"]); ax.set_xlim(0.2,n+2.6); ax.set_xlabel("Participant"); ax.set_ylabel("Residual LOO reliability"); ax.set_ylim(0,max(rel.max(),hi)*1.12); S.offset_ticks(ax,"y")

def panel_c(ax,a0,a1,summ):
    for y0,y1 in zip(a0,a1): ax.plot([0,1],[y0,y1],"-",color=S.GREY_L,lw=0.5,zorder=2); ax.plot([0,1],[y0,y1],"o",color=S.GREY,markersize=1.9,zorder=3)
    ax.plot([0,1],[summ["arm0_mean"],summ["arm1_mean"]],"-o",color=S.BLUE,lw=1.3,markersize=3.4,zorder=5); S.zeroline(ax); ax.set_xticks([0,1]); ax.set_xticklabels(["text-only\n$\\lambda$=0","neural-guided\n$\\lambda$=0.10"]); ax.set_ylabel("Participant residual RSA"); ax.tick_params(axis="x",length=0); ax.annotate("arm means\n(both below zero)",xy=(1,summ["arm1_mean"]),xytext=(5,0),textcoords="offset points",fontsize=6,color=S.BLUE,va="center",linespacing=1.4); ax.set_xlim(-0.22,1.46); S.offset_ticks(ax,"y")

def panel_d(ax,d,summ):
    order=np.argsort(d); y=np.arange(1,len(d)+1); ax.plot(d[order]*1e3,y,"o",color=S.BLUE,markersize=2.8,zorder=3); m=summ["delta_mean"]*1e3; lo,hi=[v*1e3 for v in summ["delta_ci"]]; ax.errorbar([m],[len(d)+1.8],xerr=[[m-lo],[hi-m]],fmt="D",color=S.INK,mfc="white",mec=S.INK,mew=0.9,capsize=1.8,elinewidth=0.7,markersize=3.6,zorder=4); S.zeroline(ax,"v"); ax.set_ylim(0,len(d)+3.0); ax.set_yticks([1,len(d),len(d)+1.8]); ax.set_yticklabels(["lowest","highest","mean"]); ax.set_ylabel("Participants, sorted by $\\Delta$RSA"); ax.set_xlabel("Neural-guided $-$ text-only RSA ($\\times10^{-3}$)"); ax.set_xlim(0,max(d.max()*1e3,hi)*1.10); S.offset_ticks(ax,"x")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rel-subjects",type=Path); ap.add_argument("--rel-summary",type=Path); ap.add_argument("--transfer-subjects",type=Path); ap.add_argument("--transfer-summary",type=Path); ap.add_argument("--out-prefix",type=Path,required=True); ap.add_argument("--demo",action="store_true"); args=ap.parse_args()
    if args.demo: rel,a0,a1,d=demo_data(); summ=DEMO_SUMMARY
    else:
        for req in ("rel_subjects","rel_summary","transfer_subjects","transfer_summary"):
            if getattr(args,req) is None: ap.error(f"--{req.replace('_','-')} required unless --demo")
        rr=[r for r in read_csv(args.rel_subjects) if r["candidate"]=="row_mean_all"]; rs=read_json(args.rel_summary); tm=next(x for x in rs["metrics"] if x["candidate"]=="row_mean_all"); tr=read_csv(args.transfer_subjects); ts=read_json(args.transfer_summary); pr=ts["primary_result"]
        rel=np.array([float(r["resid_loo"]) for r in rr]); a0=np.array([float(r["lambda_0_resid_rsa"]) for r in tr]); a1=np.array([float(r["lambda_0p10_resid_rsa"]) for r in tr]); d=np.array([float(r["delta_0p10_minus_0"]) for r in tr]); summ={"reliability_mean":tm["mean_resid_loo"],"reliability_ci":tm["resid_loo_bootstrap_95ci"],"arm0_mean":float(a0.mean()),"arm1_mean":float(a1.mean()),"delta_mean":pr["mean_delta"],"delta_ci":pr["bootstrap_95ci"]}
    S.apply(); fig=S.figure(S.W2,96); gs=fig.add_gridspec(2,2); ax_a=fig.add_subplot(gs[0,0]); ax_b=fig.add_subplot(gs[0,1]); ax_c=fig.add_subplot(gs[1,0]); ax_d=fig.add_subplot(gs[1,1]); panel_a(ax_a); panel_b(ax_b,rel,summ); panel_c(ax_c,a0,a1,summ); panel_d(ax_d,d,summ); S.panel(ax_a,"a",dx=-0.06)
    for ax,letter in ((ax_b,"b"),(ax_c,"c"),(ax_d,"d")): S.panel(ax,letter,dx=-0.16)
    written=S.save(fig,args.out_prefix); print(json.dumps({"status":"ok","n":int(len(d)),**written},indent=2))
if __name__=="__main__": main()

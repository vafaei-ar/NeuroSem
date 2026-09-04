#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import nmi_style as S
FLOOR=8e-5

def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def mark_prospective(ax,lam0):
    ax.axvline(lam0,color=S.GREY_L,lw=0.5,ls=(0,(1,2)),zorder=0); ax.annotate("prospective\ndose",xy=(lam0,ax.get_ylim()[0]),xytext=(0,2),textcoords="offset points",fontsize=5.5,color=S.GREY,ha="center",va="bottom")

def panel_a(ax,d):
    lam=np.asarray(d["lambda"],float)
    for key,ci_key,colour,label in (("zuco_delta","zuco_ci",S.BLUE,"ZuCo EEG"),("fmri_delta","fmri_ci",S.ORANGE,"SMN4Lang fMRI")):
        y=np.asarray(d[key],float); ci=np.asarray(d[ci_key],float); pos=y>0; lo=np.clip(ci[:,0],FLOOR,None); hi=np.clip(ci[:,1],FLOOR,None)
        ax.plot(lam[pos],y[pos],"-o",color=colour,label=label,markersize=3.0,lw=1.0,zorder=3); ax.vlines(lam[pos],lo[pos],hi[pos],color=colour,lw=0.7,zorder=2)
        for xi in lam[~pos]:
            ax.plot([xi],[FLOOR*1.25],"o",mfc="white",mec=colour,mew=0.8,markersize=3.4,zorder=4,clip_on=False); ax.annotate("sign\nreversal",xy=(xi,FLOOR*1.25),xytext=(-6,14),textcoords="offset points",fontsize=5.5,color=colour,ha="right",arrowprops=dict(arrowstyle="-",lw=0.5,color=colour))
    z=np.asarray(d["zuco_delta"],float); ref=z[0]*(lam/lam[0]); ax.plot(lam,ref,ls=(0,(2.5,2)),lw=0.6,color=S.GREY_L,zorder=1); ax.annotate("slope 1",xy=(lam[-2],ref[-2]),xytext=(4,-7),textcoords="offset points",fontsize=5.5,color=S.GREY)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.008,1.35); ax.set_ylim(FLOOR,0.055); ax.set_xticks(lam); ax.set_xticklabels(["0.01","0.03","0.10","0.30","1.0"]); ax.set_xlabel("Relational-loss weight $\\lambda$"); ax.set_ylabel("Mean participant $\\Delta$RSA vs $\\lambda$=0"); ax.legend(loc="upper left",bbox_to_anchor=(0.0,1.02)); mark_prospective(ax,d["prospective_lambda"])

def panel_b(ax,d):
    lam=np.asarray(d["lambda"],float); x=np.arange(len(lam)+1); zuco=np.concatenate([[d["zuco_baseline"]],d["zuco_baseline"]+np.asarray(d["zuco_delta"])]); fmri=np.concatenate([[d["fmri_baseline"]],d["fmri_baseline"]+np.asarray(d["fmri_delta"])])
    ax.plot(x,zuco,"-o",color=S.BLUE,markersize=3.0,zorder=3,label="ZuCo EEG"); S.zeroline(ax); cross=np.argmax(zuco>0); ax.annotate("crosses zero",xy=(x[cross],zuco[cross]),xytext=(-4,14),textcoords="offset points",fontsize=5.5,color=S.BLUE,ha="center",arrowprops=dict(arrowstyle="-",lw=0.5,color=S.BLUE)); ax.axhline(d["zuco_reliability"],color=S.GREY,lw=0.6,ls=(0,(3,2)),zorder=1); ax.annotate("target LOO reliability\n(not a noise ceiling)",xy=(0.05,d["zuco_reliability"]),xytext=(0,-2),textcoords="offset points",fontsize=5.5,color=S.GREY,va="top")
    ax.set_xticks(x); ax.set_xticklabels(["0","0.01","0.03","0.10","0.30","1.0"]); ax.set_xlabel("Relational-loss weight $\\lambda$"); ax.set_ylabel("Absolute residual RSA, ZuCo"); ax.set_ylim(-0.016,0.078); S.offset_ticks(ax,"y")

def panel_c(ax,d):
    sts=-np.asarray(d["sts_delta"],float)
    for key,colour,label in (("zuco_delta",S.BLUE,"ZuCo EEG"),("fmri_delta",S.ORANGE,"SMN4Lang fMRI")):
        y=np.asarray(d[key],float); ax.plot(sts,y,"-o",color=colour,markersize=3.0,label=label,zorder=3)
    S.zeroline(ax)
    for xi,yi,lab,off in zip(sts[2:],np.asarray(d["zuco_delta"])[2:],["$\\lambda$=0.10","0.30","1.0"],[(4,-5),(5,-2),(-4,-8)]): ax.annotate(lab,xy=(xi,yi),xytext=off,textcoords="offset points",fontsize=5.5,color=S.GREY,ha="right" if off[0]<0 else "left")
    ax.set_xlabel("Generic STS cost (decrement from $\\lambda$=0)"); ax.set_ylabel("Mean participant $\\Delta$RSA"); ax.legend(loc="upper left")

def panel_d(axes,m):
    order=m["order"]; y=np.arange(len(order))[::-1]; specs=(("eeg_to_fmri","EEG-derived constraint $\\rightarrow$ fMRI"),("fmri_to_eeg","fMRI-derived constraint $\\rightarrow$ EEG"))
    for ax,(key,title) in zip(axes,specs):
        vals=m[key]
        for yi,name in zip(y,order):
            seeds=np.asarray(vals[name],float)*1e3; colour=S.BLUE if name.startswith("E5") else S.GREY; ax.plot(seeds,[yi]*len(seeds),"o",color=colour,markersize=2.6,alpha=0.75,zorder=3); mean=seeds.mean(); ax.plot([mean],[yi],"D",mfc="white",mec=colour,mew=0.9,markersize=4.0,zorder=4)
        S.zeroline(ax,"v"); ax.set_yticks(y)
        if key=="eeg_to_fmri": ax.set_yticklabels(order)
        else: ax.set_yticklabels([]); ax.tick_params(axis="y",length=0); ax.spines["left"].set_visible(False)
        ax.set_ylim(-0.7,len(order)-0.3); ax.set_xlabel("Mean $\\Delta$RSA per seed ($\\times10^{-3}$)"); ax.set_title(title,fontsize=6.5,color=S.INK); ax.grid(axis="x",zorder=0); allv=np.concatenate([np.asarray(vals[n],float) for n in order])*1e3; pad=0.15*(allv.max()-allv.min()); ax.set_xlim(allv.min()-pad,allv.max()+pad); S.offset_ticks(ax,"x")
    axes[1].plot([],[],"o",color=S.GREY,markersize=2.6,label="individual seed"); axes[1].plot([],[],"D",mfc="white",mec=S.GREY,mew=0.9,markersize=4.0,label="three-seed mean"); axes[1].legend(loc="lower right")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dose-summary",type=Path,required=True); ap.add_argument("--model-panel",type=Path,required=True); ap.add_argument("--out-prefix",type=Path,required=True); args=ap.parse_args(); data={"dose":load_json(args.dose_summary),"models":load_json(args.model_panel)}; S.apply(); fig=S.figure(S.W2,108); gs=fig.add_gridspec(2,6,height_ratios=[1.0,1.02]); ax_a=fig.add_subplot(gs[0,0:2]); ax_b=fig.add_subplot(gs[0,2:4]); ax_c=fig.add_subplot(gs[0,4:6]); ax_d1=fig.add_subplot(gs[1,0:3]); ax_d2=fig.add_subplot(gs[1,3:6]); panel_a(ax_a,data["dose"]); panel_b(ax_b,data["dose"]); panel_c(ax_c,data["dose"]); panel_d((ax_d1,ax_d2),data["models"])
    for ax,letter,dx in ((ax_a,"a",-0.26),(ax_b,"b",-0.26),(ax_c,"c",-0.26),(ax_d1,"d",-0.17)): S.panel(ax,letter,dx=dx)
    written=S.save(fig,args.out_prefix); print(json.dumps({"status":"ok",**written},indent=2))
if __name__=="__main__": main()

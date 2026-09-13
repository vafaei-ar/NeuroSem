#!/usr/bin/env python3
"""Final Main Figure 1: frozen brain-derived supervision transfers across independent neural datasets.

Presentation-only. Every displayed scientific value is loaded from the committed frozen
Figure 1 snapshots under paper/figure_data/nmi_redesign_v2/. No model fitting, neural
analysis, target selection, dose search, or new inference is performed here.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

import style as ns
from common import OUT, save_three, write_manifest

SNAPSHOT_DIR = ROOT / "paper" / "figure_data" / "nmi_redesign_v2"
REL_SNAPSHOT = SNAPSHOT_DIR / "figure1_reliability_source.csv"
TRANSFER_SNAPSHOT = SNAPSHOT_DIR / "figure1_transfer_source.csv"
SEED_SNAPSHOT = SNAPSHOT_DIR / "figure1_seed_source.csv"
PROVENANCE = SNAPSHOT_DIR / "figure1_source_snapshot_manifest.json"
INPUTS = [REL_SNAPSHOT, TRANSFER_SNAPSHOT, SEED_SNAPSHOT, PROVENANCE]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_data() -> tuple[dict, dict]:
    meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rel_rows = read_csv(REL_SNAPSHOT); transfer_rows = read_csv(TRANSFER_SNAPSHOT); seed_rows = read_csv(SEED_SNAPSHOT)
    data = {}
    definitions = {"zuco": ("ZuCo EEG", ns.BLUE, 17), "fmri": ("SMN4Lang fMRI", ns.ORANGE, 12)}
    for key, (label, color, expected_n) in definitions.items():
        rr=[r for r in rel_rows if r["dataset"]==key]; tr=[r for r in transfer_rows if r["dataset"]==key]; sr=[r for r in seed_rows if r["dataset"]==key]
        if len(rr)!=expected_n or len(tr)!=expected_n: raise RuntimeError(f"{key}: unexpected participant count")
        if [int(r["participant_index"]) for r in rr]!=list(range(1,expected_n+1)): raise RuntimeError(f"{key}: reliability participant order changed")
        if [int(r["participant_index"]) for r in tr]!=list(range(1,expected_n+1)): raise RuntimeError(f"{key}: transfer participant order changed")
        if [r["training_run"] for r in sr] != ["Primary","29","30","31"]: raise RuntimeError(f"{key}: optimization-run labels changed")
        rel=np.asarray([float(r["residual_loo_reliability"]) for r in rr]); a0=np.asarray([float(r["text_only_residual_rsa"]) for r in tr]); a1=np.asarray([float(r["neural_guided_residual_rsa"]) for r in tr]); delta=np.asarray([float(r["delta_rsa"]) for r in tr]); seed_means=np.asarray([float(r["mean_delta_rsa"]) for r in sr]); seed_counts=[int(r["positive_participants"]) for r in sr]; statuses=[r["evidence_status"] for r in sr]
        summary=meta["displayed_summary"][key]; delta_ci=np.asarray(summary["primary_bootstrap_95ci"],float)
        if not np.allclose(a1-a0,delta,atol=5e-12): raise RuntimeError(f"{key}: participant delta arithmetic failed")
        if not np.all(delta>0): raise RuntimeError(f"{key}: primary participant direction changed")
        if not np.isclose(rel.mean(),float(summary["reliability_mean"]),atol=5e-12): raise RuntimeError(f"{key}: reliability mean differs from frozen manifest")
        if not np.isclose(delta.mean(),float(summary["primary_mean_delta"]),atol=5e-12): raise RuntimeError(f"{key}: primary delta mean differs from frozen manifest")
        if not np.allclose(seed_means,np.asarray(summary["four_run_means"],float),atol=5e-12): raise RuntimeError(f"{key}: seed means differ from frozen manifest")
        if statuses[0]!="prospective primary" or any(s!="post-confirmatory optimization robustness" for s in statuses[1:]): raise RuntimeError(f"{key}: evidence-status labels changed")
        data[key]={"label":label,"color":color,"n":expected_n,"rel":rel,"a0":a0,"a1":a1,"delta":delta,"delta_mean":float(delta.mean()),"delta_ci":delta_ci,"seed_means":seed_means,"seed_counts":seed_counts}
    return data,meta


def box(ax,x0,x1,y0,y1,text,face,edge,fontsize=8,tcolor=ns.INK):
    ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle='round,pad=.004,rounding_size=.022',facecolor=face,edgecolor=edge,lw=1,transform=ax.transAxes,clip_on=False)); ax.text((x0+x1)/2,(y0+y1)/2,text,transform=ax.transAxes,ha='center',va='center',fontsize=fontsize,color=tcolor,linespacing=1.4)

def arrow(ax,xy,xytext,rad=0): ax.add_patch(FancyArrowPatch(xytext,xy,transform=ax.transAxes,arrowstyle='-|>',mutation_scale=11,lw=1.1,color=ns.INK,connectionstyle=f'arc3,rad={rad}',clip_on=False))

def schematic(fig):
    ax=fig.add_axes([.035,.635,.435,.245]); ax.set_axis_off(); box(ax,0,.235,.30,.80,'ChineseEEG\nneural geometry\n(large-scale source)','#F0F0F0','#BDBDBD',7.2); arrow(ax,(.415,.55),(.245,.55)); ax.text(.33,.615,'train once',transform=ax.transAxes,ha='center',fontsize=7.6,fontweight='bold'); ax.text(.33,.43,'learn\nneural-to-text\nmapping',transform=ax.transAxes,ha='center',va='top',fontsize=6.2,color='#555'); box(ax,.425,.70,.26,.84,'FROZEN\n(no further updates)',ns.BLUE,ns.BLUE,7.8,'white')
    for a in range(0,180,60):
        t=np.deg2rad(a); ax.plot([.5625-.022*np.cos(t),.5625+.022*np.cos(t)],[.755-.038*np.sin(t),.755+.038*np.sin(t)],color='white',lw=1.2,transform=ax.transAxes,clip_on=False,zorder=6)
    arrow(ax,(.755,.86),(.705,.62),-.28); arrow(ax,(.755,.26),(.705,.48),.28); box(ax,.760,1,.70,1.02,'ZuCo EEG\n(independent dataset)','#EAF2FB',ns.BLUE,7.2); box(ax,.760,1,.10,.42,'SMN4Lang fMRI\n(independent dataset)','#FDEFE5',ns.ORANGE,7.2)

def reliability(fig,d):
    for i,key in enumerate(['zuco','fmri']):
        q=d[key]; ax=fig.add_axes([.575+i*.215,.665,.175,.195]); ns.zero_line(ax); vals=q['rel']; ns.observations(ax,-.13,vals,ns.BLUE_LIGHT if key=='zuco' else ns.ORANGE_LIGHT,seed=i,width=.08,size=13); ns.half_violin(ax,.16,vals,ns.BLUE_FILL if key=='zuco' else ns.ORANGE_FILL,width=.30,bw=.45); m=float(np.mean(vals)); ax.plot(.16,m,'o',ms=6,color=q['color'],mec='white',mew=.6,zorder=5); lo=min(0,float(vals.min()))-.05*np.ptp(vals); hi=float(vals.max())+.25*np.ptp(vals); ax.set_xlim(-.55,.85); ax.set_ylim(lo,hi); ax.set_xticks([]); ax.spines['bottom'].set_visible(False)
        if i==0: ax.set_ylabel('Brain–text reliability\n(correlation, r)',fontsize=7.2)
        else: ax.set_yticklabels([])
        ns.facet_strip(ax,f"{q['label']} (n = {q['n']})",ns.BLUE_STRIP if key=='zuco' else ns.ORANGE_STRIP,8); ax.text(.97,.93,f"{q['n']}/{q['n']}\npositive",transform=ax.transAxes,ha='right',fontsize=8.2,color=q['color'],fontweight='bold')

def transfer(fig,d):
    for i,key in enumerate(['zuco','fmri']):
        q=d[key]; x0=.055+i*.470; bg='#EFF5FC' if key=='zuco' else '#FDF3EC'; fig.add_artist(FancyBboxPatch((x0-.018,.297),.440,.243,boxstyle='round,pad=.004,rounding_size=.012',facecolor=bg,edgecolor='none',transform=fig.transFigure,zorder=0)); delta=q['delta']*1e3; n=q['n']; ax=fig.add_axes([x0+.035,.345,.290,.150],zorder=2); ax.patch.set_alpha(0); ns.zero_line(ax)
        for k,v in enumerate(delta,1): ax.annotate('',xy=(k,v),xytext=(k,0),arrowprops=dict(arrowstyle='-|>',lw=.8,color='#33475B',mutation_scale=7,shrinkA=3,shrinkB=3))
        ax.scatter(range(1,n+1),np.zeros(n),s=22,facecolors='white',edgecolors=q['color'],lw=1,zorder=4,label='Text-only baseline'); ax.scatter(range(1,n+1),delta,s=24,c=q['color'],zorder=4,label='Neural-guided change'); ymax=max(delta)*1.18; ax.set_xlim(.4,n+.6); ax.set_ylim(-.08*ymax,ymax); ax.set_xticks(range(1,n+1)); ax.tick_params(axis='x',labelsize=6.2); ax.set_xlabel('Participant',fontsize=7.4,labelpad=1); ax.set_ylabel('Paired ΔRSA\n(×10$^{-3}$)',fontsize=7.2); ax.set_title(f"{q['label']} (n = {n})",color=q['color'],fontsize=9,fontweight='bold',pad=16); ax.legend(loc='upper left',fontsize=5.8,frameon=True,facecolor='white',edgecolor='#DDD')
        axi=fig.add_axes([x0+.352,.345,.062,.150],zorder=2); axi.patch.set_alpha(0); ns.zero_line(axi); ns.observations(axi,-.16,delta,q['color'],seed=i+7,width=.10,size=9); ns.half_violin(axi,.14,delta,ns.BLUE_FILL if key=='zuco' else ns.ORANGE_FILL,width=.34,bw=.5); mean=q['delta_mean']*1e3; ci=q['delta_ci']*1e3; ns.point_with_ci(axi,.14,mean,ci[0],ci[1],q['color'],ms=5.5); axi.set_xlim(-.6,.9); axi.set_ylim(-.08*ymax,ymax); axi.set_xticks([]); axi.set_yticklabels([]); axi.spines['bottom'].set_visible(False); axi.set_title('Δ (neural − text)',fontsize=7.4,pad=16); axi.text(.5,-.135,f"mean = {mean:+.2f} ×10$^{{-3}}$",transform=axi.transAxes,ha='center',fontsize=7.2,fontweight='bold')

def runs(fig,d):
    xs=np.arange(4)
    for i,key in enumerate(['zuco','fmri']):
        q=d[key]; y0=.170-i*.110; bg='#EFF5FC' if key=='zuco' else '#FDF3EC'; fig.add_artist(FancyBboxPatch((.037,y0-.030),.938,.104,boxstyle='round,pad=.003,rounding_size=.010',facecolor=bg,edgecolor='none',transform=fig.transFigure,zorder=0)); ax=fig.add_axes([.215,y0,.700,.070],zorder=2); ax.patch.set_alpha(0); ns.zero_line(ax); vals=q['seed_means']*1e3; ax.plot(xs[0],vals[0],'D',ms=6,color=q['color'],mec='white',mew=.5,zorder=4); ax.plot(xs[1:],vals[1:],'o',ms=6,mfc='white',mec=q['color'],mew=1,zorder=4)
        for x,v,k in zip(xs,vals,q['seed_counts']): ax.text(x,v+.08*max(vals),f'{k}/{q["n"]}',ha='center',va='bottom',fontsize=6,color=q['color'])
        ax.axvline(.5,color='#B0B0B0',lw=.8,ls=(0,(3,3))); ax.set_xlim(-.6,3.6); ax.set_ylim(-.15*max(vals),1.35*max(vals)); ax.set_xticks(xs); ax.set_xticklabels(['Primary','Run 29','Run 30','Run 31'],fontsize=6.6); ax.set_ylabel('Mean ΔRSA\n(×10$^{-3}$)',fontsize=6.6); ax.spines['bottom'].set_visible(False); fig.text(.115,y0+.036,f"{q['label']}\n(n = {q['n']})",ha='center',va='center',fontsize=7.4,color=q['color'],fontweight='bold')
        if i==0: ax.text(.11,1.24,'Prospective primary',transform=ax.transAxes,ha='center',fontsize=7.6,color='#7A7A7A'); ax.text(.68,1.24,'Post-confirmatory optimization robustness',transform=ax.transAxes,ha='center',fontsize=7.6,color='#7A7A7A')

def main()->int:
    missing=[p for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError('Missing frozen Figure 1 source(s): '+', '.join(str(p) for p in missing))
    d,_=load_data(); ns.use(); fig=plt.figure(figsize=(10.4,7.35),dpi=200); ns.fig_title(fig,1,'Frozen brain-derived supervision transfers across independent neural datasets',size=13.5); schematic(fig); reliability(fig,d); transfer(fig,d); runs(fig,d); ns.panel_letter(fig,.016,.930,'a',13); ns.panel_title(fig,.042,.925,'Study schematic',9.5); ns.panel_letter(fig,.545,.930,'b',13); ns.panel_title(fig,.571,.925,'Reliability gates in target datasets',9.5); ns.panel_letter(fig,.016,.590,'c',13); ns.panel_title(fig,.042,.585,'Participant-level transfer: neural-guided vs. text-only',9.5); ns.panel_letter(fig,.016,.300,'d',13); ns.panel_title(fig,.042,.295,'Optimization-run consistency',9.5)
    paths=save_three(fig,'figure1'); plt.close(fig); write_manifest('figure1',Path(__file__),INPUTS,paths,{'role':'prospective transfer and optimization-run robustness','source_lineage':'committed frozen Figure 1 snapshots with RunRelay/upstream hashes in figure1_source_snapshot_manifest.json','guardrail':'Presentation only; no new model fitting, evaluation, neural analysis, dose search, or inference.'}); print(f"wrote {OUT / 'figure1.png'}"); return 0

if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
import style as ns
from common import OUT,save_three,write_manifest
DEV=ROOT/'paper/figure_data/chineseeeg_development_v1.json';REL_SUM=ROOT/'outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/summary.json';REL_SUB=ROOT/'outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/subject_summary.csv';STS1=ROOT/'outputs/bert_neurosem_cmteb_sts_v1/20260823_122332/summary.json';STS2=ROOT/'outputs/bert_neurosem_cmteb_sts_v1_seed2/20260823_123910/summary.json';INPUTS=[DEV,REL_SUM,REL_SUB,STS1,STS2];ARM_ORDER=['Base','Text-only','Neural-guided','Shuffled-neural'];ARM_MAP={'Base':'base','Text-only':'text_only','Neural-guided':'neural','Shuffled-neural':'shuffled_neural'};ARM_COLORS={'Base':ns.GREY_LIGHT,'Text-only':ns.GREY,'Neural-guided':ns.BLUE,'Shuffled-neural':'#8F8F8F'};ARM_MARKERS={'Base':'o','Text-only':'s','Neural-guided':'D','Shuffled-neural':'^'}
def rc(p):
    with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def load_data():
    dev=json.loads(DEV.read_text(encoding='utf-8'));rs=json.loads(REL_SUM.read_text(encoding='utf-8'));rr=rc(REL_SUB);sp=[json.loads(STS1.read_text(encoding='utf-8')),json.loads(STS2.read_text(encoding='utf-8'))];raw=np.asarray([float(r['raw_loo']) for r in rr]);resid=np.asarray([float(r['residual_loo']) for r in rr])
    if len(raw)!=int(rs['n_subjects']) or len(raw)!=9:raise RuntimeError('Expected nine ChineseEEG reliability participants')
    if not np.isclose(raw.mean(),float(rs['raw_loo_mean']),atol=5e-12) or not np.isclose(resid.mean(),float(rs['residual_loo_mean']),atol=5e-12):raise RuntimeError('Reliability replay summary mismatch')
    runs=np.asarray(dev['heldout_residual_correspondence'],float)
    if len(runs)!=6 or not np.all(runs>0):raise RuntimeError('Expected six positive held-out source runs')
    sealed=dev['sealed_run07'];run07={arm:np.asarray([float(sealed['seed_1'][i]),float(sealed['seed_2'][i])]) for i,arm in enumerate(sealed['arms'])};semantic={}
    for display,key in ARM_MAP.items():
        vals=[]
        for payload in sp:
            result=payload['results'][key];scores=result['task_scores'];mean=float(np.mean([float(v) for v in scores.values()]));reported=float(result['mean_spearman'])
            if len(scores)!=8 or not np.isclose(mean,reported,atol=5e-13):raise RuntimeError(f'{display}: semantic summary mismatch')
            vals.append(reported)
        semantic[display]=np.asarray(vals)
    return {'raw':raw,'resid':resid,'runs':runs,'run07':run07,'semantic':semantic}
def panel_a(fig,d):
    ax=fig.add_axes([.075,.565,.390,.290]);raw=np.asarray(d['raw']);resid=np.asarray(d['resid'])
    for a,b in zip(raw,resid):ax.plot([0,1],[a,b],color='#D0D0D0',lw=.65,zorder=1)
    ns.half_violin(ax,-.10,raw,'#DDDDDD',side='left',width=.25,bw=.45,alpha=.75);ns.half_violin(ax,.90,resid,ns.BLUE_FILL,side='left',width=.25,bw=.45,alpha=.75);ns.observations(ax,.12,raw,ns.GREY,seed=1,width=.06,size=16);ns.observations(ax,1.12,resid,ns.BLUE,seed=2,width=.06,size=16);ax.plot([0,1],[raw.mean(),resid.mean()],color=ns.INK,lw=1.3,zorder=4);ax.plot(0,raw.mean(),'o',color=ns.GREY,ms=7,mec='white',mew=.6,zorder=5);ax.plot(1,resid.mean(),'o',color=ns.BLUE,ms=7,mec='white',mew=.6,zorder=5);ax.set_xticks([0,1]);ax.set_xticklabels(['Raw LOO','Residual LOO']);ax.tick_params(axis='x',length=0);ax.set_xlim(-.55,1.45);ax.set_ylim(0,max(raw.max(),resid.max())*1.18);ax.set_ylabel('Cross-participant reliability');ax.text(.02,.96,f"mean = {raw.mean():.3f}",transform=ax.transAxes,va='top',fontsize=7,color=ns.GREY);ax.text(.98,.96,f"mean = {resid.mean():.3f}",transform=ax.transAxes,va='top',ha='right',fontsize=7,color=ns.BLUE);ns.panel_letter(fig,.018,.920,'a',13);ns.panel_title(fig,.048,.914,'Source reliability survives nuisance adjustment',9.5)
def panel_b(fig,d):
    ax=fig.add_axes([.570,.565,.350,.290]);y=np.asarray(d['runs']);x=np.arange(1,len(y)+1);ns.zero_line(ax)
    for xi,yi in zip(x,y):ax.plot([xi,xi],[0,yi],color=ns.BLUE_LIGHT,lw=1,zorder=1)
    ax.scatter(x,y,s=38,facecolor='white',edgecolor=ns.BLUE,linewidth=.9,zorder=3);ax.axhline(y.mean(),color=ns.BLUE,lw=1.3);ax.set_xticks(x);ax.set_xticklabels([f'Run {i:02d}' for i in x]);ax.set_ylabel('Held-out residual model-EEG RSA');ax.set_ylim(0,y.max()*1.28);ax.text(.98,.94,f"6/6 positive\nmean = {y.mean():.4f}\nexact one-sided P = 0.0156",transform=ax.transAxes,ha='right',va='top',fontsize=7,color=ns.BLUE,linespacing=1.3);ns.panel_letter(fig,.505,.920,'b',13);ns.panel_title(fig,.535,.914,'Held-out correspondence is positive across source runs',9.5)
def panel_c(fig,d):
    ax=fig.add_axes([.075,.105,.390,.310]);xs=np.arange(len(ARM_ORDER));seed1=[];seed2=[]
    for i,arm in enumerate(ARM_ORDER):
        vals=np.asarray(d['run07'][arm]);seed1.append(vals[0]);seed2.append(vals[1]);c=ARM_COLORS[arm];m=ARM_MARKERS[arm];ax.scatter([i-.07,i+.07],vals,s=34,marker=m,facecolor=c if arm=='Neural-guided' else 'white',edgecolor=c,linewidth=.9,zorder=4);ax.plot([i-.16,i+.16],[vals.mean(),vals.mean()],color=c,lw=1.5,zorder=3)
    ax.plot(xs-.07,seed1,color='#C8C8C8',lw=.7,zorder=1);ax.plot(xs+.07,seed2,color='#E0E0E0',lw=.7,zorder=1);ax.set_xticks(xs);ax.set_xticklabels(ARM_ORDER,rotation=12,ha='right');ax.set_ylabel('Reserved run-07 residual neural RSA');allv=np.concatenate([np.asarray(d['run07'][a]) for a in ARM_ORDER]);pad=.16*np.ptp(allv);ax.set_ylim(allv.min()-pad,allv.max()+pad);ax.text(.02,.95,'two completed development seeds per arm',transform=ax.transAxes,ha='left',va='top',fontsize=7,color=ns.GREY);ns.panel_letter(fig,.018,.470,'c',13);ns.panel_title(fig,.048,.464,'Reserved-run neural correspondence across development arms',9.5)
def panel_d(fig,d):
    ax=fig.add_axes([.570,.105,.350,.310])
    for arm in ARM_ORDER:
        x=np.asarray(d['semantic'][arm]);y=np.asarray(d['run07'][arm]);c=ARM_COLORS[arm];m=ARM_MARKERS[arm];ax.plot(x,y,color='#D4D4D4',lw=.7,zorder=1);ax.scatter(x,y,s=42 if arm=='Neural-guided' else 32,marker=m,facecolor=c if arm=='Neural-guided' else 'white',edgecolor=c,linewidth=.9,zorder=3);ax.text(float(x.mean())+.0004,float(y.mean())+(.00015 if arm!='Shuffled-neural' else -.00022),arm,fontsize=7,color=c,va='center')
    ax.set_xlabel('Eight-task semantic mean Spearman');ax.set_ylabel('Reserved run-07 residual neural RSA');ax.set_xlim(.281,.311);ax.set_ylim(.0310,.0382);ax.text(.02,.04,'Development panel only; external transfer remains the primary claim.',transform=ax.transAxes,ha='left',va='bottom',fontsize=6.5,color=ns.GREY);ns.panel_letter(fig,.505,.470,'d',13);ns.panel_title(fig,.535,.464,'Neural-semantic development trade-off',9.5)
def main()->int:
    missing=[p for p in INPUTS if not p.exists()]
    if missing:raise FileNotFoundError('Missing frozen Extended Data Figure 1 source(s): '+', '.join(str(p) for p in missing))
    d=load_data();ns.use();fig=plt.figure(figsize=(10.4,7.35),dpi=200);ns.ed_title(fig,1,'Source measurability and development-stage learnability');panel_a(fig,d);panel_b(fig,d);panel_c(fig,d);panel_d(fig,d);paths=save_three(fig,'extended_data_figure1');plt.close(fig);write_manifest('extended_data_figure1',Path(__file__),INPUTS,paths,{'role':'source measurability and development-stage evidence','guardrail':'Presentation only; no new model fitting, neural analysis, or inference.'});print(f"wrote {OUT / 'extended_data_figure1.png'}");return 0
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
import style as ns
from common import OUT,legacy_status_ok,save_three,write_manifest
FINAL=ROOT/'outputs/nmi_final_spatial_validation_v1/latest';REVERSE=ROOT/'outputs/nmi_bidirectional_fmri_to_zuco_v1/latest';REVERSE_MULTI=ROOT/'outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest';INPUTS=[FINAL/'summary.json',FINAL/'story_leave_one_out.csv',REVERSE/'summary.json',REVERSE_MULTI/'summary.json']
def rj(p):return json.loads(p.read_text(encoding='utf-8'))
def story_panel(ax,x,y,summary,title,color,ylabel):
    lo=float(summary['twofactor_bootstrap_ci_low'])*1e3;hi=float(summary['twofactor_bootstrap_ci_high'])*1e3;mean=float(summary['participant_mean'])*1e3;ax.axhspan(lo,hi,color=color,alpha=.11,zorder=0);ax.axhline(0,color=ns.RULE,lw=.9,ls=(0,(4,3)),zorder=0);ax.axhline(mean,color=color,lw=1.3,zorder=2);ax.plot(x,y,color=color,lw=1,alpha=.85,zorder=2);ax.scatter(x,y,s=16,facecolor='white',edgecolor=color,linewidth=.7,zorder=3);ax.set_xlim(.2,len(x)+.8);pad=max(.12*np.ptp(y),.02*max(abs(y).max(),1e-6));ax.set_ylim(min(0,y.min(),lo)-pad,max(y.max(),hi)+pad);ax.set_xlabel('Omitted story');ax.set_ylabel(ylabel);ax.set_title(title,loc='left',fontsize=9.5,fontweight='bold',pad=8);ax.text(.02,.96,f"60/60 leave-one-story-out estimates > 0\nparticipant × story 95% CI: [{lo:.3f}, {hi:.3f}] ×10$^{{-3}}$",transform=ax.transAxes,ha='left',va='top',fontsize=6.8,color=ns.GREY,linespacing=1.3)
def reverse_panel(fig,primary,added):
    ax=fig.add_axes([.175,.095,.650,.245]);p=primary['primary_result'];rows=added['seed_results'];means=[float(p['mean_delta'])]+[float(r['zuco']['mean_delta']) for r in rows];cis=[p['bootstrap_95ci']]+[r['zuco']['bootstrap_95ci'] for r in rows]
    if len(means)!=4:raise RuntimeError('Expected primary plus three added reverse-transfer runs')
    x=np.arange(4);y=np.asarray(means)*1e5;ci=np.asarray(cis)*1e5;err=np.vstack([y-ci[:,0],ci[:,1]-y]);ns.zero_line(ax);ax.axvline(.5,color=ns.RULE,lw=.9,ls=(0,(4,3)));ax.errorbar([0],[y[0]],yerr=err[:,[0]],fmt='D',color=ns.ORANGE,mfc=ns.ORANGE,mec='white',mew=.6,ms=7,capsize=3,lw=1.2,zorder=4);ax.errorbar(x[1:],y[1:],yerr=err[:,1:],fmt='o',color=ns.ORANGE,mfc='white',mec=ns.ORANGE,mew=1,ms=7,capsize=3,lw=1.2,zorder=4);ax.set_xticks(x);ax.set_xticklabels(['Primary','Run 29','Run 30','Run 31']);ax.set_ylabel('Reverse fMRI-to-ZuCo mean ΔRSA (×10$^{-5}$)');ax.text(.10,1.06,'Frozen primary',transform=ax.transAxes,ha='center',fontsize=8,color=ns.GREY);ax.text(.69,1.06,'Added optimization seeds',transform=ax.transAxes,ha='center',fontsize=8,color=ns.GREY);ax.text(.98,.94,'Reverse transfer remains small but directionally positive across added seeds',transform=ax.transAxes,ha='right',va='top',fontsize=7,color=ns.ORANGE);ns.panel_letter(fig,.018,.390,'c',13);ns.panel_title(fig,.048,.384,'Reverse-transfer boundary and optimization consistency',9.5)
def main()->int:
    missing=[p for p in INPUTS if not p.exists()]
    if missing:raise FileNotFoundError('Missing frozen Extended Data Figure 2 source(s): '+', '.join(str(p) for p in missing))
    final=rj(FINAL/'summary.json');primary=rj(REVERSE/'summary.json');added=rj(REVERSE_MULTI/'summary.json')
    if not all(legacy_status_ok(x) for x in [final,primary,added]):raise RuntimeError('One or more frozen Extended Data Figure 2 sources are not status=ok')
    story=pd.read_csv(FINAL/'story_leave_one_out.csv')
    if len(story)!=60:raise RuntimeError('Expected 60 leave-one-story-out rows')
    x=np.arange(1,61);y1=story['reliability_adjusted_language_mean'].to_numpy(float)*1e3;y2=story['temporal_minus_frontal_mean'].to_numpy(float)*1e3;ns.use();fig=plt.figure(figsize=(10.4,7.35),dpi=200);ns.ed_title(fig,2,'Story robustness and reverse-transfer boundary conditions');ax1=fig.add_axes([.075,.525,.390,.310]);ax2=fig.add_axes([.565,.525,.390,.310]);story_panel(ax1,x,y1,final['story_robustness']['reliability_adjusted_language'],'Reliability-adjusted language enrichment',ns.BLUE,'Language enrichment (×10$^{-3}$)');story_panel(ax2,x,y2,final['story_robustness']['temporal_minus_frontal'],'Temporal minus frontal language transfer',ns.ORANGE,'Temporal − frontal effect (×10$^{-3}$)');ns.panel_letter(fig,.018,.900,'a',13);ns.panel_title(fig,.048,.894,'Language enrichment is stable across stories',9.5);ns.panel_letter(fig,.505,.900,'b',13);ns.panel_title(fig,.535,.894,'Temporal enrichment is stable across stories',9.5);reverse_panel(fig,primary,added);paths=save_three(fig,'extended_data_figure2');plt.close(fig);write_manifest('extended_data_figure2',Path(__file__),INPUTS,paths,{'role':'story robustness and reverse-transfer boundary','guardrail':'Presentation only; all values are read from completed frozen analyses.'});print(f"wrote {OUT / 'extended_data_figure2.png'}");return 0
if __name__=='__main__':raise SystemExit(main())

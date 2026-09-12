#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import build_nmi_figure3_redesign_v1 as source
import nmi_mockup_style_v3 as ns

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/nmi_figure2_mockup_v3/latest'
LAM=np.array([.01,.03,.10,.30,1.0]); LAB=['0.01','0.03','0.10','0.30','1.0']


def draw_dose(fig,d):
    for i,key in enumerate(['zuco','smn4lang_fmri']):
        q=d[key]; ax=fig.add_axes([.085+i*.480,.580,.390,.255]); ns.zero_line(ax); ax.axvline(2,color='#777',lw=.9,ls=(0,(4,3)))
        ax.text(2,1.02,'prospective\ndose',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.1)
        y=q['delta']*1e3; lo=q['lo']*1e3; hi=q['hi']*1e3; c=ns.BLUE if key=='zuco' else ns.ORANGE; fill=ns.BLUE_FILL if key=='zuco' else ns.ORANGE_FILL
        for k in range(5):
            ns.ci_cloud(ax,k+.10,y[k],lo[k],hi[k],fill,width=.34,alpha=.75)
            ns.point_with_ci(ax,k,y[k],lo[k],hi[k],c,ms=7)
        ax.plot(range(5),y,color=c,lw=1.5,zorder=4); ax.set_xlim(-.6,4.75)
        span=max(hi.max()-min(0,lo.min()),.001); ax.set_ylim(min(-.12*span,lo.min()-.08*span),hi.max()+.18*span)
        ax.set_xticks(range(5)); ax.set_xticklabels(LAB); ax.set_xlabel('Supervision dose (λ)'); ax.set_ylabel('Mean external ΔRSA (×10$^{-3}$)')
        title='ZuCo EEG' if key=='zuco' else 'SMN4Lang fMRI'; ax.set_title(title,loc='left',color=c,fontsize=9.5,fontweight='bold',pad=9)
        note='More supervision\nincreases transfer' if key=='zuco' else 'Transfer rises through λ=0.30\nand reverses at λ=1.0'
        ax.text(1.0,1.06,note,transform=ax.transAxes,ha='right',va='bottom',fontsize=7,color='#888',style='italic')
        ax.text(.02,.03,'shaded cloud: frozen 95% CI of mean',transform=ax.transAxes,fontsize=5.8,color='#777')

def draw_traj(fig,d):
    ax=fig.add_axes([.085,.085,.345,.360]);
    for key in ['zuco','smn4lang_fmri']:
        q=d[key]; x=-q['sts']*1e3; y=q['delta']*1e3; c=ns.BLUE if key=='zuco' else ns.ORANGE
        for k in range(4):
            ax.annotate('',xy=(x[k+1],y[k+1]),xytext=(x[k],y[k]),arrowprops=dict(arrowstyle='-|>',lw=1.3,color=c,mutation_scale=9,shrinkA=5,shrinkB=5))
        ax.scatter(x,y,s=60,c=c,zorder=5,edgecolors='white',lw=.8)
        for xx,yy,ll in zip(x,y,LAB): ax.text(xx,yy+.04*(max(y)-min(y)+1e-9),ll,ha='center',fontsize=7.2,color=c)
    ax.set_xlabel('Semantic cost (−ΔSTS, ×10$^{-3}$)'); ax.set_ylabel('External ΔRSA (×10$^{-3}$)'); ns.zero_line(ax)
    ax.text(.98,.94,'ZuCo EEG',transform=ax.transAxes,ha='right',color=ns.BLUE,fontsize=8.5,fontweight='bold')
    ax.text(.98,.08,'SMN4Lang fMRI',transform=ax.transAxes,ha='right',color=ns.ORANGE,fontsize=8.5,fontweight='bold')

def draw_displacement(fig,metrics,a,b):
    ax=fig.add_axes([.685,.115,.235,.320]); y=np.arange(len(metrics))[::-1]; ns.zero_line(ax,'v')
    d10=np.array([1-float(a[k]) for _,k in metrics]); d1=np.array([1-float(b[k]) for _,k in metrics])
    for yi,l,r in zip(y,d10,d1): ns.dumbbell(ax,yi,l,r,'#B8B8B8',ns.INK,6.5)
    ax.set_yticks(y); ax.set_yticklabels([m[0] for m in metrics],fontsize=7.2); ax.set_ylim(-.75,len(metrics)-.25)
    maxx=max(d1.max(),d10.max()); ax.set_xlim(-.04*maxx,1.12*maxx); ax.set_xlabel('Displacement from text-only (1 − similarity)')
    ax.spines['left'].set_visible(False); ax.tick_params(left=False)
    ax.plot([],[],'o',color='#B8B8B8',ms=6,label='λ = 0.10'); ax.plot([],[],'o',color=ns.INK,ms=6,label='λ = 1.0'); ax.legend(loc='lower left',bbox_to_anchor=(.10,1.02),ncol=2,fontsize=6.8)

def main():
    d,metrics,a,b=source.load(); ns.use(); fig=plt.figure(figsize=(10.4,7.35),dpi=200)
    ns.fig_title(fig,2,'Transfer depends on supervision strength and model displacement',size=13.5)
    draw_dose(fig,d); draw_traj(fig,d); draw_displacement(fig,metrics,a,b)
    ns.panel_letter(fig,.016,.948,'a',13); ns.panel_title(fig,.042,.943,'Dose–response of transfer performance',9.5)
    ns.panel_letter(fig,.016,.520,'b',13); ns.panel_title(fig,.042,.515,'Transfer–utility trajectory in representational space',9.5)
    ns.panel_letter(fig,.505,.520,'c',13); ns.panel_title(fig,.531,.515,'Model displacement changes with supervision strength',9.5)
    paths=ns.save3(fig,OUT,'figure2'); (OUT/'source_manifest.json').write_text(json.dumps({'status':'ok','scientific_values_changed':False,'source':'frozen dose and model-space outputs via build_nmi_figure3_redesign_v1.py','outputs':[str(p.relative_to(ROOT)) for p in paths]},indent=2)+'\n')
    print(json.dumps({'status':'ok','output_dir':str(OUT.relative_to(ROOT))},indent=2))
if __name__=='__main__': main()

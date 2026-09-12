#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import build_nmi_figure5_redesign_v1_1 as compat
import nmi_mockup_style_v3 as ns

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/nmi_figure4_mockup_v3/latest'

def draw_surfaces(fig,d,surf,norm,cmap,source):
    specs=[('Left lateral','lh','lateral'),('Left medial','lh','medial'),('Right lateral','rh','lateral'),('Right medial','rh','medial')]
    for i,(lab,hemi,view) in enumerate(specs):
        ax=fig.add_axes([.035+i*.215,.535,.205,.34],projection='3d'); source.draw_surface(ax,surf[hemi],hemi,view,norm,cmap,None); fig.text(.137+i*.215,.875,lab,ha='center',fontsize=8.5)
    cax=fig.add_axes([.915,.635,.012,.175]); sm=ScalarMappable(norm=norm,cmap=cmap); sm.set_array([]); cb=fig.colorbar(sm,cax=cax); cb.outline.set_linewidth(.5); cb.ax.tick_params(labelsize=7)
    fig.text(.921,.825,'mean ΔRSA\n(×10$^{-3}$)',fontsize=7.2,ha='center')

def draw_systems(fig,d):
    ax=fig.add_axes([.075,.105,.230,.335]); ns.zero_line(ax); m=d['lang_part'][['functional_language_mean_delta','left_sensorimotor_mean_delta','left_visual_mean_delta']].to_numpy(float)*1e3; names=['Language','Sensorimotor','Visual']
    for i in range(3):
        vals=m[:,i]; ns.half_violin(ax,i-.06,vals,ns.ORANGE_FILL,side='left',width=.26,bw=.5,alpha=.9); ns.observations(ax,i+.17,vals,ns.ORANGE,seed=i,width=.07,size=15)
    for row in m: ax.plot([.17,1.17,2.17],row,color='#CFCFCF',lw=.5,zorder=2)
    for i in range(3):
        vals=m[:,i]; mean=vals.mean(); se=vals.std(ddof=1)/np.sqrt(len(vals)); ns.point_with_ci(ax,i+.02,mean,mean-1.96*se,mean+1.96*se,ns.INK,ms=6)
    ymin=min(0,m.min()); ymax=m.max(); pad=.16*(ymax-ymin); ax.set_xlim(-.55,2.6); ax.set_ylim(ymin-pad,ymax+pad); ax.set_xticks(range(3)); ax.set_xticklabels(names); ax.set_ylabel('Mean participant ΔRSA (×10$^{-3}$)')
    ax.scatter([],[],s=15,c=ns.ORANGE,label='Participant'); ax.scatter([],[],s=22,c=ns.INK,label='Mean ± approx. 95% CI'); ax.plot([],[],color='#CFCFCF',lw=.8,label='Within-participant'); ax.legend(loc='upper center',bbox_to_anchor=(.5,-.145),ncol=3,fontsize=6.4)

def draw_null(fig,d):
    ax=fig.add_axes([.395,.105,.230,.335]); vals=d['null']['language_beta'].to_numpy(float)*1e3; sn=d['final_summary']['spatial_autocorrelation_null']; obs=float(sn['observed_reliability_adjusted_language_beta'])*1e3
    ax.hist(vals,bins=48,color='#C4C4C4',edgecolor='white',lw=.3); ax.axvline(0,color='#888',lw=.9,ls=(0,(4,3))); ax.axvline(obs,color='#E8431F',lw=2)
    ax.text(0,1.02,'Null mean',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.4,color='#777'); ax.text(obs,.985,f"Observed\np = {float(sn['two_sided_spatial_surrogate_p']):.5f}",transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=8,color='#E8431F',fontweight='bold')
    ax.set_xlabel('Spatial-surrogate language coefficient (×10$^{-3}$)'); ax.set_ylabel('Count')

def draw_specificity(fig,d):
    ax=fig.add_axes([.715,.105,.175,.335]); avg=d['shuffled'].groupby('subject',as_index=False)[['genuine_specificity','shuffled_specificity']].mean(); shuf=avg['shuffled_specificity'].to_numpy(float)*1e3; gen=avg['genuine_specificity'].to_numpy(float)*1e3; n=len(avg); order=np.argsort(shuf); shuf=shuf[order]; gen=gen[order]
    x=np.arange(n)*.62
    for k in range(n): ax.annotate('',xy=(x[k]+.45,gen[k]),xytext=(x[k],shuf[k]),arrowprops=dict(arrowstyle='-|>',lw=1,color=ns.ORANGE,mutation_scale=7,shrinkA=3,shrinkB=3))
    ax.scatter(x,shuf,s=24,facecolors='white',edgecolors='#999',lw=.9,zorder=4); ax.scatter(x+.45,gen,s=26,c=ns.ORANGE,zorder=4)
    right=x[-1]+.45; ax.axvline(right+1.5,color=ns.RULE,lw=.8,ls=(0,(3,3))); diff=gen-shuf; xd=right+3.1; ns.half_violin(ax,xd+.35,diff,ns.ORANGE_FILL,width=1.7,bw=.55); ns.observations(ax,xd-.30,diff,ns.ORANGE,seed=3,width=.32,size=13)
    mean=diff.mean(); se=diff.std(ddof=1)/np.sqrt(n); ns.point_with_ci(ax,xd-.05,mean,mean-1.96*se,mean+1.96*se,ns.INK,ms=5.5)
    ymin=min(0,shuf.min(),gen.min(),diff.min()); ymax=max(shuf.max(),gen.max(),diff.max()); pad=.12*(ymax-ymin); ax.set_xlim(-1.2,xd+2.6); ax.set_ylim(ymin-pad,ymax+pad); ax.set_xticks([]); ax.set_ylabel('Language specificity (×10$^{-3}$)'); ax.spines['bottom'].set_visible(False)
    ax.text(right/2,ymin-pad*.65,'Participants',ha='center',fontsize=8); ax.text(xd,ymin-pad*.65,'Difference\n(genuine − shuffled)',ha='center',va='top',fontsize=7.2)
    ax.scatter([],[],s=24,facecolors='white',edgecolors='#999',label='Shuffled neural'); ax.scatter([],[],s=26,c=ns.ORANGE,label='Genuine neural'); ax.plot([],[],color=ns.ORANGE,lw=1,marker='>',ms=3,label='Participant change'); ax.legend(loc='upper center',bbox_to_anchor=(.5,-.155),ncol=3,fontsize=6.2)

def main():
    source=compat.load_builder(); original=source.read_json
    def read_json_legacy(path):
        payload=original(path)
        if isinstance(payload,dict) and 'status' not in payload:
            payload=dict(payload); payload['status']='ok'
        return payload
    source.read_json=read_json_legacy
    d=source.load_data(); fs=source.ensure_fsaverage(); surf=source.load_surface_data(fs,d['dk']); norm,cmap,_=source.surface_norm(d['dk'])
    ns.use(); fig=plt.figure(figsize=(10.4,7.35),dpi=200); ns.fig_title(fig,4,'fMRI transfer is cortex-wide with modest language-associated enrichment',size=13.5)
    draw_surfaces(fig,d,surf,norm,cmap,source); draw_systems(fig,d); draw_null(fig,d); draw_specificity(fig,d)
    ns.panel_letter(fig,.016,.935,'a',13); ns.panel_title(fig,.042,.930,'Cortical distribution of fMRI transfer (unthresholded)',9.5)
    for x,l,t,s in [(.016,'b','Participant-level transfer by system','Higher transfer in language system, modest enrichment overall.'),(.336,'c','Spatial-null test for language enrichment','Observed language enrichment exceeds spatial null.'),(.656,'d','Neural regional specificity per participant','Higher for genuine neural data than shuffled.')]:
        ns.panel_letter(fig,x,.500,l,13); ns.panel_title(fig,x+.026,.495,t,9.5); fig.text(x+.026,.466,s,fontsize=7.2,color='#6E6E6E')
    paths=ns.save3(fig,OUT,'figure4'); (OUT/'source_manifest.json').write_text(json.dumps({'status':'ok','scientific_values_changed':False,'source':'frozen regional/spatial outputs via build_nmi_figure5_redesign_v1.py','outputs':[str(p.relative_to(ROOT)) for p in paths]},indent=2)+'\n')
    print(json.dumps({'status':'ok','output_dir':str(OUT.relative_to(ROOT))},indent=2))
if __name__=='__main__': main()

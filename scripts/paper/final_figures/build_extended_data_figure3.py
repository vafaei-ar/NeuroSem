#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
import style as ns
import build_figure4 as regional
from common import OUT,save_three,write_manifest
LANGUAGE_ORDER=regional.LANGUAGE_ORDER
def language_forest(fig,d):
    ax=fig.add_axes([.095,.555,.350,.285]);lang=d['lang_regions'].copy();lang['ord']=lang['region_name'].map({v:i for i,v in enumerate(LANGUAGE_ORDER)});lang=lang.sort_values('ord');y=np.arange(len(lang))[::-1];val=lang['delta_mean'].to_numpy(float)*1e3;lo=lang['delta_bootstrap_ci_low'].to_numpy(float)*1e3;hi=lang['delta_bootstrap_ci_high'].to_numpy(float)*1e3;ax.axvline(0,color=ns.RULE,lw=.9,ls=(0,(4,3)));ax.hlines(y,lo,hi,color=ns.ORANGE_LIGHT,lw=2.1,zorder=1);ax.scatter(val,y,s=42,c=ns.ORANGE,edgecolors='white',linewidth=.6,zorder=3);ax.set_yticks(y);ax.set_yticklabels(lang['region_name']);ax.set_xlabel('Mean participant DeltaRSA (x10^-3)');ax.set_ylim(-.7,len(y)-.3);ax.text(.98,.94,'all six prespecified parcel means > 0',transform=ax.transAxes,ha='right',va='top',fontsize=7,color=ns.ORANGE,fontweight='bold');ns.panel_letter(fig,.018,.905,'a',13);ns.panel_title(fig,.048,.899,'Prespecified functional language parcels',9.5)
def dk_distribution(fig,d):
    ax=fig.add_axes([.565,.555,.345,.285]);dk=d['dk'].copy()
    for i,(hemi,color,fill) in enumerate([('L',ns.ORANGE,ns.ORANGE_FILL),('R',ns.GREY,'#E3E3E3')]):vals=dk.loc[dk['hemisphere']==hemi,'delta_mean'].to_numpy(float)*1e3;ns.half_violin(ax,i-.06,vals,fill,side='left',width=.25,bw=.40,alpha=.75);ns.observations(ax,i+.15,vals,color,seed=20+i,width=.07,size=14,alpha=.80);mean=float(vals.mean());ax.plot([i-.12,i+.28],[mean,mean],color=ns.INK,lw=1.2,zorder=4);ax.plot(i+.05,mean,'o',color=ns.INK,ms=5.5,mec='white',mew=.5,zorder=5)
    ns.zero_line(ax);ax.set_xticks([0,1]);ax.set_xticklabels(['Left','Right']);ax.tick_params(axis='x',length=0);ax.set_ylabel('DK parcel mean DeltaRSA (x10^-3)');vals=dk['delta_mean'].to_numpy(float)*1e3;pad=.12*np.ptp(vals);ax.set_ylim(min(0,vals.min())-pad,vals.max()+pad);ax.text(.98,.94,f"{int(np.sum(vals>0))}/68 parcel means > 0\nunthresholded characterization",transform=ax.transAxes,ha='right',va='top',fontsize=7,color=ns.ORANGE,linespacing=1.25);ns.panel_letter(fig,.505,.905,'b',13);ns.panel_title(fig,.535,.899,'Complete bilateral DK68 regional distribution',9.5)
def surfaces(fig,surf,norm,cmap):
    specs=[('Left lateral','lh','lateral'),('Left medial','lh','medial'),('Right medial','rh','medial'),('Right lateral','rh','lateral')]
    for i,(label,hemi,view) in enumerate(specs):ax=fig.add_axes([.050+i*.215,.090,.195,.330],projection='3d');regional.draw_surface(ax,surf[hemi],hemi,view,norm,cmap,None);fig.text(.147+i*.215,.408,label,ha='center',fontsize=8.2)
    cax=fig.add_axes([.920,.175,.012,.145]);sm=ScalarMappable(norm=norm,cmap=cmap);sm.set_array([]);cb=fig.colorbar(sm,cax=cax);cb.outline.set_linewidth(.5);cb.ax.tick_params(labelsize=7);fig.text(.926,.337,'mean DeltaRSA\n(x10^-3)',fontsize=7,ha='center');ns.panel_letter(fig,.018,.475,'c',13);ns.panel_title(fig,.048,.469,'Same complete unthresholded DK68 phenotype on fsaverage cortex',9.5)
def main()->int:
    d=regional.load_data();fs=regional.ensure_fsaverage();surf=regional.load_surface_data(fs,d['dk']);norm,cmap=regional.surface_norm(d['dk']);ns.use();fig=plt.figure(figsize=(10.4,7.35),dpi=200);ns.ed_title(fig,3,'Complete regional fMRI characterization');language_forest(fig,d);dk_distribution(fig,d);surfaces(fig,surf,norm,cmap);paths=save_three(fig,'extended_data_figure3');plt.close(fig);inputs=list(regional.INPUTS)+regional.atlas_files(fs);write_manifest('extended_data_figure3',Path(__file__),inputs,paths,{'role':'complete unthresholded regional fMRI characterization','guardrail':'No parcel is selected, thresholded, or tested for inclusion based on its displayed effect.'});print(f"wrote {OUT / 'extended_data_figure3.png'}");return 0
if __name__=='__main__':raise SystemExit(main())

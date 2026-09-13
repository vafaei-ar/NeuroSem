#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors
from matplotlib.cm import ScalarMappable
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
import style as ns
from common import OUT,legacy_status_ok,save_three,write_manifest
LANGSPEC=ROOT/'outputs/smn4lang_fmri_language_specificity_v1/latest'; SPATIAL=ROOT/'outputs/smn4lang_fmri_spatial_extensions_v1/latest'; FINAL=ROOT/'outputs/nmi_final_spatial_validation_v1/latest'; REGIONAL=ROOT/'outputs/smn4lang_regional_fmri_e5_transfer_v1/latest'; ATLAS_CACHE=ROOT/'outputs/nmi_visual_atlas_cache_v1'; LANGUAGE_ORDER=['IFGorb','IFG','MFG','AntTemp','PostTemp','AngG']; INPUTS=[LANGSPEC/'summary.json',LANGSPEC/'participant_contrasts.csv',SPATIAL/'summary.json',SPATIAL/'participant_spatial_extensions.csv',FINAL/'summary.json',FINAL/'spatial_surrogate_null.csv',FINAL/'shuffled_regional_participant_results.csv',REGIONAL/'summary.json',REGIONAL/'region_summary.csv']
def rj(p):return json.loads(p.read_text(encoding='utf-8'))
def norm_name(name):
    s=name.decode('utf-8') if isinstance(name,(bytes,bytearray)) else str(name); s=s.lower().strip()
    for prefix in ('ctx-lh-','ctx-rh-','lh_','rh_','left_','right_'):
        if s.startswith(prefix):s=s[len(prefix):]
    return re.sub(r'[^a-z0-9]','',s)
def atlas_files(fs):return [fs/'surf/lh.inflated',fs/'surf/rh.inflated',fs/'surf/lh.sulc',fs/'surf/rh.sulc',fs/'label/lh.aparc.annot',fs/'label/rh.aparc.annot']
def ensure_fsaverage():
    fs=ATLAS_CACHE/'fsaverage'; required=atlas_files(fs)
    if all(p.is_file() for p in required):return fs
    ATLAS_CACHE.mkdir(parents=True,exist_ok=True)
    try:import mne
    except Exception as exc:raise RuntimeError('mne is required to fetch the standard fsaverage rendering scaffold') from exc
    fetched=Path(mne.datasets.fetch_fsaverage(subjects_dir=str(ATLAS_CACHE),verbose=False)); fs=fetched if fetched.name=='fsaverage' else ATLAS_CACHE/'fsaverage'; missing=[str(p) for p in atlas_files(fs) if not p.is_file()]
    if missing:raise FileNotFoundError('fsaverage fetch incomplete: '+', '.join(missing))
    return fs
def load_surface_data(fs,dk):
    try:from nibabel.freesurfer.io import read_annot,read_geometry,read_morph_data
    except Exception as exc:raise RuntimeError('nibabel FreeSurfer readers are required for cortical rendering') from exc
    out={}
    for hemi_code,hemi_label in [('lh','L'),('rh','R')]:
        coords,faces=read_geometry(str(fs/f'surf/{hemi_code}.inflated')); sulc=read_morph_data(str(fs/f'surf/{hemi_code}.sulc')).astype(float); vertex_labels,_ctab,names=read_annot(str(fs/f'label/{hemi_code}.aparc.annot'),orig_ids=False); lookup={norm_name(r['region_name']):float(r['delta_mean'])*1e3 for _,r in dk.loc[dk['hemisphere']==hemi_label].iterrows()}; values=np.full(len(vertex_labels),np.nan,float); matched=set()
        for annot_idx,raw_name in enumerate(names):
            key=norm_name(raw_name)
            if key in lookup:values[vertex_labels==annot_idx]=lookup[key];matched.add(key)
        missing=sorted(set(lookup)-matched)
        if missing:raise RuntimeError(f'{hemi_label}: DK parcel names not matched to fsaverage aparc: '+', '.join(missing))
        out[hemi_code]={'coords':coords,'faces':faces,'sulc':sulc,'values':values}
    return out
def surface_norm(dk):
    vals=dk['delta_mean'].to_numpy(float)*1e3
    if np.nanmin(vals)<0<np.nanmax(vals):
        vmax=float(np.nanmax(np.abs(vals)));return colors.TwoSlopeNorm(vmin=-vmax,vcenter=0,vmax=vmax),plt.get_cmap('RdBu_r')
    return colors.Normalize(vmin=0,vmax=float(np.nanmax(vals))*1.02),plt.get_cmap('Oranges')
def draw_surface(ax,surf,hemi,view,norm,cmap,label=None):
    coords=surf['coords'];faces=surf['faces'];values=surf['values'];sulc=surf['sulc'];mesh=ax.plot_trisurf(coords[:,0],coords[:,1],coords[:,2],triangles=faces,linewidth=0,antialiased=False,shade=False);vv=values[faces];count=np.isfinite(vv).sum(axis=1);total=np.nansum(vv,axis=1);face_vals=np.divide(total,count,out=np.full(len(faces),np.nan,float),where=count>0);known=np.isfinite(face_vals);rgba=np.empty((len(faces),4),float);rgba[:]=np.array([.86,.86,.86,1.0]);rgba[known]=cmap(norm(face_vals[known])) if np.any(known) else rgba[known];face_sulc=np.mean(sulc[faces],axis=1)
    if np.nanmax(face_sulc)>np.nanmin(face_sulc):
        s=(face_sulc-np.nanmin(face_sulc))/(np.nanmax(face_sulc)-np.nanmin(face_sulc));grey=.72+.18*s;rgba[~known,:3]=grey[~known,None]
    mesh.set_facecolors(rgba);azim=180 if (hemi=='lh' and view=='lateral') or (hemi=='rh' and view=='medial') else 0;ax.view_init(elev=5,azim=azim);ax.set_axis_off();ax.set_box_aspect(tuple(np.ptp(coords,axis=0)))
    if label:ax.text2D(.5,.02,label,transform=ax.transAxes,ha='center',va='bottom',fontsize=5.6,color=ns.GREY)
def load_data():
    missing=[p for p in INPUTS if not p.exists()]
    if missing:raise FileNotFoundError('Missing frozen Figure 4 source(s): '+', '.join(str(p) for p in missing))
    lang_summary=rj(LANGSPEC/'summary.json');spatial_summary=rj(SPATIAL/'summary.json');final_summary=rj(FINAL/'summary.json');regional_summary=rj(REGIONAL/'summary.json')
    if not all(legacy_status_ok(x) for x in [lang_summary,spatial_summary,final_summary,regional_summary]):raise RuntimeError('One or more frozen regional source analyses are not status=ok')
    lang_part=pd.read_csv(LANGSPEC/'participant_contrasts.csv');spatial_part=pd.read_csv(SPATIAL/'participant_spatial_extensions.csv');null_df=pd.read_csv(FINAL/'spatial_surrogate_null.csv');shuffled=pd.read_csv(FINAL/'shuffled_regional_participant_results.csv');regions=pd.read_csv(REGIONAL/'region_summary.csv');dk=regions.loc[regions['family']=='dk68'].copy();lang_regions=regions.loc[regions['family']=='language'].copy()
    if len(lang_part)!=12 or len(spatial_part)!=12:raise RuntimeError('Expected 12 SMN4Lang participants in regional source tables')
    if len(null_df)!=10000:raise RuntimeError('Expected 10,000 spatial-surrogate rows')
    if len(dk)!=68 or set(dk['hemisphere'])!={'L','R'}:raise RuntimeError('Expected complete bilateral DK68 regional summary')
    if len(lang_regions)!=6 or set(lang_regions['region_name'])!=set(LANGUAGE_ORDER):raise RuntimeError('Expected frozen six-region functional language family')
    return {'lang_summary':lang_summary,'spatial_summary':spatial_summary,'final_summary':final_summary,'lang_part':lang_part,'spatial_part':spatial_part,'null':null_df,'shuffled':shuffled,'regions':regions,'dk':dk,'lang_regions':lang_regions}
def draw_surfaces(fig,d,surf,norm,cmap):
    specs=[('Left lateral','lh','lateral'),('Left medial','lh','medial'),('Right lateral','rh','lateral'),('Right medial','rh','medial')]
    for i,(lab,hemi,view) in enumerate(specs):ax=fig.add_axes([.035+i*.215,.535,.205,.34],projection='3d');draw_surface(ax,surf[hemi],hemi,view,norm,cmap,None);fig.text(.137+i*.215,.875,lab,ha='center',fontsize=8.5)
    cax=fig.add_axes([.915,.635,.012,.175]);sm=ScalarMappable(norm=norm,cmap=cmap);sm.set_array([]);cb=fig.colorbar(sm,cax=cax);cb.outline.set_linewidth(.5);cb.ax.tick_params(labelsize=7);fig.text(.921,.825,'mean ΔRSA\n(×10$^{-3}$)',fontsize=7.2,ha='center')
def draw_systems(fig,d):
    ax=fig.add_axes([.075,.105,.230,.335]);ns.zero_line(ax);m=d['lang_part'][['functional_language_mean_delta','left_sensorimotor_mean_delta','left_visual_mean_delta']].to_numpy(float)*1e3;names=['Language','Sensorimotor','Visual']
    for i in range(3):vals=m[:,i];ns.half_violin(ax,i-.06,vals,ns.ORANGE_FILL,side='left',width=.26,bw=.5,alpha=.9);ns.observations(ax,i+.17,vals,ns.ORANGE,seed=i,width=.07,size=15)
    for row in m:ax.plot([.17,1.17,2.17],row,color='#CFCFCF',lw=.5,zorder=2)
    for i in range(3):vals=m[:,i];mean=vals.mean();se=vals.std(ddof=1)/np.sqrt(len(vals));ns.point_with_ci(ax,i+.02,mean,mean-1.96*se,mean+1.96*se,ns.INK,ms=6)
    ymin=min(0,m.min());ymax=m.max();pad=.16*(ymax-ymin);ax.set_xlim(-.55,2.6);ax.set_ylim(ymin-pad,ymax+pad);ax.set_xticks(range(3));ax.set_xticklabels(names);ax.set_ylabel('Mean participant ΔRSA (×10$^{-3}$)');ax.scatter([],[],s=15,c=ns.ORANGE,label='Participant');ax.scatter([],[],s=22,c=ns.INK,label='Mean ± approx. 95% CI');ax.plot([],[],color='#CFCFCF',lw=.8,label='Within-participant');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.145),ncol=3,fontsize=6.4)
def draw_null(fig,d):
    ax=fig.add_axes([.395,.105,.230,.335]);vals=d['null']['language_beta'].to_numpy(float)*1e3;sn=d['final_summary']['spatial_autocorrelation_null'];obs=float(sn['observed_reliability_adjusted_language_beta'])*1e3;ax.hist(vals,bins=48,color='#C4C4C4',edgecolor='white',lw=.3);ax.axvline(0,color='#888',lw=.9,ls=(0,(4,3)));ax.axvline(obs,color='#E8431F',lw=2);ax.text(0,1.02,'Null mean',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.4,color='#777');ax.text(obs,.985,f"Observed\np = {float(sn['two_sided_spatial_surrogate_p']):.5f}",transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=8,color='#E8431F',fontweight='bold');ax.set_xlabel('Spatial-surrogate language coefficient (×10$^{-3}$)');ax.set_ylabel('Count')
def draw_specificity(fig,d):
    ax=fig.add_axes([.715,.105,.175,.335]);avg=d['shuffled'].groupby('subject',as_index=False)[['genuine_specificity','shuffled_specificity']].mean();shuf=avg['shuffled_specificity'].to_numpy(float)*1e3;gen=avg['genuine_specificity'].to_numpy(float)*1e3;n=len(avg);order=np.argsort(shuf);shuf=shuf[order];gen=gen[order];x=np.arange(n)*.62
    for k in range(n):ax.annotate('',xy=(x[k]+.45,gen[k]),xytext=(x[k],shuf[k]),arrowprops=dict(arrowstyle='-|>',lw=1,color=ns.ORANGE,mutation_scale=7,shrinkA=3,shrinkB=3))
    ax.scatter(x,shuf,s=24,facecolors='white',edgecolors='#999',lw=.9,zorder=4);ax.scatter(x+.45,gen,s=26,c=ns.ORANGE,zorder=4);right=x[-1]+.45;ax.axvline(right+1.5,color=ns.RULE,lw=.8,ls=(0,(3,3)));diff=gen-shuf;xd=right+3.1;ns.half_violin(ax,xd+.35,diff,ns.ORANGE_FILL,width=1.7,bw=.55);ns.observations(ax,xd-.30,diff,ns.ORANGE,seed=3,width=.32,size=13);mean=diff.mean();se=diff.std(ddof=1)/np.sqrt(n);ns.point_with_ci(ax,xd-.05,mean,mean-1.96*se,mean+1.96*se,ns.INK,ms=5.5);ymin=min(0,shuf.min(),gen.min(),diff.min());ymax=max(shuf.max(),gen.max(),diff.max());pad=.12*(ymax-ymin);ax.set_xlim(-1.2,xd+2.6);ax.set_ylim(ymin-pad,ymax+pad);ax.set_xticks([]);ax.set_ylabel('Language specificity (×10$^{-3}$)');ax.spines['bottom'].set_visible(False);ax.text(right/2,ymin-pad*.65,'Participants',ha='center',fontsize=8);ax.text(xd,ymin-pad*.65,'Difference\n(genuine − shuffled)',ha='center',va='top',fontsize=7.2);ax.scatter([],[],s=24,facecolors='white',edgecolors='#999',label='Shuffled neural');ax.scatter([],[],s=26,c=ns.ORANGE,label='Genuine neural');ax.plot([],[],color=ns.ORANGE,lw=1,marker='>',ms=3,label='Participant change');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.155),ncol=3,fontsize=6.2)
def main()->int:
    d=load_data();fs=ensure_fsaverage();surf=load_surface_data(fs,d['dk']);norm,cmap=surface_norm(d['dk']);ns.use();fig=plt.figure(figsize=(10.4,7.35),dpi=200);ns.fig_title(fig,4,'fMRI transfer is cortex-wide with modest language-associated enrichment',size=13.5);draw_surfaces(fig,d,surf,norm,cmap);draw_systems(fig,d);draw_null(fig,d);draw_specificity(fig,d);ns.panel_letter(fig,.016,.935,'a',13);ns.panel_title(fig,.042,.930,'Cortical distribution of fMRI transfer (unthresholded)',9.5)
    for x,l,t,s in [(.016,'b','Participant-level transfer by system','Higher transfer in language system, modest enrichment overall.'),(.336,'c','Spatial-null test for language enrichment','Observed language enrichment exceeds spatial null.'),(.656,'d','Neural regional specificity per participant','Higher for genuine neural data than shuffled.')]:ns.panel_letter(fig,x,.500,l,13);ns.panel_title(fig,x+.026,.495,t,9.5);fig.text(x+.026,.466,s,fontsize=7.2,color='#6E6E6E')
    paths=save_three(fig,'figure4');plt.close(fig);write_manifest('figure4',Path(__file__),INPUTS+atlas_files(fs),paths,{'role':'cortex-wide fMRI transfer, language-associated enrichment, spatial null, and genuine-target specificity','atlas_role':'FreeSurfer fsaverage Desikan-Killiany geometry/labels only','guardrail':'Presentation only; no ROI selection, thresholding, model fitting, neural analysis, or new inference.'});print(f"wrote {OUT / 'figure4.png'}");return 0
if __name__=='__main__':raise SystemExit(main())

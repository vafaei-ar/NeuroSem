#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import build_nmi_figure4_redesign_v1 as source
import nmi_mockup_style_v3 as ns

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/nmi_figure3_mockup_v3/latest'
MODELS=[('e5_large','E5-large'),('e5_base','E5-base'),('multilingual_mpnet','mMPNet'),('multilingual_minilm','mMiniLM'),('xlmr_base','XLM-R'),('mbert','mBERT')]
METRICS=[('Item cosine','corresponding_item_cosine_similarity_mean'),('RDM Pearson','pairwise_cosine_distance_pearson'),('RDM Spearman','pairwise_cosine_distance_spearman'),('Centered CKA','linear_centered_cka'),('k=10 Jaccard','mean_knn_jaccard_overlap')]

def panel_a(fig,signals):
    for row,(key,title,powr) in enumerate([('zuco','ZuCo EEG (target)',-3),('fmri','SMN4Lang fMRI (target)',-3)]):
        ax=fig.add_axes([.085,.670-row*.205,.365,.145]); ns.zero_line(ax)
        c=[ns.BLUE,ns.ORANGE,ns.GREY]; cats=['Shuffled','Genuine','MPNet']; scale=10**(-powr)
        for i,(cat,col) in enumerate(zip(cats,c)):
            vals=np.asarray(signals[key][cat.lower()])*scale
            ns.observations(ax,i,vals,ns.BLUE_LIGHT if cat=='Shuffled' else ns.ORANGE_LIGHT if cat=='Genuine' else ns.GREY_LIGHT,seed=row*10+i,width=.10,size=16)
            ax.plot([i-.16,i+.16],[vals.mean(),vals.mean()],color=col,lw=1.5,zorder=4); ax.plot(i,vals.mean(),'o',color=col,ms=7,mec='white',mew=.6,zorder=5)
        allv=np.concatenate([np.asarray(signals[key][x])*scale for x in ['shuffled','genuine','mpnet']]); pad=.18*np.ptp(allv)
        ax.set_xlim(-.55,2.55); ax.set_ylim(allv.min()-pad,allv.max()+pad); ax.set_xticks(range(3)); ax.set_xticklabels(cats); ax.set_ylabel('Transfer vs text\n(×10$^{-3}$)'); ax.set_title(title,loc='left',pad=8,fontsize=9.5)

def panel_b(fig,rows):
    y=np.arange(len(MODELS))[::-1]
    for col,(direction,title,color,strip,scale,label) in enumerate([
        ('eeg_to_fmri','ChineseEEG → fMRI',ns.BLUE,ns.BLUE_STRIP,1e3,'Mean ΔRSA (×10$^{-3}$)'),
        ('fmri_to_eeg','fMRI → ZuCo',ns.ORANGE,ns.ORANGE_STRIP,1e4,'Mean ΔRSA (×10$^{-4}$)')]):
        ax=fig.add_axes([.585+col*.205,.545,.185,.285]); ns.zero_line(ax,'v')
        for k,(mk,mlab) in enumerate(MODELS):
            rr=sorted([r for r in rows if r['model_key']==mk and r['direction']==direction],key=lambda r:int(r['seed']))
            vals=np.array([float(r['external_mean_delta']) for r in rr])*scale; yi=y[k]
            ns.observations(ax,yi,vals,ns.BLUE_LIGHT if col==0 else ns.ORANGE_LIGHT,vertical=False,seed=col*20+k,width=.14,size=14)
            ax.plot([vals.min(),vals.max()],[yi,yi],color=ns.GREY_LIGHT,lw=1.0,zorder=2); ax.plot(vals.mean(),yi,'o',ms=7,color=color,mec='white',mew=.6,zorder=5)
        ax.set_ylim(-.7,len(MODELS)-.3); ax.set_yticks(y); ax.set_yticklabels([m[1] for m in MODELS] if col==0 else []); ax.set_xlabel(label); ns.facet_strip(ax,title,strip,9)
        if col: ax.spines['left'].set_visible(False); ax.tick_params(left=False)

def panel_c(fig,space_rows):
    ax=fig.add_axes([.205,.075,.590,.255]); y=np.arange(len(METRICS))[::-1]; ns.zero_line(ax,'v')
    neural=[]; mpnet=[]
    for _,k in METRICS:
        g=np.array([float(r[k]) for r in space_rows if r['comparison']=='genuine_neural_vs_text_only'])
        m=np.array([float(r[k]) for r in space_rows if r['comparison']=='mpnet_surrogate_vs_text_only'])
        neural.append(1-g.mean()); mpnet.append(1-m.mean())
    neural=np.array(neural); mpnet=np.array(mpnet)
    for yi,nv,mv in zip(y,neural,mpnet): ns.dumbbell(ax,yi,nv,mv,ns.BLUE,ns.ORANGE,7)
    ax.set_yticks(y); ax.set_yticklabels([m[0] for m in METRICS]); ax.set_ylim(-.8,len(METRICS)-.2); maxx=max(neural.max(),mpnet.max()); ax.set_xlim(-.06*maxx,1.12*maxx); ax.set_xlabel('Representation-space displacement from text-only (1 − similarity)'); ax.spines['left'].set_visible(False); ax.tick_params(left=False)
    ax.text(1.02,1.06,'Genuine',transform=ax.transAxes,color=ns.BLUE,ha='center',fontsize=9); ax.text(1.12,1.06,'MPNet',transform=ax.transAxes,color=ns.ORANGE,ha='center',fontsize=9)
    for yi,nv,mv in zip(y,neural,mpnet):
        ax.text(1.02,yi,f'{nv:.3f}',transform=ax.get_yaxis_transform(),ha='center',va='center',fontsize=8,color=ns.BLUE)
        ax.text(1.12,yi,f'{mv:.3f}',transform=ax.get_yaxis_transform(),ha='center',va='center',fontsize=8,color=ns.ORANGE)

def main():
    rows=source.rc(source.MODELS); signals=source.signal_values(); space_rows=source.rc(source.MP_SPACE)
    ns.use(); fig=plt.figure(figsize=(10.4,7.35),dpi=200); ns.fig_title(fig,3,'Target structure and model architecture determine transfer',size=13.5)
    panel_a(fig,signals); panel_b(fig,rows); panel_c(fig,space_rows)
    ns.panel_letter(fig,.018,.925,'a'); ns.panel_title(fig,.048,.919,'Target-structure comparison')
    ns.panel_letter(fig,.492,.925,'b'); ns.panel_title(fig,.522,.919,'Backbone heterogeneity')
    ns.panel_letter(fig,.018,.400,'c'); ns.panel_title(fig,.048,.394,'Perturbation-magnitude caveat')
    fig.add_artist(plt.Line2D([.478,.478],[.435,.900],transform=fig.transFigure,color=ns.RULE,lw=.8)); fig.add_artist(plt.Line2D([.018,.975],[.415,.415],transform=fig.transFigure,color=ns.RULE,lw=.8))
    paths=ns.save3(fig,OUT,'figure3'); (OUT/'source_manifest.json').write_text(json.dumps({'status':'ok','scientific_values_changed':False,'source':'frozen model-family, target-structure and model-space outputs via build_nmi_figure4_redesign_v1.py','outputs':[str(p.relative_to(ROOT)) for p in paths]},indent=2)+'\n')
    print(json.dumps({'status':'ok','output_dir':str(OUT.relative_to(ROOT))},indent=2))
if __name__=='__main__': main()

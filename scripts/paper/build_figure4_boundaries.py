#!/usr/bin/env python3
from pathlib import Path
import argparse,csv,json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

OUTCOMES=[
 ('ZuCo 2.0','reliable: 17/17','positive: +0.001664\n17/17, P=7.63×10⁻⁶'),
 ('SMN4Lang fMRI','reliable: 12/12','positive: +0.0008525\n12/12, P=0.000244'),
 ('TMNRED','weakly reliable','null: +0.000020\nP=0.402'),
 ('Garnett Dream','reliable: 10/10','inconclusive: +0.0003266\n6/10, P=0.1016'),
 ('Directional inner speech','out-of-task','boundary: ≈−0.001786'),
]
SEM={'Base':[0.283464,0.283464],'Text':[0.308486,0.305020],'Neural':[0.308575,0.301607],'Shuffle':[0.307943,0.305266]}
DESIGN=[
 ('ZuCo 2.0','Independent','English','Natural reading','EEG','No','Yes'),
 ('SMN4Lang fMRI','Independent','Mandarin','Auditory narratives','fMRI','No','Yes'),
 ('TMNRED','Independent','Chinese','Natural reading','EEG','No','Yes'),
 ('Garnett Dream','Same cohort','Chinese','Natural reading','EEG','No','Yes'),
 ('Directional','Independent','English','Inner speech','EEG','No','Model tested'),
]

def read_csv(p):
    with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def label(ax,s):ax.text(-0.08,1.05,s,transform=ax.transAxes,fontsize=13,fontweight='bold',va='top')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--meg-table',type=Path,required=True);ap.add_argument('--out-prefix',type=Path,required=True);args=ap.parse_args()
    meg=read_csv(args.meg_table)
    fig=plt.figure(figsize=(14.2,8.8));gs=GridSpec(2,2,figure=fig,width_ratios=[1.08,1],height_ratios=[1,1],wspace=.30,hspace=.42)

    ax=fig.add_subplot(gs[0,0]);label(ax,'a');ax.axis('off');ax.set_title('External generalization is selective',loc='left',fontsize=11)
    ax.set_xlim(0,1);ax.set_ylim(0,1)
    ax.text(.02,.88,'Dataset',fontweight='bold',fontsize=9);ax.text(.36,.88,'Neural target',fontweight='bold',fontsize=9);ax.text(.66,.88,'Frozen model outcome',fontweight='bold',fontsize=9)
    ys=np.linspace(.76,.12,len(OUTCOMES))
    for y,(ds,rel,tr) in zip(ys,OUTCOMES):
        ax.text(.02,y,ds,fontsize=8.8,va='center');ax.text(.36,y,rel,fontsize=8.5,va='center');ax.text(.66,y,tr,fontsize=8.3,va='center')
        ax.plot([.02,.98],[y-.065,y-.065],linewidth=.45,color='0.85')
    ax.text(.02,.015,'Raw RSA deltas are reported descriptively and are not treated as a common cross-modality effect-size scale.',fontsize=8.1)

    ax=fig.add_subplot(gs[0,1]);label(ax,'b');
    meg=sorted(meg,key=lambda r:int(r['n_bins'])); x=np.arange(len(meg));means=np.array([float(r['mean_loo_spearman']) for r in meg]);lo=np.array([float(r['ci_low']) for r in meg]);hi=np.array([float(r['ci_high']) for r in meg])
    ax.errorbar(x,means,yerr=np.vstack([means-lo,hi-means]),fmt='o',capsize=4,linewidth=1.4);ax.axhline(0,linewidth=.8);ax.set_xticks(x,[r['n_bins'] for r in meg]);ax.set_xlabel('Normalized-time RMS bins per sensor type');ax.set_ylabel('LOO reliability');ax.set_title('SMN4Lang MEG reliability boundary',fontsize=11)
    for i,r in enumerate(meg):
        status='prospective primary' if int(r['n_bins'])==32 else 'post-confirmatory'
        ax.annotate(f"{r['n_positive']}/12 positive\n{status}",(i,hi[i]),xytext=(0,8),textcoords='offset points',ha='center',fontsize=7.5)
    ax.set_ylim(-0.01,0.039)
    ax.text(.03,.04,'No representation passed its reliability criterion.\nNo E5 model evaluation was performed.',transform=ax.transAxes,fontsize=8.5)

    ax=fig.add_subplot(gs[1,0]);label(ax,'c');ax.axis('off');ax.set_title('Independence and analysis design',loc='left',fontsize=11)
    cols=['Dataset','Cohort','Lang.','Task','Mod.','Tuning','Gate']
    cell=[[a,b,c,d,e,f,g] for a,b,c,d,e,f,g in DESIGN]
    tbl=ax.table(cellText=cell,colLabels=cols,cellLoc='center',colLoc='center',loc='center',colWidths=[.18,.16,.10,.18,.08,.10,.12])
    tbl.auto_set_font_size(False);tbl.set_fontsize(7.2);tbl.scale(1,1.75)
    for (r,c),cellobj in tbl.get_celld().items():
        if r==0: cellobj.set_text_props(fontweight='bold');cellobj.set_facecolor('0.94')
        if c in (0,1,3): cellobj._loc='left'
    ax.text(.01,.02,'No target dataset was used to retune λ, model, layer or checkpoint.',fontsize=8.2,transform=ax.transAxes)

    ax=fig.add_subplot(gs[1,1]);label(ax,'d');ax.set_title('Neural alignment is not generic semantic improvement',fontsize=11)
    names=list(SEM);xp=np.arange(len(names))
    for seed in range(2):ax.plot(xp,[SEM[n][seed] for n in names],marker='o',linewidth=1.2,label=f'Seed {seed+1}')
    ax.set_xticks(xp,names);ax.set_ylabel('Eight-task mean Spearman');ax.set_ylim(.278,.312);ax.legend(frameon=False,fontsize=8)
    ax.text(.04,.78,'Portable but selective relational constraint\n≠ universal language-model improvement',transform=ax.transAxes,fontsize=9,fontweight='bold')

    fig.suptitle('Figure 4 | Generalization map and boundary conditions',fontsize=15,fontweight='bold',y=.985)
    fig.text(.5,.012,'Positive cross-language EEG and cross-modal fMRI transfer coexist with null/inconclusive transfer and a model-blind MEG reliability boundary.',ha='center',fontsize=8.8)
    fig.subplots_adjust(left=.06,right=.985,bottom=.08,top=.91,wspace=.30,hspace=.42)
    args.out_prefix.parent.mkdir(parents=True,exist_ok=True);fig.savefig(str(args.out_prefix)+'.png',dpi=300,bbox_inches='tight');fig.savefig(str(args.out_prefix)+'.pdf',bbox_inches='tight')
    print(json.dumps({'status':'ok','out_prefix':str(args.out_prefix),'n_outcomes':len(OUTCOMES)},indent=2))
if __name__=='__main__':main()

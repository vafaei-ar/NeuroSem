#!/usr/bin/env python3
from pathlib import Path
import argparse, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

RUNS=np.array([0.0057,0.0034,0.0145,0.0045,0.0174,0.0056])
RUN07={
 'Base':[0.0319,0.0319],
 'Text-only':[0.0354,0.0341],
 'Neural-guided':[0.0371,0.0375],
 'Shuffled-neural':[0.0353,0.0338],
}
SEM={
 'Base':[0.283464,0.283464],
 'Text-only':[0.308486,0.305020],
 'Neural-guided':[0.308575,0.301607],
 'Shuffled-neural':[0.307943,0.305266],
}

def label(ax,s): ax.text(-0.08,1.05,s,transform=ax.transAxes,fontsize=13,fontweight='bold',va='top')
def box(ax,x,y,w,h,text,fs=9):
    ax.add_patch(plt.Rectangle((x,y),w,h,fill=False,linewidth=1.1)); ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,wrap=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-prefix',type=Path,required=True); args=ap.parse_args()
    fig=plt.figure(figsize=(12.8,8.1)); gs=GridSpec(2,3,figure=fig,width_ratios=[1.05,1.15,1.15],wspace=.48,hspace=.44)
    ax=fig.add_subplot(gs[0,0]); ax.axis('off'); ax.set_xlim(0,1); ax.set_ylim(0,1); label(ax,'a'); ax.set_title('Relational neural constraint',loc='left',fontsize=11)
    box(ax,.05,.68,.38,.18,'Natural-reading EEG\nreproducible neural RDM',8.6); box(ax,.57,.68,.38,.18,'Language model\npairwise geometry',8.6)
    ax.annotate('',xy=(.57,.77),xytext=(.43,.77),arrowprops=dict(arrowstyle='->',lw=1.2))
    box(ax,.18,.34,.64,.18,'Auxiliary neural relational objective\n+ matched text-learning objective',8.6); ax.annotate('',xy=(.50,.52),xytext=(.76,.68),arrowprops=dict(arrowstyle='->',lw=1.2))
    box(ax,.18,.06,.64,.16,'Sealed development test → frozen external transfer',8.6); ax.annotate('',xy=(.50,.22),xytext=(.50,.34),arrowprops=dict(arrowstyle='->',lw=1.2))

    ax=fig.add_subplot(gs[0,1]); label(ax,'b'); ax.set_title('Reliability-led EEG target',fontsize=11)
    vals=[.220,.121]; ax.bar([0,1],vals,width=.55); ax.set_xticks([0,1],['Raw LOO','Residual LOO']); ax.set_ylabel('Cross-participant reliability'); ax.set_ylim(0,.25)
    for i,v in enumerate(vals): ax.text(i,v+.007,f'{v:.3f}',ha='center',fontsize=9)
    ax.text(.04,.92,'Temporal-mean representation\nselected before model testing',transform=ax.transAxes,fontsize=8.7,va='top')

    ax=fig.add_subplot(gs[0,2]); label(ax,'c'); ax.set_title('Residual BERT correspondence',fontsize=11)
    x=np.arange(1,7); ax.plot(x,RUNS,marker='o',linewidth=1.2); ax.axhline(0,linewidth=.8); ax.set_xticks(x,[f'{i:02d}' for i in x]); ax.set_xlabel('Held-out narrative run'); ax.set_ylabel('Partial Spearman')
    ax.text(.04,.78,f'6/6 positive\nMean {RUNS.mean():.4f}\nExact one-sided P=0.015625',transform=ax.transAxes,fontsize=8.7)

    ax=fig.add_subplot(gs[1,0:2]); label(ax,'d'); ax.set_title('Sealed run-07 neural alignment',fontsize=11)
    names=list(RUN07); xp=np.arange(len(names));
    for seed in range(2): ax.plot(xp,[RUN07[n][seed] for n in names],marker='o',linewidth=1.1,label=f'Seed {seed+1}')
    ax.set_xticks(xp,names,rotation=0); ax.set_ylabel('Residual neural alignment'); ax.set_ylim(.0305,.0383); ax.legend(frameon=False,fontsize=8,loc='lower left')
    ax.text(.02,.92,'Neural-guided is highest in both sealed seeds',transform=ax.transAxes,fontsize=9,fontweight='bold',va='top')

    ax=fig.add_subplot(gs[1,2]); label(ax,'e'); ax.set_title('E5 replication and semantic dissociation',fontsize=11)
    names=list(SEM); xp=np.arange(len(names));
    for seed in range(2): ax.plot(xp,[SEM[n][seed] for n in names],marker='o',linewidth=1.1,label=f'Seed {seed+1}')
    ax.set_xticks(xp,['Base','Text','Neural','Shuffle'],rotation=15); ax.set_ylabel('Eight-task mean Spearman'); ax.set_ylim(.278,.312); ax.legend(frameon=False,fontsize=8,loc='lower left')
    ax.text(.04,.91,'Multilingual E5 reproduced the neural-guided\nalignment phenomenon; no stable neural-specific\ngeneric semantic gain',transform=ax.transAxes,fontsize=8.1,va='top')

    fig.suptitle('Figure 1 | From reproducible neural geometry to a learnable relational constraint',fontsize=15,fontweight='bold',y=.985)
    fig.text(.5,.012,'Locked ChineseEEG development and sealed-validation summaries. Figure assembly only; no new representation selection, model fitting or hypothesis testing.',ha='center',fontsize=8.7)
    fig.subplots_adjust(left=.07,right=.985,bottom=.10,top=.91,wspace=.48,hspace=.44)
    args.out_prefix.parent.mkdir(parents=True,exist_ok=True); fig.savefig(str(args.out_prefix)+'.png',dpi=300,bbox_inches='tight'); fig.savefig(str(args.out_prefix)+'.pdf',bbox_inches='tight')
    print(json.dumps({'status':'ok','run_mean':float(RUNS.mean()),'out_prefix':str(args.out_prefix)},indent=2))
if __name__=='__main__': main()

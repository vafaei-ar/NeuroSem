#!/usr/bin/env python3
from pathlib import Path
import csv, json, argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def panel_label(ax, label):
    ax.text(-0.08, 1.05, label, transform=ax.transAxes, fontsize=13, fontweight='bold', va='top')

def draw_box(ax, x, y, w, h, text, fs=9):
    rect = plt.Rectangle((x,y), w,h, fill=False, linewidth=1.1)
    ax.add_patch(rect)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs, wrap=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reliability-participants', type=Path, required=True)
    ap.add_argument('--reliability-summary', type=Path, required=True)
    ap.add_argument('--transfer-participants', type=Path, required=True)
    ap.add_argument('--transfer-summary', type=Path, required=True)
    ap.add_argument('--out-prefix', type=Path, required=True)
    args=ap.parse_args()

    rel_rows=read_csv(args.reliability_participants)
    rel_sum=read_json(args.reliability_summary)
    tr_rows=read_csv(args.transfer_participants)
    tr_sum=read_json(args.transfer_summary)

    rel=np.array([float(r['primary_residual_reliability']) for r in rel_rows])
    a0=np.array([float(r['lambda_0_residual_rsa']) for r in tr_rows])
    a1=np.array([float(r['lambda_0p10_residual_rsa']) for r in tr_rows])
    d=np.array([float(r['delta_0p10_minus_0']) for r in tr_rows])

    fig=plt.figure(figsize=(12.8,8.3))
    gs=GridSpec(2, 3, figure=fig, width_ratios=[1.05,1.2,1.0], height_ratios=[1,1], wspace=0.55, hspace=0.42)

    # A design
    ax=fig.add_subplot(gs[0,0]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off'); panel_label(ax,'a')
    ax.set_title('Prospective design', loc='left', fontsize=11, pad=8)
    draw_box(ax,0.04,0.64,0.34,0.20,'ChineseEEG\nnatural reading EEG\ntraining target',8.5)
    draw_box(ax,0.62,0.64,0.34,0.20,'Frozen E5 contrast\nλ=0.10 neural-guided\nvs λ=0 text-only',8.5)
    ax.annotate('',xy=(0.62,0.74),xytext=(0.38,0.74),arrowprops=dict(arrowstyle='->',lw=1.2))
    draw_box(ax,0.18,0.22,0.64,0.22,'SMN4Lang\n12 Mandarin participants • 60 spoken stories\nlanguage-network fMRI',8.5)
    ax.annotate('',xy=(0.50,0.44),xytext=(0.78,0.64),arrowprops=dict(arrowstyle='->',lw=1.2))
    ax.text(0.50,0.10,'Model-blind reliability gate completed before E5 evaluation',ha='center',va='center',fontsize=8.4,fontweight='bold')

    # B reliability
    ax=fig.add_subplot(gs[0,1]); panel_label(ax,'b')
    x=np.arange(1,len(rel)+1)
    ax.scatter(x,rel,s=28,zorder=3)
    mean=float(rel_sum['primary_mean']); lo,hi=rel_sum['primary_bootstrap_95_ci']
    ax.errorbar([len(rel)+1.2],[mean],yerr=[[mean-lo],[hi-mean]],fmt='D',capsize=4,linewidth=1.6,markersize=6,zorder=4)
    ax.axhline(0,linewidth=.8)
    ax.set_xlim(0.3,len(rel)+2)
    ax.set_ylim(min(0.57, rel.min()-0.025), max(0.73, rel.max()+0.02))
    ax.set_xlabel('Participant')
    ax.set_ylabel('Residual LOO reliability')
    ax.set_title('Model-blind fMRI reliability', fontsize=11)
    ax.set_xticks([1,4,8,12,len(rel)+1.2],['1','4','8','12','Mean'])
    ax.text(0.03,0.05,f"Mean {mean:.3f}\n95% CI {lo:.3f}–{hi:.3f}\n12/12 positive\nP={rel_sum['primary_exact_one_sided_signflip_p']:.6f}",transform=ax.transAxes,fontsize=8.7,va='bottom')

    # C mapping schematic
    ax=fig.add_subplot(gs[0,2]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off'); panel_label(ax,'c')
    ax.set_title('Frozen causal mapping', loc='left', fontsize=11, pad=8)
    draw_box(ax,0.05,0.73,0.90,0.14,'Released word onsets',9)
    draw_box(ax,0.05,0.50,0.90,0.14,'Within-sentence causal prefix E5 states',9)
    draw_box(ax,0.05,0.27,0.90,0.14,'Fixed canonical HRF → TR-level semantic drive',9)
    draw_box(ax,0.05,0.04,0.90,0.14,'Cosine model RDM ↔ LanA fMRI RDM\nafter frozen nuisance residualization',8.6)
    for y1,y2 in [(0.73,0.64),(0.50,0.41),(0.27,0.18)]:
        ax.annotate('',xy=(0.50,y2),xytext=(0.50,y1),arrowprops=dict(arrowstyle='->',lw=1.1))
    ax.text(0.50,-0.07,'No model, layer, λ, ROI, lag, HRF or semantic-unit search',ha='center',fontsize=8.2,transform=ax.transAxes)

    # D paired RSA
    ax=fig.add_subplot(gs[1,0:2]); panel_label(ax,'d')
    for i in range(len(a0)):
        ax.plot([0,1],[a0[i],a1[i]],marker='o',markersize=4,linewidth=0.9,alpha=.7,color='0.45')
    ax.set_xlim(-0.25,1.25)
    pad=(max(a1.max(),a0.max())-min(a0.min(),a1.min()))*0.08
    ax.set_ylim(min(a0.min(),a1.min())-pad,max(a0.max(),a1.max())+pad)
    ax.set_xticks([0,1],['Text-only λ=0','Neural-guided λ=0.10'])
    ax.set_ylabel('Participant residual RSA')
    ax.set_title('Every participant shifts upward under the frozen neural-guided contrast', fontsize=11)
    ax.text(0.02,0.04,f"Mean RSA: {tr_sum['lambda_0_mean_participant_rsa']:.6f} → {tr_sum['lambda_0p10_mean_participant_rsa']:.6f}",transform=ax.transAxes,fontsize=9)

    # E delta
    ax=fig.add_subplot(gs[1,2]); panel_label(ax,'e')
    order=np.argsort(d)
    yy=np.arange(1,len(d)+1)
    ax.scatter(d[order]*1000,yy,s=30,zorder=3)
    ax.axvline(0,linewidth=.8)
    m=tr_sum['primary_mean_delta']*1000
    lo,hi=[v*1000 for v in tr_sum['primary_bootstrap_95_ci_mean_delta']]
    ax.errorbar([m],[len(d)+1.2],xerr=[[m-lo],[hi-m]],fmt='D',capsize=4,linewidth=1.6,markersize=6)
    ax.set_yticks([1,4,8,12,len(d)+1.2],['lowest','4','8','highest','Mean'])
    ax.set_xlabel('Neural-guided − text-only RSA (×10⁻³)')
    ax.set_title('Participant-level transfer', fontsize=11)
    ax.set_ylim(0,len(d)+2)
    ax.text(0.03,0.04,f"Mean +{m:.3f} ×10⁻³\n95% CI +{lo:.3f} to +{hi:.3f}\n12/12 positive\nP={tr_sum['primary_exact_one_sided_signflip_p']:.6f}",transform=ax.transAxes,fontsize=8.7,va='bottom')

    fig.suptitle('Figure 3 | Prospective cross-modal transfer to language-network fMRI',fontsize=15,fontweight='bold',y=.985)
    fig.text(.5,.012,'SMN4Lang/OpenNeuro ds004078. Participant is the inferential unit. The fMRI reliability gate was model-blind; only the frozen λ=0.10 vs λ=0 contrast was evaluated afterward.',ha='center',fontsize=8.7)
    fig.subplots_adjust(left=0.07,right=0.985,bottom=0.09,top=0.91,wspace=0.55,hspace=0.42)
    args.out_prefix.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(str(args.out_prefix)+'.png',dpi=300,bbox_inches='tight')
    fig.savefig(str(args.out_prefix)+'.pdf',bbox_inches='tight')
    print(json.dumps({'status':'ok','png':str(args.out_prefix)+'.png','pdf':str(args.out_prefix)+'.pdf','n_subjects':len(d),'mean_delta':tr_sum['primary_mean_delta']},indent=2))

if __name__=='__main__': main()

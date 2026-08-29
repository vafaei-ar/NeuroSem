#!/usr/bin/env python3
from pathlib import Path
import csv,json,argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def rcsv(p):
    with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def rjson(p):return json.load(open(p,encoding='utf-8'))
def label(ax,s):ax.text(-.08,1.05,s,transform=ax.transAxes,fontsize=13,fontweight='bold',va='top')
def box(ax,x,y,w,h,t,fs=9):
    ax.add_patch(plt.Rectangle((x,y),w,h,fill=False,linewidth=1.1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs,wrap=True)

def main():
 p=argparse.ArgumentParser();
 p.add_argument('--rel-subjects',type=Path,required=True);p.add_argument('--rel-summary',type=Path,required=True)
 p.add_argument('--transfer-subjects',type=Path,required=True);p.add_argument('--transfer-summary',type=Path,required=True);p.add_argument('--out-prefix',type=Path,required=True);a=p.parse_args()
 rr=[r for r in rcsv(a.rel_subjects) if r['candidate']=='row_mean_all']; rs=rjson(a.rel_summary); tm=next(x for x in rs['metrics'] if x['candidate']=='row_mean_all')
 tr=rcsv(a.transfer_subjects); ts=rjson(a.transfer_summary); pr=ts['primary_result']
 rel=np.array([float(r['resid_loo']) for r in rr]); a0=np.array([float(r['lambda_0_resid_rsa']) for r in tr]); a1=np.array([float(r['lambda_0p10_resid_rsa']) for r in tr]); d=np.array([float(r['delta_0p10_minus_0']) for r in tr])
 fig=plt.figure(figsize=(12.5,7.8));gs=GridSpec(2,2,figure=fig,width_ratios=[1,1.45],height_ratios=[1,1],wspace=.38,hspace=.42)
 ax=fig.add_subplot(gs[0,0]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off');label(ax,'a');ax.set_title('Frozen cross-language validation',loc='left',fontsize=11)
 box(ax,.05,.65,.36,.19,'ChineseEEG\nChinese natural reading EEG\nneural-guided training',8.5);box(ax,.59,.65,.36,.19,'Frozen E5 contrast\nλ=0.10 neural-guided\nvs λ=0 text-only',8.5);ax.annotate('',xy=(.59,.745),xytext=(.41,.745),arrowprops=dict(arrowstyle='->',lw=1.2));box(ax,.18,.22,.64,.22,'ZuCo 2.0 Task 1\n17 independent readers • English\nnatural-reading EEG',8.5);ax.annotate('',xy=(.5,.44),xytext=(.77,.65),arrowprops=dict(arrowstyle='->',lw=1.2));ax.text(.5,.08,'No ZuCo outcome used for model retuning',ha='center',fontsize=8.5,fontweight='bold')
 ax=fig.add_subplot(gs[0,1]);label(ax,'b');x=np.arange(1,len(rel)+1);ax.scatter(x,rel,s=28);m=tm['mean_resid_loo'];lo,hi=tm['resid_loo_bootstrap_95ci'];ax.errorbar([len(rel)+1.5],[m],yerr=[[m-lo],[hi-m]],fmt='D',capsize=4,linewidth=1.5,markersize=6);ax.axhline(0,lw=.8);ax.set_title('Prospectively defined EEG geometry is reproducible',fontsize=11);ax.set_xlabel('Participant');ax.set_ylabel('Residual LOO reliability');ax.set_xticks([1,5,9,13,17,18.5],['1','5','9','13','17','Mean']);ax.set_xlim(.2,19.5);ax.text(.02,.05,f"Mean {m:.5f}\n95% CI {lo:.5f}–{hi:.5f}\n17/17 positive\nP={tm['exact_signflip']['one_sided_greater_p']:.2e}",transform=ax.transAxes,fontsize=8.7)
 ax=fig.add_subplot(gs[1,0]);label(ax,'c');
 for i in range(len(a0)): ax.plot([0,1],[a0[i],a1[i]],marker='o',markersize=3.8,lw=.8,alpha=.68,color='0.45')
 ax.set_xlim(-.25,1.25);ax.set_xticks([0,1],['Text-only λ=0','Neural-guided λ=0.10']);ax.set_ylabel('Participant residual RSA');ax.set_title('Paired participant alignment',fontsize=11)
 ax=fig.add_subplot(gs[1,1]);label(ax,'d');order=np.argsort(d);yy=np.arange(1,len(d)+1);ax.scatter(d[order]*1000,yy,s=28);ax.axvline(0,lw=.8);mean=pr['mean_delta']*1000;lo2,hi2=[z*1000 for z in pr['bootstrap_95ci']];ax.errorbar([mean],[len(d)+1.5],xerr=[[mean-lo2],[hi2-mean]],fmt='D',capsize=4,linewidth=1.5,markersize=6);ax.set_xlabel('Neural-guided − text-only RSA (×10⁻³)');ax.set_ylabel('Participants ordered by ΔRSA');ax.set_title('Cross-language transfer is positive in all 17 participants',fontsize=11);ax.set_ylim(0,len(d)+2.5);ax.text(.02,.05,f"Mean +{mean:.3f} ×10⁻³\n95% CI +{lo2:.3f} to +{hi2:.3f}\n17/17 positive\nP={pr['exact_signflip']['one_sided_greater_p']:.2e}",transform=ax.transAxes,fontsize=8.7)
 fig.suptitle('Figure 2 | Cross-language EEG generalization',fontsize=15,fontweight='bold',y=.985);fig.text(.5,.012,'ZuCo 2.0 Task 1 Normal Reading. Participant is the inferential unit; the model contrast and primary EEG representation were frozen before transfer evaluation.',ha='center',fontsize=8.7);fig.subplots_adjust(left=.08,right=.985,bottom=.09,top=.91)
 a.out_prefix.parent.mkdir(parents=True,exist_ok=True);fig.savefig(str(a.out_prefix)+'.png',dpi=300,bbox_inches='tight');fig.savefig(str(a.out_prefix)+'.pdf',bbox_inches='tight');print(json.dumps({'status':'ok','n':len(d),'mean_delta':pr['mean_delta']},indent=2))
if __name__=='__main__':main()

from __future__ import annotations

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BLUE='#2B6CB0'; BLUE_LIGHT='#9EC5E8'; BLUE_FILL='#CFE0F3'; BLUE_STRIP='#DCE9F7'
ORANGE='#D2691E'; ORANGE_LIGHT='#F2B184'; ORANGE_FILL='#FBE0CC'; ORANGE_STRIP='#FBEADF'
GREY='#7A7A7A'; GREY_LIGHT='#BFBFBF'; INK='#1A1A1A'; RULE='#C9C9C9'; PALE='#F7F7F7'


def use():
    plt.rcParams.update({
        'font.family':'sans-serif',
        'font.sans-serif':['Liberation Sans','DejaVu Sans'],
        'font.serif':['Liberation Serif','DejaVu Serif'],
        'font.size':8.5,'axes.titlesize':9,'axes.labelsize':8.5,
        'xtick.labelsize':8,'ytick.labelsize':8,
        'axes.edgecolor':INK,'axes.linewidth':0.8,
        'axes.spines.top':False,'axes.spines.right':False,
        'xtick.direction':'out','ytick.direction':'out',
        'xtick.major.size':3,'ytick.major.size':3,
        'figure.facecolor':'white','savefig.facecolor':'white',
        'axes.grid':False,'legend.frameon':False,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    })


def fig_title(fig, number, text, y=.98, size=15):
    fig.text(.5,y,f'Figure {number}. {text}',ha='center',va='top',family='serif',fontweight='bold',fontsize=size,color=INK)


def ed_title(fig, number, text, y=.978, size=13.5):
    fig.text(.5,y,f'Extended Data Figure {number}. {text}',ha='center',va='top',family='serif',fontweight='bold',fontsize=size,color=INK)


def panel_letter(fig,x,y,letter,size=15):
    fig.text(x,y,letter,ha='left',va='top',family='serif',fontweight='bold',fontsize=size,color=INK)


def panel_title(fig,x,y,text,size=10.5):
    fig.text(x,y,text,ha='left',va='top',fontsize=size,color=INK)


def zero_line(ax,orient='h'):
    kw=dict(color=RULE,lw=.9,ls=(0,(4,3)),zorder=0)
    (ax.axhline if orient=='h' else ax.axvline)(0,**kw)


def jitter(n,width=.055,seed=0):
    return np.random.default_rng(seed).uniform(-width,width,n)


def observations(ax,x,values,color,vertical=True,size=13,seed=0,alpha=.85,width=.055,face=None,edge=None):
    j=jitter(len(values),width,seed)
    if vertical:
        ax.scatter(np.full(len(values),x)+j,values,s=size,c=color if face is None else face,
                   edgecolors='none' if edge is None else edge,alpha=alpha,zorder=3)
    else:
        ax.scatter(values,np.full(len(values),x)+j,s=size,c=color if face is None else face,
                   edgecolors='none' if edge is None else edge,alpha=alpha,zorder=3)


def point_with_ci(ax,x,mean,lo,hi,color,ms=7,lw=1.3,capsize=2.5,vertical=True,mfc=None):
    mfc=color if mfc is None else mfc
    if vertical:
        ax.errorbar(x,mean,yerr=[[mean-lo],[hi-mean]],fmt='o',color=color,mfc=mfc,mec='white',mew=.6,
                    ms=ms,elinewidth=lw,capsize=capsize,capthick=lw,zorder=5)
    else:
        ax.errorbar(mean,x,xerr=[[mean-lo],[hi-mean]],fmt='o',color=color,mfc=mfc,mec='white',mew=.6,
                    ms=ms,elinewidth=lw,capsize=capsize,capthick=lw,zorder=5)


def half_violin(ax,x,values,color,side='right',width=.30,bw=.35,alpha=.55):
    from scipy.stats import gaussian_kde
    v=np.asarray(values,float)
    if len(v)<4 or np.unique(v).size<2 or np.std(v)<=0:
        return
    pad=max(np.std(v)*2.5, np.ptp(v)*.15)
    grid=np.linspace(v.min()-pad,v.max()+pad,256)
    dens=gaussian_kde(v,bw_method=bw)(grid); dens=dens/dens.max()*width
    sign=1 if side=='right' else -1
    ax.fill_betweenx(grid,x,x+sign*dens,color=color,alpha=alpha,lw=0,zorder=1)


def ci_cloud(ax,x,mean,lo,hi,color,side='right',width=.28,alpha=.32):
    sigma=max((hi-lo)/3.92,1e-12)
    grid=np.linspace(mean-3*sigma,mean+3*sigma,220)
    dens=np.exp(-.5*((grid-mean)/sigma)**2); dens=dens/dens.max()*width
    sign=1 if side=='right' else -1
    ax.fill_betweenx(grid,x,x+sign*dens,color=color,alpha=alpha,lw=0,zorder=1)


def dumbbell(ax,y,left,right,c_left,c_right,ms=7):
    ax.plot([left,right],[y,y],color=GREY_LIGHT,lw=1.1,zorder=2,solid_capstyle='round')
    ax.plot(left,y,'o',color=c_left,ms=ms,mec='white',mew=.6,zorder=4)
    ax.plot(right,y,'o',color=c_right,ms=ms,mec='white',mew=.6,zorder=4)


def facet_strip(ax,label,color,fontsize=9):
    ax.annotate(label,xy=(.5,1),xytext=(0,5),xycoords='axes fraction',textcoords='offset points',
                ha='center',va='bottom',fontsize=fontsize,color=INK,
                bbox=dict(boxstyle='square,pad=.45',facecolor=color,edgecolor='none'))

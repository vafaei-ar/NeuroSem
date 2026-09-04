#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
import nmi_style as S
LANG_PARCELS=["IFGorb","IFG","MFG","AntTemp","PostTemp","AngG"]

def read_region_summary(path:Path):
    with open(path,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    lang=[r for r in rows if r.get("family")=="language"]; dk=[r for r in rows if r.get("family")=="dk68"]
    if len(lang)!=6 or len(dk)!=68: raise RuntimeError(f"expected 6 language and 68 DK rows, found {len(lang)} and {len(dk)}")
    dk_rows=[[r["hemisphere"],r["region_name"],float(r["model_blind_reliability_mean"]),float(r["delta_mean"])] for r in dk]
    return lang,dk_rows

def panel_a(ax,lang_rows):
    by={r["region_name"]:r for r in lang_rows}; names=LANG_PARCELS; d=np.asarray([float(by[n]["delta_mean"]) for n in names])*1e3; ci=np.asarray([[float(by[n]["delta_bootstrap_ci_low"]),float(by[n]["delta_bootstrap_ci_high"])] for n in names])*1e3; y=np.arange(len(names))[::-1]
    ax.hlines(y,ci[:,0],ci[:,1],color=S.ORANGE,lw=0.8,zorder=2); ax.plot(d,y,"o",color=S.ORANGE,markersize=3.2,zorder=3); S.zeroline(ax,"v"); ax.set_yticks(y); ax.set_yticklabels(names); ax.set_ylim(-0.7,len(names)-0.3); ax.set_xlabel(r"Mean participant $\Delta$RSA ($\times10^{-3}$)"); ax.set_xlim(0,ci.max()*1.08); ax.grid(axis="x",zorder=0); S.offset_ticks(ax,"x")

def panel_b(ax,rows,lang_rows):
    vals=np.asarray([r[3] for r in rows])*1e3; rng=np.random.default_rng(0); y=rng.uniform(-0.28,0.28,len(vals)); ax.plot(vals,y,"o",color=S.GREY_L,markersize=2.4,zorder=2,label="DK68 parcel means"); by={r["region_name"]:r for r in lang_rows}; lang=np.asarray([float(by[n]["delta_mean"]) for n in LANG_PARCELS])*1e3; ax.plot(lang,np.zeros_like(lang)+0.42,"v",color=S.ORANGE,markersize=3.4,zorder=3,label="predefined language parcels"); S.zeroline(ax,"v"); ax.set_yticks([]); ax.set_ylim(-0.6,0.75); ax.spines["left"].set_visible(False); ax.set_xlabel(r"Mean participant $\Delta$RSA ($\times10^{-3}$)"); ax.set_xlim(0,max(vals.max(),lang.max())*1.08); ax.legend(loc="upper left",bbox_to_anchor=(0.0,1.28)); S.offset_ticks(ax,"x")

def panel_c(ax,rows):
    parcels=sorted({r[1] for r in rows}); grid=np.full((2,len(parcels)),np.nan)
    for hemi,parcel,_rel,delta in rows: grid[0 if hemi=="L" else 1,parcels.index(parcel)]=delta*1e3
    vmax=np.nanmax(np.abs(grid))*1.05; im=ax.imshow(grid,cmap=S.DIVERGING,vmin=-vmax,vmax=vmax,aspect="auto",interpolation="nearest"); ax.set_yticks([0,1]); ax.set_yticklabels(["left","right"]); ax.set_xticks(np.arange(len(parcels))); ax.set_xticklabels(parcels,rotation=90,fontsize=5.0); ax.tick_params(axis="both",length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
    cax=ax.inset_axes([1.008,0.0,0.014,1.0]); cb=ax.figure.colorbar(im,cax=cax); cb.set_label(r"Mean participant $\Delta$RSA ($\times10^{-3}$)",fontsize=6); cb.ax.tick_params(labelsize=5.5,length=1.5,width=0.5); cb.outline.set_linewidth(0.4); n_pos=int(np.nansum(grid>0)); n_tot=int(np.sum(~np.isnan(grid))); ax.text(0.0,1.30,f"{n_pos} of {n_tot} parcel means positive; scale symmetric about zero",transform=ax.transAxes,fontsize=6,color=S.GREY,va="bottom")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--region-summary",type=Path,required=True); ap.add_argument("--out-prefix",type=Path,required=True); args=ap.parse_args(); lang,rows=read_region_summary(args.region_summary); S.apply(); fig=S.figure(S.W2,112); gs=fig.add_gridspec(2,20,height_ratios=[1.0,1.9]); ax_a=fig.add_subplot(gs[0,0:9]); ax_b=fig.add_subplot(gs[0,11:20]); ax_c=fig.add_subplot(gs[1,0:20]); panel_a(ax_a,lang); panel_b(ax_b,rows,lang); panel_c(ax_c,rows); S.panel(ax_a,"a",dx=-0.24); S.panel(ax_b,"b",dx=-0.09,dy=1.34); S.panel(ax_c,"c",dx=-0.055,dy=1.40); written=S.save(fig,args.out_prefix); print(json.dumps({"status":"ok","n_parcels":len(rows),**written},indent=2))
if __name__=="__main__": main()

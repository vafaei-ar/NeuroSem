#!/usr/bin/env python3
"""Diagnostic decomposition of mirrored vs no-mirror AHBA language-panel results.

This is a post-hoc method-sensitivity analysis. It does not redefine the frozen
published panels or change the confirmatory conclusion. It quantifies whether the
large no-mirror dyslexia-panel association is attributable to parcel support,
hemisphere-specific structure, donor coverage, or particular frozen panel genes.
"""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

DONOR_IDS=["9861","10021","12876","14380","15496","15697"]
PANEL_IDS=["wong_2024_language_connectivity_6","wong_2024_language_dyslexia_14"]


def jload(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def zcols_support(X, keep):
    X=np.asarray(X,float); out=np.full_like(X,np.nan,float)
    sub=X[keep]
    mu=np.nanmean(sub,0); sd=np.nanstd(sub,0,ddof=0)
    if np.any(~np.isfinite(sd)) or np.any(sd<=0): raise RuntimeError("degenerate gene map on support")
    out[keep]=(sub-mu)/sd
    return out

def corr(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<3: return float("nan")
    a=rankdata(a); b=rankdata(b)
    a=(a-a.mean())/a.std(ddof=0); b=(b-b.mean())/b.std(ddof=0)
    return float(np.mean(a*b))

def donor_mean(stack, keep_donors):
    sub=stack[keep_donors]
    c=np.sum(np.isfinite(sub),0); s=np.nansum(sub,0)
    with np.errstate(divide="ignore",invalid="ignore"): return s/c

def read_bundle(root, subdir):
    d=Path(root)/subdir
    genes=[str(x).upper() for x in jload(d/"gene_symbols.json")]
    region_ids=[int(x) for x in jload(d/"region_ids.json")]
    donor_ids=[str(x) for x in jload(d/"donor_ids.json")]
    files={str(k):str(v) for k,v in jload(d/"donor_files.json").items()}
    if donor_ids!=DONOR_IDS or len(region_ids)!=68: raise RuntimeError(f"unexpected bundle {subdir}")
    mats=[]
    for did in donor_ids:
        with np.load(d/files[did],allow_pickle=False) as z: a=np.asarray(z["expression"],float)
        if a.shape!=(68,len(genes)) or np.isinf(a).any(): raise RuntimeError(f"bad donor matrix {subdir} {did}")
        mats.append(a)
    stack=np.stack(mats,0)
    return genes,region_ids,stack,donor_mean(stack,np.ones(6,bool))

def read_panels(path):
    obj=jload(path); panels=obj.get("panels",obj); out={}
    for pid in PANEL_IDS:
        x=panels[pid]
        if isinstance(x,list): genes=x
        else: genes=x.get("retained_primary_ahba_genes",x.get("genes",x.get("published_genes")))
        if not genes: raise RuntimeError(f"missing panel genes {pid}")
        out[pid]=[str(g).upper() for g in genes]
    return out

def read_target(path, region_ids):
    rows=list(csv.DictReader(Path(path).open("r",encoding="utf-8-sig",newline="")))
    by={int(r["parcel_id"]):r for r in rows}
    if set(by)!=set(region_ids): raise RuntimeError("target/expression parcel mismatch")
    y=np.asarray([float(by[i]["mean_semantic_contribution_backprojection"]) for i in region_ids])
    hemi=np.asarray([by[i]["hemisphere"] for i in region_ids])
    return y,hemi

def write_csv(path,rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expression-root",type=Path,default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--panel-json",type=Path,default=Path("outputs/published_language_gene_panels_v2/latest/gene_panels.json"))
    ap.add_argument("--parcel-target",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/population_parcel_target.csv"))
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/ahba_language_mirroring_diagnostic_v1/latest"))
    args=ap.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)

    panels=read_panels(args.panel_json)
    gM,rM,sM,pM=read_bundle(args.expression_root,"primary_leftright")
    gN,rN,sN,pN=read_bundle(args.expression_root,"sensitivity_no_mirror")
    if rM!=rN: raise RuntimeError("region order mismatch")
    y,hemi=read_target(args.parcel_target,rM)
    ixM={g:i for i,g in enumerate(gM)}; ixN={g:i for i,g in enumerate(gN)}

    panel_rows=[]; gene_rows=[]; parcel_rows=[]; lodo_rows=[]; summaries=[]
    for pid in PANEL_IDS:
        genes=panels[pid]
        missM=[g for g in genes if g not in ixM]; missN=[g for g in genes if g not in ixN]
        if missM or missN: raise RuntimeError(f"panel gene missing {pid}: primary={missM}, no_mirror={missN}")
        iM=np.asarray([ixM[g] for g in genes]); iN=np.asarray([ixN[g] for g in genes])
        support=np.all(np.isfinite(pN[:,iN]),axis=1)
        n_support=int(support.sum())
        if n_support<30: raise RuntimeError(f"too few no-mirror common parcels {pid}: {n_support}")
        zm_full=zcols_support(pM[:,iM],np.ones(68,bool)); mapM_full=np.nanmean(zm_full[:,iM*0+np.arange(len(iM))] if False else zm_full,axis=1)
        zm=zcols_support(pM[:,iM],support); zn=zcols_support(pN[:,iN],support)
        mapM=np.nanmean(zm,axis=1); mapN=np.nanmean(zn,axis=1)
        full_r=corr(mapM_full,y)
        common_rM=corr(mapM[support],y[support]); common_rN=corr(mapN[support],y[support])
        panel_rows.append({"panel_id":pid,"n_genes":len(genes),"n_common_parcels":n_support,
            "primary_full68_spearman":full_r,"primary_common_support_spearman":common_rM,
            "no_mirror_common_support_spearman":common_rN,"delta_no_mirror_minus_primary_common":common_rN-common_rM,
            "primary_vs_no_mirror_map_spearman":corr(mapM[support],mapN[support]),
            "delta_map_vs_semantic_spearman":corr((mapN-mapM)[support],y[support])})
        for h in ["lh","rh"]:
            k=support & (hemi==h)
            panel_rows.append({"panel_id":pid,"n_genes":len(genes),"n_common_parcels":int(k.sum()),"subset":h,
                "primary_common_support_spearman":corr(mapM[k],y[k]),"no_mirror_common_support_spearman":corr(mapN[k],y[k]),
                "delta_no_mirror_minus_primary_common":corr(mapN[k],y[k])-corr(mapM[k],y[k]),
                "primary_vs_no_mirror_map_spearman":corr(mapM[k],mapN[k]),"delta_map_vs_semantic_spearman":corr((mapN-mapM)[k],y[k])})
        for j,g in enumerate(genes):
            gene_rows.append({"panel_id":pid,"gene":g,"n_common_parcels":n_support,
                "primary_gene_vs_semantic_spearman":corr(zm[support,j],y[support]),
                "no_mirror_gene_vs_semantic_spearman":corr(zn[support,j],y[support]),
                "delta_gene_semantic":corr(zn[support,j],y[support])-corr(zm[support,j],y[support]),
                "primary_vs_no_mirror_gene_map_spearman":corr(zm[support,j],zn[support,j]),
                "gene_delta_map_vs_semantic_spearman":corr((zn[:,j]-zm[:,j])[support],y[support])})
        donor_count=np.sum(np.all(np.isfinite(sN[:,:,iN]),axis=2),axis=0)
        for q,rid in enumerate(rM):
            parcel_rows.append({"panel_id":pid,"parcel_id":rid,"hemisphere":hemi[q],"in_common_support":bool(support[q]),
                "semantic_target":y[q],"primary_panel_map":mapM[q] if support[q] else "",
                "no_mirror_panel_map":mapN[q] if support[q] else "","no_mirror_minus_primary":(mapN[q]-mapM[q]) if support[q] else "",
                "no_mirror_donors_with_complete_panel":int(donor_count[q])})
        for di,did in enumerate(DONOR_IDS):
            keepd=np.ones(6,bool); keepd[di]=False
            m=donor_mean(sM,keepd)[:,iM]; n=donor_mean(sN,keepd)[:,iN]
            fixed=support & np.all(np.isfinite(m),axis=1) & np.all(np.isfinite(n),axis=1)
            if fixed.sum()<30:
                lodo_rows.append({"panel_id":pid,"excluded_donor":did,"status":"insufficient_fixed_support","n_parcels":int(fixed.sum())}); continue
            zm_l=zcols_support(m,fixed); zn_l=zcols_support(n,fixed)
            mm=np.nanmean(zm_l,axis=1); nn=np.nanmean(zn_l,axis=1)
            lodo_rows.append({"panel_id":pid,"excluded_donor":did,"status":"written","n_parcels":int(fixed.sum()),
                "primary_spearman":corr(mm[fixed],y[fixed]),"no_mirror_spearman":corr(nn[fixed],y[fixed]),
                "delta":corr(nn[fixed],y[fixed])-corr(mm[fixed],y[fixed]),"map_similarity":corr(mm[fixed],nn[fixed])})
        dg=[r for r in gene_rows if r["panel_id"]==pid]
        dp=[r for r in parcel_rows if r["panel_id"]==pid and r["in_common_support"]]
        summaries.append({"panel_id":pid,"n_common_parcels":n_support,
            "largest_gene_delta_abs":sorted(dg,key=lambda r:abs(r["delta_gene_semantic"]),reverse=True)[:5],
            "largest_parcel_map_delta_abs":sorted(dp,key=lambda r:abs(float(r["no_mirror_minus_primary"])),reverse=True)[:10]})

    write_csv(args.output_dir/"panel_decomposition.csv",panel_rows)
    write_csv(args.output_dir/"gene_decomposition.csv",gene_rows)
    write_csv(args.output_dir/"parcel_decomposition.csv",parcel_rows)
    write_csv(args.output_dir/"donor_lodo_matched_support.csv",lodo_rows)
    summary={"schema_version":1,"analysis":"posthoc AHBA left-right mirroring diagnostic v1","confirmatory_status":"diagnostic only; does not alter frozen null conclusion",
        "question":"why the no-mirror Wong dyslexia panel association is stronger than the primary mirrored association",
        "design":["compare primary full-68 to primary restricted to exact no-mirror panel common support","compare mirrored and no-mirror maps on identical parcel support","decompose by hemisphere, frozen panel gene, parcel, and donor LODO"],
        "panel_results":[r for r in panel_rows if "subset" not in r],"diagnostic_extremes":summaries,
        "interpretation_guardrail":"No posthoc diagnostic feature is a confirmatory positive result. Mirroring was primary and remains primary."}
    (args.output_dir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","panels":len(PANEL_IDS),"output_dir":str(args.output_dir)},indent=2))

if __name__=="__main__": main()

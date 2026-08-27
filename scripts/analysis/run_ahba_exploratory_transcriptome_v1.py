#!/usr/bin/env python3
"""Exploratory AHBA whole-transcriptome analysis for the frozen DK68 semantic map.

This is a new exploratory phase, separate from the frozen GABA/serotonin null.
It uses the AHBA-blind DK68 semantic back-projection, the frozen primary mirrored
AHBA expression bundle, and hemisphere-constrained spherical rotations.

Analyses:
1) PLS1-style whole-transcriptome discovery. With one response, the gene-weight
   vector is proportional to X.T @ y and the regional score is K @ y where
   K = X @ X.T. Significance of the score-y correlation is assessed by spins
   that rebuild PLS1 for each rotated phenotype.
2) Intrinsic transcriptomic gradients from SVD/PCA of X. Correlations of the
   first 10 regional transcriptomic components with y are tested by the same
   spins with BH-FDR across components.
3) Six-donor leave-one-out stability of the observed PLS1 gene-weight ranking.

No external language-gene panels are tested here; those are reserved for a
separate validation task frozen independently of these discovery results.
"""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.transform import Rotation
from scipy.stats import rankdata

DONOR_IDS = ["9861", "10021", "12876", "14380", "15496", "15697"]


def jload(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def zcols(X):
    X = np.asarray(X, float)
    mu = X.mean(0, keepdims=True); sd = X.std(0, ddof=0, keepdims=True)
    if np.any(~np.isfinite(sd)) or np.any(sd <= 0):
        raise RuntimeError("zero/nonfinite spatial gene variance")
    return (X-mu)/sd

def zvec(y):
    y=np.asarray(y,float); s=y.std(ddof=0)
    if not np.isfinite(s) or s<=0: raise RuntimeError("degenerate phenotype")
    return (y-y.mean())/s

def pearson(a,b):
    a=zvec(a); b=zvec(b); return float(np.mean(a*b))

def spearman(a,b): return pearson(rankdata(a), rankdata(b))

def bh(p):
    p=np.asarray(p,float); n=len(p); o=np.argsort(p); q=p[o]*n/np.arange(1,n+1)
    q=np.minimum.accumulate(q[::-1])[::-1]; out=np.empty(n); out[o]=np.clip(q,0,1); return out

def donor_mean(stack, keep):
    sub=stack[keep]; c=np.sum(np.isfinite(sub),0); s=np.nansum(sub,0)
    with np.errstate(divide="ignore",invalid="ignore"): m=s/c
    return m

def read_expression(root):
    d=Path(root)/"primary_leftright"
    genes=[str(x) for x in jload(d/"gene_symbols.json")]
    region_ids=[int(x) for x in jload(d/"region_ids.json")]
    donor_ids=[str(x) for x in jload(d/"donor_ids.json")]
    files={str(k):str(v) for k,v in jload(d/"donor_files.json").items()}
    if donor_ids != DONOR_IDS or len(region_ids)!=68: raise RuntimeError("unexpected expression bundle")
    mats=[]
    for did in donor_ids:
        with np.load(d/files[did],allow_pickle=False) as z: a=np.asarray(z["expression"],float)
        if a.shape!=(68,len(genes)) or np.isinf(a).any(): raise RuntimeError(f"bad donor matrix {did}")
        mats.append(a)
    stack=np.stack(mats,0)
    pop=donor_mean(stack,np.ones(6,bool))
    if not np.isfinite(pop).all(): raise RuntimeError("population expression incomplete")
    return genes, region_ids, stack, pop

def read_target(path, region_ids):
    rows=list(csv.DictReader(Path(path).open("r",encoding="utf-8-sig",newline="")))
    by={int(r["parcel_id"]):r for r in rows}
    if set(by)!=set(region_ids): raise RuntimeError("target/expression parcel mismatch")
    y=np.asarray([float(by[i]["mean_semantic_contribution_backprojection"]) for i in region_ids],float)
    hemi=[by[i]["hemisphere"] for i in region_ids]
    name=[by[i]["parcel_name"] for i in region_ids]
    return y,hemi,name

def parcel_sphere_centroids(source_freeze, vertex_map, region_ids):
    src=jload(source_freeze); fs=Path(src["template_resources"]["fsaverage_dir"])
    import nibabel.freesurfer.io as fsio
    lh,_=fsio.read_geometry(str(fs/"surf"/"lh.sphere")); rh,_=fsio.read_geometry(str(fs/"surf"/"rh.sphere"))
    rows=list(csv.DictReader(Path(vertex_map).open("r",encoding="utf-8-sig",newline="")))
    by={i:[] for i in region_ids}
    for r in rows:
        if r["mapped_to_dk68"].strip().lower()!="true": continue
        pid=int(r["parcel_id"]); v=int(r["surface_vertex"]); h=r["hemisphere"]
        xyz=(lh if h=="lh" else rh)[v]
        by[pid].append(np.asarray(xyz,float)/np.linalg.norm(xyz))
    C=[]
    for pid in region_ids:
        if not by[pid]: raise RuntimeError(f"no sphere vertices parcel {pid}")
        c=np.mean(by[pid],0); C.append(c/np.linalg.norm(c))
    return np.vstack(C)

def make_spins(C, hemis, n, seed):
    rng=np.random.default_rng(seed); hemis=np.asarray(hemis); idxL=np.where(hemis=="lh")[0]; idxR=np.where(hemis=="rh")[0]
    if len(idxL)!=34 or len(idxR)!=34: raise RuntimeError("expected 34 parcels/hemisphere")
    out=np.empty((n,len(C)),dtype=np.int16)
    for k in range(n):
        R=Rotation.random(random_state=rng).as_matrix(); perm=np.empty(len(C),int)
        for idx in (idxL,idxR):
            rot=C[idx]@R.T; cost=1.0-rot@C[idx].T; a,b=linear_sum_assignment(cost); perm[idx[a]]=idx[b]
        out[k]=perm
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parcel-summary",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/summary.json"))
    ap.add_argument("--parcel-target",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/population_parcel_target.csv"))
    ap.add_argument("--expression-summary",type=Path,default=Path("outputs/ahba_expression_dk_v1/latest/summary.json"))
    ap.add_argument("--expression-root",type=Path,default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--source-freeze",type=Path,default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"))
    ap.add_argument("--vertex-map",type=Path,default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/vertex_parcel_map.csv"))
    ap.add_argument("--spins",type=int,default=5000); ap.add_argument("--seed",type=int,default=20260827)
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/ahba_exploratory_transcriptome_v1/latest")); args=ap.parse_args()
    if args.spins!=5000 or args.seed!=20260827: raise SystemExit("frozen exploratory design requires 5000 spins and seed 20260827")
    ps=jload(args.parcel_summary); es=jload(args.expression_summary)
    if not ps.get("ready_for_exploratory_transcriptomics",False): raise RuntimeError("parcel phenotype gate not ready")
    if not es.get("ready_for_molecular_sensitivity_matrix",False): raise RuntimeError("expression gate not ready")
    genes,region_ids,stack,pop=read_expression(args.expression_root)
    y,hemis,names=read_target(args.parcel_target,region_ids); yz=zvec(y); X=zcols(pop)
    C=parcel_sphere_centroids(args.source_freeze,args.vertex_map,region_ids); spins=make_spins(C,hemis,args.spins,args.seed)

    # PLS1 kernel form.
    w=X.T@yz; w=w/np.linalg.norm(w); score=X@w; obs_pls=pearson(score,yz); obs_pls_r2=obs_pls**2
    K=X@X.T
    null_pls=np.empty(args.spins,float)
    for i,p in enumerate(spins):
        yp=yz[p]; s=K@yp; null_pls[i]=abs(pearson(s,yp))
    pls_p=float((1+np.sum(null_pls>=abs(obs_pls)))/(args.spins+1))

    # Transcriptomic gradients.
    U,S,Vt=np.linalg.svd(X,full_matrices=False); scores=U*S
    grad=[]
    for j in range(10):
        r=spearman(scores[:,j],y); null=np.asarray([abs(spearman(scores[:,j],yz[p])) for p in spins]); p=float((1+np.sum(null>=abs(r)))/(args.spins+1))
        grad.append({"component":j+1,"variance_fraction":float(S[j]**2/np.sum(S**2)),"spearman":r,"spin_p_two_sided":p})
    qs=bh([g["spin_p_two_sided"] for g in grad])
    for g,q in zip(grad,qs): g["bh_fdr_q_10_components"]=float(q)

    # Donor LODO stability of gene weights.
    full_rank=rankdata(w); lodo=[]
    for di,did in enumerate(DONOR_IDS):
        keep=np.ones(6,bool); keep[di]=False; m=donor_mean(stack,keep)
        if not np.isfinite(m).all():
            lodo.append({"excluded_donor":did,"status":"incomplete_full_68","weight_rank_spearman":""}); continue
        Xl=zcols(m); wl=Xl.T@yz; wl=wl/np.linalg.norm(wl)
        lodo.append({"excluded_donor":did,"status":"written","weight_rank_spearman":spearman(full_rank,rankdata(wl))})

    out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    order=np.argsort(w)
    with (out/"gene_weights.csv").open("w",encoding="utf-8",newline="") as f:
        cw=csv.writer(f); cw.writerow(["gene","pls1_weight","rank_absolute","direction"])
        absrank=rankdata(np.abs(w),method="ordinal")
        for i in np.argsort(-np.abs(w)): cw.writerow([genes[i],float(w[i]),int(len(w)+1-absrank[i]),"positive" if w[i]>0 else "negative"])
    with (out/"gradient_results.csv").open("w",encoding="utf-8",newline="") as f:
        dw=csv.DictWriter(f,fieldnames=list(grad[0])); dw.writeheader(); dw.writerows(grad)
    with (out/"donor_lodo_weight_stability.csv").open("w",encoding="utf-8",newline="") as f:
        dw=csv.DictWriter(f,fieldnames=list(lodo[0])); dw.writeheader(); dw.writerows(lodo)
    with (out/"spin_null_summary.csv").open("w",encoding="utf-8",newline="") as f:
        cw=csv.writer(f); cw.writerow(["analysis","observed","n_spins","empirical_p_two_sided","null_abs_mean","null_abs_sd"]); cw.writerow(["pls1_score_correlation",obs_pls,args.spins,pls_p,float(null_pls.mean()),float(null_pls.std(ddof=0))])
    top_pos=[genes[i] for i in order[-25:][::-1]]; top_neg=[genes[i] for i in order[:25]]
    payload={
      "schema_version":1,"analysis":"exploratory AHBA whole-transcriptome + gradient analysis v1","exploratory":True,
      "separate_from_frozen_gaba_serotonin_null":True,"n_parcels":68,"n_genes":len(genes),"n_spins":args.spins,"spin_seed":args.seed,
      "spatial_null":"hemisphere-constrained spherical rotations on fsaverage sphere parcel centroids with one-to-one Hungarian reassignment",
      "pls1":{"score_phenotype_pearson":obs_pls,"score_phenotype_r2":obs_pls_r2,"spin_p_two_sided":pls_p,"top_positive_genes":top_pos,"top_negative_genes":top_neg},
      "transcriptomic_gradients":grad,"donor_lodo_weight_stability":lodo,
      "language_gene_panels_tested":False,
      "interpretation_guardrails":["PLS1 is exploratory whole-transcriptome discovery, not confirmatory prediction.","Gene ranking should be interpreted through independent enrichment/validation rather than single-gene p-values.","Published language-gene panels must be frozen independently before testing.","The prior prespecified GABA/serotonin null remains unchanged."],
      "next_step":"If PLS1 or a transcriptomic gradient survives spatial nulls, inspect gene-weight stability and run independent published language-network gene-set validation plus pathway enrichment with co-expression-aware gene-set nulls."
    }
    (out/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"completed","pls1_r":obs_pls,"pls1_spin_p":pls_p,"best_gradient":min(grad,key=lambda g:g["spin_p_two_sided"])},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())

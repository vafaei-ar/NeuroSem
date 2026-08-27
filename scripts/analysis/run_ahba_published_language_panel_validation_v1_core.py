#!/usr/bin/env python3
"""Independent validation of frozen Wong et al. 2024 language-related gene panels.

Two outcome-blind panels were frozen before this analysis:
- wong_2024_language_connectivity_6
- wong_2024_language_dyslexia_14

Primary statistic: Spearman correlation across DK68 parcels between the frozen
ChineseEEG semantic-contribution phenotype and the mean of spatially standardized
AHBA expression maps for genes in each panel.

Inference:
1) 5000 hemisphere-constrained spherical rotations of the semantic phenotype.
2) 5000 ordinary size-matched random-gene sets.
3) 5000 panel-coexpression-profile-matched random-gene sets. For each observed
   panel gene, its mean absolute correlation with the other panel genes is
   computed across DK68. Genome-wide candidate genes are scored by mean absolute
   correlation with the observed panel genes, binned into 20 quantiles, and each
   null set samples one non-panel gene from the corresponding bin for every
   observed panel gene. This is a conservative transcriptomic-structure control,
   not a perfect generative model of co-expression.

BH-FDR is applied across the two published panels separately for each null family.
A panel is marked jointly supported only if both spatial-spin FDR and the stricter
coexpression-profile null FDR are < .05. Size-matched nulls, donor LODO, and
no-mirror analyses are robustness summaries and cannot rescue a failed primary
joint test.
"""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.transform import Rotation
from scipy.stats import rankdata

DONOR_IDS = ["9861", "10021", "12876", "14380", "15496", "15697"]
PANEL_IDS = ["wong_2024_language_connectivity_6", "wong_2024_language_dyslexia_14"]


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def zvec(x):
    x=np.asarray(x,float); s=x.std(ddof=0)
    if not np.isfinite(s) or s<=0: raise RuntimeError("degenerate vector")
    return (x-x.mean())/s


def zcols(X):
    X=np.asarray(X,float); mu=X.mean(0,keepdims=True); sd=X.std(0,ddof=0,keepdims=True)
    if np.any(~np.isfinite(sd)) or np.any(sd<=0): raise RuntimeError("zero/nonfinite gene spatial variance")
    return (X-mu)/sd


def pearson(a,b):
    a=zvec(a); b=zvec(b); return float(np.mean(a*b))


def spearman(a,b):
    return pearson(rankdata(a), rankdata(b))


def bh(p):
    p=np.asarray(p,float); n=len(p); o=np.argsort(p)
    q=p[o]*n/np.arange(1,n+1); q=np.minimum.accumulate(q[::-1])[::-1]
    out=np.empty(n); out[o]=np.clip(q,0,1); return out


def donor_mean(stack, keep):
    sub=stack[keep]; c=np.sum(np.isfinite(sub),0); s=np.nansum(sub,0)
    with np.errstate(divide="ignore",invalid="ignore"): return s/c


def read_expression_bundle(root, subdir):
    d=Path(root)/subdir
    genes=[str(x).upper() for x in jload(d/"gene_symbols.json")]
    region_ids=[int(x) for x in jload(d/"region_ids.json")]
    donor_ids=[str(x) for x in jload(d/"donor_ids.json")]
    files={str(k):str(v) for k,v in jload(d/"donor_files.json").items()}
    if donor_ids != DONOR_IDS or len(region_ids)!=68: raise RuntimeError(f"unexpected expression bundle {subdir}")
    mats=[]
    for did in donor_ids:
        with np.load(d/files[did],allow_pickle=False) as z: a=np.asarray(z["expression"],float)
        if a.shape!=(68,len(genes)) or np.isinf(a).any(): raise RuntimeError(f"bad donor matrix {subdir} {did}")
        mats.append(a)
    stack=np.stack(mats,0); pop=donor_mean(stack,np.ones(6,bool))
    return genes,region_ids,stack,pop


def read_target(path, region_ids):
    rows=list(csv.DictReader(Path(path).open("r",encoding="utf-8-sig",newline="")))
    by={int(r["parcel_id"]):r for r in rows}
    if set(by)!=set(region_ids): raise RuntimeError("target/expression parcel mismatch")
    y=np.asarray([float(by[i]["mean_semantic_contribution_backprojection"]) for i in region_ids],float)
    hemi=[by[i]["hemisphere"] for i in region_ids]
    return y,hemi


def parcel_sphere_centroids(source_freeze, vertex_map, region_ids):
    src=jload(source_freeze); fs=Path(src["template_resources"]["fsaverage_dir"])
    import nibabel.freesurfer.io as fsio
    lh,_=fsio.read_geometry(str(fs/"surf"/"lh.sphere")); rh,_=fsio.read_geometry(str(fs/"surf"/"rh.sphere"))
    rows=list(csv.DictReader(Path(vertex_map).open("r",encoding="utf-8-sig",newline="")))
    by={i:[] for i in region_ids}
    for r in rows:
        if r["mapped_to_dk68"].strip().lower()!="true": continue
        pid=int(r["parcel_id"]); v=int(r["surface_vertex"]); h=r["hemisphere"]
        xyz=(lh if h=="lh" else rh)[v]; by[pid].append(np.asarray(xyz,float)/np.linalg.norm(xyz))
    C=[]
    for pid in region_ids:
        if not by[pid]: raise RuntimeError(f"no sphere vertices parcel {pid}")
        c=np.mean(by[pid],0); C.append(c/np.linalg.norm(c))
    return np.vstack(C)


def make_spins(C, hemis, n, seed):
    rng=np.random.default_rng(seed); hemis=np.asarray(hemis)
    idxL=np.where(hemis=="lh")[0]; idxR=np.where(hemis=="rh")[0]
    if len(idxL)!=34 or len(idxR)!=34: raise RuntimeError("expected 34 parcels/hemisphere")
    out=np.empty((n,len(C)),dtype=np.int16)
    for k in range(n):
        R=Rotation.random(random_state=rng).as_matrix(); perm=np.empty(len(C),int)
        for idx in (idxL,idxR):
            rot=C[idx]@R.T; cost=1.0-rot@C[idx].T; a,b=linear_sum_assignment(cost); perm[idx[a]]=idx[b]
        out[k]=perm
    return out


def load_panels(panel_summary, panel_json):
    s=jload(panel_summary)
    if not s.get("ready_for_independent_language_gene_validation",False): raise RuntimeError("published panels not ready")
    obj=jload(panel_json)
    panels=obj.get("panels",obj)
    if set(PANEL_IDS)-set(panels): raise RuntimeError("expected frozen panel ids missing")
    out={}
    for pid in PANEL_IDS:
        x=panels[pid]
        genes=x.get("retained_primary_ahba_genes",x.get("genes",x.get("published_genes")))
        if not genes: raise RuntimeError(f"no genes for {pid}")
        out[pid]=[str(g).upper() for g in genes]
    return out


def panel_map(X, indices):
    return np.mean(X[:,indices],axis=1)


def random_set_null(X, y, n_genes, n_null, rng, excluded):
    universe=np.asarray([i for i in range(X.shape[1]) if i not in excluded],int)
    vals=np.empty(n_null,float)
    for k in range(n_null):
        idx=rng.choice(universe,size=n_genes,replace=False)
        vals[k]=abs(spearman(panel_map(X,idx),y))
    return vals


def coexpression_profile_null(X, y, panel_idx, n_null, rng):
    # X columns are spatially standardized. Pearson correlations equal dot/68.
    P=X[:,panel_idx]
    corr_pp=(P.T@P)/X.shape[0]
    obs=[]
    for j in range(len(panel_idx)):
        others=np.delete(np.abs(corr_pp[j]),j)
        obs.append(float(np.mean(others)))
    corr_all=np.abs((X.T@P)/X.shape[0])
    panel_set=set(panel_idx)
    score_all=np.mean(corr_all,axis=1)
    # Candidate bins are defined by genome-wide score quantiles; panel genes excluded.
    qs=np.quantile(score_all,np.linspace(0,1,21))
    bins=[]
    for target in obs:
        b=int(np.searchsorted(qs,target,side="right")-1); b=max(0,min(19,b))
        lo,hi=qs[b],qs[b+1]
        if b==19: cand=np.where((score_all>=lo)&(score_all<=hi))[0]
        else: cand=np.where((score_all>=lo)&(score_all<hi))[0]
        cand=np.asarray([i for i in cand if i not in panel_set],int)
        if len(cand)<50:
            order=np.argsort(np.abs(score_all-target))
            cand=np.asarray([i for i in order if i not in panel_set][:500],int)
        bins.append(cand)
    vals=np.empty(n_null,float)
    for k in range(n_null):
        chosen=[]
        for cand in bins:
            avail=np.asarray([i for i in cand if i not in chosen],int)
            if len(avail)==0: raise RuntimeError("coexpression matching exhausted candidate bin")
            chosen.append(int(rng.choice(avail)))
        vals[k]=abs(spearman(panel_map(X,np.asarray(chosen,int)),y))
    return vals, obs


def empirical_p(null_abs, obs):
    return float((1+np.sum(null_abs>=abs(obs)))/(len(null_abs)+1))


def analyze_bundle(genes, region_ids, stack, pop, panels, y, spins, n_random, seed, label):
    if not np.isfinite(pop).all(): raise RuntimeError(f"population expression incomplete: {label}")
    X=zcols(pop); gix={g:i for i,g in enumerate(genes)}
    rng=np.random.default_rng(seed)
    results=[]; lodo=[]
    for pi,pid in enumerate(PANEL_IDS):
        missing=[g for g in panels[pid] if g not in gix]
        if missing: raise RuntimeError(f"{label} missing panel genes {pid}: {missing}")
        idx=np.asarray([gix[g] for g in panels[pid]],int)
        m=panel_map(X,idx); obs=spearman(m,y)
        spatial=np.asarray([abs(spearman(m,y[p])) for p in spins],float)
        size_null=random_set_null(X,y,len(idx),n_random,rng,set(idx))
        coex_null,coex_profile=coexpression_profile_null(X,y,idx,n_random,rng)
        results.append({
            "bundle":label,"panel_id":pid,"n_genes":len(idx),"observed_spearman":obs,
            "spatial_spin_p_two_sided":empirical_p(spatial,obs),
            "size_matched_gene_p_two_sided":empirical_p(size_null,obs),
            "coexpression_profile_gene_p_two_sided":empirical_p(coex_null,obs),
            "spatial_null_abs_mean":float(spatial.mean()),"size_null_abs_mean":float(size_null.mean()),
            "coexpression_null_abs_mean":float(coex_null.mean()),
            "panel_mean_abs_within_coexpression":float(np.mean(coex_profile)),
        })
        if label=="primary_leftright":
            for di,did in enumerate(DONOR_IDS):
                keep=np.ones(6,bool); keep[di]=False; mpop=donor_mean(stack,keep)
                if not np.isfinite(mpop).all():
                    lodo.append({"panel_id":pid,"excluded_donor":did,"status":"incomplete_full_68","spearman":""}); continue
                Xl=zcols(mpop); ml=panel_map(Xl,idx)
                lodo.append({"panel_id":pid,"excluded_donor":did,"status":"written","spearman":spearman(ml,y)})
    return results,lodo


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parcel-summary",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/summary.json"))
    ap.add_argument("--parcel-target",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/population_parcel_target.csv"))
    ap.add_argument("--expression-root",type=Path,default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--panel-summary",type=Path,default=Path("outputs/published_language_gene_panels_v2/latest/summary.json"))
    ap.add_argument("--panel-json",type=Path,default=Path("outputs/published_language_gene_panels_v2/latest/gene_panels.json"))
    ap.add_argument("--source-freeze",type=Path,default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"))
    ap.add_argument("--vertex-map",type=Path,default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/vertex_parcel_map.csv"))
    ap.add_argument("--spins",type=int,default=5000); ap.add_argument("--random-sets",type=int,default=5000); ap.add_argument("--seed",type=int,default=20260827)
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/ahba_published_language_panel_validation_v1/latest")); args=ap.parse_args()
    if args.spins!=5000 or args.random_sets!=5000 or args.seed!=20260827: raise SystemExit("frozen design requires 5000 spins, 5000 random sets, seed 20260827")
    ps=jload(args.parcel_summary)
    if not ps.get("ready_for_exploratory_transcriptomics",False): raise RuntimeError("parcel phenotype gate not ready")
    panels=load_panels(args.panel_summary,args.panel_json)
    genes,region_ids,stack,pop=read_expression_bundle(args.expression_root,"primary_leftright")
    y,hemis=read_target(args.parcel_target,region_ids)
    C=parcel_sphere_centroids(args.source_freeze,args.vertex_map,region_ids); spins=make_spins(C,hemis,args.spins,args.seed)
    primary,lodo=analyze_bundle(genes,region_ids,stack,pop,panels,y,spins,args.random_sets,args.seed,"primary_leftright")
    # Multiple-testing correction across the two independent published panels.
    for key,qkey in [
        ("spatial_spin_p_two_sided","spatial_spin_bh_q_2_panels"),
        ("size_matched_gene_p_two_sided","size_matched_gene_bh_q_2_panels"),
        ("coexpression_profile_gene_p_two_sided","coexpression_profile_gene_bh_q_2_panels")]:
        qs=bh([r[key] for r in primary])
        for r,q in zip(primary,qs): r[qkey]=float(q)
    for r in primary:
        r["jointly_supported"] = bool(r["spatial_spin_bh_q_2_panels"]<0.05 and r["coexpression_profile_gene_bh_q_2_panels"]<0.05)

    # Bilateral no-mirror sensitivity: same frozen panels, no multiplicity-driven claim changes.
    genes2,region_ids2,stack2,pop2=read_expression_bundle(args.expression_root,"sensitivity_no_mirror")
    if region_ids2!=region_ids: raise RuntimeError("no-mirror region order mismatch")
    sens=[]
    if np.isfinite(pop2).all():
        sens,_=analyze_bundle(genes2,region_ids2,stack2,pop2,panels,y,spins,args.random_sets,args.seed+101,"sensitivity_no_mirror")
    else:
        # Preserve missingness: use the common set of parcels finite for all panel genes.
        X2=pop2; g2={g:i for i,g in enumerate(genes2)}
        for pid in PANEL_IDS:
            idx=[g2[g] for g in panels[pid] if g in g2]
            if len(idx)!=len(panels[pid]):
                sens.append({"bundle":"sensitivity_no_mirror","panel_id":pid,"status":"panel_gene_missing"}); continue
            keep=np.all(np.isfinite(X2[:,idx]),axis=1)
            if keep.sum()<30:
                sens.append({"bundle":"sensitivity_no_mirror","panel_id":pid,"status":"insufficient_complete_parcels","n_complete":int(keep.sum())}); continue
            Xk=zcols(X2[keep][:,idx]); mk=np.mean(Xk,axis=1); sens.append({"bundle":"sensitivity_no_mirror","panel_id":pid,"status":"written_common_complete","n_complete":int(keep.sum()),"observed_spearman":spearman(mk,y[keep])})

    out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    with (out/"panel_results.csv").open("w",encoding="utf-8",newline="") as f:
        dw=csv.DictWriter(f,fieldnames=list(primary[0])); dw.writeheader(); dw.writerows(primary)
    with (out/"donor_lodo_results.csv").open("w",encoding="utf-8",newline="") as f:
        dw=csv.DictWriter(f,fieldnames=list(lodo[0])); dw.writeheader(); dw.writerows(lodo)
    fields=sorted(set().union(*(r.keys() for r in sens)))
    with (out/"bilateral_sensitivity.csv").open("w",encoding="utf-8",newline="") as f:
        dw=csv.DictWriter(f,fieldnames=fields); dw.writeheader(); dw.writerows(sens)
    summary={
        "schema_version":1,"analysis":"independent published language-panel AHBA validation v1",
        "frozen_before_outcome":True,"n_panels":2,"n_spins":args.spins,"n_random_sets":args.random_sets,"seed":args.seed,
        "primary_statistic":"Spearman correlation across DK68 between frozen semantic phenotype and mean spatially z-scored panel-gene expression map",
        "spatial_null":"hemisphere-constrained spherical rotations on fsaverage sphere parcel centroids with one-to-one Hungarian reassignment",
        "gene_nulls":{
            "size_matched":"uniform random genes excluding observed panel genes",
            "coexpression_profile_matched":"one matched non-panel gene per observed gene using 20-quantile bins of genome-wide mean absolute correlation to observed panel genes; observed target for each slot is that panel gene's mean absolute within-panel correlation"
        },
        "multiple_testing":"BH-FDR across the two published panels separately for each null family",
        "joint_support_rule":"spatial-spin BH q < 0.05 AND coexpression-profile gene-null BH q < 0.05",
        "primary_results":primary,"donor_lodo":lodo,"bilateral_sensitivity":sens,
        "guardrails":[
            "This validation cannot change the earlier frozen GABA/serotonin null.",
            "A size-matched-only signal is insufficient for support.",
            "Donor and bilateral sensitivities describe robustness and cannot rescue a failed primary joint test.",
            "The cortical phenotype is a deterministic forward-sensitivity-weighted back-projection, not anatomical source localization.",
            "AHBA is a six-donor population transcriptomic prior, not participant molecular measurement."
        ],
        "any_jointly_supported":bool(any(r["jointly_supported"] for r in primary))
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"completed","results":[{"panel_id":r["panel_id"],"rho":r["observed_spearman"],"spin_q":r["spatial_spin_bh_q_2_panels"],"coex_q":r["coexpression_profile_gene_bh_q_2_panels"],"joint":r["jointly_supported"]} for r in primary]},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())

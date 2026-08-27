#!/usr/bin/env python3
"""Test two independently frozen literature-defined language gene panels against the frozen DK68 NeuroSem semantic map."""
from __future__ import annotations
import argparse, csv, itertools, json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.transform import Rotation
from scipy.stats import rankdata

DONOR_IDS=["9861","10021","12876","14380","15496","15697"]

def jload(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def zvec(x):
    x=np.asarray(x,float); s=x.std(ddof=0)
    if not np.isfinite(x).all() or not np.isfinite(s) or s<=0: raise RuntimeError("degenerate vector")
    return (x-x.mean())/s

def zcols(X):
    X=np.asarray(X,float); mu=X.mean(0,keepdims=True); sd=X.std(0,ddof=0,keepdims=True)
    if not np.isfinite(X).all() or np.any(sd<=0): raise RuntimeError("invalid expression matrix")
    return (X-mu)/sd

def pearson(a,b): return float(np.mean(zvec(a)*zvec(b)))
def spearman(a,b): return pearson(rankdata(a),rankdata(b))
def fisher(r): return float(np.arctanh(np.clip(r,-0.999999,0.999999)))
def bh(p):
    p=np.asarray(p,float); n=len(p); o=np.argsort(p); q=p[o]*n/np.arange(1,n+1); q=np.minimum.accumulate(q[::-1])[::-1]; out=np.empty(n); out[o]=np.clip(q,0,1); return out

def signflip_p(z):
    z=np.asarray(z,float); obs=abs(z.mean()); vals=[]
    for signs in itertools.product((-1.0,1.0),repeat=len(z)): vals.append(abs(np.mean(z*np.asarray(signs))))
    vals=np.asarray(vals); return float(np.mean(vals>=obs-1e-15))

def donor_mean(stack,keep):
    sub=stack[keep]; c=np.sum(np.isfinite(sub),0); s=np.nansum(sub,0)
    with np.errstate(divide="ignore",invalid="ignore"): return s/c

def read_expression(root):
    d=Path(root)/"primary_leftright"; genes=[str(x) for x in jload(d/"gene_symbols.json")]; region_ids=[int(x) for x in jload(d/"region_ids.json")]
    donor_ids=[str(x) for x in jload(d/"donor_ids.json")]; files={str(k):str(v) for k,v in jload(d/"donor_files.json").items()}
    if donor_ids!=DONOR_IDS or len(region_ids)!=68: raise RuntimeError("unexpected expression bundle")
    mats=[]
    for did in donor_ids:
        with np.load(d/files[did],allow_pickle=False) as z: a=np.asarray(z["expression"],float)
        if a.shape!=(68,len(genes)) or np.isinf(a).any(): raise RuntimeError(f"bad donor matrix {did}")
        mats.append(a)
    stack=np.stack(mats,0); pop=donor_mean(stack,np.ones(6,bool))
    if not np.isfinite(pop).all(): raise RuntimeError("population expression incomplete")
    return genes,region_ids,stack,pop

def read_population(path,region_ids):
    rows=list(csv.DictReader(Path(path).open("r",encoding="utf-8-sig",newline=""))); by={int(r["parcel_id"]):r for r in rows}
    if set(by)!=set(region_ids): raise RuntimeError("population parcel mismatch")
    y=np.asarray([float(by[i]["mean_semantic_contribution_backprojection"]) for i in region_ids]); hemis=[by[i]["hemisphere"] for i in region_ids]
    return y,hemis

def read_participants(path,region_ids):
    rows=list(csv.DictReader(Path(path).open("r",encoding="utf-8-sig",newline=""))); subs=sorted({r["subject"] for r in rows})
    if len(subs)!=9: raise RuntimeError("expected 9 participants")
    out={}
    for s in subs:
        rr={int(r["parcel_id"]):r for r in rows if r["subject"]==s}
        if set(rr)!=set(region_ids): raise RuntimeError(f"participant parcel mismatch {s}")
        out[s]=np.asarray([float(rr[i]["semantic_contribution_backprojection"]) for i in region_ids])
    return subs,out

def parcel_sphere_centroids(source_freeze,vertex_map,region_ids):
    src=jload(source_freeze); fs=Path(src["template_resources"]["fsaverage_dir"])
    import nibabel.freesurfer.io as fsio
    lh,_=fsio.read_geometry(str(fs/"surf"/"lh.sphere")); rh,_=fsio.read_geometry(str(fs/"surf"/"rh.sphere"))
    rows=list(csv.DictReader(Path(vertex_map).open("r",encoding="utf-8-sig",newline=""))); by={i:[] for i in region_ids}
    for r in rows:
        if r["mapped_to_dk68"].strip().lower()!="true": continue
        pid=int(r["parcel_id"]); v=int(r["surface_vertex"]); xyz=(lh if r["hemisphere"]=="lh" else rh)[v]; by[pid].append(xyz/np.linalg.norm(xyz))
    C=[]
    for pid in region_ids:
        c=np.mean(by[pid],0); C.append(c/np.linalg.norm(c))
    return np.vstack(C)

def make_spins(C,hemis,n,seed):
    rng=np.random.default_rng(seed); hemis=np.asarray(hemis); L=np.where(hemis=="lh")[0]; Ridx=np.where(hemis=="rh")[0]
    if len(L)!=34 or len(Ridx)!=34: raise RuntimeError("expected 34 parcels per hemisphere")
    out=np.empty((n,len(C)),dtype=np.int16)
    for k in range(n):
        rot=Rotation.random(random_state=rng).as_matrix(); perm=np.empty(len(C),int)
        for idx in (L,Ridx):
            xyz=C[idx]@rot.T; cost=1.0-xyz@C[idx].T; a,b=linear_sum_assignment(cost); perm[idx[a]]=idx[b]
        out[k]=perm
    return out

def mean_internal_corr(X,idx):
    A=X[:,idx]; C=np.corrcoef(A,rowvar=False); u=C[np.triu_indices(len(idx),1)]; return float(np.mean(u)) if len(u) else 0.0

def coexpr_null(X,y,n_genes,target_corr,n_null,seed):
    rng=np.random.default_rng(seed); G=X.shape[1]; pool=[]; n_candidates=max(50000,n_null*10)
    for _ in range(n_candidates):
        idx=rng.choice(G,size=n_genes,replace=False); mc=mean_internal_corr(X,idx); r=spearman(X[:,idx].mean(1),y); pool.append((abs(mc-target_corr),mc,r))
    pool.sort(key=lambda t:t[0]); chosen=pool[:n_null]
    return np.asarray([x[2] for x in chosen]),np.asarray([x[1] for x in chosen]),float(chosen[-1][0])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parcel-summary",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/summary.json"))
    ap.add_argument("--population-target",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/population_parcel_target.csv"))
    ap.add_argument("--participant-target",type=Path,default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest/participant_parcel_target.csv"))
    ap.add_argument("--panel-summary",type=Path,default=Path("outputs/published_language_gene_panels_v2/latest/summary.json"))
    ap.add_argument("--panels",type=Path,default=Path("outputs/published_language_gene_panels_v2/latest/gene_panels.json"))
    ap.add_argument("--expression-root",type=Path,default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--source-freeze",type=Path,default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"))
    ap.add_argument("--vertex-map",type=Path,default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/vertex_parcel_map.csv"))
    ap.add_argument("--spins",type=int,default=5000); ap.add_argument("--random-sets",type=int,default=5000); ap.add_argument("--seed",type=int,default=20260827)
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/ahba_published_language_panel_association_v1/latest")); args=ap.parse_args()
    if (args.spins,args.random_sets,args.seed)!=(5000,5000,20260827): raise SystemExit("frozen design requires 5000 spins, 5000 random sets, seed 20260827")
    ps=jload(args.parcel_summary); gs=jload(args.panel_summary); panels=jload(args.panels)
    if not ps.get("ready_for_exploratory_transcriptomics",False): raise RuntimeError("parcel target not ready")
    if not gs.get("ready_for_independent_language_gene_validation",False): raise RuntimeError("panel freeze not ready")
    genes,region_ids,stack,pop=read_expression(args.expression_root); gix={g:i for i,g in enumerate(genes)}; X=zcols(pop)
    y,hemis=read_population(args.population_target,region_ids); subs,ymap=read_participants(args.participant_target,region_ids)
    C=parcel_sphere_centroids(args.source_freeze,args.vertex_map,region_ids); spins=make_spins(C,hemis,args.spins,args.seed)
    results=[]; participant_rows=[]; donor_rows=[]; null_rows=[]
    panel_items=panels["panels"] if isinstance(panels,dict) and "panels" in panels else panels
    for pi,(pid,pobj) in enumerate(panel_items.items()):
        pgenes=list(pobj) if isinstance(pobj,list) else pobj.get("retained_primary_ahba_genes",pobj.get("genes",pobj.get("published_genes")))
        if not pgenes: raise RuntimeError(f"no genes for {pid}")
        if any(g not in gix for g in pgenes): raise RuntimeError(f"panel gene missing from expression {pid}")
        idx=[gix[g] for g in pgenes]; v=X[:,idx].mean(1); obs=spearman(v,y)
        sn=np.asarray([abs(spearman(v,y[p])) for p in spins]); spin_p=float((1+np.sum(sn>=abs(obs)))/(args.spins+1))
        pr=[]
        for s in subs:
            r=spearman(v,ymap[s]); z=fisher(r); pr.append(z); participant_rows.append({"panel":pid,"subject":s,"spearman":r,"fisher_z":z})
        sign_p=signflip_p(pr); mean_z=float(np.mean(pr)); mean_r=float(np.mean([np.tanh(z) for z in pr]))
        tc=mean_internal_corr(X,idx); rn,rc,tol=coexpr_null(X,y,len(idx),tc,args.random_sets,args.seed+1000+pi)
        gene_p=float((1+np.sum(np.abs(rn)>=abs(obs)))/(args.random_sets+1))
        for j,(r,mc) in enumerate(zip(rn,rc)): null_rows.append({"panel":pid,"null_index":j,"spearman":float(r),"mean_internal_gene_correlation":float(mc)})
        for di,did in enumerate(DONOR_IDS):
            keep=np.ones(6,bool); keep[di]=False; m=donor_mean(stack,keep)
            if not np.isfinite(m).all(): donor_rows.append({"panel":pid,"excluded_donor":did,"status":"incomplete_full_68","spearman":""}); continue
            Xl=zcols(m); donor_rows.append({"panel":pid,"excluded_donor":did,"status":"written","spearman":spearman(Xl[:,idx].mean(1),y)})
        results.append({"panel":pid,"n_genes":len(idx),"population_spearman":obs,"spin_p_two_sided":spin_p,"participant_mean_fisher_z":mean_z,"participant_mean_spearman":mean_r,"participant_signflip_p_two_sided":sign_p,"target_mean_internal_gene_correlation":tc,"coexpression_matched_random_p_two_sided":gene_p,"coexpression_match_max_abs_difference":tol})
    q=bh([r["spin_p_two_sided"] for r in results])
    for r,qq in zip(results,q):
        r["spin_bh_q_two_panels"]=float(qq); r["positive_claim_gate"]=bool(qq<0.05 and r["participant_signflip_p_two_sided"]<0.05 and r["coexpression_matched_random_p_two_sided"]<0.05)
    out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    def write_csv(name,rows):
        with (out/name).open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    write_csv("panel_results.csv",results); write_csv("participant_results.csv",participant_rows); write_csv("donor_lodo.csv",donor_rows); write_csv("coexpression_matched_nulls.csv",null_rows)
    summary={"schema_version":1,"analysis":"independent published language-panel AHBA association v1","n_panels":2,"n_subjects":9,"n_parcels":68,"n_spins":5000,"n_coexpression_matched_random_sets":5000,"seed":20260827,"primary_spatial_test":"two-sided Spearman between each frozen panel mean standardized AHBA expression map and frozen population DK68 semantic map, hemisphere-constrained spherical rotations","participant_inference":"exact two-sided sign-flip of participant Fisher-z Spearman associations","multiplicity":"BH-FDR across the two frozen literature panels for spatial spin p-values","gene_set_null":"size-matched random gene sets chosen as the 5000 closest among at least 50000 candidates to the observed panel mean internal cortical expression correlation","positive_claim_rule":"spin BH q < 0.05 AND participant sign-flip p < 0.05 AND co-expression-matched random-set p < 0.05","results":results,"claim_ready":any(r["positive_claim_gate"] for r in results),"guardrails":["Do not alter either panel after seeing these outcomes.","Treat the two panels as exploratory independent literature-defined hypotheses, separate from the frozen GABA/serotonin null.","A positive association would be spatial correspondence with a six-donor population postmortem transcriptomic prior, not causal or participant-level molecular evidence."]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"completed","results":results},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())

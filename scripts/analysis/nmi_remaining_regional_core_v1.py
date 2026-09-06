#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, json, math, os, sys, time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import nibabel as nib
import numpy as np
from scipy.signal import fftconvolve
from scipy.spatial.distance import pdist

from scripts.analysis.run_smn4lang_fmri_reliability import STORIES, SUBJECTS, TR, canonical_hrf, fisher_mean, residualize
from scripts.analysis.run_smn4lang_regional_fmri_reliability_v1 import load_and_validate_preflight, region_rdm_from_loaded_bold
from scripts.audit.preflight_smn4lang_regional_atlases_v1 import affine_equal
from scripts.robustness.run_nmi_bidirectional_model_family_panel_v1 import MODEL_SPECS, SEEDS, load_adapter_generic, model_prefix, pooled_embeddings
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import safe_spearman, story_context
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import TEXT_ONLY_ADAPTER, encode_texts, load_adapter

ROOT = Path("outputs/nmi_remaining_regional_ideas_v1/latest")
CACHE = Path("outputs/nmi_remaining_regional_ideas_v1/cache_selected_regions")
PREFLIGHT_DIR = Path("outputs/smn4lang_regional_atlas_preflight_v1/latest")
MAIN_REGIONAL = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
MODEL_PANEL_ROOT = Path("outputs/nmi_bidirectional_model_family_panel_v1")
MODEL_RESOLVED = MODEL_PANEL_ROOT / "latest/resolved_models.json"
BOOTSTRAP_SEED = 20260906
N_BOOT = 10_000
FUNCTIONAL_LANGUAGE = ("IFG", "IFGorb", "MFG", "AntTemp", "PostTemp", "AngG")
FUNCTIONAL_FRONTAL = ("IFG", "IFGorb", "MFG")
FUNCTIONAL_TEMPORAL = ("AntTemp", "PostTemp")
LEFT_SENSORIMOTOR = ("precentral", "postcentral", "paracentral")
LEFT_VISUAL = ("pericalcarine", "cuneus", "lingual", "lateraloccipital")
POOLED_CONTROL = LEFT_SENSORIMOTOR + LEFT_VISUAL
DOSES = (0.01, 0.03, 0.10, 0.30, 1.00)
NEW_DOSES = (0.01, 0.03, 0.30, 1.00)
DOSE_LABEL = {0.01:"lambda_0p01",0.03:"lambda_0p03",0.10:"lambda_0p10",0.30:"lambda_0p30",1.00:"lambda_1"}
DOSE_ROOT = {
    0.01: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural"),
    0.03: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural"),
    0.30: Path("outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural"),
    1.00: Path("outputs/e5_neural_tuning_v1/neural"),
}

def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f: return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows: raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def atomic_progress(current:int,total:int,phase:str,message:str="") -> None:
    raw=os.environ.get("RUNRELAY_PROGRESS_FILE","").strip()
    if not raw: return
    p=Path(raw); p.parent.mkdir(parents=True, exist_ok=True)
    d={"schema_version":1,"current":int(current),"total":int(total),"fraction":float(current/total) if total else None,"phase":phase,"message":message,"unit":"frozen-condition stages","updated_at_epoch":time.time()}
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d),encoding="utf-8"); os.replace(t,p)

def exact_two_sided_signflip_p(values:np.ndarray)->float:
    x=np.asarray(values,float); obs=abs(float(x.mean())); ge=0; total=1<<len(x)
    for bits in range(total):
        signs=np.ones(len(x),float)
        for j in range(len(x)):
            if (bits>>j)&1: signs[j]=-1.0
        if abs(float(np.mean(x*signs)))>=obs-1e-15: ge+=1
    return ge/total

def exact_maxstat_p(matrix:np.ndarray)->np.ndarray:
    x=np.asarray(matrix,float); obs=np.abs(np.mean(x,axis=0)); null=np.empty(1<<x.shape[0],float)
    for bits in range(1<<x.shape[0]):
        signs=np.ones(x.shape[0],float)
        for j in range(x.shape[0]):
            if (bits>>j)&1: signs[j]=-1.0
        null[bits]=float(np.max(np.abs(np.mean(x*signs[:,None],axis=0))))
    return np.asarray([np.mean(null>=v-1e-15) for v in obs],float)

def bootstrap_ci(values:np.ndarray)->tuple[float,float]:
    x=np.asarray(values,float); rng=np.random.default_rng(BOOTSTRAP_SEED); idx=rng.integers(0,len(x),size=(N_BOOT,len(x))); m=x[idx].mean(axis=1)
    return float(np.percentile(m,2.5)),float(np.percentile(m,97.5))

def latest_completed_adapter(root:Path)->Path:
    c=[]
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and (d/"summary.json").is_file() and (d/"adapter").is_dir(): c.append(d)
    if not c: raise FileNotFoundError(f"no completed adapter under {root}")
    return sorted(c)[-1]/"adapter"

def selected_region_meta(data_root:Path):
    regions,shape,affine,preflight_hash=load_and_validate_preflight(data_root,PREFLIGHT_DIR.resolve()); selected=[]
    for r in regions:
        family,hemi,name=str(r["family"]),str(r["hemisphere"]),str(r["region_name"])
        if (family=="language" and name in FUNCTIONAL_LANGUAGE) or (family=="dk68" and hemi=="L" and name in POOLED_CONTROL): selected.append(r)
    if sum(str(r["family"])=="language" for r in selected)!=6 or sum(str(r["family"])=="dk68" for r in selected)!=7: raise RuntimeError("selected regional system count mismatch")
    return selected,shape,affine,preflight_hash

def build_selected_neural_cache(data_root:Path):
    CACHE.mkdir(parents=True,exist_ok=True); selected,shape,affine,_=selected_region_meta(data_root)
    meta=[{"index":i,"region_key":str(r["key"]),"family":str(r["family"]),"hemisphere":str(r["hemisphere"]),"region_name":str(r["region_name"])} for i,r in enumerate(selected)]
    (CACHE/"region_index.json").write_text(json.dumps({"subjects":list(SUBJECTS),"regions":meta},indent=2)+"\n",encoding="utf-8")
    hrf=canonical_hrf(TR); contexts={story:story_context(data_root,story,hrf) for story in STORIES}
    for si,story in enumerate(STORIES,1):
        out=CACHE/f"story_{story:02d}.npz"
        if out.exists(): continue
        ctx=contexts[story]; valid_idx=np.asarray(ctx["valid_idx"],int); iu=np.triu_indices(len(valid_idx),k=1); payload={}
        for subj_i,sub in enumerate(SUBJECTS):
            p=data_root/f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"; img=nib.load(str(p))
            if tuple(img.shape[:3])!=shape or not affine_equal(img.affine,affine): raise RuntimeError(f"{sub} story {story}: grid mismatch")
            data=np.asarray(img.get_fdata(dtype=np.float32),dtype=np.float32)
            for ri,region in enumerate(selected):
                neural,_,reason=region_rdm_from_loaded_bold(data,np.asarray(region["mask"],bool),valid_idx,iu)
                if neural is None: raise RuntimeError(f"{sub} story {story} region {region['key']}: {reason}")
                payload[f"s{subj_i:02d}_r{ri:02d}"]=residualize(neural,ctx["nuisance"]).astype(np.float32)
            del data
        np.savez_compressed(out,**payload); atomic_progress(si,len(STORIES)+22,"regional-neural-cache",f"cached story {story}/60")
    return meta,contexts

def e5_model_residual(model,tok,ctx,device,hrf):
    emb=encode_texts(model,tok,ctx["prefixes"],device); events=np.zeros((ctx["n_tp"],emb.shape[1]),np.float64)
    for start,vec in zip(ctx["starts"],emb,strict=True):
        idx=int(math.floor(float(start)/TR))
        if 0<=idx<ctx["n_tp"]: events[idx]+=vec
    drive=fftconvolve(events,hrf[:,None],mode="full",axes=0)[:ctx["n_tp"]]; return residualize(pdist(drive[ctx["valid_idx"]],metric="cosine"),ctx["nuisance"])

def generic_model_residual(model,tok,ctx,device,prefix,hrf):
    emb=pooled_embeddings(model,tok,ctx["prefixes"],device,prefix,8,grad=False).detach().cpu().numpy(); events=np.zeros((ctx["n_tp"],emb.shape[1]),np.float64)
    for start,vec in zip(ctx["starts"],emb,strict=True):
        idx=int(math.floor(float(start)/TR))
        if 0<=idx<ctx["n_tp"]: events[idx]+=vec
    drive=fftconvolve(events,hrf[:,None],mode="full",axes=0)[:ctx["n_tp"]]; return residualize(pdist(drive[ctx["valid_idx"]],metric="cosine"),ctx["nuisance"])

def aggregate_regional_condition(condition:dict,device:str,meta:list[dict],contexts:dict[int,dict])->list[dict]:
    import torch
    hrf=canonical_hrf(TR); vals={ri:{sub:{"text":[],"neural":[]} for sub in SUBJECTS} for ri in range(len(meta))}
    if condition["kind"]=="e5_dose":
        loaders={"text":lambda:load_adapter(TEXT_ONLY_ADAPTER,device),"neural":lambda:load_adapter(condition["neural_adapter"],device)}
        residual_fn=lambda m,t,c:e5_model_residual(m,t,c,device,hrf)
    else:
        spec=MODEL_SPECS[condition["model_key"]]; revision=condition["revision"]; prefix=model_prefix(spec)
        loaders={"text":lambda:load_adapter_generic(spec,revision,condition["unit"]/"text/adapter",device),"neural":lambda:load_adapter_generic(spec,revision,condition["unit"]/"neural/adapter",device)}
        residual_fn=lambda m,t,c:generic_model_residual(m,t,c,device,prefix,hrf)
    for arm in ("text","neural"):
        tok,model=loaders[arm]()
        for story in STORIES:
            mr=residual_fn(model,tok,contexts[story])
            with np.load(CACHE/f"story_{story:02d}.npz") as cache:
                for si,sub in enumerate(SUBJECTS):
                    for ri in range(len(meta)): vals[ri][sub][arm].append(safe_spearman(cache[f"s{si:02d}_r{ri:02d}"],mr))
        del model
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    rows=[]
    for ri,rmeta in enumerate(meta):
        for sub in SUBJECTS:
            a0=fisher_mean(vals[ri][sub]["text"]); a1=fisher_mean(vals[ri][sub]["neural"])
            rows.append({"condition_family":condition["kind"],"condition":condition["label"],"dose":condition.get("dose",""),"model_key":condition.get("model_key",""),"seed":condition.get("seed",""),**{k:rmeta[k] for k in ("region_key","family","hemisphere","region_name")},"subject":sub,"text_rsa":a0,"neural_rsa":a1,"delta":a1-a0})
    return rows

def make_conditions():
    resolved=json.loads(MODEL_RESOLVED.read_text(encoding="utf-8")); conditions=[]
    for dose in NEW_DOSES: conditions.append({"kind":"e5_dose","label":DOSE_LABEL[dose],"dose":dose,"neural_adapter":latest_completed_adapter(DOSE_ROOT[dose])})
    for model_key in MODEL_SPECS:
        revision=str(resolved[model_key]["revision"])
        for seed in SEEDS:
            unit=MODEL_PANEL_ROOT/"units"/model_key/f"seed_{seed}"/"eeg_to_fmri"
            for arm in ("text","neural"):
                if not (unit/arm/"adapter").is_dir(): raise FileNotFoundError(unit/arm/"adapter")
            conditions.append({"kind":"model_family","label":f"{model_key}_seed_{seed}","model_key":model_key,"seed":seed,"revision":revision,"unit":unit})
    return conditions,resolved

def reuse_lambda010_rows()->list[dict]:
    keep=[]
    for r in read_csv(MAIN_REGIONAL/"participant_results.csv"):
        family,hemi,name=r["family"],r["hemisphere"],r["region_name"]
        if (family=="language" and name in FUNCTIONAL_LANGUAGE) or (family=="dk68" and hemi=="L" and name in POOLED_CONTROL):
            keep.append({"condition_family":"e5_dose","condition":"lambda_0p10","dose":0.10,"model_key":"","seed":"","region_key":r["region_key"],"family":family,"hemisphere":hemi,"region_name":name,"subject":r["subject"],"text_rsa":float(r["lambda_0_residual_rsa"]),"neural_rsa":float(r["lambda_0p10_residual_rsa"]),"delta":float(r["delta_0p10_minus_0"])})
    if len(keep)!=13*len(SUBJECTS): raise RuntimeError(f"unexpected lambda=.10 selected rows: {len(keep)}")
    return keep

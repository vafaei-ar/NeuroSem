#!/usr/bin/env python3
"""Stage 1 of the frozen NeuroSem target-compatibility mechanism project.

Evaluate the already-trained six-dose ChineseEEG E5 grid on the three reliable
boundary targets that did not previously have a full dose curve (DERCo, TMNRED,
Garnett Dream), with numerical reproduction gates at lambda=0 and lambda=.10.
Reuse the already-completed ZuCo and SMN4Lang fMRI six-dose curves unchanged.

No retraining, dose selection, target rescue, representation search, or new target
selection is performed.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROTOCOL = "docs/TARGET_COMPATIBILITY_MECHANISM_V1.md"
OUT = ROOT / "outputs" / "target_compatibility_dose_v1" / "latest"
FORWARD = ROOT / "outputs" / "nmi_forward_external_dose_characterization_v1" / "latest"

DOSES = [0.00, 0.01, 0.03, 0.10, 0.30, 1.00]
LABEL = {0.00:"lambda_0",0.01:"lambda_0p01",0.03:"lambda_0p03",0.10:"lambda_0p10",0.30:"lambda_0p30",1.00:"lambda_1"}
ADAPTERS = {
    0.00: ROOT / "outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter",
    0.01: ROOT / "outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural/20260823_192219/adapter",
    0.03: ROOT / "outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural/20260823_192323/adapter",
    0.10: ROOT / "outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/20260823_192425/adapter",
    0.30: ROOT / "outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural/20260823_192528/adapter",
    1.00: ROOT / "outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter",
}
REPRO_ATOL = 2e-10
BOOT_N = 10000
BOOT_SEED = 20260926

from scripts.tuning import evaluate_tmnred_e5_transfer_v1 as tmn
from scripts.tuning import evaluate_garnett_dream_e5_transfer_v1 as gar
from scripts.analysis import run_garnett_dream_primary_reliability as garrel


def atomic_progress(current:int,total:int,phase:str,message:str)->None:
    raw=os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p=Path(raw); p.parent.mkdir(parents=True,exist_ok=True)
    payload={"schema_version":1,"current":current,"total":total,
             "fraction":current/total if total else 0.0,"phase":phase,
             "message":message,"unit":"target dose curves","updated_at_epoch":time.time()}
    tmp=p.with_suffix(p.suffix+".tmp"); tmp.write_text(json.dumps(payload)+"\n",encoding="utf-8"); tmp.replace(p)


def read_csv(path:Path)->list[dict[str,str]]:
    with path.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path:Path,rows:list[dict])->None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)


def load_all_model_embeddings(texts:list[str],device:str)->tuple[dict[float,np.ndarray],dict[str,str]]:
    import torch
    out={}; provenance={}
    for dose in DOSES:
        adapter=ADAPTERS[dose]
        if not adapter.is_dir():
            raise FileNotFoundError(adapter)
        tok,model=tmn.load_adapter(adapter,device)
        out[dose]=tmn.encode_texts(model,tok,texts,device)
        provenance[str(dose)]=str(adapter.relative_to(ROOT))
        del model
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    return out,provenance


def bootstrap_ci(v:np.ndarray,seed:int=BOOT_SEED)->list[float]:
    v=np.asarray(v,float); rng=np.random.default_rng(seed)
    idx=rng.integers(0,len(v),size=(BOOT_N,len(v)))
    m=v[idx].mean(axis=1)
    q=np.quantile(m,[.025,.975]); return [float(q[0]),float(q[1])]


def signflip_two_sided(v:np.ndarray,seed:int=BOOT_SEED)->dict:
    v=np.asarray(v,float); n=len(v); obs=abs(float(v.mean()))
    if n <= 22:
        total=1<<n; extreme=0; chunk=1<<15; bitpos=np.arange(n,dtype=np.uint64)
        for start in range(0,total,chunk):
            stop=min(total,start+chunk)
            ids=np.arange(start,stop,dtype=np.uint64)[:,None]
            signs=np.where(((ids>>bitpos)&1)==1,1.0,-1.0)
            means=np.abs((signs@v)/n)
            extreme += int(np.count_nonzero(means >= obs-1e-15))
        return {"method":"exact","p_two_sided":float(extreme/total),"n_patterns":int(total)}
    rng=np.random.default_rng(seed); nperm=200000; ge=0; done=0
    while done<nperm:
        b=min(10000,nperm-done)
        signs=rng.choice(np.array([-1.0,1.0]),size=(b,n),replace=True)
        means=np.abs((signs*v[None,:]).mean(axis=1))
        ge += int(np.sum(means>=obs-1e-15)); done+=b
    return {"method":"monte_carlo","p_two_sided":float((ge+1)/(nperm+1)),"n_patterns":int(nperm),"seed":seed}


def summarize_participants(dataset:str,participant_rows:list[dict])->list[dict]:
    out=[]
    for dose in DOSES:
        rr=[r for r in participant_rows if math.isclose(float(r["lambda"]),dose)]
        if not rr: raise RuntimeError(f"{dataset}: missing dose {dose}")
        vals=np.asarray([float(r["delta_rsa_vs_lambda0"]) for r in rr],float)
        arm=np.asarray([float(r["dose_rsa"]) for r in rr],float)
        base=np.asarray([float(r["lambda_0_rsa"]) for r in rr],float)
        if dose==0:
            ci=[0.0,0.0]; sf={"method":"baseline","p_two_sided":1.0,"n_patterns":0}
        else:
            ci=bootstrap_ci(vals,BOOT_SEED+int(round(dose*1000)))
            sf=signflip_two_sided(vals,BOOT_SEED+int(round(dose*1000)))
        out.append({
            "dataset":dataset,"lambda":dose,"lambda_label":LABEL[dose],
            "n_participants":len(rr),
            "lambda_0_mean_rsa":float(base.mean()),"dose_mean_rsa":float(arm.mean()),
            "mean_delta_rsa":float(vals.mean()),"median_delta_rsa":float(np.median(vals)),
            "n_positive":int(np.sum(vals>0)),"fraction_positive":float(np.mean(vals>0)),
            "bootstrap_95ci_low":ci[0],"bootstrap_95ci_high":ci[1],
            "two_sided_signflip_p":sf["p_two_sided"],"signflip_method":sf["method"],
            "signflip_n_patterns":sf["n_patterns"],
        })
    return out


def assert_reproduction(dataset:str,new_rows:list[dict],old_path:Path,id_col:str,old0:str,old10:str,unit_col:str|None=None)->dict:
    old=read_csv(old_path)
    index={}
    for r in old:
        key=(r[id_col],r[unit_col]) if unit_col else (r[id_col],)
        index[key]=r
    errs0=[]; errs10=[]; missing=[]
    for r in new_rows:
        if float(r["lambda"]) not in (0.0,0.10): continue
        key=(str(r["subject"]),str(r[unit_col])) if unit_col else (str(r["subject"]),)
        o=index.get(key)
        if o is None:
            missing.append(key); continue
        col=old0 if float(r["lambda"])==0 else old10
        err=abs(float(r["dose_rsa"])-float(o[col]))
        (errs0 if float(r["lambda"])==0 else errs10).append(err)
    max0=max(errs0) if errs0 else float("inf"); max10=max(errs10) if errs10 else float("inf")
    passed=(not missing and max0<=REPRO_ATOL and max10<=REPRO_ATOL)
    if not passed:
        raise RuntimeError(f"{dataset} reproduction gate failed: max0={max0} max10={max10} missing={missing[:3]}")
    return {"dataset":dataset,"path":str(old_path.relative_to(ROOT)),"atol":REPRO_ATOL,
            "max_abs_error_lambda0":max0,"max_abs_error_lambda0p10":max10,"passed":True}


# ---------------- DERCo ----------------
DERCO_EVENT_RE=re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")
DERCO_ARTICLES=list(range(5))

def derco_parse_items(ep,article:int):
    inv={int(code):label for label,code in ep.event_id.items()}; out=[]
    for row_i,code in enumerate(ep.events[:,2].tolist()):
        m=DERCO_EVENT_RE.match(inv[int(code)])
        if not m: raise RuntimeError("unexpected DERCo event label")
        if int(m.group("article"))!=article: raise RuntimeError("DERCo article mismatch")
        out.append((int(m.group("stim_index")),m.group("word"),row_i))
    idx=[x[0] for x in out]
    if len(set(idx))!=len(idx) or any(b<=a for a,b in zip(idx,idx[1:])):
        raise RuntimeError("DERCo non-monotonic items")
    return out

def derco_zscore(x):
    mu=np.nanmean(x,axis=0,keepdims=True); sd=np.nanstd(x,axis=0,ddof=0,keepdims=True)
    sd=np.where((~np.isfinite(sd))|(sd==0),1.0,sd); return (x-mu)/sd

def derco_resid(y,X):
    beta,*_=np.linalg.lstsq(X,y,rcond=None); return y-X@beta

def derco_fisher(v):
    x=np.asarray(v,float); return float(np.tanh(np.mean(np.arctanh(np.clip(x,-.999999,.999999)))))

def derco_curve(device:str):
    import mne, torch
    root=ROOT/"data/raw/derco"
    rel=json.loads((ROOT/"outputs/derco_eeg_reliability/latest/summary.json").read_text())
    if rel.get("n_subjects")!=22 or rel.get("reliability_gate_pass") is not True:
        raise RuntimeError("DERCo reliability gate mismatch")
    subjects=sorted(p.name for p in root.iterdir() if p.is_dir() and p.name!="prediction")
    if len(subjects)!=22: raise RuntimeError("DERCo subject count mismatch")

    words={a:{} for a in DERCO_ARTICLES}
    for a in DERCO_ARTICLES:
        for s in subjects:
            ep=mne.read_epochs(root/s/f"article_{a}"/"preprocessed_epoch.fif",preload=False,verbose="ERROR")
            for idx,word,_ in derco_parse_items(ep,a):
                prev=words[a].get(idx)
                if prev is not None and prev.casefold()!=word.casefold(): raise RuntimeError("DERCo word conflict")
                words[a][idx]=word
    canonical={a:[(idx,words[a][idx]) for idx in sorted(words[a])] for a in DERCO_ARTICLES}
    flat=[w for a in DERCO_ARTICLES for _,w in canonical[a]]
    emb,prov=load_all_model_embeddings(flat,device)
    model={d:{} for d in DOSES}; off=0
    counts={a:len(canonical[a]) for a in DERCO_ARTICLES}
    for a in DERCO_ARTICLES:
        n=counts[a]
        for d in DOSES: model[d][a]=squareform(pdist(emb[d][off:off+n],metric="cosine"))
        off+=n
    posmap={a:{idx:i for i,(idx,_) in enumerate(canonical[a])} for a in DERCO_ARTICLES}

    unit_rows=[]; acc={s:{d:[] for d in DOSES} for s in subjects}
    for s in subjects:
        for a in DERCO_ARTICLES:
            ep=mne.read_epochs(root/s/f"article_{a}"/"preprocessed_epoch.fif",preload=False,verbose="ERROR")
            items=derco_parse_items(ep,a); indices=[x[0] for x in items]; words_i=[x[1] for x in items]; rows=[x[2] for x in items]
            data=ep.get_data(picks="eeg")[rows]
            feat=derco_zscore(np.mean(data,axis=2)); neural=pdist(feat,metric="correlation")
            positions=np.asarray(indices,float); lengths=np.asarray([len(w) for w in words_i],float)
            X=np.column_stack([np.ones(len(neural)),pdist(positions[:,None],metric="cityblock"),pdist(lengths[:,None],metric="cityblock")])
            nr=derco_resid(neural,X); canon_ix=np.asarray([posmap[a][idx] for idx in indices],int)
            for d in DOSES:
                mv=squareform(model[d][a][np.ix_(canon_ix,canon_ix)],checks=False)
                rho=float(spearmanr(nr,derco_resid(mv,X)).statistic)
                acc[s][d].append(rho)
                unit_rows.append({"dataset":"derco","subject":s,"article":a,"lambda":d,"dose_rsa":rho})
    participant=[]
    for s in subjects:
        vals={d:derco_fisher(acc[s][d]) for d in DOSES}; base=vals[0.0]
        for d in DOSES:
            participant.append({"dataset":"derco","subject":s,"lambda":d,"lambda_label":LABEL[d],
                                "lambda_0_rsa":base,"dose_rsa":vals[d],"delta_rsa_vs_lambda0":vals[d]-base})
    gate1=assert_reproduction("derco_article",unit_rows,ROOT/"outputs/derco_e5_transfer_v1/latest/participant_article_results.csv","subject","lambda_0_resid_rsa","lambda_0p10_resid_rsa","article")
    gate2=assert_reproduction("derco_participant",participant,ROOT/"outputs/derco_e5_transfer_v1/latest/participant_results.csv","subject","lambda_0_resid_rsa","lambda_0p10_resid_rsa")
    return participant, summarize_participants("derco",participant), [gate1,gate2], prov


# ---------------- TMNRED ----------------
def tmnred_curve(device:str):
    import torch
    root=ROOT/"data/raw/tmnred"
    freeze=json.loads((ROOT/"outputs/tmnred_representation_input_materialization/latest/summary.json").read_text())
    if freeze.get("ready_subjects_all_8_sessions")!=tmn.READY_SUBJECTS: raise RuntimeError("TMNRED cohort mismatch")
    blocks=tmn.stimulus_blocks(root/"derivatives/source material/source material.xlsx")
    flat=[t for s in tmn.SESSIONS for t in blocks[s]]
    emb,prov=load_all_model_embeddings(flat,device)
    model={d:{} for d in DOSES}; off=0
    for s in tmn.SESSIONS:
        for d in DOSES:
            model[d][s]=squareform(pdist(emb[d][off:off+50],metric="cosine"))
        off+=50
    unit=[]; acc={sub:{d:[] for d in DOSES} for sub in tmn.READY_SUBJECTS}
    for sub in tmn.READY_SUBJECTS:
        for ses in tmn.SESSIONS:
            arr,emap=tmn.load_signal(root,sub,ses); items=sorted(emap); epidx=[emap[i]-1 for i in items]
            feat=tmn.zscore_cols(tmn.row_mean_features(arr)[epidx,:]); neural=pdist(feat,metric="correlation")
            X=tmn.nuisance_for_items(items,blocks[ses]); nr=tmn.residualize(neural,X); ix=np.asarray(items,dtype=int)-1
            for d in DOSES:
                mv=squareform(model[d][ses][np.ix_(ix,ix)],checks=False)
                rho=tmn.safe_rho(nr,tmn.residualize(mv,X)); acc[sub][d].append(rho)
                unit.append({"dataset":"tmnred","subject":sub,"session":ses,"lambda":d,"dose_rsa":rho})
    participant=[]
    for sub in tmn.READY_SUBJECTS:
        vals={d:tmn.fisher_mean(acc[sub][d]) for d in DOSES}; base=vals[0.0]
        for d in DOSES:
            participant.append({"dataset":"tmnred","subject":sub,"lambda":d,"lambda_label":LABEL[d],
                                "lambda_0_rsa":base,"dose_rsa":vals[d],"delta_rsa_vs_lambda0":vals[d]-base})
    gate1=assert_reproduction("tmnred_session",unit,ROOT/"outputs/tmnred_e5_transfer_v1/latest/session_results.csv","subject","resid_lambda_0","resid_lambda_0p10","session")
    gate2=assert_reproduction("tmnred_participant",participant,ROOT/"outputs/tmnred_e5_transfer_v1/latest/subject_results.csv","subject","resid_lambda_0","resid_lambda_0p10")
    return participant,summarize_participants("tmnred",participant),[gate1,gate2],prov


# ---------------- Garnett Dream ----------------
def garnett_curve(device:str):
    import torch
    data_root=(ROOT/"data/raw/chineseeeg").resolve()
    freeze=json.loads((ROOT/"outputs/garnett_dream_input_materialization/latest/summary.json").read_text())
    if not freeze.get("freeze_gate",{}).get("ready_for_reliability"): raise RuntimeError("Garnett freeze not ready")
    expected={int(k):int(v) for k,v in freeze.get("chapter_item_counts",{}).items()}
    mapping=json.loads((ROOT/"outputs/garnett_dream_segmented_xlsx_mapping_probe_v1/latest/summary.json").read_text())
    texts_by_chapter,_=gar.load_frozen_texts(mapping,data_root,expected)
    text_nuis={ch:gar.text_nuisance_edges(texts_by_chapter[ch]) for ch in range(1,19)}
    flat=[t for ch in range(1,19) for t in texts_by_chapter[ch]]
    emb,prov=load_all_model_embeddings(flat,device)
    model={d:{} for d in DOSES}; off=0
    for ch in range(1,19):
        n=len(texts_by_chapter[ch])
        for d in DOSES: model[d][ch]=pdist(emb[d][off:off+n],metric="cosine")
        off+=n

    inventory=garrel.read_csv(ROOT/"outputs/garnett_dream_input_materialization/latest/session_inventory.csv")
    items=garrel.read_csv(ROOT/"outputs/garnett_dream_input_materialization/latest/item_identity.csv")
    vhdrs=garrel.companion_vhdr_by_run(inventory); items_by_key=defaultdict(list)
    for r in items: items_by_key[(str(r["subject"]),int(r["run"]),int(r["chapter"]))].append(r)
    acc=defaultdict(lambda:{d:[] for d in DOSES}); unit=[]
    for key,vhdr_rel in sorted(vhdrs.items(),key=lambda kv:(kv[0][2],kv[0][0])):
        sub,_,ch=key
        feats,durations,_=garrel.features_for_run(data_root,vhdr_rel,items_by_key[key])
        x=feats["row_mean_all"]; n=expected[ch]
        if x.shape[0]!=n: raise RuntimeError("Garnett item count mismatch")
        neural=garrel.rdm_from_features(x); duration=pdist(np.asarray(durations,float)[:,None],metric="cityblock"); tn=text_nuis[ch]
        nuis=[tn["order"],duration,tn["character_count"],tn["punctuation_count"],tn["character_set_jaccard"]]
        nr=garrel.residualize(neural,nuis)
        for d in DOSES:
            mr=garrel.residualize(model[d][ch],nuis); rho=gar.safe_rho(nr,mr)
            acc[sub][d].append(rho); unit.append({"dataset":"garnett_dream","subject":sub,"chapter":ch,"lambda":d,"dose_rsa":rho})
    subjects=sorted(acc)
    participant=[]
    for sub in subjects:
        vals={d:garrel.fisher_mean(acc[sub][d]) for d in DOSES}; base=vals[0.0]
        for d in DOSES:
            participant.append({"dataset":"garnett_dream","subject":sub,"lambda":d,"lambda_label":LABEL[d],
                                "lambda_0_rsa":base,"dose_rsa":vals[d],"delta_rsa_vs_lambda0":vals[d]-base})
    gate1=assert_reproduction("garnett_chapter",unit,ROOT/"outputs/garnett_dream_e5_transfer_v1/latest/chapter_results.csv","subject","lambda_0_resid_rsa","lambda_0p10_resid_rsa","chapter")
    gate2=assert_reproduction("garnett_participant",participant,ROOT/"outputs/garnett_dream_e5_transfer_v1/latest/subject_results.csv","subject","lambda_0_resid_rsa","lambda_0p10_resid_rsa")
    return participant,summarize_participants("garnett_dream",participant),[gate1,gate2],prov


def main()->int:
    import torch
    OUT.mkdir(parents=True,exist_ok=True)
    for d,p in ADAPTERS.items():
        if not p.is_dir(): raise FileNotFoundError(p)
    if not (FORWARD/"participant_dose_results.csv").is_file() or not (FORWARD/"dose_summary.csv").is_file():
        raise FileNotFoundError("completed ZuCo/SMN4Lang dose characterization missing")
    device="cuda" if torch.cuda.is_available() else "cpu"
    total=3; atomic_progress(0,total,"derco","starting DERCo fixed dose curve")

    all_part=[]; all_sum=[]; gates=[]; provenance={}
    p,s,g,pr=derco_curve(device); all_part+=p; all_sum+=s; gates+=g; provenance["derco"]=pr
    atomic_progress(1,total,"tmnred","DERCo complete; starting TMNRED")
    p,s,g,pr=tmnred_curve(device); all_part+=p; all_sum+=s; gates+=g; provenance["tmnred"]=pr
    atomic_progress(2,total,"garnett","TMNRED complete; starting Garnett Dream")
    p,s,g,pr=garnett_curve(device); all_part+=p; all_sum+=s; gates+=g; provenance["garnett_dream"]=pr
    atomic_progress(3,total,"complete","all new boundary-target dose curves complete")

    # Reuse already-completed positive-target full curves unchanged.
    prior_part=read_csv(FORWARD/"participant_dose_results.csv")
    prior_sum=read_csv(FORWARD/"dose_summary.csv")
    for r in prior_part:
        all_part.append({
            "dataset":r["dataset"],"subject":r["subject"],"lambda":float(r["lambda"]),
            "lambda_label":r["lambda_label"],"lambda_0_rsa":float(r["lambda_0_rsa"]),
            "dose_rsa":float(r["dose_rsa"]),"delta_rsa_vs_lambda0":float(r["delta_rsa_vs_lambda0"])
        })
    for r in prior_sum:
        all_sum.append({
            "dataset":r["dataset"],"lambda":float(r["lambda"]),"lambda_label":r["lambda_label"],
            "n_participants":int(r["n_participants"]),"lambda_0_mean_rsa":float(r["lambda_0_mean_rsa"]),
            "dose_mean_rsa":float(r["dose_mean_rsa"]),"mean_delta_rsa":float(r["mean_delta_rsa"]),
            "median_delta_rsa":float(r["median_delta_rsa"]),"n_positive":int(r["n_positive"]),
            "fraction_positive":float(r["fraction_positive"]),
            "bootstrap_95ci_low":float(r["bootstrap_95ci_low"]),"bootstrap_95ci_high":float(r["bootstrap_95ci_high"]),
            "two_sided_signflip_p":float(r["exact_two_sided_signflip_p"]),
            "signflip_method":"exact_reused","signflip_n_patterns":int(r["n_sign_patterns"]),
        })

    all_sum.sort(key=lambda r:(r["dataset"],float(r["lambda"])))
    all_part.sort(key=lambda r:(r["dataset"],str(r["subject"]),float(r["lambda"])))
    write_csv(OUT/"participant_dose_results.csv",all_part)
    write_csv(OUT/"dose_summary.csv",all_sum)
    (OUT/"reproduction_gates.json").write_text(json.dumps(gates,indent=2)+"\n",encoding="utf-8")
    payload={
        "schema_version":1,"status":"ok","analysis_stage":"post-confirmatory target-compatibility stage-1 dose curves",
        "protocol":PROTOCOL,"grid":DOSES,
        "historical_target_classes":{"zuco":"reliable-positive","smn4lang_fmri":"reliable-positive",
            "derco":"reliable-negative","tmnred":"reliable-null/inconclusive","garnett_dream":"reliable-null/inconclusive"},
        "newly_evaluated_targets":["derco","tmnred","garnett_dream"],
        "reused_completed_targets":["zuco","smn4lang_fmri"],
        "all_reproduction_gates_passed":bool(all(x["passed"] for x in gates)),
        "reproduction_gates":gates,"adapter_provenance":provenance,
        "dose_summary":all_sum,
        "guardrails":["No model retraining.","No target-specific dose selection.","No representation/nuisance/participant/item rescue.",
                      "Lambda=0 and .10 outputs reproduced before accepting new boundary-target dose values.",
                      "Complete six-dose curves retained for all five reliable targets."]
    }
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text("Target-compatibility Stage 1 dose curves complete.\nAll reproduction gates passed.\n",encoding="utf-8")
    print(json.dumps({"status":"ok","out":str(OUT),"n_summary_rows":len(all_sum)},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

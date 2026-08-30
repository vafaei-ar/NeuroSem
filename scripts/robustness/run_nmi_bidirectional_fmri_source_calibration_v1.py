#!/usr/bin/env python3
from __future__ import annotations

import json, math, os, random, time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analysis.run_smn4lang_fmri_reliability import TR, canonical_hrf
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import story_context

MODEL_ID = "intfloat/multilingual-e5-large"
MODEL_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
PREFIX = "query: "
LAMBDAS = [0.0, 0.01, 0.03, 0.10, 0.30, 1.0]
SEED = 20260823
TRAIN_STORIES = [56,15,48,55,27,3,23,6,21,58,36,40,12,30,9,35,20,5,49,28]
VAL_STORIES = [2,7,11,16,22,26,34,37,38,41,45,50]
EPOCH_SCHEDULE = [TRAIN_STORIES[i:i+4] for i in range(0,20,4)]


def report_progress(current, total, phase):
    raw=os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw: return
    p=Path(raw); p.parent.mkdir(parents=True,exist_ok=True)
    d={"schema_version":1,"current":current,"total":total,"fraction":current/total,"phase":phase,"unit":"lambda-models","updated_at_epoch":time.time()}
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d),encoding="utf-8"); os.replace(t,p)


def set_seed(seed):
    random.seed(seed); np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def masked_mean(h,m):
    m=m.to(h.dtype).unsqueeze(-1); return (h*m).sum(1)/m.sum(1).clamp_min(1.)


def encode(model,tok,texts,device,max_length=64,batch_size=24):
    import torch
    xs=[]
    for i in range(0,len(texts),batch_size):
        b=[PREFIX+x for x in texts[i:i+batch_size]]
        e=tok(b,padding=True,truncation=True,max_length=max_length,return_tensors="pt")
        a=e["attention_mask"].to(device); e={k:v.to(device) for k,v in e.items()}
        o=model(**e,return_dict=True)
        x=masked_mean(o.last_hidden_state,a.bool()); x=torch.nn.functional.normalize(x,p=2,dim=1); xs.append(x)
    return torch.cat(xs,0)


def pairdist(x):
    import torch
    s=x@x.T; iu=torch.triu_indices(x.shape[0],x.shape[0],1,device=x.device); return 1-s[iu[0],iu[1]]


def z(x):
    return (x-x.mean())/x.std(unbiased=False).clamp_min(1e-8)


def residualize_torch(y,nuis):
    import torch
    cols=[torch.ones_like(y)]+[torch.as_tensor(v,dtype=y.dtype,device=y.device) for v in nuis]
    X=torch.stack(cols,1); beta=torch.linalg.lstsq(X,y[:,None]).solution[:,0]; return y-X@beta


def hrf_states(model,tok,ctx,device,hrf):
    import torch
    emb=encode(model,tok,ctx["prefixes"],device)
    n_tp=ctx["n_tp"]; d=emb.shape[1]
    events=torch.zeros((n_tp,d),dtype=emb.dtype,device=device)
    idx=torch.as_tensor([int(math.floor(float(s)/TR)) for s in ctx["starts"]],device=device)
    good=(idx>=0)&(idx<n_tp)
    events.index_add_(0,idx[good],emb[good])
    drive=torch.zeros_like(events)
    h=torch.as_tensor(hrf,dtype=events.dtype,device=device)
    for k in range(len(hrf)):
        if k>=n_tp: break
        drive[k:]+=events[:n_tp-k]*h[k]
    return torch.nn.functional.normalize(drive[torch.as_tensor(ctx["valid_idx"],device=device)],p=2,dim=1)


def neural_loss(model,tok,ctx,target,device,hrf):
    was=model.training; model.eval()
    states=hrf_states(model,tok,ctx,device,hrf)
    d=pairdist(states); d=residualize_torch(d,ctx["nuisance"]); d=z(d)
    t=__import__('torch').as_tensor(target,dtype=d.dtype,device=device)
    corr=(d*t).mean()
    if was: model.train()
    return 1-corr,corr


def text_loss(model,tok,prefixes,device,temp=0.05):
    import torch
    model.train(); n=min(32,len(prefixes)); ids=np.linspace(0,len(prefixes)-1,n,dtype=int); texts=[prefixes[int(i)] for i in ids]
    a=encode(model,tok,texts,device); b=encode(model,tok,texts,device)
    logits=(a@b.T)/temp; labels=torch.arange(n,device=device)
    return .5*(torch.nn.functional.cross_entropy(logits,labels)+torch.nn.functional.cross_entropy(logits.T,labels))


def main():
    import torch
    from transformers import AutoModel,AutoTokenizer
    from peft import LoraConfig,get_peft_model
    from torch.optim import AdamW

    device="cuda" if torch.cuda.is_available() else "cpu"
    if device!="cuda": raise RuntimeError("GPU required")
    source=Path("outputs/nmi_bidirectional_fmri_source_v1/latest")
    if not (source/"summary.json").exists(): raise FileNotFoundError(source/"summary.json")
    root=Path("data/raw/smn4lang").resolve(); hrf=canonical_hrf(TR)
    needed=sorted(set(TRAIN_STORIES+VAL_STORIES)); contexts={s:story_context(root,s,hrf) for s in needed}
    targets={}
    for s in needed:
        p=source/"targets"/f"story_{s:02d}.npz"
        if not p.exists(): raise FileNotFoundError(p)
        targets[s]=np.load(p)["target"].astype(np.float32)
    out=Path("outputs/nmi_bidirectional_fmri_calibration_v1/latest").resolve(); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for li,lam in enumerate(LAMBDAS,1):
        set_seed(SEED)
        tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=MODEL_REVISION)
        base=AutoModel.from_pretrained(MODEL_ID,revision=MODEL_REVISION)
        model=get_peft_model(base,LoraConfig(r=8,lora_alpha=16,lora_dropout=.05,target_modules=["query","value"],bias="none")); model.to(device)
        opt=AdamW([p for p in model.parameters() if p.requires_grad],lr=2e-4,weight_decay=.01)
        train_hist=[]
        for epoch,stories in enumerate(EPOCH_SCHEDULE,1):
            vals=[]
            for s in stories:
                opt.zero_grad(set_to_none=True)
                tl=text_loss(model,tok,contexts[s]["prefixes"],device)
                nl,c=neural_loss(model,tok,contexts[s],targets[s],device,hrf)
                loss=tl+lam*nl; loss.backward(); opt.step(); vals.append(float(c.detach().cpu()))
            train_hist.append({"epoch":epoch,"stories":stories,"mean_train_fmri_corr":float(np.mean(vals))})
        model.eval(); vc=[]
        with torch.no_grad():
            for s in VAL_STORIES:
                _,c=neural_loss(model,tok,contexts[s],targets[s],device,hrf); vc.append(float(c.detach().cpu()))
        mean=float(np.mean(vc)); se=float(np.std(vc,ddof=1)/np.sqrt(len(vc)))
        d=out/f"lambda_{str(lam).replace('.','p')}"; d.mkdir(exist_ok=True)
        model.save_pretrained(d/"adapter"); tok.save_pretrained(d/"adapter")
        rec={"lambda":lam,"validation_story_corrs":vc,"validation_mean":mean,"validation_se":se,"train_history":train_hist,"adapter":str((d/"adapter").resolve())}
        (d/"summary.json").write_text(json.dumps(rec,indent=2)+"\n"); rows.append(rec)
        del model,base; torch.cuda.empty_cache(); report_progress(li,len(LAMBDAS),f"Source-only lambda calibration {li}/{len(LAMBDAS)}")
    positive=[r for r in rows if r["lambda"]>0]; best=max(positive,key=lambda r:r["validation_mean"]); threshold=best["validation_mean"]-best["validation_se"]
    eligible=[r for r in positive if r["validation_mean"]>=threshold]; selected=min(eligible,key=lambda r:r["lambda"])
    zero=next(r for r in rows if r["lambda"]==0)
    gate=selected["validation_mean"]>zero["validation_mean"]
    summary={"schema_version":1,"analysis_stage":"post-confirmatory fMRI-source-only E5 calibration","protocol":"docs/18_NMI_BIDIRECTIONAL_FMRI_SOURCE_CALIBRATION_V1.md","model_id":MODEL_ID,"model_revision":MODEL_REVISION,"seed":SEED,"lambda_grid":LAMBDAS,"training_stories":TRAIN_STORIES,"validation_stories":VAL_STORIES,"results":rows,"selection_rule":"smallest positive lambda within 1 SE of best positive validation mean; proceed only if selected mean > lambda0 mean","best_positive_lambda":best["lambda"],"best_positive_mean":best["validation_mean"],"best_positive_se":best["validation_se"],"selected_lambda":selected["lambda"],"selected_validation_mean":selected["validation_mean"],"lambda0_validation_mean":zero["validation_mean"],"source_gate_pass":bool(gate),"external_eeg_read":False}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:summary[k] for k in ["selected_lambda","selected_validation_mean","lambda0_validation_mean","source_gate_pass"]},indent=2))

if __name__=="__main__": main()

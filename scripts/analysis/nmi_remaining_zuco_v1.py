#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scipy.spatial.distance import pdist

from scripts.analysis.nmi_remaining_regional_core_v1 import MODEL_SPECS, safe_spearman
from scripts.analysis.run_zuco2_nr_primary_representation_reliability import (
    EXPECTED,
    fisher_mean as zuco_fisher_mean,
    load_inventory,
    load_material_rows,
    load_run_features,
    nuisance_matrix,
    rdm_edges,
    residualize as zuco_residualize,
)
from scripts.robustness.run_nmi_bidirectional_model_family_panel_v1 import load_adapter_generic, model_prefix, pooled_embeddings


def evaluate_zuco_model_unit(model_key:str,revision:str,unit:Path,device:str)->list[dict]:
    import torch
    spec=MODEL_SPECS[model_key]
    data_root=Path("data/raw/zuco2_nr")
    input_freeze=Path("outputs/zuco2_nr_input_materialization/latest/summary.json")
    mapping_freeze=Path("outputs/zuco2_nr_format_probe/latest/summary.json")
    stimulus_root=Path("data/raw/zuco2_probe")
    cohort=json.loads(input_freeze.read_text()); mapping=json.loads(mapping_freeze.read_text()); ready=list(cohort.get("ready_subjects_all_7_runs") or [])
    if len(ready)!=17 or "YTL" in ready: raise RuntimeError("unexpected ZuCo cohort")
    maps={r["run"]:r for r in mapping.get("wordcount_mapping_diagnostics",[])}; inventory=load_inventory(input_freeze.parent/"session_inventory.csv"); path_by={}
    for r in inventory:
        if r.get("subject") in ready and str(r.get("ready","")).lower()=="true": path_by[(r["subject"],int(r["run"]))]=data_root.resolve()/r["osf_path"]
    nuis={}; flat=[]
    for run in range(1,8):
        rows=load_material_rows(stimulus_root/"task_materials"/f"nr_{run}.csv"); selected=maps[f"NR{run}"]["selected_material_rows_1based"]
        texts=[str(rows[i-1][2]).strip() for i in selected]; nuis[run]=nuisance_matrix(texts); flat.extend(texts)
    model_edges={}
    for arm in ("text","neural"):
        tok,model=load_adapter_generic(spec,revision,unit/arm/"adapter",device)
        emb=pooled_embeddings(model,tok,flat,device,model_prefix(spec),64,grad=False).detach().cpu().numpy(); model_edges[arm]={}; off=0
        for run in range(1,8):
            n=EXPECTED[run]; model_edges[arm][run]=pdist(emb[off:off+n],metric="cosine"); off+=n
        del model
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    by={s:{"text":[],"neural":[]} for s in ready}
    for sub in ready:
        for run in range(1,8):
            feats,_=load_run_features(path_by[(sub,run)],EXPECTED[run]); nr=zuco_residualize(rdm_edges(feats["row_mean_all"]),nuis[run])
            for arm in ("text","neural"):
                mr=zuco_residualize(model_edges[arm][run],nuis[run]); by[sub][arm].append(safe_spearman(nr,mr))
    out=[]
    for sub in ready:
        a0=zuco_fisher_mean(by[sub]["text"]); a1=zuco_fisher_mean(by[sub]["neural"])
        out.append({"subject":sub,"text_rsa":a0,"neural_rsa":a1,"delta":a1-a0})
    return out

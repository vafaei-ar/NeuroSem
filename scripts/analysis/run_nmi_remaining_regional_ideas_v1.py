#!/usr/bin/env python3
"""Frozen post-confirmatory remaining regional ideas suite."""
from __future__ import annotations

import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from scipy.stats import spearmanr

from scripts.analysis.nmi_remaining_regional_core_v1 import (
    DOSES, FUNCTIONAL_FRONTAL, FUNCTIONAL_LANGUAGE, FUNCTIONAL_TEMPORAL,
    LEFT_SENSORIMOTOR, LEFT_VISUAL, MAIN_REGIONAL, MODEL_RESOLVED,
    MODEL_SPECS, POOLED_CONTROL, PREFLIGHT_DIR, ROOT, SEEDS, STORIES, SUBJECTS,
    aggregate_regional_condition, atomic_progress, bootstrap_ci, build_selected_neural_cache,
    exact_maxstat_p, exact_two_sided_signflip_p, make_conditions, read_csv, reuse_lambda010_rows,
    sha256, write_csv,
)
from scripts.analysis.nmi_remaining_zuco_v1 import evaluate_zuco_model_unit

PROTOCOL="docs/29_NMI_REMAINING_REGIONAL_IDEAS_V1.md"
DOSE_SUMMARY=Path("outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv")


def system_rows_from_region_rows(region_rows:list[dict])->list[dict]:
    by={}
    for r in region_rows:
        key=(r["condition_family"],r["condition"],str(r.get("dose","")),str(r.get("model_key","")),str(r.get("seed","")),r["subject"])
        by.setdefault(key,{})[r["region_name"]]=float(r["delta"])
    out=[]
    for key,vals in by.items():
        missing=set(FUNCTIONAL_LANGUAGE+POOLED_CONTROL)-set(vals)
        if missing: raise RuntimeError(f"missing selected regions for {key}: {sorted(missing)}")
        language=float(np.mean([vals[n] for n in FUNCTIONAL_LANGUAGE])); motor=float(np.mean([vals[n] for n in LEFT_SENSORIMOTOR])); visual=float(np.mean([vals[n] for n in LEFT_VISUAL])); pooled=float(np.mean([vals[n] for n in POOLED_CONTROL])); temporal=float(np.mean([vals[n] for n in FUNCTIONAL_TEMPORAL])); frontal=float(np.mean([vals[n] for n in FUNCTIONAL_FRONTAL]))
        family,condition,dose,model_key,seed,sub=key
        out.append({"condition_family":family,"condition":condition,"dose":dose,"model_key":model_key,"seed":seed,"subject":sub,"language_mean_delta":language,"sensorimotor_mean_delta":motor,"visual_mean_delta":visual,"pooled_control_mean_delta":pooled,"language_specificity":language-pooled,"temporal_mean_delta":temporal,"frontal_mean_delta":frontal,"temporal_minus_frontal":temporal-frontal})
    return out


def summarize_dose(system_rows:list[dict]):
    dose_rows=[r for r in system_rows if r["condition_family"]=="e5_dose"]; by_dose={}
    for dose in DOSES:
        rr=[r for r in dose_rows if abs(float(r["dose"])-dose)<1e-12]; rr.sort(key=lambda r:r["subject"])
        if len(rr)!=len(SUBJECTS): raise RuntimeError(f"dose {dose}: expected 12 rows")
        by_dose[dose]=rr
    spec_mat=np.column_stack([[float(r["language_specificity"]) for r in by_dose[d]] for d in DOSES]); fwer=exact_maxstat_p(spec_mat); summaries=[]
    for j,dose in enumerate(DOSES):
        rr=by_dose[dose]; spec=np.asarray([float(r["language_specificity"]) for r in rr]); lang=np.asarray([float(r["language_mean_delta"]) for r in rr]); motor=np.asarray([float(r["sensorimotor_mean_delta"]) for r in rr]); visual=np.asarray([float(r["visual_mean_delta"]) for r in rr]); lo,hi=bootstrap_ci(spec)
        summaries.append({"lambda":dose,"language_mean_delta":float(lang.mean()),"sensorimotor_mean_delta":float(motor.mean()),"visual_mean_delta":float(visual.mean()),"language_specificity_mean":float(spec.mean()),"specificity_n_positive":int(np.sum(spec>0)),"specificity_ci_low":lo,"specificity_ci_high":hi,"specificity_exact_p":exact_two_sided_signflip_p(spec),"specificity_fwer_p_across_5_doses":float(fwer[j])})
    high=np.asarray([float(r["language_specificity"]) for r in by_dose[1.00]]); ref=np.asarray([float(r["language_specificity"]) for r in by_dose[0.10]]); diff=high-ref; lo,hi=bootstrap_ci(diff)
    interaction={"lambda1_minus_lambda010_specificity_change_mean":float(diff.mean()),"n_positive":int(np.sum(diff>0)),"bootstrap_ci_low":lo,"bootstrap_ci_high":hi,"exact_two_sided_signflip_p":exact_two_sided_signflip_p(diff)}
    return summaries,interaction


def parse_dose_external()->dict[float,dict]:
    rows=read_csv(DOSE_SUMMARY); out={}
    for d in DOSES:
        zuco=[r for r in rows if r["dataset"]=="zuco" and abs(float(r["lambda"])-d)<1e-12]; fmri=[r for r in rows if r["dataset"]=="smn4lang_fmri" and abs(float(r["lambda"])-d)<1e-12]
        if len(zuco)!=1 or len(fmri)!=1: raise RuntimeError(f"dose summary missing {d}")
        out[d]={"zuco_mean_delta":float(zuco[0]["mean_delta_rsa"]),"whole_fmri_mean_delta":float(fmri[0]["mean_delta_rsa"]),"sts_delta":float(zuco[0]["delta_external_sts_vs_lambda0_already_observed"])}
    return out


def summarize_model_family(system_rows:list[dict],zuco_rows:list[dict]):
    rr=[r for r in system_rows if r["condition_family"]=="model_family"]; zuco_by={}
    for r in zuco_rows: zuco_by.setdefault((r["model_key"],int(r["seed"])),[]).append(float(r["delta"]))
    seed_rows=[]
    for model_key in MODEL_SPECS:
        for seed in SEEDS:
            sub=[r for r in rr if r["model_key"]==model_key and int(r["seed"])==seed]; sub.sort(key=lambda r:r["subject"])
            if len(sub)!=len(SUBJECTS): raise RuntimeError(f"missing regional rows {model_key} {seed}")
            spec=np.asarray([float(r["language_specificity"]) for r in sub]); lang=np.asarray([float(r["language_mean_delta"]) for r in sub]); z=np.asarray(zuco_by[(model_key,seed)])
            seed_rows.append({"model_key":model_key,"model_class":MODEL_SPECS[model_key]["class"],"seed":seed,"language_mean_delta":float(lang.mean()),"language_specificity_mean":float(spec.mean()),"specificity_n_positive":int(np.sum(spec>0)),"specificity_exact_p":exact_two_sided_signflip_p(spec),"zuco_mean_delta":float(z.mean()),"zuco_n_positive":int(np.sum(z>0))})
    model_rows=[]; model_spec_vectors=[]
    for model_key in MODEL_SPECS:
        sr=[r for r in seed_rows if r["model_key"]==model_key]; spec_seed=np.asarray([float(r["language_specificity_mean"]) for r in sr]); lang_seed=np.asarray([float(r["language_mean_delta"]) for r in sr]); zuco_seed=np.asarray([float(r["zuco_mean_delta"]) for r in sr]); participant_avg=[]
        for sub in SUBJECTS:
            vals=[float(r["language_specificity"]) for r in rr if r["model_key"]==model_key and r["subject"]==sub]; participant_avg.append(float(np.mean(vals)))
        participant_avg=np.asarray(participant_avg); model_spec_vectors.append(participant_avg); lo,hi=bootstrap_ci(participant_avg)
        model_rows.append({"model_key":model_key,"model_class":MODEL_SPECS[model_key]["class"],"mean_language_delta_across_seeds":float(lang_seed.mean()),"mean_language_specificity_across_seeds":float(spec_seed.mean()),"all_3_seed_specificities_positive":bool(np.all(spec_seed>0)),"participant_avg_specificity_n_positive":int(np.sum(participant_avg>0)),"participant_avg_specificity_ci_low":lo,"participant_avg_specificity_ci_high":hi,"participant_avg_specificity_exact_p":exact_two_sided_signflip_p(participant_avg),"mean_zuco_delta_across_seeds":float(zuco_seed.mean())})
    fwer=exact_maxstat_p(np.column_stack(model_spec_vectors))
    for j,r in enumerate(model_rows): r["specificity_fwer_p_across_6_models"]=float(fwer[j])
    rho_lang=float(spearmanr([r["mean_zuco_delta_across_seeds"] for r in model_rows],[r["mean_language_delta_across_seeds"] for r in model_rows]).statistic); rho_spec=float(spearmanr([r["mean_zuco_delta_across_seeds"] for r in model_rows],[r["mean_language_specificity_across_seeds"] for r in model_rows]).statistic)
    return seed_rows,model_rows,{"model_level_spearman_zuco_vs_fmri_language":rho_lang,"model_level_spearman_zuco_vs_language_specificity":rho_spec,"n_models":6,"descriptive_only":True}


def make_figures(dose_rows,model_rows,dose_external):
    import matplotlib.pyplot as plt
    x=np.arange(len(DOSES)); fig,ax=plt.subplots(figsize=(6.6,4.2)); ax.plot(x,[r["language_mean_delta"]*1e3 for r in dose_rows],marker="o",label="Language"); ax.plot(x,[r["sensorimotor_mean_delta"]*1e3 for r in dose_rows],marker="o",label="Sensorimotor"); ax.plot(x,[r["visual_mean_delta"]*1e3 for r in dose_rows],marker="o",label="Visual"); ax.set_xticks(x,[str(d) for d in DOSES]); ax.set_xlabel("Neural-supervision dose lambda"); ax.set_ylabel("Mean delta RSA x 10^-3"); ax.set_title("Dose by cortical system"); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(ROOT/"figure_dose_by_system.png",dpi=600); fig.savefig(ROOT/"figure_dose_by_system.pdf"); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.5,4.5)); mx=np.arange(len(model_rows)); vals=np.asarray([r["mean_language_specificity_across_seeds"] for r in model_rows])*1e3; ax.bar(mx,vals); ax.axhline(0,linewidth=0.8); ax.set_xticks(mx,[r["model_key"] for r in model_rows],rotation=25,ha="right"); ax.set_ylabel("Language minus control delta RSA x 10^-3"); ax.set_title("Language enrichment across backbones"); fig.tight_layout(); fig.savefig(ROOT/"figure_model_family_enrichment.png",dpi=600); fig.savefig(ROOT/"figure_model_family_enrichment.pdf"); plt.close(fig)
    specs=np.asarray([r["language_specificity_mean"] for r in dose_rows])*1e3; zuco=np.asarray([dose_external[d]["zuco_mean_delta"] for d in DOSES])*1e3; sts=np.asarray([dose_external[d]["sts_delta"] for d in DOSES])*1e3
    fig,ax=plt.subplots(figsize=(6.6,4.2)); ax.scatter(zuco,specs); [ax.annotate(str(d),(zuco[i],specs[i])) for i,d in enumerate(DOSES)]; ax.set_xlabel("ZuCo delta RSA x 10^-3"); ax.set_ylabel("fMRI language specificity x 10^-3"); ax.set_title("Cross-modal coupling across dose"); fig.tight_layout(); fig.savefig(ROOT/"figure_crossmodal_coupling.png",dpi=600); fig.savefig(ROOT/"figure_crossmodal_coupling.pdf"); plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.6,4.2)); ax.scatter(sts,specs); [ax.annotate(str(d),(sts[i],specs[i])) for i,d in enumerate(DOSES)]; ax.set_xlabel("STS change vs lambda=0 x 10^-3"); ax.set_ylabel("fMRI language specificity x 10^-3"); ax.set_title("Semantic cost versus cortical specificity"); fig.tight_layout(); fig.savefig(ROOT/"figure_semantic_cost_specificity.png",dpi=600); fig.savefig(ROOT/"figure_semantic_cost_specificity.pdf"); plt.close(fig)


def main()->int:
    ROOT.mkdir(parents=True,exist_ok=True); required=[PREFLIGHT_DIR/"summary.json",MAIN_REGIONAL/"participant_results.csv",DOSE_SUMMARY,MODEL_RESOLVED]; missing=[str(p) for p in required if not p.exists()]
    if missing: raise FileNotFoundError("missing frozen inputs: "+", ".join(missing))
    conditions,resolved=make_conditions(); total=len(STORIES)+len(conditions); data_root=Path("data/raw/smn4lang").resolve(); meta,contexts=build_selected_neural_cache(data_root)
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("GPU required")
    all_region_rows=reuse_lambda010_rows(); zuco_model_rows=[]
    for completed,cond in enumerate(conditions,1):
        rows=aggregate_regional_condition(cond,"cuda",meta,contexts); zrows=[]
        if cond["kind"]=="model_family":
            zrows=evaluate_zuco_model_unit(cond["model_key"],cond["revision"],cond["unit"],"cuda")
            for zr in zrows: zr.update({"model_key":cond["model_key"],"seed":cond["seed"]})
        all_region_rows.extend(rows); zuco_model_rows.extend(zrows); atomic_progress(len(STORIES)+completed,total,"regional-condition-evaluation",f"completed {cond['label']} ({completed}/{len(conditions)})")
    write_csv(ROOT/"regional_participant_results.csv",all_region_rows); write_csv(ROOT/"model_family_zuco_participant_results.csv",zuco_model_rows); systems=system_rows_from_region_rows(all_region_rows); write_csv(ROOT/"participant_system_results.csv",systems)
    dose_rows,dose_interaction=summarize_dose(systems); dose_external=parse_dose_external(); dose_specs=[r["language_specificity_mean"] for r in dose_rows]; dose_zuco=[dose_external[d]["zuco_mean_delta"] for d in DOSES]; dose_sts=[dose_external[d]["sts_delta"] for d in DOSES]
    dose_coupling={"spearman_zuco_vs_fmri_language_specificity":float(spearmanr(dose_zuco,dose_specs).statistic),"spearman_semantic_sts_change_vs_fmri_language_specificity":float(spearmanr(dose_sts,dose_specs).statistic),"n_nonzero_doses":5,"descriptive_only":True}
    seed_rows,model_rows,model_coupling=summarize_model_family(systems,zuco_model_rows); write_csv(ROOT/"dose_system_summary.csv",dose_rows); write_csv(ROOT/"model_seed_enrichment_summary.csv",seed_rows); write_csv(ROOT/"model_backbone_enrichment_summary.csv",model_rows); make_figures(dose_rows,model_rows,dose_external)
    summary={"schema_version":1,"analysis":"NeuroSem remaining regional ideas suite","protocol":PROTOCOL,"status":"ok","post_confirmatory":True,"n_subjects_fmri":len(SUBJECTS),"doses":list(DOSES),"model_keys":list(MODEL_SPECS),"model_seeds":list(SEEDS),"selected_regions":meta,"dose_system_summary":dose_rows,"dose_high_vs_low_specificity_interaction":dose_interaction,"dose_crossmodal_and_semantic_coupling":dose_coupling,"model_backbone_summary":model_rows,"model_crossmodal_coupling":model_coupling,"input_sha256":{str(MAIN_REGIONAL/"participant_results.csv"):sha256(MAIN_REGIONAL/"participant_results.csv"),str(DOSE_SUMMARY):sha256(DOSE_SUMMARY),str(MODEL_RESOLVED):sha256(MODEL_RESOLVED)},"guardrails":{"definitions_frozen_before_execution":True,"no_new_model_training":True,"no_new_dose_search":True,"no_new_roi_search":True,"no_target_side_selection":True,"lambda010_regional_result_reused":True,"model_family_uses_existing_eeg_to_fmri_adapters":True,"coupling_tests_are_descriptive_condition_level_analyses":True}}
    (ROOT/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["NeuroSem remaining regional ideas suite v1","Status: ok","Post-confirmatory: yes","",f"Dose lambda1 - lambda0.10 specificity change: {dose_interaction['lambda1_minus_lambda010_specificity_change_mean']:.9g}; P={dose_interaction['exact_two_sided_signflip_p']:.9g}",f"Dose ZuCo-vs-fMRI-specificity Spearman rho: {dose_coupling['spearman_zuco_vs_fmri_language_specificity']:.6g}",f"Dose STS-change-vs-specificity Spearman rho: {dose_coupling['spearman_semantic_sts_change_vs_fmri_language_specificity']:.6g}",f"Model-level ZuCo-vs-fMRI-language Spearman rho: {model_coupling['model_level_spearman_zuco_vs_fmri_language']:.6g}",f"Model-level ZuCo-vs-language-specificity Spearman rho: {model_coupling['model_level_spearman_zuco_vs_language_specificity']:.6g}","","Backbone enrichment means:"]
    for r in model_rows: lines.append(f"{r['model_key']}: specificity={r['mean_language_specificity_across_seeds']:.9g}; FWER P={r['specificity_fwer_p_across_6_models']:.9g}")
    (ROOT/"report.txt").write_text("\n".join(lines)+"\n",encoding="utf-8"); atomic_progress(total,total,"complete","completed frozen remaining regional ideas suite"); return 0

if __name__=="__main__": raise SystemExit(main())

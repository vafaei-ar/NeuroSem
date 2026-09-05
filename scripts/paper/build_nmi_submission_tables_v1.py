#!/usr/bin/env python3
"""Build all NeuroSem NMI v1.13 manuscript and supplementary tables.

The tables are presentation exports of already-completed frozen results. No model fitting,
target selection, new neural analysis, or new scientific hypothesis search is performed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "nmi_submission_assets_v1" / "latest" / "tables"

MODEL = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
SPEC = ROOT / "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json"
MS010 = ROOT / "outputs/nmi_model_space_characterization_v1/latest/summary.json"
MS1 = ROOT / "outputs/nmi_model_space_characterization_lambda1_v1/latest/summary.json"
REG = ROOT / "outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv"
REG_TF = ROOT / "outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/language_twofactor_bootstrap.csv"
REV_DOSE = ROOT / "outputs/nmi_bidirectional_fmri_eeg_dose_response_v1/latest/zuco_subject_dose_results.csv"
REV_MULTI_DOSE = ROOT / "outputs/nmi_fmri_to_chineseeeg_multiseed_dose_v1/latest/summary.json"
REV_SEEDS = ROOT / "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json"
FORWARD_DOSE = ROOT / "outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv"

INPUTS = [MODEL, SPEC, MS010, MS1, REG, REG_TF, REV_DOSE, REV_MULTI_DOSE, REV_SEEDS, FORWARD_DOSE]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(name: str, rows: list[dict], fields: list[str] | None = None) -> Path:
    if not rows:
        raise RuntimeError(f"No rows for {name}")
    path = OUT / f"{name}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    return path


def exact_one_sided_signflip(x: np.ndarray) -> float:
    """Deterministic reporting verification for a previously completed frozen contrast."""
    x = np.asarray(x, float); obs = float(x.mean()); n = len(x); count = 0
    for mask in range(1 << n):
        signs = np.array([1.0 if (mask >> i) & 1 else -1.0 for i in range(n)])
        if float(np.mean(x * signs)) >= obs - 1e-15:
            count += 1
    return float(count / (1 << n))


def build_extended_data_1() -> list[dict]:
    return [
        {"Evidence":"Learnability","Source → target":"ChineseEEG → run-07","Design status":"Sealed holdout","Key result":"Neural-guided highest in both seeds","Message":"Source relation is learnable"},
        {"Evidence":"Primary EEG transfer","Source → target":"ChineseEEG → ZuCo EEG","Design status":"Fresh external","Key result":"17/17 positive; ΔRSA +1.66×10^-3","Message":"Positive external displacement"},
        {"Evidence":"Primary fMRI transfer","Source → target":"ChineseEEG → SMN4Lang fMRI","Design status":"Prospective","Key result":"12/12 positive; ΔRSA +8.53×10^-4","Message":"Cross-modal external displacement"},
        {"Evidence":"Forward dose scope","Source → target":"ChineseEEG E5 grid → ZuCo/fMRI","Design status":"Post-confirmatory","Key result":"ZuCo rises through λ=1; fMRI reverses at λ=1","Message":"Dose- and target-dependent transfer"},
        {"Evidence":"Reverse transfer","Source → target":"SMN4Lang fMRI → ZuCo EEG","Design status":"Post-confirmatory","Key result":"Frozen λ=.01 positive; three added seeds positive","Message":"Small reverse effect is seed-robust"},
        {"Evidence":"Model-family scope","Source → target":"EEG/fMRI → EEG/fMRI","Design status":"Post-confirmatory","Key result":"E5 variants positive both directions; other backbones heterogeneous","Message":"Transfer is model-dependent"},
    ]


def model_summary_rows() -> list[dict]:
    rows = read_csv(MODEL)
    order = [("e5_large","multilingual-E5-large","E5 embedding"),("e5_base","multilingual-E5-base","E5 embedding"),("multilingual_mpnet","multilingual MPNet","sentence embedding"),("multilingual_minilm","multilingual MiniLM","sentence embedding"),("xlmr_base","XLM-R-base","generic MLM"),("mbert","multilingual BERT","generic MLM")]
    out=[]
    for key,label,cls in order:
        rec={"Model":label,"Class":cls}
        for direction,col in (("eeg_to_fmri","ChineseEEG → fMRI"),("fmri_to_eeg","fMRI → ZuCo EEG")):
            rr=[r for r in rows if r["model_key"]==key and r["direction"]==direction]
            vals=[float(r["external_mean_delta"]) for r in rr]; n=sum(v>0 for v in vals)
            rec[col] = "3/3 positive" if n==3 else ("3/3 negative" if n==0 else f"mixed ({n} positive, {3-n} negative)")
        out.append(rec)
    return out


def extended_data_3() -> list[dict]:
    s=read_json(SPEC); spec=s["specificity_control"]; hb=s["hierarchical_bootstrap"]
    out=[]
    for ds,label in (("zuco","ZuCo EEG"),("smn4lang_fmri","SMN4Lang fMRI")):
        for contrast,label2 in (("genuine_minus_shuffled","Specificity: genuine − shuffled"),("shuffled_minus_text","Specificity: shuffled − text")):
            vals=[float(r["targets"][ds][contrast]["mean_delta"]) for r in spec["seed_results"]]
            out.append({"Analysis":label2,"Target":label,"Result":"; ".join(f"{v:+.7g}" for v in vals),"Inference/status":"Post-confirmatory seed panel"})
    for ds,label in (("zuco","ZuCo EEG"),("smn4lang_fmri","SMN4Lang fMRI")):
        t=hb[ds]["two_factor_bootstrap"]
        out.append({"Analysis":"Participant × stimulus bootstrap","Target":label,"Result":f"95% CI {t['percentile_95ci'][0]:+.7g} to {t['percentile_95ci'][1]:+.7g}; fraction >0 {t['fraction_bootstrap_means_gt_0']:.3f}","Inference/status":"Sensitivity only"})
    for lab,path in (("λ=.10",MS010),("λ=1.0",MS1)):
        m=read_json(path)["metrics"]
        out.append({"Analysis":f"Model-space perturbation ({lab})","Target":"E5 on frozen 349 ZuCo items","Result":f"cosine {m['corresponding_item_cosine_similarity_mean']:.5f}; RDM Pearson {m['pairwise_cosine_distance_pearson']:.5f}; RDM Spearman {m['pairwise_cosine_distance_spearman']:.5f}; CKA {m['linear_centered_cka']:.5f}; k=10 Jaccard {m['mean_knn_jaccard_overlap']:.4f}","Inference/status":"Post-confirmatory descriptive characterization" if lab=="λ=1.0" else "Prospective-dose perturbation characterization"})
    return out


def regional_language_rows() -> list[dict]:
    rows=[r for r in read_csv(REG) if r.get("family")=="language"]
    tf={r["region_name"]:r for r in read_csv(REG_TF)}
    order=["IFGorb","IFG","MFG","AntTemp","PostTemp","AngG"]; by={r["region_name"]:r for r in rows}; out=[]
    for name in order:
        r=by[name]; t=tf[name]
        out.append({
            "Parcel":name,"Reliability":r["model_blind_reliability_mean"],"Text-only RSA":r["lambda_0_mean"],"Neural-guided RSA":r["lambda_0p10_mean"],
            "ΔRSA":r["delta_mean"],"95% participant CI":f"[{float(r['delta_bootstrap_ci_low']):.7g}, {float(r['delta_bootstrap_ci_high']):.7g}]",
            "Positive":f"{r['delta_n_positive']}/12","Exact P":r["delta_exact_two_sided_signflip_p"],"FWER P":r["language_family_fwer_p"],
            "2-factor 95% CI":f"[{float(t['ci_low']):.7g}, {float(t['ci_high']):.7g}]",
        })
    return out


def supplementary_1() -> list[dict]:
    return [
        {"Stage":"ChineseEEG development","Information available when fixed":"ChineseEEG development runs","Model/contrast status":"Model and objective developed","Neural target status":"Reliability-led development","Outcome role":"Exploratory/development"},
        {"Stage":"ChineseEEG run-07","Information available when fixed":"Runs 01–06 only","Model/contrast status":"BERT/E5 recipes fixed; run-07 excluded from training","Neural target status":"Target fixed","Outcome role":"Sealed holdout"},
        {"Stage":"E5 dose-response","Information available when fixed":"Run-07 and generic STS already observed","Model/contrast status":"λ grid 0,.01,.03,.10,.30,1 prespecified","Neural target status":"ChineseEEG fixed","Outcome role":"Exploratory characterization"},
        {"Stage":"ZuCo 2.0","Information available when fixed":"No ZuCo neural outcome","Model/contrast status":"λ=.10 vs 0 fixed","Neural target status":"Representation fixed before interpretation","Outcome role":"Fresh external validation"},
        {"Stage":"SMN4Lang fMRI","Information available when fixed":"Fixed model contrast; no fMRI model outcome","Model/contrast status":"λ=.10 vs 0 fixed","Neural target status":"Model-blind LanA reliability gate","Outcome role":"Prospective cross-modal validation"},
        {"Stage":"SMN4Lang MEG","Information available when fixed":"fMRI branch complete; no MEG model outcome","Model/contrast status":"Model gated by reliability","Neural target status":"32-bin target prospective; 4/8/16 family later","Outcome role":"Reliability boundary"},
        {"Stage":"Reverse fMRI→ZuCo","Information available when fixed":"Primary forward outcomes known; source calibration used fMRI only","Model/contrast status":"λ=.01 vs 0 frozen before EEG read","Neural target status":"Existing ZuCo target unchanged","Outcome role":"Post-confirmatory bidirectionality"},
        {"Stage":"Reverse E5 dose response","Information available when fixed":"Frozen λ=.01 reverse result observed","Model/contrast status":"Pre-existing trained grid only","Neural target status":"Existing ZuCo target unchanged","Outcome role":"Post-confirmatory characterization"},
        {"Stage":"ChineseEEG multi-seed dose","Information available when fixed":"Single-seed reverse dose behavior observed","Model/contrast status":"Frozen grid at seeds 20260829–31","Neural target status":"ChineseEEG run-07 unchanged","Outcome role":"Post-confirmatory robustness"},
        {"Stage":"Six-model family panel","Information available when fixed":"Some E5/mBERT outcomes known","Model/contrast status":"6 models × 3 seeds × 2 directions; λ=.10 common","Neural target status":"Existing fMRI and ZuCo targets","Outcome role":"Post-confirmatory scope"},
        {"Stage":"Regional SMN4Lang fMRI","Information available when fixed":"Whole-network result known; regional protocol frozen before regional outcomes","Model/contrast status":"λ=.10 vs 0 only","Neural target status":"6 language parcels + complete DK68; reliability first","Outcome role":"Post-confirmatory spatial characterization"},
    ]


def supplementary_2() -> list[dict]:
    rows=read_csv(MODEL); out=[]
    for r in rows:
        out.append({"Model":r["model_key"],"Direction":r["direction"],"Seed":r["seed"],"Source Δ":r.get("source_delta",r.get("source_mean_delta","")),"External mean Δ":r["external_mean_delta"],"n positive":r["external_n_positive"],"95% CI low":r["external_bootstrap_95ci_low"],"95% CI high":r["external_bootstrap_95ci_high"],"one-sided P":r["external_one_sided_p"]})
    return out


def supplementary_3() -> list[dict]:
    rows=read_csv(REV_DOSE); out=[]
    for lam in [.01,.03,.10,.30,1.0]:
        rr=[r for r in rows if abs(float(r["lambda"])-lam)<1e-12]
        d=np.asarray([float(r["delta"]) for r in rr]); out.append({"λ":lam,"Mean RSA Δ":float(d.mean()),"Positive participants":f"{int(np.sum(d>0))}/{len(d)}","One-sided P":exact_one_sided_signflip(d)})
    return out


def supplementary_4() -> list[dict]:
    s=read_json(REV_MULTI_DOSE)["lambda_aggregate"]; out=[]
    for lam in [.01,.03,.10,.30,1.0]:
        vals=s[str(lam)]["seed_mean_deltas"]
        out.append({"λ":lam,"Seed 20260829 Δ":vals[0],"Seed 20260830 Δ":vals[1],"Seed 20260831 Δ":vals[2],"Mean of seed means":s[str(lam)]["mean_of_seed_mean_deltas"]})
    return out


def supplementary_5() -> list[dict]:
    spec=read_json(SPEC)["specificity_control"]["seed_results"]; out=[]
    for rec in spec:
        for ds,label in (("zuco","ZuCo EEG"),("smn4lang_fmri","SMN4Lang fMRI")):
            t=rec["targets"][ds]; g=t["genuine_minus_shuffled"]
            out.append({"Seed":rec["seed"],"Target":label,"Shuffled − text mean ΔRSA":t["shuffled_minus_text"]["mean_delta"],"Genuine − shuffled mean ΔRSA":g["mean_delta"],"Positive participants, genuine − shuffled":f"{g['n_positive']}/{g['n_participants']}","Two-sided exact P, genuine − shuffled":g["exact_two_sided_signflip_p"]})
    return out


def supplementary_6() -> list[dict]:
    s=read_json(SPEC); hb=s["hierarchical_bootstrap"]; out=[]
    for ds,label in (("zuco","ZuCo two-factor bootstrap"),("smn4lang_fmri","SMN4Lang fMRI two-factor bootstrap")):
        t=hb[ds]["two_factor_bootstrap"]; out.extend([
            {"Analysis":label,"Statistic":"95% percentile CI","Result":f"[{t['percentile_95ci'][0]:+.7g}, {t['percentile_95ci'][1]:+.7g}]"},
            {"Analysis":label,"Statistic":"Fraction bootstrap means >0","Result":t["fraction_bootstrap_means_gt_0"]},
        ])
    for lab,path in (("E5 perturbation (λ=.10)",MS010),("E5 perturbation (λ=1.0)",MS1)):
        m=read_json(path)["metrics"]
        for stat,key in (("Corresponding-item cosine similarity","corresponding_item_cosine_similarity_mean"),("Pairwise RDM Pearson","pairwise_cosine_distance_pearson"),("Pairwise RDM Spearman","pairwise_cosine_distance_spearman"),("Linear centered CKA","linear_centered_cka"),("k=10 neighborhood Jaccard","mean_knn_jaccard_overlap")):
            out.append({"Analysis":lab,"Statistic":stat,"Result":m[key]})
    return out


def supplementary_8() -> list[dict]:
    rows=[r for r in read_csv(REG) if r.get("family")=="dk68"]
    return [{"Hem.":r["hemisphere"],"DK parcel":r["region_name"],"Reliability":r["model_blind_reliability_mean"],"Mean RSA Δ":r["delta_mean"],"Positive":f"{r['delta_n_positive']}/12"} for r in rows]


def supplementary_9() -> list[dict]:
    s=read_json(REV_SEEDS); out=[]
    for r in s["seed_results"]:
        z=r["zuco"]; out.append({"Seed":r["seed"],"Mean ΔRSA":z["mean_delta"],"Positive participants":f"{z['n_positive']}/{s['n_zuco_subjects']}","95% participant-bootstrap CI":f"[{z['bootstrap_95ci'][0]:+.7g}, {z['bootstrap_95ci'][1]:+.7g}]","Status":"Positive" if z["mean_delta"]>0 else "Negative"})
    return out


def supplementary_10() -> list[dict]:
    rows=read_csv(FORWARD_DOSE); by={(r["dataset"],float(r["lambda"])):r for r in rows}; out=[]
    for lam in [0,.01,.03,.10,.30,1.0]:
        z=by[("zuco",lam)]; f=by[("smn4lang_fmri",lam)]
        if lam==0:
            out.append({"λ":"0.00 (reference)","ZuCo mean ΔRSA [95% CI]":"reference","SMN4Lang fMRI mean ΔRSA [95% CI]":"reference","STS delta vs λ=0":"reference","Status":"prospective baseline reused"}); continue
        status="prospective primary result reused" if abs(lam-.10)<1e-12 else "post-confirmatory"
        out.append({"λ":f"{lam:.2f}" if lam<1 else "1.00","ZuCo mean ΔRSA [95% CI]":f"{float(z['mean_delta_rsa']):+.7g} [{float(z['bootstrap_95ci_low']):+.7g}, {float(z['bootstrap_95ci_high']):+.7g}]","SMN4Lang fMRI mean ΔRSA [95% CI]":f"{float(f['mean_delta_rsa']):+.7g} [{float(f['bootstrap_95ci_low']):+.7g}, {float(f['bootstrap_95ci_high']):+.7g}]","STS delta vs λ=0":z["delta_external_sts_vs_lambda0_already_observed"],"Status":status})
    return out


def main() -> int:
    missing=[str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError("Missing frozen table input(s): "+", ".join(missing))
    OUT.mkdir(parents=True,exist_ok=True)
    outputs=[]
    outputs.append(write("extended_data_table_1",build_extended_data_1()))
    outputs.append(write("extended_data_table_2",model_summary_rows()))
    outputs.append(write("extended_data_table_3",extended_data_3()))
    outputs.append(write("extended_data_table_4",regional_language_rows()))
    outputs.append(write("supplementary_table_1",supplementary_1()))
    outputs.append(write("supplementary_table_2",supplementary_2()))
    outputs.append(write("supplementary_table_3",supplementary_3()))
    outputs.append(write("supplementary_table_4",supplementary_4()))
    outputs.append(write("supplementary_table_5",supplementary_5()))
    outputs.append(write("supplementary_table_6",supplementary_6()))
    outputs.append(write("supplementary_table_7",regional_language_rows()))
    outputs.append(write("supplementary_table_8",supplementary_8()))
    outputs.append(write("supplementary_table_9",supplementary_9()))
    outputs.append(write("supplementary_table_10",supplementary_10()))
    manifest={"schema_version":1,"analysis":"NeuroSem NMI v1.13 submission table export","status":"ok","guardrails":["Presentation export of already-completed frozen results.","No model fitting, target selection, neural analysis or new scientific hypothesis search.","The reverse-dose exact sign-flip column is a deterministic verification of the previously completed frozen participant contrasts, not a new contrast."],"inputs":{str(p.relative_to(ROOT)):sha256(p) for p in INPUTS},"outputs":{str(p.relative_to(ROOT)):sha256(p) for p in outputs}}
    (OUT/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","tables":14,"output_dir":str(OUT)},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

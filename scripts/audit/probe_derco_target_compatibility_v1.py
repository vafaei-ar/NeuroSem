#!/usr/bin/env python3
"""Read-only DERCo structure/provenance probe for target-compatibility extension.

No model weights are loaded and no neural-model RSA is computed. The script inventories
one representative preprocessed Epochs file, the completed DERCo transfer tables, and
searches repository history for DERCo-related tracked source paths.
"""
from __future__ import annotations
import csv, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/derco_target_compat_probe_v1/latest"

def read_csv(path):
    with path.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f))

def main():
    import mne
    OUT.mkdir(parents=True,exist_ok=True)
    fif=ROOT/"data/raw/derco/ACB71/article_0/preprocessed_epoch.fif"
    if not fif.is_file(): raise FileNotFoundError(fif)
    ep=mne.read_epochs(fif,preload=False,verbose="ERROR")
    info={
      "representative_fif":str(fif.relative_to(ROOT)),
      "n_epochs":len(ep),
      "n_channels":len(ep.ch_names),
      "sfreq":float(ep.info["sfreq"]),
      "tmin":float(ep.tmin),"tmax":float(ep.tmax),
      "event_id":ep.event_id,
      "event_shape":list(ep.events.shape),
      "first_events":ep.events[:20].tolist(),
      "metadata_columns":None if ep.metadata is None else list(ep.metadata.columns),
      "metadata_head":None if ep.metadata is None else ep.metadata.head(10).to_dict(orient="records"),
      "channel_names":ep.ch_names,
      "bads":list(ep.info.get("bads",[])),
    }

    pa=read_csv(ROOT/"outputs/derco_e5_transfer_v1/latest/participant_article_results.csv")
    pp=read_csv(ROOT/"outputs/derco_e5_transfer_v1/latest/participant_results.csv")
    info["participant_article_columns"]=list(pa[0]) if pa else []
    info["participant_article_first_rows"]=pa[:8]
    info["participant_columns"]=list(pp[0]) if pp else []
    info["participant_first_rows"]=pp[:8]

    cp=subprocess.run(["git","log","--all","--name-only","--pretty=format:%H %s"],cwd=ROOT,text=True,capture_output=True,check=True)
    lines=[ln for ln in cp.stdout.splitlines() if "derco" in ln.lower()]
    info["git_log_derco_lines"]=lines[:500]

    (OUT/"summary.json").write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text("DERCo target-compatibility probe complete; no model loaded and no new RSA computed.\n",encoding="utf-8")
    print(json.dumps({"status":"ok","n_epochs":info["n_epochs"],"event_id_n":len(info["event_id"]),"metadata_columns":info["metadata_columns"],"git_derco_hits":len(lines)},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())

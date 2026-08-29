#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.robustness.mbert_adapter_io_v1 import MODEL_ID, MODEL_REVISION, PREFIX, encode_texts, load_adapter


def rewrite_summary(path: Path, dataset: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["analysis_stage"] = "post-confirmatory second-model-family robustness"
    payload["postconfirmatory_contrast"] = "ChineseEEG-trained multilingual-BERT lambda=0.10 neural-guided minus lambda=0 text-only"
    if "confirmatory_contrast" in payload:
        payload["confirmatory_contrast"] = payload["postconfirmatory_contrast"]
    if "primary_contrast" in payload:
        payload["primary_contrast"] = payload["postconfirmatory_contrast"]
    payload["model_id"] = MODEL_ID
    payload["model_revision"] = MODEL_REVISION
    payload["model_prefix"] = PREFIX
    payload["model_family_guardrail"] = "Second-model-family analysis; post-confirmatory because target outcomes were historically known before execution."
    if dataset == "smn4lang_fmri" and isinstance(payload.get("semantic_mapping"), dict):
        payload["semantic_mapping"]["unit"] = "TR-level causal within-sentence-prefix multilingual-BERT state"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["zuco", "smn4lang_fmri"], required=True)
    ap.add_argument("--text-adapter", type=Path, required=True)
    ap.add_argument("--neural-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    if args.dataset == "zuco":
        import scripts.tuning.evaluate_zuco2_nr_e5_transfer_v1 as mod
        mod.TEXT_ONLY_ADAPTER = args.text_adapter.resolve()
        mod.LAMBDA_010_ROOT = args.neural_root.resolve()
        mod.load_adapter = load_adapter
        mod.encode_texts = encode_texts
        sys.argv = [mod.__file__, "--output-dir", str(args.output_dir), "--device", "auto"]
        mod.main()
    else:
        import scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 as mod
        mod.TEXT_ONLY_ADAPTER = args.text_adapter.resolve()
        mod.LAMBDA_010_ROOT = args.neural_root.resolve()
        mod.load_adapter = load_adapter
        mod.encode_texts = encode_texts
        mod.MODEL_ID = MODEL_ID
        mod.MODEL_REVISION = MODEL_REVISION
        mod.PREFIX = PREFIX
        sys.argv = [mod.__file__, "--output-dir", str(args.output_dir), "--device", "auto"]
        rc = mod.main()
        if rc not in (None, 0):
            return int(rc)

    rewrite_summary(args.output_dir / "summary.json", args.dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

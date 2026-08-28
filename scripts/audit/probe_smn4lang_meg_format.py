#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import mne

S3_BUCKET = "openneuro.org"
# Use path-style S3 URLs. The dotted bucket name cannot be used safely as a
# virtual-host TLS name (openneuro.org.s3.amazonaws.com certificate mismatch).
S3_BASE = f"https://s3.amazonaws.com/{S3_BUCKET}/"
DATASET_PREFIX = "ds004078/"
REP_REL = "derivatives/preprocessed_data/sub-01/MEG/sub-01_task-RDR_run-10_meg.fif"
EXPECTED_MD5 = "f58c0e675bb36f17d23a0a22420ba98a"
EXPECTED_SIZE = 373_698_310
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def list_objects(prefix: str):
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        url = S3_BASE + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as r:
            root = ET.fromstring(r.read())
        for item in root.findall("s3:Contents", NS):
            key = item.findtext("s3:Key", default="", namespaces=NS)
            size = int(item.findtext("s3:Size", default="0", namespaces=NS))
            etag = item.findtext("s3:ETag", default="", namespaces=NS).strip('"')
            yield key, size, etag
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=NS).lower() == "true"
        if not truncated:
            break
        token = root.findtext("s3:NextContinuationToken", default=None, namespaces=NS)
        if not token:
            raise RuntimeError("S3 listing truncated without continuation token")


def find_representative() -> tuple[str, int, str]:
    matches = []
    for key, size, etag in list_objects(DATASET_PREFIX):
        # Accept both direct and snapshot-prefixed dataset object layouts.
        if key.endswith(REP_REL):
            matches.append((key, size, etag))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one S3 object ending with {REP_REL}; found {len(matches)}: {matches[:5]}")
    return matches[0]


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-SMN4Lang-MEG-probe/1"})
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(8 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_format_probe/latest"))
    args = ap.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cache = args.data_root.resolve().parent / "smn4lang_meg_probe_cache" / "sub-01_task-RDR_run-10_meg.fif"

    key, s3_size, etag = find_representative()
    if s3_size != EXPECTED_SIZE:
        raise RuntimeError(f"S3 size mismatch: expected {EXPECTED_SIZE}, observed {s3_size}")

    object_url = S3_BASE + urllib.parse.quote(key, safe="/")
    if not cache.exists() or cache.stat().st_size != EXPECTED_SIZE:
        download(object_url, cache)

    observed_md5 = md5_file(cache)
    if observed_md5 != EXPECTED_MD5:
        raise RuntimeError(f"MD5 mismatch: expected {EXPECTED_MD5}, observed {observed_md5}")

    raw = mne.io.read_raw_fif(cache, preload=False, verbose="ERROR")
    channel_types = raw.get_channel_types()
    counts: dict[str, int] = {}
    for x in channel_types:
        counts[x] = counts.get(x, 0) + 1

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "MEG model-blind representative materialization and metadata probe",
        "model_blind": True,
        "computes_reliability": False,
        "loads_model_embeddings": False,
        "public_materialization_route": {
            "source": "OpenNeuro public AWS S3 mirror",
            "bucket": S3_BUCKET,
            "endpoint_style": "path-style HTTPS",
            "object_key": key,
            "object_url": object_url,
            "s3_size_bytes": s3_size,
            "s3_etag": etag,
            "local_cache": str(cache),
            "expected_git_annex_md5": EXPECTED_MD5,
            "observed_md5": observed_md5,
            "integrity_verified": observed_md5 == EXPECTED_MD5,
        },
        "representative_fif": {
            "released_relative_path": REP_REL,
            "subject": 1,
            "run": 10,
            "sfreq_hz": float(raw.info["sfreq"]),
            "n_times": int(raw.n_times),
            "duration_seconds": float(raw.n_times / raw.info["sfreq"]),
            "n_channels": len(raw.ch_names),
            "channel_type_counts": dict(sorted(counts.items())),
            "bad_channels": list(raw.info.get("bads", [])),
            "highpass_hz": float(raw.info.get("highpass", 0.0)),
            "lowpass_hz": float(raw.info.get("lowpass", 0.0)),
            "n_annotations": len(raw.annotations),
            "annotation_description_counts": {
                k: list(raw.annotations.description).count(k)
                for k in sorted(set(map(str, raw.annotations.description)))
            },
            "dev_head_t_present": raw.info.get("dev_head_t") is not None,
            "preload": False,
        },
        "next_decision": "freeze one MEG temporal/sensor representation and a model-blind reliability gate from acquisition and released preprocessing metadata only",
        "guardrails": {
            "one_deterministic_representative_only": True,
            "no_reliability_computed": True,
            "no_model_outcomes": True,
            "no_latency_search": True,
            "no_frequency_search": True,
            "no_sensor_subset_search": True,
            "no_source_localization_search": True,
            "tls_verification_disabled": False,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

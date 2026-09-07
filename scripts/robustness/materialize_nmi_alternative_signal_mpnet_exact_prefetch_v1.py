#!/usr/bin/env python3
"""Prefetch the exact frozen MPNet revision, then materialize the fixed surrogate targets.

Implementation-only wrapper for the alternative-signal control. The scientific target
is defined in materialize_nmi_alternative_signal_mpnet_v1.py. This wrapper resolves
that script's already-frozen immutable model revision, downloads only that exact
revision if it is absent from the local Hugging Face cache, and then delegates to the
original materializer, which reloads with local_files_only=True.
"""
from __future__ import annotations

from huggingface_hub import snapshot_download

from scripts.robustness import materialize_nmi_alternative_signal_mpnet_v1 as impl


def main() -> int:
    model_id, revision = impl.frozen_panel_revision()
    print(f"Prefetching exact frozen model: {model_id}@{revision}", flush=True)
    snapshot_download(
        repo_id=model_id,
        revision=revision,
        repo_type="model",
        local_files_only=False,
    )
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())

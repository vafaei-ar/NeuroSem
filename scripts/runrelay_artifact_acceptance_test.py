#!/usr/bin/env python3
"""Create tiny, safe artifacts for the RunRelay end-to-end delivery acceptance test."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


OUTPUT_DIR = Path("outputs/runrelay_artifact_acceptance/latest")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "test": "runrelay_artifact_acceptance",
        "status": "ok",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "message": "Safe synthetic artifact created on the bound RunRelay workstation.",
    }
    (OUTPUT_DIR / "acceptance.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "acceptance.txt").write_text(
        "RunRelay end-to-end artifact acceptance test: OK\n", encoding="utf-8"
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

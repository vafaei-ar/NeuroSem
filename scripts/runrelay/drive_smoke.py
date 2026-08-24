#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

out = Path("outputs/runrelay_drive_smoke/latest")
out.mkdir(parents=True, exist_ok=True)
payload = {
    "ok": True,
    "purpose": "RunRelay Google Drive artifact delivery smoke test",
    "project": "neurosem",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
}
path = out / "summary.json"
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"RUNRELAY_DRIVE_SMOKE_OK {path}")

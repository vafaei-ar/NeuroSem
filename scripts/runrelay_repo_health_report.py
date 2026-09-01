#!/usr/bin/env python3
"""Create a small safe derived health report from the public NeuroSem RunRelay config."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".runrelay" / "project.yaml"
AGENTS = ROOT / "AGENTS.md"
OUTPUT_DIR = ROOT / "outputs" / "runrelay_repo_health" / "latest"


def main() -> None:
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    agents_text = AGENTS.read_text(encoding="utf-8")

    task_names = re.findall(r"^  ([A-Za-z0-9_]+):\s*$", manifest_text, flags=re.MULTILINE)
    machine_match = re.search(r"^  machine_id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    project_match = re.search(r"^  id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    script_paths = sorted(set(re.findall(r"^\s+-\s+(scripts/[A-Za-z0-9_./-]+\.py)\s*$", manifest_text, flags=re.MULTILINE)))

    script_checks = [
        {"path": rel, "exists": (ROOT / rel).is_file()}
        for rel in script_paths
    ]
    missing_scripts = [item["path"] for item in script_checks if not item["exists"]]

    payload = {
        "schema_version": 1,
        "report": "neurosem_runrelay_repo_health",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": project_match.group(1) if project_match else None,
        "machine_id": machine_match.group(1) if machine_match else None,
        "task_count": len(task_names),
        "tasks": task_names,
        "referenced_python_script_count": len(script_checks),
        "missing_referenced_scripts": missing_scripts,
        "agents_declares_runrelay": "RunRelay" in agents_text,
        "status": "ok" if not missing_scripts and task_names else "attention",
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "health.txt").write_text(
        "\n".join(
            [
                "NeuroSem RunRelay repository health report",
                f"Status: {payload['status']}",
                f"Project: {payload['project_id']}",
                f"Machine: {payload['machine_id']}",
                f"Registered tasks: {payload['task_count']}",
                f"Referenced Python scripts checked: {payload['referenced_python_script_count']}",
                f"Missing referenced scripts: {len(missing_scripts)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()

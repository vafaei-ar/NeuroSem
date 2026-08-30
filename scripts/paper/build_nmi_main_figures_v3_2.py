#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


def load_v3():
    path = Path(__file__).with_name("build_nmi_main_figures_v3.py")
    spec = importlib.util.spec_from_file_location("neurosem_nmi_figures_v3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_rows(required: set[str]) -> tuple[int | None, str | None]:
    if {"candidate", "resid_loo"}.issubset(required):
        return 17, "zuco_reliability"
    if {"lambda_0_resid_rsa", "lambda_0p10_resid_rsa", "delta_0p10_minus_0"}.issubset(required):
        return 17, "zuco_transfer"
    if {"primary_residual_reliability"}.issubset(required):
        return 12, "fmri_reliability"
    if {"lambda_0_residual_rsa", "lambda_0p10_residual_rsa", "delta_0p10_minus_0"}.issubset(required):
        return 12, "fmri_transfer"
    return None, None


def safe_discover_csv(module, root: Path, required: set[str], prefer: str | None = None) -> Path:
    candidates = list(root.glob("*/latest/*.csv"))
    candidates.extend(root.glob("*/latest/*/*.csv"))
    n_expected, role = expected_rows(required)
    matches = []
    for p in candidates:
        try:
            if not required.issubset(module.headers(p)):
                continue
            rows = module.read_csv(p)
            if role == "zuco_reliability":
                n_primary = sum(r.get("candidate") == "row_mean_all" for r in rows)
                if n_primary != n_expected:
                    continue
            elif n_expected is not None and len(rows) != n_expected:
                continue
            score = 0
            if prefer is not None and prefer.lower() in str(p).lower():
                score += 10
            name = p.name.lower()
            if "subject" in name or "participant" in name:
                score += 4
            if "session" in name or "run" in name:
                score -= 4
            matches.append((score, p.stat().st_mtime, p, len(rows)))
        except Exception:
            continue
    if not matches:
        raise FileNotFoundError(
            f"No validated frozen CSV under {root} with columns {sorted(required)}; role={role} expected_rows={n_expected}"
        )
    matches.sort(key=lambda z: (z[0], z[1]), reverse=True)
    score, _, chosen, n_rows = matches[0]
    print(f"figure-source: role={role} rows={n_rows} score={score} path={chosen}", flush=True)
    return chosen


def capped_exact_signflip(module, x):
    n = len(x)
    if n > 20:
        raise RuntimeError(
            f"Refusing exact sign-flip over n={n}; figure inference must use participant-level tables (n<=20)."
        )
    return module._original_exact_signflip(x)


def main() -> int:
    module = load_v3()
    module.discover_csv = lambda root, required, prefer=None: safe_discover_csv(
        module, root, required, prefer
    )
    module._original_exact_signflip = module.exact_signflip
    module.exact_signflip = lambda x: capped_exact_signflip(module, x)
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())

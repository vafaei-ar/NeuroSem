#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python scripts/robustness/nmi_hierarchical_bootstrap_v1.py
.venv/bin/python scripts/robustness/nmi_model_space_characterization_v1.py
.venv/bin/python scripts/robustness/run_nmi_multiseed_e5_v1.py

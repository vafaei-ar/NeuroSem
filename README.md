# NeuroSem

**NeuroSem** is a research project on the relationship between biological neural representations and the semantic geometry of language-model embedding spaces.

The central question is whether human neural responses contain reproducible semantic relational structure that is not already captured by conventional language representations, and whether that residual structure can provide a useful supervision signal for language models.

## Scientific scope

The project is organized around three sequential hypotheses:

1. **Residual neural semantic geometry exists.** Human neural responses retain reproducible semantic relational structure after accounting for lexical, syntactic, phonological, positional, timing, and other experimental nuisance structure.
2. **The residual geometry generalizes.** The structure replicates across participants and, where datasets allow, across tasks, modalities, languages, and neural recording technologies.
3. **Biological supervision adds information.** Using residual neural geometry as an auxiliary training signal changes language-model representations and improves semantic generalization beyond matched text-only fine-tuning.

The first two hypotheses are go/no-go criteria before substantial LLM tuning.

## Initial study strategy

The first milestone is **Go/No-Go: Residual Neural Semantic Geometry**. We will:

- curate and rank candidate open neural-language datasets;
- reproduce the validation pipeline for one primary dataset;
- extract neural and language-model representations;
- quantify representational geometry using RSA and related methods;
- partial out linguistic and experimental nuisance structure;
- test statistical significance with permutation procedures;
- evaluate cross-subject generalization.

Only if this milestone supports the core premise will we proceed to brain-guided LLM tuning.

## Candidate datasets

Initial candidates include ChineseEEG / ChineseEEG-2, Chisco, SIGNAL, ZuCo, the Russian-Spanish overt/covert directional-concept EEG dataset, and selected fMRI/ECoG/sEEG language datasets for external validation. Dataset selection and evidence are documented in `DATASETS.md`.

## Repository organization

- `SCIENTIFIC_HYPOTHESES.md`: hypotheses, falsification criteria, and interpretation rules
- `DATASETS.md`: candidate dataset matrix and selection rationale
- `LITERATURE.md`: focused literature map
- `ANALYSIS_PLAN.md`: preregistration-style computational and statistical plan
- `PROJECT_PLAN.md`: milestones and work packages
- `docs/`: study decisions, meeting notes, and figure planning
- `src/`: reusable analysis code
- `scripts/`: executable workflow entry points
- `configs/`: dataset and experiment configurations
- `results/`: derived tables, figures, and logs only
- `paper/`: manuscript development

## Collaboration

Project leads: Alireza Vafaei Sadr and Abbas Khanbeigy.

Analyses should be developed through issues and pull requests. Raw neural datasets, large derived arrays, and model checkpoints should not be committed to GitHub.

## Status

Repository initialization and scientific design phase.

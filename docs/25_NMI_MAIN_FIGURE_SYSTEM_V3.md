# NMI main figure system v3

## Status

Publication-figure redesign for the current Nature Machine Intelligence manuscript. This is a visualization-only layer over locked derived results. It must not perform model fitting, target selection, representation search, participant exclusion, lambda selection or new hypothesis testing.

## Editorial objective

The four main figures should make the scientific story understandable before the reader reaches Methods:

1. **Figure 1: learnability.** Reproducible human EEG geometry can be used as a relational training signal, and neural guidance improves sealed neural alignment.
2. **Figure 2: independent EEG transfer.** The learned perturbation transfers to independent English-reading EEG.
3. **Figure 3: prospective cross-modal transfer.** The same frozen perturbation transfers prospectively to independent Mandarin language-network fMRI after a model-blind reliability gate.
4. **Figure 4: scope.** Reverse fMRI-to-EEG transfer is graded within E5, and stable bidirectional portability is reproduced across E5-large and E5-base but not universally across the tested multilingual encoders.

Technical diagnostics that do not advance one of these four arguments belong in Extended Data or Supplementary Information rather than being compressed into the main figures.

## Reproducibility contract

The authoritative builder is:

`scripts/paper/build_nmi_main_figures_v3.py`

It reads only:

- committed frozen derived development values in `paper/figure_data/chineseeeg_development_v1.json`;
- already-completed derived result CSVs under `outputs/`;
- no raw neural data are required for figure assembly once the analysis outputs exist.

The builder automatically locates the frozen ZuCo and SMN4Lang participant-level output tables by required column signatures and uses fixed explicit paths for the post-confirmatory dose-response and model-family panel when available. Every input file used in a run is SHA-256 hashed into `source_manifest.json`.

The builder writes all four figures in:

- PDF, editable vector;
- SVG, editable vector;
- PNG, 600 dpi.

The maximum authored width is 178 mm, below the Nature Machine Intelligence 180-mm maximum. Typography is set at final physical size rather than enlarged and later downscaled.

## Visual system

- Sans-serif family with Arial/Helvetica-compatible fallbacks.
- Restrained, color-blind-safe palette: dark navy for primary summaries, teal for neural/reliability evidence, orange for neural-guided effects, blue for external targets, neutral gray for controls and non-primary encoders.
- No rainbow scales.
- No decorative gradients, shadows, 3D effects or unnecessary borders.
- Panel labels are bold and outside the plotting region.
- Legends are avoided when direct encoding is clearer.
- Axes are stripped to left/bottom spines unless a diagram has no axes.
- Participant-level observations remain visible whenever the primary inference is participant-level.
- Mean and bootstrap intervals are visually secondary to the participant data, not replacements for them.
- Restricted axes are used only for point/line displays where appropriate; bar charts are avoided for small RSA differences.
- Figure titles belong in manuscript legends. Inside the art, each panel gets only a short claim-oriented subtitle.

## Figure-specific decisions

### Figure 1

The previous generic-semantic benchmark panel is removed from the main figure because it dilutes the learnability story. The main figure contains the conceptual pipeline, reliability-led target, held-out run correspondence and sealed run-07 comparison. Generic semantic dissociation remains a valid Extended Data/Supplementary result.

### Figure 2

The participant-paired ZuCo transfer is the dominant visual evidence. Reliability is retained as a compact prerequisite panel. The delta panel shows all 17 participant effects plus the mean bootstrap interval.

### Figure 3

The frozen causal-HRF implementation schematic is moved out of the main figure. The main figure instead gives visual priority to the prospective design, model-blind reliability gate and the 12 participant paired transfer result. Detailed causal prefix/HRF/nuisance construction belongs in Methods/Extended Data.

### Figure 4

The old miscellaneous boundary panel is replaced by a scope figure: reverse-direction dose response, a compact bidirectionality statement, and two matched model-family panels showing all three seeds in each direction. E5 variants are visually emphasized but all prespecified models and seeds remain visible.

## Nature Machine Intelligence production target

Current official Nature Machine Intelligence guidance states that figure panels should be at least 300 dpi, no wider than 180 mm, use a 5-7 pt sans-serif font for standard labels, and retain editable labels/vector art where possible. The v3 system exports 600-dpi PNG plus editable PDF/SVG and uses approximately 6.7-8.4 pt standard text at final width.

## Main versus supplementary policy

The main figures should communicate the four arguments above. Detailed tables should carry exact seed-, model-, lambda- and participant-level statistics. Candidate Extended Data items include:

- full reliability matrix across external datasets;
- generic semantic benchmark results;
- model-space conservation metrics;
- complete ChineseEEG reverse-direction multi-seed dose characterization;
- MEG reliability-boundary analysis;
- full model-family source-learning diagnostics;
- AHBA/transcriptomic analyses.

## Required QA before manuscript integration

1. Run the named RunRelay figure-build task at an exact commit.
2. Inspect all four 600-dpi PNGs at full figure size and at approximate one-column/two-column print size.
3. Check for collisions, tiny text, wasted whitespace, misleading scales, hidden participant observations and inconsistent panel alignment.
4. Verify the source manifest hashes and source file paths.
5. If visual fixes are needed, commit a new exact figure-builder revision and run a new job. Do not hand-edit exported figures.

# NeuroSem agent instructions

## Project scope

Treat `vafaei-ar/NeuroSem` as the only active project when working from this repository unless the user explicitly expands scope.

Do not inspect, infer from, or mix in other repositories or projects owned by the user. Do not enumerate neighboring repositories to gather context. If a request appears to refer to another project, ask for clarification before reading or modifying it.

## RunRelay execution

This repository uses RunRelay for workstation execution.

- Project id: `neurosem`
- RunRelay control repository: `vafaei-ar/RunRelay`
- Execution manifest: `.runrelay/project.yaml`
- Bound RunRelay machine: `pshjl4vf24`
- Treat `.runrelay/project.yaml` as the authoritative list of named tasks and execution policy.
- For every RunRelay job for this repository, set `requested_machine_id` to `pshjl4vf24`. Never create or claim to queue a job with a missing, null, empty, inferred-from-another-project, or different machine id.
- For public-repository safe-mode execution, require exact commits and Telegram human approval through the private RunRelay control repository.
- Prefer RunRelay over asking the user to execute shell commands manually when an equivalent named task can be used safely.

When a new execution operation is needed, add a narrowly scoped named task to `.runrelay/project.yaml` rather than using arbitrary shell execution.

## Standard execution flow

1. Modify NeuroSem code/configuration in this repository.
2. Commit the intended state and retrieve the exact full commit SHA.
3. Re-read the committed `.runrelay/project.yaml` and this `AGENTS.md` before creating the job.
4. Create a unique job JSON under `jobs/` in `vafaei-ar/RunRelay` using project id `neurosem`, the exact NeuroSem commit, an allowed task, and `requested_machine_id: "pshjl4vf24"`.
5. Verify the created job file in the RunRelay repository. Do not tell the user that Telegram approval is pending unless the saved job has a non-empty machine id and all required fields.
6. Let Telegram provide the approval boundary.
7. After approval, RunRelay may safely fast-forward the clean local NeuroSem checkout to the requested exact commit. It must refuse dirty tracked files, divergent history, or non-fast-forward movement rather than overwrite local work.
8. Inspect the actual RunRelay result and safe declared artifacts before deciding the next change.
9. If a fix is needed, create a new commit and a new exact-commit job rather than weakening validation.

## Artifacts and sensitive data

Use RunRelay artifact storage only for safe derived outputs such as reports, figures, aggregate tables, metrics, sanitized logs, and deliberately shareable archives.

Do not upload PHI, credentials, `.env` files, raw sensitive datasets, restricted Penn State data, or entire project roots as artifacts.

## Scientific context

Use the files and documentation in this repository as the source of truth for NeuroSem-specific scientific assumptions, datasets, analyses, and workflow state. Do not import scientific context from another project unless the user explicitly requests it.

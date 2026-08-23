# NeuroSem agent instructions

## Project scope

Treat `vafaei-ar/NeuroSem` as the only active project when working from this repository unless the user explicitly expands scope.

Do not inspect, infer from, or mix in other repositories or projects owned by the user. Do not enumerate neighboring repositories to gather context. If a request appears to refer to another project, ask for clarification before reading or modifying it.

## RunRelay execution

This repository uses RunRelay for workstation execution.

- Project id: `neurosem`
- RunRelay control repository: `vafaei-ar/RunRelay`
- Execution manifest: `.runrelay/project.yaml`
- Treat `.runrelay/project.yaml` as the authoritative list of named tasks and execution policy.
- Use the repository's configured/bound RunRelay machine. Do not borrow a machine id from another project.
- For public-repository safe-mode execution, require exact commits and Telegram human approval through the private RunRelay control repository.
- Prefer RunRelay over asking the user to execute shell commands manually when an equivalent named task can be used safely.

When a new execution operation is needed, add a narrowly scoped named task to `.runrelay/project.yaml` rather than using arbitrary shell execution.

## Standard execution flow

1. Modify NeuroSem code/configuration in this repository.
2. Commit the intended state and retrieve the exact full commit SHA.
3. Create a unique job JSON under `jobs/` in `vafaei-ar/RunRelay` using project id `neurosem`, the exact NeuroSem commit, an allowed task, and the project-bound machine.
4. Let Telegram provide the approval boundary.
5. After approval, inspect the actual RunRelay result and safe declared artifacts before deciding the next change.
6. If a fix is needed, create a new commit and a new exact-commit job rather than weakening validation.

## Artifacts and sensitive data

Use RunRelay artifact storage only for safe derived outputs such as reports, figures, aggregate tables, metrics, sanitized logs, and deliberately shareable archives.

Do not upload PHI, credentials, `.env` files, raw sensitive datasets, restricted Penn State data, or entire project roots as artifacts.

## Scientific context

Use the files and documentation in this repository as the source of truth for NeuroSem-specific scientific assumptions, datasets, analyses, and workflow state. Do not import scientific context from another project unless the user explicitly requests it.

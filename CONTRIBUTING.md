# Contributing To SARIagent

This document defines the default collaboration workflow for this repository.

## Core Rules

- Do not commit private raw data unless the team has explicitly agreed to publish it.
- Do not commit generated outputs under `outputs/` unless there is a clear review need.
- Keep each branch focused on one change topic.
- Open a Pull Request instead of pushing directly to `main`.
- Document any data, model, or metadata assumptions in the PR description.

## Branch Strategy

`main` is the integration branch and should stay stable.

Create short-lived working branches from `main`:

- `feat/...`
- `fix/...`
- `docs/...`
- `refactor/...`
- `chore/...`

Examples:

- `feat/add-source-manifest-validation`
- `fix/docx-title-extraction`
- `docs/improve-setup-guide`

## Standard Workflow

1. Update local `main`

```powershell
git checkout main
git pull
```

2. Create a feature branch

```powershell
git checkout -b feat/your-change
```

3. Make your changes and inspect status

```powershell
git status
```

4. Commit with a clear message

```powershell
git add .
git commit -m "feat: describe your change"
```

5. Push the branch

```powershell
git push -u origin feat/your-change
```

6. Open a Pull Request on GitHub

## Commit Message Style

Recommended format:

```text
type: short summary
```

Common `type` values:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `chore`

Examples:

- `feat: add manifest-based metadata enrichment`
- `fix: prevent empty chunk merge regression`
- `docs: add repository quick start`

## Pull Request Expectations

Each Pull Request should include:

- what changed
- why the change is needed
- how it was tested
- whether any local data or outputs were used
- whether follow-up work is still needed

Keep PRs small enough to review. If a change is large, split it into multiple PRs.

## Review Checklist

Reviewers should verify:

- the branch solves the stated problem
- no unintended binary or private files were added
- `data/` and `outputs/` are still handled appropriately
- documentation is updated if behavior changed
- integration with Task 03 is still valid if affected

## Data Handling

Default policy:

- keep raw source materials in `data/` locally
- keep generated outputs in `outputs/` locally
- obtain real project data through the designated internal channel
- for this project, members who need source data should contact 肖老师
- only publish sample, desensitized, or explicitly approved files

Do not force-add files under `data/` or `outputs/` unless the team has explicitly approved the specific files.

If the team decides to version any real data in the future, document:

- data ownership
- update frequency
- privacy constraints
- storage strategy

## Protected Main Branch

Recommended GitHub repository settings:

- protect `main`
- require Pull Request review before merge
- block direct pushes to `main`
- require branches to be up to date before merge

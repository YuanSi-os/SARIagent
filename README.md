# SARIagent

SARIagent is a knowledge processing and retrieval support project for the "党建 + 研究生业务" scenario. The current repository mainly contains the Task 04 pipeline: ingesting raw documents, cleaning text, splitting semantically meaningful chunks, attaching metadata, and optionally forwarding the processed records to a vector storage layer.

At this stage, the runnable core is under `task04_pipeline/`. It supports:

- Reading `md`, `docx`, and `pdf` source files
- Normalizing and cleaning raw text
- Splitting documents into semantic chunks
- Attaching metadata such as source path, source URL, source name, and publish year
- Exporting JSONL / JSON output
- Optionally calling `insert_vectors(data)` to hand off records to Task 03

## Repository Structure

```text
SARIagent/
+-- task04_pipeline/          # Task 04 data processing pipeline
|   +-- build_chunks.py       # Main entry point
|   +-- task03_adapter.py     # Adapter for insert_vectors(data)
|   +-- source_manifest.example.json
|   \-- README.md
+-- data/                     # Versioned raw documents used by the pipeline
+-- outputs/                  # Versioned generated results
+-- ref/                      # Reference documents and design materials
+-- .gitignore
+-- CONTRIBUTING.md
\-- README.md
```

## Repository Data Policy

This repository currently versions both `data/` and `outputs/` on GitHub.

Current intent:

- `data/` stores the source files used by the pipeline
- `outputs/` stores generated chunking results that the team wants to review and share
- collaborators can clone the repository and immediately inspect both input and output artifacts

When adding new files to these directories, keep these rules in mind:

- avoid uploading files that contain private or unapproved content
- avoid committing oversized binaries unless the team has agreed to keep them in Git
- if files become too large for normal Git collaboration, consider moving them to Git LFS or external storage

## Environment

Recommended:

- Python 3.9+
- Windows PowerShell or any shell with Python available

Notes:

- `md` input works with the standard library only.
- `docx` input is parsed through `zipfile` and XML, so no extra dependency is required.
- `pdf` input first tries `pdftotext`; if unavailable, it falls back to `pypdf` or `PyPDF2`.

If you need PDF support and do not have `pdftotext`, install one of:

```powershell
pip install pypdf
```

or

```powershell
pip install PyPDF2
```

## Quick Start

Run the pipeline on a local document:

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\graduate\your_document.docx" `
  --domain graduate `
  --output "outputs\graduate_chunks.jsonl" `
  --pretty
```

The command will:

- read the input file
- clean and normalize the text
- split it into chunks
- write JSONL output to `outputs/graduate_chunks.jsonl`
- write a pretty JSON file when `--pretty` is set

## Input And Output

### Supported Input Types

- Markdown: `.md`
- Word documents: `.docx`
- PDF documents: `.pdf`

### Output Format

Each output line is a JSON object containing:

- `id`
- `text`
- `metadata`

Typical metadata includes:

- `domain`
- `source_file`
- `source_path`
- `source_type`
- `source_url`
- `source_name`
- `doc_title`
- `doc_code`
- `publish_date`
- `publish_year`
- `section_path`
- `chunk_id`
- `chunk_index`
- `char_count`
- `token_estimate`

## Using A Source Manifest

If you want to attach official source links or collection information, use the manifest file:

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\graduate\your_document.docx" `
  --domain graduate `
  --manifest "task04_pipeline\source_manifest.example.json" `
  --output "outputs\graduate_chunks.jsonl" `
  --pretty
```

The manifest can be used to supply:

- `source_url`
- `source_name`
- `source_type`
- `publish_year`
- `extra_metadata`

## Optional Vector Database Insertion

If Task 03 exposes `insert_vectors(data)`, the pipeline can call it directly:

```powershell
python task04_pipeline\build_chunks.py `
  --input "data\graduate\your_document.docx" `
  --domain graduate `
  --output "outputs\graduate_chunks.jsonl" `
  --insert
```

The adapter searches for `insert_vectors` in one of these modules:

- `task03_vector_api.py`
- `vector_api.py`
- `rag/vector_store.py`

Expected signature:

```python
def insert_vectors(data: list[dict]) -> None:
    ...
```

## Team Collaboration

This repository is set up for GitHub-based collaboration. Recommended workflow:

1. Keep `main` stable and deployable.
2. Create a dedicated branch for each feature or fix.
3. Push that branch to GitHub.
4. Open a Pull Request for review.
5. Merge into `main` only after review.

Examples:

```powershell
git checkout main
git pull
git checkout -b feat/chunking-rules
```

After finishing work:

```powershell
git add .
git commit -m "feat: refine chunk splitting rules"
git push -u origin feat/chunking-rules
```

Then open a Pull Request on GitHub.

Detailed collaboration rules are documented in `CONTRIBUTING.md`.

## Daily Collaboration Workflow

Because `main` is protected, team members should not work directly on `main`.

Use this workflow for every task:

1. Update local `main`

```powershell
git checkout main
git pull
```

2. Create a task branch

```powershell
git checkout -b feat/your-task-name
```

3. Make changes locally

4. Commit and push the branch

```powershell
git add .
git commit -m "feat: describe your change"
git push -u origin feat/your-task-name
```

5. Open a Pull Request on GitHub

6. Merge into `main` only after review

## Main Branch Protection

The repository is intended to use a protected `main` branch.

Expected team behavior:

- do not push directly to `main`
- do not develop new work on `main`
- always open a Pull Request from a feature branch
- keep Pull Requests focused and reviewable

If direct pushes to `main` are rejected by GitHub, that is expected behavior after branch protection is enabled.

## Recommended Team Rules

For this repository, the default collaboration rules should be:

- one task, one branch
- one branch, one Pull Request
- do not mix documentation changes, data updates, and code refactors in one large PR unless they are tightly related
- explain any `data/` or `outputs/` changes in the PR description
- if a PR changes generated outputs, state how those outputs were produced

## Pull Request Template

This repository includes a built-in Pull Request template at `.github/pull_request_template.md`.

When creating a PR, contributors should clearly describe:

- what changed
- why it changed
- what was tested
- whether `data/` or `outputs/` were modified
- whether follow-up work is still needed

## Common Team Commands

Check current branch and status:

```powershell
git branch
git status
```

Sync local `main`:

```powershell
git checkout main
git pull
```

Create a new work branch:

```powershell
git checkout -b feat/example-change
```

Push a branch for review:

```powershell
git push -u origin feat/example-change
```

Switch back after a branch is merged:

```powershell
git checkout main
git pull
```

## Recommended Branch Names

- `feat/...` for new features
- `fix/...` for bug fixes
- `docs/...` for documentation changes
- `refactor/...` for structural cleanup
- `chore/...` for maintenance tasks

Examples:

- `feat/add-party-manifest-support`
- `fix/pdf-read-fallback`
- `docs/update-readme`

## Pull Request Workflow

Before opening a Pull Request:

- sync with the latest `main`
- make sure the branch is focused on one topic
- include the reason for the change
- describe what was tested
- describe whether `data/` or `outputs/` changed

For team use, reviewers should check:

- whether the change matches the intended task
- whether data and outputs were intentionally updated
- whether data paths and outputs are handled safely
- whether the change affects downstream Task 03 integration

## Suggested Next Steps

- Add a small anonymized demo file under a future `examples/` directory for new collaborators
- Add automated tests for chunk splitting and metadata extraction
- Protect the `main` branch on GitHub and require Pull Request reviews before merge

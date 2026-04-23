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
+-- data/                     # Local raw documents, not committed by default
+-- outputs/                  # Local generated results, not committed by default
+-- ref/                      # Reference documents and design materials
+-- .gitignore
+-- CONTRIBUTING.md
\-- README.md
```

## Why `data/` And `outputs/` Are Not On GitHub

`data/` and `outputs/` are intentionally ignored by `.gitignore`.

Reasons:

- `data/` usually contains original source documents, which may be private, copyrighted, or too large for routine collaboration.
- `outputs/` contains generated artifacts. These files can usually be regenerated from the source pipeline and should not create noisy diffs in Git.
- Keeping both directories local makes the repository smaller and reduces accidental leakage of internal materials.

If you later decide to publish part of the data, prefer one of these approaches:

1. Commit only small desensitized sample files for demonstration.
2. Store large datasets outside GitHub and document the download process.
3. Use Git LFS only when you are sure the team wants binary files versioned in Git.

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

- rebase or merge the latest `main`
- make sure the branch is focused on one topic
- include the reason for the change
- describe what was tested

For team use, reviewers should check:

- whether the change matches the intended task
- whether data paths and outputs are handled safely
- whether generated files are excluded unless intentionally committed
- whether the change affects downstream Task 03 integration

## Suggested Next Steps

- Add a small anonymized demo file under a future `examples/` directory for new collaborators
- Add automated tests for chunk splitting and metadata extraction
- Protect the `main` branch on GitHub and require Pull Request reviews before merge

# MongoDB Specifications — Agent Guidance

## Repository Purpose

This is the official MongoDB Specifications repository containing technical specifications for MongoDB drivers and
associated products. It includes:

- Specification documents (Markdown in `source/`)
- Unified test format files (YAML + auto-generated JSON) consumed by all MongoDB drivers
- Documentation published via MkDocs and ReadTheDocs

## Common Commands

### Documentation

```bash
pip install -r source/requirements.txt   # Install Python deps
mkdocs serve                             # Live preview at localhost:8000
mkdocs build --strict                    # Build (CI mode, no warnings allowed)
```

### Pre-commit Hooks

```bash
pre-commit install                                          # Set up hooks
pre-commit run --all-files                                  # Run all hooks manually
pre-commit run --all-files --hook-stage manual shellcheck   # Run shellcheck manually
```

### YAML → JSON Test Conversion

CI will fail if JSON files are out of date with their YAML sources. Always run `make -C source` after editing YAML test
files.

```bash
npm install -g js-yaml   # Required once
make -C source           # Convert most YAML test files to JSON
```

### Schema Latest Update (after adding a new unified test format schema version)

```bash
make update-schema-latest -C source
```

## Architecture

### Unified Test Format

The unified test format (`source/unified-test-format/`) defines a YAML/JSON schema for cross-driver tests. Key rules:

- Schema versions live in `source/unified-test-format/schema-*.json`; `schema-latest.json` must match the highest
    version (run `make update-schema-latest -C source` to update it)
- CI validates test files against the declared schema version using `ajv-cli`. Using any fields from a newer schema
    version than declared will fail validation.

### Documentation Build (`mkdocs.yml`)

MkDocs with `pymdown-extensions` and `mkdocs-github-admonitions-plugin`. The navigation is largely auto-generated via
`scripts/generate_index.py`. The build must pass in `--strict` mode (no warnings).

## Linting & Formatting

| Tool                  | Purpose                                     |
| --------------------- | ------------------------------------------- |
| `mdformat`            | Auto-formats Markdown (GFM, 120-char lines) |
| `markdown-link-check` | Validates links                             |
| `codespell`           | Spell checking                              |
| `shellcheck`          | Shell script linting                        |

All checks run via `pre-commit`. CI enforces them in `.github/workflows/lint.yml`.

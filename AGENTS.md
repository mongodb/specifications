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
pre-commit install           # Set up hooks
pre-commit run --all-files   # Run all hooks manually
```

### YAML → JSON Test Conversion

```bash
make -C source                           # Convert YAML test files to JSON (requires npm js-yaml)
```

### Test Generation Scripts (in `source/etc/`)

```bash
python source/etc/generate-error-tests.py     # SDAM error tests
python source/etc/generate-corpus.py          # Client-side encryption corpus tests
```

## Architecture

### Specification Documents (`source/`)

Each subdirectory under `source/` is a specification area (e.g., `crud/`, `transactions/`, `auth/`). Specs are written
in GitHub Flavored Markdown at 120-character line width. Each spec typically contains:

- `*.md` — the specification itself
- `tests/` — YAML test files (human-editable) and auto-generated JSON (never edit manually)

### Unified Test Format

The unified test format (`source/unified-test-format/`) defines a YAML/JSON schema for cross-driver tests. Key rules:

- **Always use the lowest possible schema version** that satisfies a test's requirements — do not default to the latest
- YAML files are the source of truth; JSON files are auto-generated and committed
- Schema versions live in `source/unified-test-format/schema-*.json`; `schema-latest.json` symlinks to the current
    latest

### Test File Conventions

- YAML test files are human-editable and located in `tests/` subdirectories
- JSON files are generated automatically by CI from YAML — never edit `.json` test files manually
- Use `runOnRequirements` to restrict tests to specific server versions/topologies
- Topologies to consider: standalone, replica set, sharded cluster, load balanced

### Documentation Build (`mkdocs.yml`)

MkDocs with `pymdown-extensions` and `mkdocs-github-admonitions-plugin`. The navigation is largely auto-generated via
`generate_index.py`. The build must pass in `--strict` mode (no warnings).

## Linting & Formatting

| Tool                  | Purpose                                     |
| --------------------- | ------------------------------------------- |
| `mdformat`            | Auto-formats Markdown (GFM, 120-char lines) |
| `markdown-link-check` | Validates links                             |
| `codespell`           | Spell checking                              |
| `shellcheck`          | Shell script linting                        |

All checks run via `pre-commit`. CI enforces them in `.github/workflows/lint.yml`.

## PR Requirements

Per the PR template:

- Title must include a DRIVERS ticket (e.g., `DRIVERS-1234`)
- Update the spec changelog
- New tests must be validated against at least one driver implementation
- Tests must pass against all supported server versions and topologies

## Specification Writing Guidelines

From `source/driver-mantras.md`:

- Prefer **MUST** over **SHOULD** — wishy-washy specs produce incompatible drivers
- Be topology-agnostic wherever possible
- Minimize configuration options ("No Knobs" principle)
- Check wire protocol version, not server version
- Follow semantic versioning for behavior changes

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

```bash
npm install -g js-yaml   # Required once
make -C source           # Convert all YAML test files to JSON
```

### Schema Latest Update (after adding a new unified test format schema version)

```bash
make update-schema-latest -C source
```

### Test Generation Scripts (in `source/etc/`)

```bash
python source/etc/generate-error-tests.py     # SDAM error tests
python source/etc/generate-corpus.py          # Client-side encryption corpus tests
```

## Architecture

### Specification Documents (`source/`)

Each subdirectory under `source/` is a specification area (e.g., `crud/`, `transactions/`, `auth/`). Specs are written
in GitHub Flavored Markdown at 120-character line width, following the
[MongoDB Documentation Style Guidelines](https://www.mongodb.com/docs/meta/style-guide/). Each spec typically contains:

- `*.md` — the specification itself, with a `## Changelog` section at the bottom
- `tests/` — YAML test files (human-editable) and auto-generated JSON (never edit manually)

### Changelog Format

Each spec file contains its own `## Changelog` section (not a separate file). Entries are dated and prepended at the
top:

```markdown
## Changelog

- 2026-05-13: Describe the change made.

- 2024-03-01: Previous change.
```

### Unified Test Format

The unified test format (`source/unified-test-format/`) defines a YAML/JSON schema for cross-driver tests. Key rules:

- **Always use the lowest possible schema version** that satisfies a test's requirements — do not default to the latest
- YAML files are the source of truth; JSON files are auto-generated and committed
- Schema versions live in `source/unified-test-format/schema-*.json`; `schema-latest.json` must match the highest
    version (run `make update-schema-latest -C source` to update it)

### Test File Conventions

- YAML test files are human-editable and located in `tests/` subdirectories
- JSON files are generated automatically by CI from YAML — never edit `.json` test files manually
- Use `runOnRequirements` to restrict tests to specific server versions/topologies
- Topologies to consider: standalone, replica set, sharded cluster, load balanced

### Documentation Build (`mkdocs.yml`)

MkDocs with `pymdown-extensions` and `mkdocs-github-admonitions-plugin`. The navigation is largely auto-generated via
`generate_index.py`. The build must pass in `--strict` mode (no warnings).

## Test Authoring Rules

### Immutability of Existing Tests

**Do not modify existing tests** unless they are testing incorrect behavior. Default to creating new tests or new test
files instead of altering existing ones.

- Test files can only be deleted once **no driver runs them anymore**.
- For spec changes that remove functionality: use `runOnRequirements` (unified tests) or have drivers skip the test
    (non-unified tests like SDAM).
- Outdated prose tests must not be removed — mark them as such (e.g., strikethrough or *Removed*).

### Prose Test Numbering

Always use relative numbered bullets (`1.`) for prose tests. **New tests must be appended at the end** of the list,
since drivers may reference existing tests by number.

### Test Isolation

Only test functionality directly related to the new spec requirements. Omit irrelevant fields in command expectations.
This makes tests more resilient against future spec updates.

## Linting & Formatting

| Tool                  | Purpose                                     |
| --------------------- | ------------------------------------------- |
| `mdformat`            | Auto-formats Markdown (GFM, 120-char lines) |
| `markdown-link-check` | Validates links                             |
| `codespell`           | Spell checking                              |
| `shellcheck`          | Shell script linting                        |

All checks run via `pre-commit`. CI enforces them in `.github/workflows/lint.yml`.

## PR Requirements

Per the PR template and project workflow:

- Title must include a DRIVERS ticket (e.g., `DRIVERS-1234`)
- Update the `## Changelog` section in each modified spec file
- Spec changes must be implemented and validated in **at least 2 driver languages** before the PR can be merged
- Include links to the driver implementation PRs in the PR description (e.g.,
    `Python implementation: https://github.com/mongodb/mongo-python-driver/pull/…`)
- Tests must pass against all supported server versions and topologies

## Specification Writing Guidelines

From `source/driver-mantras.md`:

- Prefer **MUST** over **SHOULD** — wishy-washy specs produce incompatible drivers
- Be topology-agnostic wherever possible
- Minimize configuration options ("No Knobs" principle)
- Check wire protocol version, not server version
- Follow semantic versioning for behavior changes
- Design for the next release, not hypothetical future ones ("Defy augury")

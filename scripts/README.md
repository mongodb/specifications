# Scripts for use with Drivers specifications repository

## migrate_to_md

Use this file to automate the process of converting a specification from rst to GitHub Flavored Markdown.

The goal of the script is to do most of the work, including updating relative links to the new document from other
files. Note that all known features will translate, including explicit cross-reference markers (e.g. `.. _foo`) which
are translated to a `<div id="foo">`. It will also create a new changelog entry with today's date marking the
conversion.

### Prerequisites

```bash
brew install pandoc
brew install pre-commit
brew install python # or get python through your preferred channel
pre-commit install
```

### Usage

- Run the script as:

```bash
python3 -m venv .venv
source activate .venv/bin/activate
python -m pip install docutils
python scripts/migrate_to_md.py "source/<path_to_rst_file>"
```

- Address any errors that were printed during the run.

- Ensure that the generated markdown file is properly formatted.

- Ensure that the RST stub file has appropriate links to sections in the markdown file.

- Ensure that the links in the new file are working, by running `pre-commit run markdown-link-check` and addressing
  failures until that passes.

- Create a PR. When you commit the changes, the `mdformat` `pre-commit` hook will update the formatting as appropriate.

## generate_index

Use this file to generate the top level Markdown index file. It is independent to be used as a pre-commit hook.

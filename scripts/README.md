# Scripts for use with Drivers specifications repository

## migrate_to_md

Use this file to automate the process of converting a
specification from rst to GitHub Flavored Markdown.

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
python3 scripts/migrate_to_md.py "source/<path_to_rst_file>"
```

- Ensure that the generated markdown file is properly formatted.

- Add a changelog entry for the migration of the spec.

- Ensure the links in the file are up to date.  As we migrate files, relative links that point to `.rst` files will need to be updated.

  - Run `pre-commit run markdown-link-check` and address failures until that passes.
  - Run a `git grep` for the converted source file name
    and update any relative links to use the new `.md`
    extension.

- Remove the rst file using `git rm`.

- Create a PR.  When you commit the changes, the `mdformat` `pre-commit` hook will update the formatting as appropriate.

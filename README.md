# MongoDB Specifications

[![Documentation Status](https://readthedocs.org/projects/specifications/badge/?version=latest)](http://specifications.readthedocs.io/en/latest/?badge=latest)

This repository holds in progress and completed specification for features of MongoDB, Drivers, and associated products.
Also contained is a rudimentary system for producing these documents.

## Driver Mantras

See [Documentation](./source/driver-mantras.md).

## Writing Documents

Write documents using [GitHub Flavored Markdown](https://github.github.com/gfm/), following the
[MongoDB Documentation Style Guidelines](https://www.mongodb.com/docs/meta/style-guide/).

Store all source documents in the `source/` directory.

## Linting

This repo uses [pre-commit](https://pypi.org/project/pre-commit/) for managing linting. `pre-commit` performs various
checks on the files and uses tools that help follow a consistent style within the repo.

To set up `pre-commit` locally, run:

```bash
brew install pre-commit
pre-commit install
```

To run `pre-commit` manually, run `pre-commit run --all-files`.

To run a manual hook like `shellcheck` manually, run:

```bash
pre-commit run --all-files --hook-stage manual shellcheck
```

## Prose test numbering

When numbering prose tests, always use relative numbered bullets (`1.`). New tests must be appended at the end of the
test list, since drivers may refer to existing tests by number.

Outdated tests must not be removed completely, but may be marked as such (e.g. by striking through or replacing the
entire test with a note (e.g. *Removed*).

## Building Documents

We use [mkdocs](https://www.mkdocs.org/) to render the documentation. To see a live view of the documentation, in a
Python [venv](https://docs.python.org/3/library/venv.html) run:

```bash
pip install -r source/requirements.txt
mkdocs serve
```

To build the docs, use `mkdocs build`.

In CI we verify that there are no warnings. To replicate locally, run `mkdocs build --strict`.

## Converting to JSON

There are many YAML to JSON converters. There are even several converters called `yaml2json` in NPM. Alas, we are not
using `yaml2json` anymore, but instead the [js-yaml](https://www.npmjs.com/package/js-yaml) package. Use only that
converter, so that JSON is formatted consistently.

Run `npm install -g js-yaml`, then run `make` in the `source` directory at the top level of this repository to convert
all YAML test files to JSON.

## Licensing

All the specs in this repository are available under the
[Creative Commons Attribution-NonCommercial-ShareAlike 3.0 United States License](https://creativecommons.org/licenses/by-nc-sa/3.0/us/).

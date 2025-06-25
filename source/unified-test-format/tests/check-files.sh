#!/usr/bin/env bash

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <mode> files"
  echo "Modes:"
  echo "  valid: Check that files are valid"
  echo "  invalid: Check that files are invalid"
  exit 1
fi

mode=$1
shift

for file in "$@"; do
  schema=$(grep -m 1 "^schemaVersion:" "${file}" | sed -E 's:^schemaVersion\: .*(1\.[0-9]+).*$:\1:')
  minorSchemaVersion=$(echo "${schema}" | sed -E 's:1\.([0-9]+):\1:')
  schemaFile="../schema-${schema}.json"

  if [[ ! -f "${schemaFile}" ]]; then
    echo "Warning: File ${file} specifies an invalid schema ${schema}, using latest instead"
    schemaFile="../schema-latest.json"
    # Latest always uses json-schema draft-2019-09
    spec="draft2019"
  elif [[ "${minorSchemaVersion}" -gt "23" ]]; then
    # Starting with 1.24, the schema uses draft-2019-09
    spec="draft2019"
  else
    # Versions up to 1.23 use draft-7
    spec="draft7"
  fi

  ajv test --spec ${spec} -s "${schemaFile}" -d "${file}" --${mode}
done

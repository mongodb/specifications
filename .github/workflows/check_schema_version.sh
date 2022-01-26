#! /usr/bin/env bash

# Collect error codes so we can see all the invalid json files in one run
exitCode=0

# $1 - takes a single argument of the path to the JSON file containing a schemaVersion key at the top level.
function get_schema_version() {
  node << EOF
    const { readFileSync } = require('fs')
    const { load } = require('js-yaml')
    console.log(load(readFileSync("./$1", { encoding: 'utf-8' })).schemaVersion)
EOF
}

function get_all_schemaVersion_defining_files () {
  # look for all yaml files with "schemaVersion: ["'][1-9]"
  grep --include=*.{yml,yaml} --files-with-matches --recursive --word-regexp --regexp="schemaVersion: [\"'][1-9]" source | \
  # Remove the known invalid test files from 'unified-test-format/tests/invalid'
  grep --word-regexp --invert-match 'unified-test-format/tests/invalid' | \
  # sort the result!
  sort
}

for testFile in $(get_all_schemaVersion_defining_files)
do
    schemaVersion=$(get_schema_version "$testFile")
    if ! ajvCheck=$(ajv -s "source/unified-test-format/schema-$schemaVersion.json" -d "$testFile"); then
      exitCode=1
    fi
    echo "$ajvCheck using schema v$schemaVersion"
done

exit $exitCode

#! /usr/bin/env bash

# Collect error codes so we can see all the invalid json files in one run
exitCode=0

# $1 - takes a single argument of the path to the JSON file containing a schemaVersion key at the top level.
function get_schema_version() {
  js-yaml $1 | jq -r .schemaVersion
}

function get_json_schema_url () {
  schemaVersion=$(get_schema_version "$1")
  schemaFile="source/unified-test-format/schema-$schemaVersion.json"
  cat "$schemaFile" | jq -r '.["$schema"]'
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
    jsonSchemaURL=$(get_json_schema_url "$testFile")
    if [ "$jsonSchemaURL" = "https://json-schema.org/draft/2019-09/schema#" ]; then
      spec="draft2019"
    elif [ "$jsonSchemaURL" = "http://json-schema.org/draft-07/schema#" ]; then
      spec="draft7"
    else
      echo "Do not know how to validate $jsonSchemaURL"
      exit 1
    fi

    if ! ajvCheck=$(ajv --spec="$spec" -s "source/unified-test-format/schema-$schemaVersion.json" -d "$testFile"); then
      exitCode=1
    fi
    echo "$ajvCheck using schema v$schemaVersion"
done

exit $exitCode

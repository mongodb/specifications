#!user/bin/env bash

# Find the max X in unified-test-format/schema-1.X.json
max=0
for file in schema-1.*.json; do
  # Extract the version number from the filename
  version=${f##*schema-1.}
  version=${version%.json}

  if [[ $version =~ ^[0-9]+$ ]]; then
    # Compare the version number with the current max
    if ((version > max)); then
      max=$version
    fi
  fi
done

if ((max == 0)); then
  echo "No schema files found."
  exit 1
fi

# Compare that file vs schema-latest.json
expected="schema-$max.json"
if ! diff -u "$expected" schema-latest.json >/dev/null; then
  echo "schema-latest.json is not up to date with schema-$max.json"
  exit 1
fi

exit 0

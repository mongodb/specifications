SCHEMA=../schema-1.2.json

.PHONY: all invalid valid-fail valid-pass client-side-operations-timeout HAS_AJV

all: invalid valid-fail valid-pass client-side-operations-timeout

invalid: HAS_AJV
	@# Redirect stdout to hide expected validation errors
	@ajv test -s $(SCHEMA) -d "invalid/*.yml" --invalid > /dev/null && echo "invalid/*.yml passed test"

valid-fail: HAS_AJV
	@ajv test -s $(SCHEMA) -d "valid-fail/*.yml" --valid

valid-pass: HAS_AJV
	@ajv test -s $(SCHEMA) -d "valid-pass/*.yml" --valid

client-side-operations-timeout: HAS_AJV
	@ajv test -s $(SCHEMA) -d "../../client-side-operations-timeout/tests/*.yml" --valid

HAS_AJV:
	@if ! command -v ajv > /dev/null; then                \
	    echo 'Error: need "npm install -g ajv-cli"' 1>&2; \
	    exit 1;                                           \
	fi

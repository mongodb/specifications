SCHEMA=../schema-1.0.json

.PHONY: all invalid HAS_AJV

all: invalid

invalid:
	@if ajv test -s $(SCHEMA) -d "invalid/*" --invalid > /dev/null; then \
	    echo "PASSED";                                                   \
	else                                                                 \
	    echo "FAILED";                                                   \
	fi

HAS_AJV:
	@if ! command -v ajv > /dev/null; then                \
	    echo 'Error: need "npm install -g ajv-cli"' 1>&2; \
	    exit 1;                                           \
	fi

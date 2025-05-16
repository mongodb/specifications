YAML_FILES=$(shell find . -iname '*.yml')
JSON_FILES=$(patsubst %.yml,%.json,$(YAML_FILES))

all: $(JSON_FILES) HAS_JSYAML

%.json: %.yml
	tmpfile=$$(mktemp);               \
	if js-yaml $< > "$$tmpfile"; then \
	    mv "$$tmpfile" $@;            \
	else                              \
	    rm "$$tmpfile";               \
	    exit 1;                       \
	fi

HAS_JSYAML:
	@if ! command -v js-yaml > /dev/null; then            \
	    echo 'Error: need "npm install -g js-yaml"' 1>&2; \
	    exit 1;                                           \
	fi

VERSION := $(shell \
	find unified-test-format -maxdepth 1 -type f -name 'schema-1.*.json' \
	| sed -E 's:.*/schema-1\.([0-9]+)\.json:\1:' \
	| sort -n \
	| tail -n1 \
)

.PHONY: update-schema-latest
update-schema-latest:
	cp unified-test-format/schema-1.$(VERSION).json \
		unified-test-format/schema-latest.json


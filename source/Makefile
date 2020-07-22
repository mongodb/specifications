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

HAS_AJV:
	@if ! command -v ajv > /dev/null; then            \
	    echo 'Error: need "npm install -g ajv"' 1>&2; \
	    exit 1;                                           \
	fi

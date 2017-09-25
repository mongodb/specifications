YAML_FILES=$(shell find . -iname '*.yml')
JSON_FILES=$(patsubst %.yml,%.json,$(YAML_FILES))

all: $(JSON_FILES) HAS_JSYAML

%.json: %.yml
	js-yaml $< > $@

HAS_JSYAML:
	@if ! command -v js-yaml > /dev/null; then            \
	    echo 'Error: need "npm install -g js-yaml"' 1>&2; \
	    exit 1;                                           \
	fi

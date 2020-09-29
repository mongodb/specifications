YAML_FILES=$(shell find tests/ -iname '*.yml')
JSON_FILES=$(shell find tests/ -iname '*.json')

.PHONY: all validate HAS_AJV

all: validate

validate: HAS_AJV
	@for f in $(YAML_FILES) $(JSON_FILES); do   \
	    ajv validate -s schema-1.0.json -d $$f; \
	done

HAS_AJV:
	@if ! command -v ajv > /dev/null; then            \
	    echo 'Error: need "npm install -g ajv"' 1>&2; \
	    exit 1;                                       \
	fi

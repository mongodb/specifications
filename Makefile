.PHONY: all lint doc8 rstcheck html serve clean prep

.SILENT:

all: html lint

# Lint rst files
lint: rstcheck doc8

# Input rST files
RST_FILES=$(shell find source/ -name '*.rst')

prep:
	mkdir -p build/

DOC8_STAMP := build/doc8.stamp
doc8: $(DOC8_STAMP)
$(DOC8_STAMP): $(RST_FILES) prep
	echo "Running doc8..."
	doc8 --quiet source/
	echo "Running doc8... - OK"
	touch $@

RSTCHECK_STAMP := build/rstcheck.stamp
rstcheck: $(RSTCHECK_STAMP)
$(RSTCHECK_STAMP): $(RST_FILES) prep
	echo "Running rstcheck..."
	rstcheck --recursive source/ \
		--ignore-language c,python,java \
		--report error
	echo "Running rstcheck... - OK"
	touch $@

# Build the Sphinx HTML rendering of the documentation pages
html: build/html.stamp
SPHINX_ARGS := -Wnaj12 source/ build/html/
build/html.stamp: $(RST_FILES) source/conf.py $(RSTCHECK_STAMP) $(DOC8_STAMP) prep
	echo "Building HTML pages..."
	sphinx-build $(SPHINX_ARGS)
	echo "HTML Pages were written to ./build/html"
	touch $@

# Run an HTTP server on localhost serving the HTML directory
serve:
	sphinx-autobuild $(SPHINX_ARGS)

clean:
	rm build/ -rf

.PHONY: all lint doc8 rstcheck html _build-html serve clean

.SILENT:

all: html lint

# Lint rst files
lint: rstcheck doc8

doc8:
	echo "Running doc8..."
	doc8 --quiet source/
	echo "Running doc8... - OK"

rstcheck:
	echo "Running rstcheck..."
	rstcheck --recursive source/ \
		--ignore-language c,python,java \
		--report error
	echo "Running rstcheck... - OK"

# Build the Sphinx HTML rendering of the documentation pages
html: build/html.stamp
# Input rST files
RST_FILES=$(shell find source/ -name '*.rst')
build/html.stamp: $(RST_FILES) source/conf.py
	$(MAKE) _build-html
	touch $@
_build-html:
	echo "Building HTML pages..."
	sphinx-build -Wqnaj12 source/ build/html/
	echo "HTML Pages were written to ./build/html"

# Run an HTTP server on localhost serving the HTML directory
serve:
	sphinx-autobuild -Wqnaj12 source build/html/

clean:
	rm build/ -rf

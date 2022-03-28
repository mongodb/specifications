.PHONY: all lint doc8 rstcheck html _build-html run-server clean

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
	sphinx-build -Wqnaj8 source/ build/html/
	echo "HTML Pages were written to ./build/html"

# Run an HTTP server on localhost serving the HTML directory
run-server:
	mkdir -p build/html/
	python3 -m http.server --directory build/html/ --bind 127.0.0.1

clean:
	rm build/ -rf

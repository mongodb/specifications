#!/usr/bin/python

import os

input_dirs = ['source/']

build_dir = 'build/'
OUTPUT_FILE = build_dir + 'makefile.generated'

JOB = "\n\t"
TARGET = "\n"

######################################################################

def generate_file_tree(input_dir):
    targets = []

    for dirname, dirnames, filenames in os.walk(input_dir):
        for filename in filenames:
            source = os.path.join(dirname, filename)
            target = os.path.join('build/', filename).rsplit('.',1)[0]
            shortcut = filename.rsplit('.',1)[0]

            if source.rsplit('.',1)[1] == "tmpl":
                pass
            else:
                targets.append((source, target, shortcut))

    return targets

def generate_converters(input_dir, output_dir):
    tex_converter = (JOB + "@$(LATEXCMD) $< >$@" +
                     JOB + "@echo [rst2latex]: created '$@'")
    html_converter = (JOB + "@$(HTMLCMD) $< >$@" +
                      JOB + "@echo [rst2html]: created '$@'")

    converters = (TARGET + output_dir + "%.tex" + ":" + input_dir + "%.rst" + tex_converter +
                  TARGET + output_dir + "%.tex" + ":" + input_dir + "%.txt" + tex_converter +
                  TARGET + output_dir + "%.html" + ":" + input_dir + "%.rst" + html_converter +
                  TARGET + output_dir + "%.html" + ":" + input_dir + "%.txt" + html_converter)

    return converters

def generate_builders(output_dir):
    pdf_builder = (TARGET + output_dir + "%.pdf" + ":" + output_dir + "%.tex" +
                   JOB + "@$(PDFCMD) '$<' >|$@.log" +
                   JOB + "@echo [pdflatex]: \(1/3\) built '$@'" +
                   JOB + "@$(PDFCMD) '$<' >>$@.log" +
                   JOB + "@echo [pdflatex]: \(2/3\) built '$@'" +
                   JOB + "@$(PDFCMD) '$<' >>$@.log" +
                   JOB + "@echo [pdflatex]: \(3/3\) built '$@'" +
                   JOB + "@echo [PDF]: see '$@.log' for a full report of the pdf build process.")

    builder = pdf_builder

    return builder

def build_latex_targets(source, target):
    intermediate = target.rsplit('.',1)[0] + ".tex"

    output = (TARGET + target + ".pdf" + ':' + source +
              TARGET + intermediate + ":" + source)

    return output

def build_html_targets(source, target):
    output = (target + ".html" + ':' + source)

    return output

def build_shortcut_targets(target, shortcut):
    output = (shortcut + ':' + target + ".html" + " " + target + ".pdf")

    return output

######################################################################

class GeneratedMakefile(object):
    def __init__(self):

        self.converters = []
        self.targets = []

        self.builder = generate_builders(build_dir)

        for dir in input_dirs:
            self.converters.append(generate_converters(dir, build_dir))

        for dir in input_dirs:
            for (src, trg, shc) in generate_file_tree(dir):
                self.targets.append(build_latex_targets(src, trg))
                self.targets.append(build_html_targets(src, trg))
                self.targets.append(build_shortcut_targets(trg, shc))

makefile = GeneratedMakefile()

########################################################################

def main():
    output = open(OUTPUT_FILE, "w")

    for line in makefile.converters:
        output.write(line)

    output.write(makefile.builder)
    output.write('\n\n')

    for line in makefile.targets:
        output.write(line)
        output.write('\n')

    output.close()

if __name__ == "__main__":
    main()

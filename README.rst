======================
MongoDB Specifications
======================

This repository holds in progress and completed specification for
features of MongoDB, Drivers, and associated products. Also contained
is a rudimentary system for producing these documents.

Writing Documents
-----------------

Write documents using `reStructuredText`_, following the `MongoDB
Documentation Style Guidelines <http://docs.mongodb.org/manual/meta/style-guide/>`_.

Store all source documents in the ``source/`` directory.

.. _`reStructuredText`: http://docutils.sourceforge.net/rst.html

Building Documents
------------------

To build documents issue the ``make`` command in a local copy of this
repository. The output PDFs end up in the ``build/`` directory. The
build depends on:

- `Python Docutils <http://pypi.python.org/pypi/docutils>`_

- A functioning basic LaTeX/TeX install with ``pdflatex``. If you run
  OS X, use `MacTeX`_

``make all`` will build all documents in the ``source/`` folder.  The
system builds all targets in ``build/``.

Run ``make setup`` to generate (or regenerate) a ``makefile.generated``
file which provides specific targets for all files in the source file
so you can choose to compile only some of the files that you
need. Once generated, running "``make [file-name-without-extension]``"
will rebuild only those files (if needed.)

Use ``make clean`` to remove the ``build/`` directory and "``make
cleanup``" to remove the LaTeX by-products from ``build/``.

.. _`MacTeX` : http://www.tug.org/mactex/

Licensing
----------------
All the specs in this repository are available under the  `Creative Commons Share Alike 3.0 license <https://creativecommons.org/licenses/by-nc-sa/3.0/>`_.

In the future...
----------------

- Templates will have logos, and templates for authorship, copyright,
  disclaimers, etc.

- Non-PDF output targets.

If you have specific feature requests, or need help getting things
running, please contact samk@10gen.com.

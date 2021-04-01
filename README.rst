======================
MongoDB Specifications
======================

This repository holds in progress and completed specification for
features of MongoDB, Drivers, and associated products. Also contained
is a rudimentary system for producing these documents.

Driver Mantras
--------------

When developing specifications -- and the drivers themselves -- we follow the
following principles:

Strive to be idiomatic, but favor consistency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers attempt to provide the easiest way to work with MongoDB in a given 
language ecosystem, while specifications attempt to provide a consistent 
behavior and experience across all languages. Drivers should strive to be as 
idiomatic as possible while meeting the specification and staying true to the 
original intent.

No Knobs
~~~~~~~~

Too many choices stress out users.  Whenever possible, we aim to minimize the
number of configuration options exposed to users.  In particular, if a typical
user would have no idea how to choose a correct value, we pick a good default
instead of adding a knob.

Topology agnostic
~~~~~~~~~~~~~~~~~

Users test and deploy against different topologies or might scale up from
replica sets to sharded clusters.  Applications should never need to use the
driver differently based on topology type.

Where possible, depend on server to return errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The features available to users depend on a server's version, topology, storage
engine and configuration.  So that drivers don't need to code and test all
possible variations, and to maximize forward compatibility, always let users
attempt operations and let the server error when it can't comply.  Exceptions
should be rare: for cases where the server might not error and correctness is
at stake.

Minimize administrative helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Administrative helpers are methods for admin tasks, like user creation.  These
are rarely used and have maintenance costs as the server changes the
administrative API.  Don't create administrative helpers; let users rely on
"RunCommand" for administrative commands.

Check wire version, not server version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When determining server capabilities within the driver, rely only on the
maxWireVersion in the hello response, not on the X.Y.Z server version.  An
exception is testing server development releases, as the server bumps wire
version early and then continues to add features until the GA.

When in doubt, use "MUST" not "SHOULD" in specs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specs guide our work.  While there are occasionally valid technical reasons for
drivers to differ in their behavior, avoid encouraging it with a wishy-washy
"SHOULD" instead of a more assertive "MUST".

Defy augury
~~~~~~~~~~~

While we have some idea of what the server will do in the future, don't design
features with those expectations in mind.  Design and implement based on what
is expected in the next release.

Case Study: In designing OP_MSG, we held off on designing support for Document
Sequences in Replies in drivers until the server would support it. We
subsequently decided not to implement that feature in the server.

The best way to see what the server does is to test it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For any unusual case, relying on documentation or anecdote to anticipate the
server's behavior in different versions/topologies/etc. is error-prone.  The
best way to check the server's behavior is to use a driver or the shell and
test it directly.

Drivers follow semantic versioning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers should follow X.Y.Z versioning, where breaking API changes require a
bump to X.  See `semver.org <https://semver.org/>`_  for more.

Writing Documents
-----------------

Write documents using `reStructuredText`_, following the `MongoDB
Documentation Style Guidelines <https://docs.mongodb.com/meta/style-guide/>`_.

Store all source documents in the ``source/`` directory.

.. _`reStructuredText`: http://docutils.sourceforge.net/rst.html

Prose test numbering
--------------------

When numbering prose tests, always use relative numbered bullets (``#.``). New
tests must be appended at the end of the test list, since drivers may refer to
existing tests by number.

Outdated tests must not be removed completely, but may be marked as such (e.g.
by striking through or replacing the entire test with a note (e.g. **Removed**).

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

Converting to JSON
------------------

There are many YAML to JSON converters. There are even several converters called
``yaml2json`` in NPM.  Alas, we are not using ``yaml2json`` anymore, but instead
the `js-yaml <https://www.npmjs.com/package/js-yaml>`_ package. Use only that
converter, so that JSON is formatted consistently.

Run ``npm install -g js-yaml``, then run ``make`` in the ``source`` directory
at the top level of this repository to convert all YAML test files to JSON.

Licensing
----------------
All the specs in this repository are available under the  `Creative Commons Attribution-NonCommercial-ShareAlike 3.0 United States License <https://creativecommons.org/licenses/by-nc-sa/3.0/us/>`_.

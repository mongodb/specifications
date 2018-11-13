=======================
URI Options Tests
=======================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the URI Options spec.

These tests use the same format as the Connection String spec tests.

Version
-------

Files in the "specifications" repository have no version scheme. They are not
tied to a MongoDB server version.

Format
------

Each YAML file contains an object with a single ``tests`` key. This key is an
array of test case objects, each of which have the following keys:

- ``description``: A string describing the test.
- ``uri``: A string containing the URI to be parsed.
- ``valid``: A boolean indicating if the URI should be considered valid. 
  This will always be true, as the Connection String spec tests the validity of the structure, but 
  it's still included to make it easier to reuse the connection string spec test runners that 
  drivers already have.
- ``warning``: A boolean indicating whether URI parsing should emit a warning.
- ``hosts``: An array of host objects, each of which have the following keys:
  - ``type``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
  - ``host``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
  - ``port``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
- ``auth``: An object containing the following keys:
  - ``username``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
  - ``password``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
  - ``db``: Included for compatibility with the Connection String spec tests. This will always be ``~``.
- ``options``: An object containing key/value pairs for each parsed query string
  option.

If a test case includes a null value for one of these keys (e.g. ``auth: ~``,
``port: ~``), no assertion is necessary. This both simplifies parsing of the
test files (keys should always exist) and allows flexibility for drivers that
might substitute default values *during* parsing (e.g. omitted ``port`` could be
parsed as 27017).

The ``valid`` and ``warning`` fields are boolean in order to keep the tests
flexible. We are not concerned with asserting the format of specific error or
warnings messages strings.

Use as unit tests
=================

Testing whether a URI is valid or not requires testing whether URI parsing (or
MongoClient construction) causes a warning due to a URI option being valid and asserting that the 
options parsed from the URI match those listed in the ``options`` field.

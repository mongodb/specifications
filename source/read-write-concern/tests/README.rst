=======================
Connection String Tests
=======================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Read and Write Concern 
specification.

Version
-------

Files in the "specifications" repository have no version scheme. They are not
tied to a MongoDB server version.

Format
------

Connection String
~~~~~~~~~~~~~~~~~

These tests are designed to exercise the connection string parsing related
to read concern and write concern.

Each YAML file contains an object with a single ``tests`` key. This key is an
array of test case objects, each of which have the following keys:

- ``description``: A string describing the test.
- ``uri``: A string containing the URI to be parsed.
- ``valid:``: a boolean indicating if parsing the uri should result in an error.
- ``writeConcern:`` A document indicating the expected write concern.
- ``readConcern:`` A document indicating the expected read concern.

If a test case includes a null value for one of these keys, or if the key is missing,
no assertion is necessary. This both simplifies parsing of the test files and allows flexibility
for drivers that might substitute default values *during* parsing.

Document
~~~~~~~~

These tests are designed to ensure compliance with the spec in relation to what should be 
sent to the server.

Each YAML file contains an object with a single ``tests`` key. This key is an
array of test case objects, each of which have the following keys:

- ``description``: A string describing the test.
- ``valid:``: a boolean indicating if the write concern created from the document is valid.
- ``writeConcern:`` A document indicating the write concern to use.
- ``writeConcernDocument:`` A document indicating the write concern to be sent to the server.
- ``readConcern:`` A document indicating the read concern to use.
- ``readConcernDocument:`` A document indicating the read concern to be sent to the server.
- ``isServerDefault:`` Indicates whether the read or write concern is considered the server's default.
- ``isAcknowledged:`` Indicates if the write concern should be considered acknowledged.

Aggregation
~~~~~~~~~~~

These tests are designed to ensure compliance with the spec in relation to what should be
sent to the server when using the aggregation framework.

Each YAML file contains the following keys:

- ``data``: The data that should exist in the collection under test before each
  test run.
- ``minServerVersion`` (optional): The minimum server version (inclusive)
  required to successfully run the test. If this field is not present, it should
  be assumed that there is no lower bound on the required server version.
- ``maxServerVersion`` (optional): The maximum server version (exclusive)
  against which this test can run successfully. If this field is not present,
  it should be assumed that there is no upper bound on the required server
  version.
- ``tests``: An array of tests that are to be run independently of each other.
  Each test will have some or all of the following fields:
  - ``description``: The name of the test.
  - ``operation``: Document describing the operation to be executed. This will
    have the following fields:
    - ``name``: The name of the operation as defined in the specification. The
      name `db-aggregate` refers to database-level aggregation.
    - ``arguments``: The names and values of arguments from the specification.
  - ``error``: If ``true``, the test should expect an error or exception. Note
      that some drivers may report server-side errors as a write error within a
      write result object.
  - ``readConcernDocument:`` A document indicating the read concern to be sent to the server.


Use as unit tests
=================

Testing whether a URI is valid or not should simply be a matter of checking
whether URI parsing raises an error or exception.
Testing for emitted warnings may require more legwork (e.g. configuring a log
handler and watching for output).

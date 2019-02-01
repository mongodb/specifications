==========
CRUD Tests
==========

.. contents::

----

Introduction
============

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the CRUD spec.

Running these integration tests will require a running MongoDB server or
cluster with server versions 2.6.0 or later. Some tests have specific server
version requirements as noted by ``minServerVersion`` and ``maxServerVersion``.

Test Format
===========

Each YAML file has the following keys:

- ``collection_name`` (optional): The collection to use for testing.

- ``database_name`` (optional): The database to use for testing.

- ``data`` (optional): The data that should exist in the collection under test before each
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

  - ``skipReason`` (optional): If present, the test should be skipped and the
    string value will specify a reason.

  - ``failPoint`` (optional): The ``configureFailPoint`` command document to run
    to configure a fail point on the primary server.

  - ``clientOptions`` (optional): Names and values of options used to construct
    the MongoClient for this test.

  - ``operations``: Array of documents, each describing an operation to be
    executed. Each document has the following fields:

    - ``object`` (optional): The name of the object to perform the operation on. Can be
      "database" or "collection". Defaults to "collection" if undefined.

    - ``collectionOptions`` (optional): Names and values of options used to
      construct the collection object for this test.

    - ``name``: The name of the operation as defined in the specification.

    - ``arguments``: The names and values of arguments from the specification.

    - ``error`` (optional): If ``true``, the test should expect the operation
      to emit an error or exception. If ``false`` or omitted, drivers MUST
      assert that no error occurred.

    - ``result`` (optional): The result of executing the operation. This will
      correspond to operation's return value as defined in the specification.
      This field may be omitted if ``error`` is ``true``. If this field is
      present and ``error`` is ``true`` (generally for multi-statement tests),
      the result reports information about statements that succeeded before an
      unrecoverable failure. In that case, drivers may choose to check the
      result object if their BulkWriteException (or equivalent) provides access
      to a write result object.

  - ``expectations`` (optional): Array of documents, each describing a 
    `CommandStartedEvent <../../command-monitoring/command-monitoring.rst#api>`_
    from the
    `Command Monitoring <../../command-monitoring/command-monitoring.rst>`_
    specification. If present, drivers should use command monitoring to observe
    events emitted during execution of the test operation(s) and assert that
    they match the expected CommandStartedEvent(s). Each document will have the
    following field:

    - ``command_started_event``: Document corresponding to an expected
      `CommandStartedEvent <../../command-monitoring/command-monitoring.rst#api>`_.

  - ``outcome`` (optional): Document describing the expected state of the
    collection after the operation is executed. Contains the following fields:

    - ``collection``:

      - ``name`` (optional): The name of the collection to verify. If this isn't
        present then use the collection under test.

      - ``data``: The data that should exist in the collection after the
        operation has been run.

Legacy Test Format for Single Operations
----------------------------------------

The test format above supports both multiple operations and APM expectations,
and is consistent with the formats used by other specifications. Previously, the
CRUD spec tests used a simplified format that only allowed for executing a
single operation. Notable differences from the current format are as follows:

- Instead of a `tests[i].operations` array, a single operation was defined as a
  document in `tests[i].operation`. That document consisted of only the `name`,
  `arguments`, and an optional `object` field.

- Instead of `error` and `result` fields within each element in the
  `tests[i].operations` array, the single operation's error and result were
  defined under the `tests[i].outcome.error` and `tests[i].outcome.result`
  fields.

The legacy format should not conflict with the newer, multi-operation format
used by other specs. Several drivers currently handle both formats using a
unified test runner.

Expectations
============

Optional Fields in Results
--------------------------

Expected results for some tests may include optional fields, such as
``insertedId`` (for InsertOneResult), ``insertedIds`` (for InsertManyResult),
and ``upsertedCount`` (for UpdateResult). Drivers that do not implement these
fields can ignore them.

Asserting Nonexistent Fields
----------------------------

Some command-started events in ``expectations`` include ``{ $exists: false }``
as values for fields such as ``writeConcern``. Tests MUST assert that the actual
command **omits** any field that has such a value in the expected command.

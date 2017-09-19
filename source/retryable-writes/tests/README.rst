=====================
Retryable Write Tests
=====================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Retryable Writes spec.

Server Fail Point
=================

The tests depend on a server fail point, ``onPrimaryTransactionalWrite``, which
allows us to force a network error after the server executes and commits a write
but before it would return a write result. The fail point may be configured like
so::

    db.runCommand({
        configureFailPoint: "onPrimaryTransactionalWrite",
        mode: <string|document>
    });

``mode`` is a generic fail point option and may be assigned a string or document
value. The string values ``"alwaysOn"`` and ``"off"`` may be used to enable or
disable the fail point, respectively. A document may be used to specify either
``times`` or ``skip``, which are mutually exclusive.

``{ times: <integer> }`` may be used to limit the number of times the fail point
may trigger before transitioning to ``"off"``.

``{ skip: <integer> }`` may be used to defer the first trigger of a fail point,
after which it will transition to ``"alwaysOn"``.

The ``onPrimaryTransactionalWrite`` fail point cannot currently be used to test
a multi-statement write operation where each command in the sequence fails on
the first attempt but succeeds on the second. This is being tracked in
`SERVER-31142`_

.. _SERVER-31142: https://jira.mongodb.org/browse/SERVER-31142

Disabling Fail Point after Test Failure
---------------------------------------

In the event of a test failure, drivers should disable the
``onPrimaryTransactionalWrite`` fail point to avoid spurious failures in
subsequent tests. The fail point may be disabled like so::

    db.runCommand({
        configureFailPoint: "onPrimaryTransactionalWrite",
        mode: "off"
    });

Format
======

Each YAML file has the following keys:

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

  - ``writeConcern``: Document describing the write concern for the operation.
    This may be applied to the collection object or, if supported by the driver,
    the individual operation.

  - ``failPoint``: Document describing options for configuring the
    ``disconnectAfterWrite`` fail point. This will have some or all of the
    following fields:

    - ``times``: The number of times that the fail point remains on before it
      deactivates.

  - ``operation``: Document describing the operation to be executed. The
    operation should be executed through a collection object derived from a
    driver session that has been created with the ``retryWrites=true`` option.
    This will have some or all of the following fields:

    - ``name``: The name of the operation as defined in the CRUD specification.

    - ``arguments``: The names and values of arguments from the CRUD
      specification.

  - ``outcome``: Document describing the return value and/or expected state of
    the collection after the operation is executed. This will have some or all
    of the following fields:

    - ``error``: If ``true``, the test should expect an error or exception. Note
      that some drivers may report server-side errors as a write error within a
      write result object.

    - ``result``: The return value from the operation. This will correspond to
      an operation's result object as defined in the CRUD specification.

    - ``collection``:

      - ``name`` (optional): The name of the collection to verify. If this isn't
        present then use the collection under test.

      - ``data``: The data that should exist in the collection after the
        operation has been run.

Use as Integration Tests
========================

Running these as integration tests will require a running mongod server. Each of
these tests is valid against a standalone mongod, a replica set, and a sharded
system for server version 3.6.0 or later.

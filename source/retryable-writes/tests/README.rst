=====================
Retryable Write Tests
=====================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Retryable Writes spec.

Converting to JSON
==================

The tests are written in YAML because it is easier for humans to write and read,
and because YAML includes a standard comment format. A JSONified version of each
YAML file is included in this repository. Whenever a YAML file is modified, the
corresponding JSON file should be regenerated. One method to convert to JSON is
using `yamljs <https://www.npmjs.com/package/yamljs>`_::

    npm install -g yamljs
    yaml2json -s -p -r .

Server Fail Point
=================

The tests depend on a server fail point, ``disconnectAfterWrite``, which allows
us to force a network error after the server executes a write command but before
it would return a write result. The fail point may be configured like so::

    db.runCommand({
        configureFailPoint: "disconnectAfterWrite",
        mode: { times: <integer> },
        data: { errorOnFirstAttemptOnly: <boolean> }
    });

The ``times`` option is a generic fail point option and specifies the number of
times that the fail point remains on before it deactivates. Each write command
will count towards the ``times`` limit regardless of whether a network error
occurs.

The ``errorOnFirstAttemptOnly`` option defaults to ``false``, but may be set to
``true`` to have the fail point allow retry attempts to succeed. This is needed
to test a bulk write operation consisting of multiple write commands, so that we
can expect one network error for each command in the batch and still expect the
entire bulk write operation to succeed.

Disabling Fail Point after Test Failure
---------------------------------------

In the event of a test failure, drivers should disable the
``disconnectAfterWrite`` fail point to avoid spurious failures in subsequent
tests. The fail point may be disabled like so::

    db.runCommand({
        configureFailPoint: "disconnectAfterWrite",
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

    - ``errorOnFirstAttemptOnly``: Whether network errors should occur on only
      the first attempt of each write command.

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

=====================
Retryable Reads Tests
=====================

.. contents::

----

Introduction
============

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Retryable Reads spec.

Several prose tests, which are not easily expressed in YAML, are also presented
in this file. Those tests will need to be manually implemented by each driver.

Tests will require a MongoClient created with options defined in the tests.
Integration tests will require a running MongoDB cluster with server versions
4.2.0 or later. N.B. Strictly speaking, the server should implement the
"Early Failure on Socket Disconnect" slated for 4.2.0, but this is not
neccessary for initial testing.


Server Fail Point
=================

Some tests depend on a server fail point, expressed in the ``failPoint`` field.
For example the ``failCommand`` fail point allows the client to force the
server to return an error. Keep in mind that the fail point only triggers for
commands listed in the "failCommands" field. See `SERVER-35004`_ and
`SERVER-35083`_ for more information.

.. _SERVER-35004: https://jira.mongodb.org/browse/SERVER-35004
.. _SERVER-35083: https://jira.mongodb.org/browse/SERVER-35083

The ``failCommand`` fail point may be configured like so::

    db.adminCommand({
        configureFailPoint: "failCommand",
        mode: <string|document>,
        data: {
          failCommands: ["commandName", "commandName2"],
          closeConnection: <true|false>,
          errorCode: <Number>,
        }
    });
Some tests depend on a server fail point, ``failCommand``, which
allows us to force a network error before the server would return a read result
to the client.  See `SERVER-35004`_ for
more information.

.. _SERVER-29606: https://jira.mongodb.org/browse/SERVER-35004

The fail point may be configured like so::

    db.runCommand({
        configureFailPoint: "failCommand",
        mode: <string|document>,
        data: <document>
    });
    
``mode`` is a generic fail point option and may be assigned a string or document
value. The string values ``"alwaysOn"`` and ``"off"`` may be used to enable or
disable the fail point, respectively. A document may be used to specify either
``times`` or ``skip``, which are mutually exclusive:

- ``{ times: <integer> }`` may be used to limit the number of times the fail
  point may trigger before transitioning to ``"off"``.
- ``{ skip: <integer> }`` may be used to defer the first trigger of a fail
  point, after which it will transition to ``"alwaysOn"``.

The ``data`` option is a document that may be used to specify options that
control the fail point's behavior. ``failCommand`` supports the following
``data`` options, which may be combined if desired:

- ``failCommands``: Required, the list of command names to fail.
- ``closeConnection``: Boolean option, which defaults to ``false``. If
  ``true``, the connection on which the command is executed will be closed
  and the client will see a network error.
- ``errorCode``: Integer option, which is unset by default. If set, the
  specified command error code will be returned as a command error.

Disabling Fail Point after Test Execution
-----------------------------------------

After each test that configures a fail point, drivers should disable the
``failCommands`` fail point to avoid spurious failures in
subsequent tests. The fail point may be disabled like so::

    db.runCommand({
        configureFailPoint: "failCommands",
        mode: "off"
    });

Network Error Tests
===================

Network error tests are expressed in YAML and should be run against a standalone,
shard cluster, or single-node replica set. Until `SERVER-34943`_ is resolved,
these tests cannot be run against a multi-node replicaset.


.. _SERVER-34943: https://jira.mongodb.org/browse/SERVER-34943

Test Format
-----------

Test Format
===========

Each YAML file has the following keys:

- ``database_name`` and ``collection_name``: Optional. The database and collection to use
  for testing.

- ``data``: The data that should exist in the collection under test before each
  test run.

- ``tests``: An array of tests that are to be run independently of each other.
  Each test will have some or all of the following fields:

  - ``description``: The name of the test.

  - ``clientOptions``: Optional, parameters to pass to MongoClient().

  - ``failPoint``: Optional, a server failpoint to enable expressed as the
    configureFailPoint command to run on the admin database.

  - ``sessionOptions``: Optional, parameters to pass to
    MongoClient.startSession().

  - ``operation``: A document describing an operation to be
    executed. The document has the following fields:

    - ``name``: The name of the operation on ``object``.

    - ``object``: The name of the object to perform the operation on. Can be
      "database" or "collection".

    - ``collectionOptions``: Optional, parameters to pass to the Collection()
      used for this operation.

    - ``command_name``: Present only when ``name`` is "runCommand". The name
      of the command to run. Required for languages that are unable preserve
      the order keys in the "command" argument when parsing JSON/YAML.

    - ``arguments``: Optional, the names and values of arguments.

    - ``result``: The return value from the operation, if any. This field may
      be a scalar (e.g. in the case of a count), a single document, or an array
      of documents in the case of a multi-document read. If the operation is
      expected to return an error, the ``result`` is a single document that has
      one or more of the following fields:

      - ``errorContains``: A substring of the expected error message.

      - ``errorCodeName``: The expected "codeName" field in the server
        error response.

      - ``errorLabelsContain``: A list of error label strings that the
        error is expected to have.

      - ``errorLabelsOmit``: A list of error label strings that the
        error is expected not to have.

  - ``expectations``: Optional list of command-started events.


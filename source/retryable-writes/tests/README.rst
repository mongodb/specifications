=====================
Retryable Write Tests
=====================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Retryable Writes spec.

Additionally, a prose test for retrying writes in the event of a replica set
failover is presented later in this file. It is not expressed in YAML and will
need to be manually implemented by each driver.

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
`SERVER-31142`_.

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

  - ``failPoint``: Document describing options for configuring the
    ``onPrimaryTransactionalWrite`` fail point. This will have some or all of
    the following fields:

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

Replica Set Failover Test
=========================

In addition to network errors, writes should also be retried in the event of a
primary failover, which results in a "not master" command error (or similar).
The ``stepdownHangBeforePerformingPostMemberStateUpdateActions`` fail point
implemented in `d4eb562`_ for `SERVER-31355`_ may be used for this test, as it
allows a primary to keep its client connections open after a step down. This
fail point operates by hanging the step down procedure (i.e. ``replSetStepDown``
command) until the fail point is later deactivated.

.. _d4eb562: https://github.com/mongodb/mongo/commit/d4eb562ac63717904f24de4a22e395070687bc62
.. _SERVER-31355: https://jira.mongodb.org/browse/SERVER-31355

The following test requires three MongoClient instances and will generally
require two execution contexts (async drivers may get by with a single thread).

- The client under test will connect to the replica set and be used to execute
  write operations.
- The fail point client will connect directly to the initial primary and be used
  to toggle the fail point.
- The step down client will connect to the replica set and be used to step down
  the primary. This client will generally require its own execution context,
  since the step down will hang.

In order to guarantee that the client under test does not detect the stepped
down primary's state change via SDAM, it must be configured with a large
`heartbeatFrequencyMS`_ value (e.g. 60 seconds). Single-threaded drivers may
also need to set `serverSelectionTryOnce`_ to ``false`` to ensure that server
selection for the retry attempt waits until a new primary is elected.

.. _heartbeatFrequencyMS: https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#heartbeatfrequencyms
.. _serverSelectionTryOnce: https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#serverselectiontryonce

The test proceeds as follows:

- Using the client under test, insert a document and observe a successful write
  result. This will ensure that initial discovery takes place.
- Using the fail point client, activate the fail point by setting ``mode``
  to ``"alwaysOn"``.
- Using the step down client, step down the primary by executing the command
  ``{ replSetStepDown: 60, force: true}``. This operation will hang so long as
  the fail point is activated. When the fail point is later deactivated, the
  step down will complete and the primary's client connections will be dropped.
  At that point, any ensuing network error should be ignored.
- Using the client under test, insert a document and observe a successful write
  result. The test MUST assert that the insert command fails once against the
  stepped down node and is successfully retried on the newly elected primary
  (after SDAM discovers the topology change). The test MAY use APM or another
  means to observe both attempts.
- Using the fail point client, deactivate the fail point by setting ``mode``
  to ``"off"``.

=====================
Retryable Reads Tests
=====================

.. contents::

----

Introduction
============

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the Retryable Reads spec.

Prose tests, which are not easily expressed in YAML, are also presented
in this file. Those tests will need to be manually implemented by each driver.

Tests will require a MongoClient created with options defined in the tests.
Integration tests will require a running MongoDB cluster with server versions
4.2.0 or later. N.B. Strictly speaking, the server should implement the
"Early Failure on Socket Disconnect" slated for 4.2.0, but this is not
necessary for initial testing.


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
``failCommand`` fail point to avoid spurious failures in
subsequent tests. The fail point may be disabled like so::

    db.runCommand({
        configureFailPoint: "failCommand",
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
      "database", "collection", or "client."

    - ``collectionOptions``: Optional, parameters to pass to the Collection()
      used for this operation.

    - ``arguments``: Optional, the names and values of arguments.

    - ``result``: The return value from the operation, if any. This field may
      be a scalar (e.g. in the case of a count), a single document, or an array
      of documents in the case of a multi-document read. If the operation is
      expected to return an error, the ``result`` is a single document that has
      one or more of the following fields:

      - ``error``: Optional. If ``true``, the test should expect an error or
        exception. Implicitly true if ``result`` contains ``errorContains``,
        ``errorCodeName``, ``errorLabelsContain``, and/or
        ``errorLabelsOmit``. If ``false``, the test should expect no error or
        exception, even if ``result`` contains ``errorContains``,
        ``errorCodeName``, ``errorLabelsContain``, and/or ``errorLabelsOmit``.

      - ``errorContains``: Optional. A substring of the expected error message.

      - ``errorCodeName``: Optional. The expected "codeName" field in the server
        error response.

      - ``errorLabelsContain``: Optional. A list of error label strings that the
        error is expected to have.

      - ``errorLabelsOmit``: Optional. A list of error label strings that the
        error is expected not to have.

  - ``expectations``: Optional list of command-started events.

MapReduce Tests
===============

Drivers MUST ensure that ``mapReduce`` is retried only when ``out: { inline:
1}``.  The tests for ``mapReduce`` should test against the same conditions as
described in ``aggregate.yml`` and ``aggregate-serverErrors.yml``, with the
exception that ``mapReduce`` MUST not retry when the `out` stage is not
``{inline: 1}``.

A recommended data set would be three documents that contain values for x such
that ``x:0``, ``x:1`` and ``x:2``. The map function should increment each of
these values by one, and the reduce function should add all x's together.
    
GridFS Tests
============

Since the GridFS API is implemented using ``find`` commands, the `File
Download`_ and `Generic Find on File Collection`_ parts of the GridFS API should
be retryable under the same conditions that ``find`` is retryable. These
functions should be tested against the same conditions described in ``find.yml``
and ``find-ServerErrors.yml``. The tests' setup and expectations can be adapted
from the "Download by Name when revision is 0" test at
https://github.com/mongodb/specifications/blob/master/source/gridfs/tests/download_by_name.yml
and the "Download when there is one chunk" test at
https://github.com/mongodb/specifications/blob/master/source/gridfs/tests/download.yml.

.. _File Download: https://github.com/mongodb/specifications/blob/master/source/gridfs/gridfs-spec.rst#file-download-by-filename

.. _Generic Find on File Collection:  https://github.com/mongodb/specifications/blob/master/source/gridfs/gridfs-spec.rst#generic-find-on-files-collection

Optionally Retryable Commands
=============================

If a driver chooses to implement retryability for the optionally retryable
enumeration commands (e.g. ``client.listDatabases()``,
``db.listCollections()``), the tests for the enumeration commands should test
against the same conditions as described in ``find.yml`` and
``find-serverErrors.yml``.

    
Replica Set Failover Test
=========================

This test is adapted from the `Retryable Write Tests: Replica Set Failover Test`_.

N.B.: Until `SERVER-34943`_ is resolved, this test cannot be run.

In addition to network errors, reads should also be retried in the event of a
primary failover, which results in a "not master" command error (or similar).
The ``stepdownHangBeforePerformingPostMemberStateUpdateActions`` fail point
implemented in `d4eb562`_ for `SERVER-31355`_ may be used for this test, as it
allows a primary to keep its client connections open after a step down. This
fail point operates by hanging the step down procedure (i.e. ``replSetStepDown``
command) until the fail point is later deactivated.

.. _d4eb562: https://github.com/mongodb/mongo/commit/d4eb562ac63717904f24de4a22e395070687bc62
.. _SERVER-31355: https://jira.mongodb.org/browse/SERVER-31355
.. _Retryable Write Tests\: Replica Set Failover Test: https://github.com/mongodb/specifications/tree/master/source/retryable-writes/tests#replica-set-failover-test

The following test requires three MongoClient instances and will generally
require two execution contexts (async drivers may get by with a single thread).

- The client under test will connect to the replica set and be used to execute
  read operations.
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
- Using the client under test, execute a read command. The test MUST assert that
  the read command fails once against the stepped down node and is successfully
  retried on the newly elected primary (after SDAM discovers the topology
  change). The test MAY use APM or another means to observe both attempts.
- Using the fail point client, deactivate the fail point by setting ``mode``
  to ``"off"``.

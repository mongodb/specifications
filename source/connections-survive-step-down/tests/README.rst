===========================================
Connections Survive Primary Step Down Tests
===========================================

These tests can be used to verify a driver's compliance with server discovery
and monitoring requirements with respect to handling "not master" and
"node is shutting down" error responses from the server.

.. contents::

These tests apply only to replica set topologies.

Server Fail Point
-----------------

See: `Server Fail Point`_ in the Transactions spec test suite.

.. _Server Fail Point: ../../transactions/tests#server-fail-point

Disabling Fail Point after Test Execution
`````````````````````````````````````````

After each test that configures a fail point, drivers should disable the
``failCommand`` fail point to avoid spurious failures in
subsequent tests. The fail point may be disabled like so::

    db.runCommand({
        configureFailPoint: "failCommand",
        mode: "off"
    });

Consideration when using serverStatus
`````````````````````````````````````

Drivers executing `serverStatus`_ for connection assertions MUST take its own
connection into account when making their calculations. Those drivers SHOULD
execute `serverStatus`_ using a separate client not under test.


Tests
-----


Test setup
``````````

For each test, make sure the following steps have been completed before running the actual test:

- Create a ``MongoClient`` with ``retryWrites=false``
- Create a collection object from the ``MongoClient``, using ``step-down`` for the database and collection name.
- Drop the test collection, using ``writeConcern`` "majority".
- Execute the "create" command to recreate the collection, using ``writeConcern``
  "majority".

The driver should implement the following tests:

getMore Iteration
`````````````````

This test requires a replica set with server version 4.2 or higher.

Perform the following operations:

- Insert 5 documents into a collection with a majority write concern.
- Start a find operation on the collection with a batch size of 2, and
  retrieve the first batch of results.
- Send a ``{replSetStepDown: 5, force: true}`` command to the current primary and verify that
  the command succeeded.
- Retrieve the next batch of results from the cursor obtained in the find
  operation, and verify that this operation succeeded.
- If the driver implements the `CMAP`_ specification, verify that no new `PoolClearedEvent`_ has been
  published. Otherwise verify that `connections.totalCreated`_ in `serverStatus`_ has not changed.

**Note:** The "replSetStepDown" command often fails with the following
transient error (see `SERVER-48154`_)::

  {
    "ok" : 0,
    "errmsg" : "Unable to acquire X lock on '{4611686018427387905: ReplicationStateTransition, 1}' within 1000ms. opId: 922, op: conn30, connId: 30.",
    "code" : 24,
    "codeName" : "LockTimeout",
  }

When running the "replSetStepDown" command, drivers MUST retry until the
command succeeds. The number of retries should be limited to avoid an infinite
failure loop.

Not Master - Keep Connection Pool
`````````````````````````````````

This test requires a replica set with server version 4.2 or higher.

- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 10107}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 10107 code.
- Execute an insert into the test collection of a ``{test: 1}``
  document and verify that it succeeds.
- If the driver implements the `CMAP`_ specification, verify that no new `PoolClearedEvent`_ has been
  published. Otherwise verify that `connections.totalCreated`_ in `serverStatus`_ has not changed.



Not Master - Reset Connection Pool
``````````````````````````````````

This test requires a replica set with server version 4.0.


- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 10107}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 10107 code.
- If the driver implements the `CMAP`_ specification, verify that a `PoolClearedEvent`_
  has been published
- Execute an insert into the test collection of a ``{test: 1}``
  document and verify that it succeeds.
- If the driver does NOT implement the `CMAP`_ specification, use the `serverStatus`_
  command to verify `connections.totalCreated`_ has increased by 1.


Shutdown in progress - Reset Connection Pool
````````````````````````````````````````````

This test should be run on all server versions >= 4.0.

Perform the following operations on a client configured to NOT retry writes:

- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 91}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 91 code.
- If the driver implements the `CMAP`_ specification, verify that a `PoolClearedEvent`_
  has been published
- Execute an insert into the test collection of a ``{test: 1}``
  document and verify that it succeeds.
- If the driver does NOT implement the `CMAP`_ specification, use the `serverStatus`_
  command to verify `connections.totalCreated`_ has increased by 1.


Interrupted at shutdown - Reset Connection Pool
```````````````````````````````````````````````

This test should be run on all server versions >= 4.0.

Perform the following operations on a client configured to NOT retry writes:

- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 11600}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 11600 code.
- If the driver implements the `CMAP`_ specification, verify that a `PoolClearedEvent`_
  has been published
- Execute an insert into the test collection of a ``{test: 1}``
  document and verify that it succeeds.
- If the driver does NOT implement the `CMAP`_ specification, use the `serverStatus`_
  command to verify `connections.totalCreated`_ has increased by 1.



Questions and Answers
---------------------

Do we need to wait for re-election after the first test?
````````````````````````````````````````````````````````

Since test setup requires creation of a collection, a primary must exist, so subsequent tests will block in server selection until a primary is available again.


Why do tests check for a successful insert operation in addition to checking that the pool was updated appropriately?
`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````

Ensuring that we can run a successful insert after the primary steps down and without needing to recreate the
``MongoClient`` serves to test the resiliency of drivers in the event of a failover/election. Even though checking for
a successful insert operation does not directly test functionality introduced in this specification, it is a
straightforward way to test driver resiliency against a live replica set undergoing an election. This testing
methodology is in contrast to the one adopted by the SDAM spec tests that rely entirely on mocking with no actual
server communication.


.. _CMAP: /source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst
.. _PoolClearedEvent: /source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst#events
.. _serverStatus: https://docs.mongodb.com/manual/reference/command/serverStatus
.. _connections.totalCreated: https://docs.mongodb.com/manual/reference/command/serverStatus/#serverstatus.connections.totalCreated
.. _SERVER-48154: https://jira.mongodb.org/browse/SERVER-48154

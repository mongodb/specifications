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

How to verify connection count
``````````````````````````````

If the driver implements the CMAP specification, verify that a
ConnectionCreatedEvent event has been published. Otherwise, verify that
`connections.totalCreated <https://docs.mongodb.com/manual/reference/command/serverStatus/#serverstatus.connections.totalCreated>`_
in ``serverStatus`` has increased by 1.

How to verify the connection pool has been cleared
``````````````````````````````````````````````````

If the driver implements the CMAP specification, verify that a PoolCleared event
has been published. Otherwise, verify that ``connections.totalCreated`` in
``serverStatus`` has increased by 1.

How to verify the connection pool has not been cleared
``````````````````````````````````````````````````````

If the driver implements the CMAP specification, verify that no new PoolCleared
CMAP event has been published. Otherwise verify that
``connections.totalCreated`` in ``serverStatus`` has not changed.

Consideration when using serverStatus
`````````````````````````````````````

Drivers executing ``serverStatus`` for connection assertions MUST take its own
connection into account when making their calculations. Those drivers SHOULD
execute ``serverStatus`` using a separate client not under test.


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
- Verify that no new connections have been created following the instructions in section `How to verify the connection pool has not been cleared`_

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
- Verify that the connection pool has not been cleared,
  following the instructions in section `How to verify the connection pool has not been cleared`_



Not Master - Reset Connection Pool
``````````````````````````````````

This test requires a replica set with server version 4.0.


- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 10107}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 10107 code.
- Verify that the pool has been cleared following the instructions in section `How to verify the connection pool has been cleared`_


Shutdown in progress - Reset Connection Pool
````````````````````````````````````````````

This test should be run on all server versions >= 4.0.

Perform the following operations on a client configured to NOT retry writes:

- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 91}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 91 code.
- Verify that the pool has been cleared following the instructions in section `How to verify the connection pool has been cleared`_


Interrupted at shutdown - Reset Connection Pool
```````````````````````````````````````````````

This test should be run on all server versions >= 4.0.

Perform the following operations on a client configured to NOT retry writes:

- Set the following fail point: ``{configureFailPoint: "failCommand", mode: {times: 1},
  data: {failCommands: ["insert"], errorCode: 11600}}``
- Execute an insert into the test collection of a ``{test: 1}``
  document.
- Verify that the insert failed with an operation failure with 11600 code.
- Verify that the pool has been cleared following the instructions in section `How to verify the connection pool has been cleared`_



Questions and Answers
---------------------

Do we need to wait for re-election after the first test?
``````````````````````````````````````````````````````````

Since test setup requires creation of a collection, a primary must exist, so subsequent tests will block in server selection until a primary is available again.

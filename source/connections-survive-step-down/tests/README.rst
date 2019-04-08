===========================================
Connections Survive Primary Step Down Tests
===========================================

These tests can be used to verify a driver's compliance with server discovery
and monitoring requirements with respect to handling "not master" and
"node is shutting down" error responses from the server.

.. contents::

These tests apply only to replica set topologies.

Tests
-----

The driver should implement the following tests:

getMore Iteration
`````````````````

This test requires server version 4.2 or higher, and makes use of events
defined in the `CMAP specification
<https://github.com/mongodb/specifications/blob/master/source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst>`_.

Perform the following operations:

- Insert 5 documents into a collection.
- Clear the connection pool to the current primary (see CMAP spec for
  the definition of connection pool clear operation, and
  `Why clear the pool in getMore test?`_ for rationale).
- Start a find operation on the collection with a batch size of 2, and
  retrieve the first batch of results.
- Verify that a ConnectionCreated CMAP event has been published.
- Send a ``replSetStepDown`` command to the current primary and verify that
  the command succeeded, or follow `Server Step Down Procedure`_ below.
- Retrieve the next batch of results from the cursor obtained in the find
  operation, and verify that this operation succeeded.
- Verify that no new ConnectionCreated CMAP events have been published.

Not Master - Keep Connection Pool
`````````````````````````````````

This test requires server version 4.2 or higher.

Perform the following operations:

- Perform server selection for the primary server to obtain a server object
  with an initialized connection pool.
- Mock an operation returning NotMaster operation failure error code.
- Verify that:

  - Connection pool generation (per CMAP spec) has not changed
  - PoolCleared CMAP event has not been published

Not Master - Reset Connection Pool
``````````````````````````````````

This test requires server version 4.0 or lower.

Perform the following operations:

- Perform server selection for the primary server to obtain a server object
  with an initialized connection pool.
- Mock an operation returning NotMaster operation failure error code.
- Verify that:
  - Connection pool generation (per CMAP spec) has been incremented by 1
  - PoolCleared CMAP event has been published

Shutdown - Reset Connection Pool
````````````````````````````````

This test should be run on all supported server versions.

Perform the following operations:

- Perform server selection for the primary server to obtain a server object
  with an initialized connection pool.
- Mock an operation returning ShutdownInProgress (91) operation
  failure error code.
- Verify that:
  - Connection pool generation (per CMAP spec) has been incremented by 1
  - PoolCleared CMAP event has been published


Server Step Down Procedure
--------------------------

In principle, the current primary may be stepped down by running the following
admin command on it: ``{replSetStepDown: null}``. This will cause the current
primary to step down and an election to be held to elect a new primary.
A driver MAY use this simple procedure to step down the current primary.

Note that MongoDB server 4.0 and lower will close all connections on step down,
including the one which sent the ``replSetStepDown`` command. Therefore
on these server versions the step down command will always fail, and the driver
should expect such failure.

On MongoDB server 4.2 and higher the step down command will not close active
connections, and the driver MUST verify that it succeeds.

Although this simple procedure works in principle, it may cause extended
cluster unavailability when used multiple times in succession (see
`SERVER-39846 <https://jira.mongodb.org/browse/SERVER-39846>`_).
To perform multiple step downs in quick succession, or have predictable
performance characteristics of the step downs, the guidance below is provided.

Cluster Configuration
---------------------

In order to have quick and repeatable elections, the deployment needs to be
configured in a specific way. This configuration should be done prior to
running any of the below tests. When the tests are finished, the default
cluster configuration should be restored.

Adjust replica set configuration using `replSetReconfig
<https://docs.mongodb.com/manual/reference/command/replSetReconfig/>`_
to have the following settings:

- ``electionTimeoutMillis``: 1000

Connect to each of the servers in the deployment directly and set the
following server parameters using `setParameter
<https://docs.mongodb.com/manual/reference/command/setParameter/#dbcmd.setParameter>`_:

- ``enableElectionHandoff``: false

Note: for the elections to work correctly, the values specified for
replSetStepDown, secondaryCatchUpPeriodSecs (as provided in replSetStepDown
command) and electionTimeoutMillis must satisfy the following relationship:

``replSetStepDown`` >= ``secondaryCatchUpPeriodSecs`` + ``electionTimeoutMillis``/1000.0

This ensures that each of the servers has time to vote in the election after
the existing primary finishes waiting for other servers to catch up to it
and before the existing primary's election black list time ends.

For reference, the default values of the changed settings which should be
reinstated once the tests are finished are as follows:

- ``electionTimeoutMillis``: ``10000``
- ``enableElectionHandoff``: ``true``
- Replica set member ``priority``: 1

Server Election Procedure
-------------------------

The following procedure should be used to elect a server N as the new primary,
when another server E is the existing primary.

1. Connect to the server E and retrieve current replica set configuration using
   the `replSetGetConfig <https://docs.mongodb.com/manual/reference/command/replSetGetConfig/>`_
   admin command.
2. For each item in the ``members`` field of the configuration, examine the
   value of the ``host`` field. If the value matches the address of the
   server N, set ``priority`` of the respective item to 10. If the value
   matches the address of the server E, set ``priority`` to 1. Otherwise
   set ``priority`` to 0.
3. Increment the ``version`` field of the replica set configuration.
4. Reconfigure the replica set using the `replSetReconfig
   <https://docs.mongodb.com/manual/reference/command/replSetReconfig/>`_
   command, providing the modified configuration.
5. Directly connect to the server N and execute `replSetFreeze
   <https://docs.mongodb.com/manual/reference/command/replSetFreeze/>`_
   admin command as follows: ``{replSetFreeze: 0}``. If this command
   fails with operation failure code 95 ("cannot freeze node when primary or
   running for election. state: Primary"), perform server selection to
   discover the current primary. If the current primary is server N, stop
   as the procedure is complete. Otherwise propagate the operation failure
   error(*).
6. Connect to the server E and execute the `replSetStepDown
   <https://docs.mongodb.com/manual/reference/command/replSetStepDown/>`_
   admin command as follows:
   ``{replSetStepDown: 4, secondaryCatchUpPeriodSecs: 2}``.
7. Connect directly to the server N and execute the following admin command:
   ``{replSetStepUp: 1}``. If this command fails with an operation failure
   error with code 125 ("Election failed"), repeat this step 7.
8. Trigger a rescan of the topology, such as by setting the status of all
   servers in the topology to Unknown.
9. Perform server selection to obtain the current primary.
10. If the current primary is not N, go to step 7 and step up the server N
    again.

(*) The cluster may have held an election after the replica set was reconfigured
in step 4, making the server N the current primary. If this happens,
``replSetFreeze`` command will fail, but the overall goal of having the
server N as the primary has been achieved.

As the above procedure contains a potentially infinite loop, the driver MAY
impose a time limit and fail if the server N has not become a primary in the
allotted time. This time limit SHOULD be at least 10 seconds.

Stepping Down A Server
``````````````````````

If the driver does not care which server becomes the new primary, as would be
the case in the getMore test for example, the driver should perform the
following procedure:

- Obtain a list of servers in the cluster.
- Randomly or otherwise choose a server to be the new primary, other than the
  current primary.
- Follow the above server election procedure to elect the chosen server as
  the new primary.


Questions and Answers
---------------------

Why clear the pool in getMore test?
```````````````````````````````````

Since the following assertion is that a CMAP event is NOT sent, it makes
sense to assert that one is sent by the driver is some other circumstance,
otherwise a driver which doesn't implement CMAP events at all will pass the
test. To guarantee that the event is sent, pool is cleared first.

Alternative method of asserting connection behavior
```````````````````````````````````````````````````

Drivers which do not implement connection pools and CMAP specification may,
instead of using CMAP events to assert that no new connections have been
established, check the `connections.totalCreated
<https://docs.mongodb.com/manual/reference/command/serverStatus/#serverstatus.connections.totalCreated>`_
value in serverStatus.

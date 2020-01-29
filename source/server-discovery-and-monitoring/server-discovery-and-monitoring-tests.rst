============================================
Server Discovery And Monitoring -- Test Plan
============================================

:Spec: 101
:Title: Server Discovery And Monitoring
:Author: A\. Jesse Jiryu Davis
:Advisors: David Golden, Craig Wilson
:Status: Draft
:Type: Standards
:Last Modified: September 8, 2014

See also the YAML test files and their accompanying README in the "tests"
directory.

.. contents::

--------

All servers unavailable
-----------------------

A MongoClient can be constructed without an exception,
even with all seeds unavailable.

Network error writing to primary
--------------------------------

Scenario: With TopologyType ReplicaSetWithPrimary, a write to the primary fails
with a network error other than timeout.

Outcome: The former primary's ServerType MUST become Unknown.
The TopologyType MUST change to ReplicaSetNoPrimary.
The client MUST NOT immediately re-check the former primary.

"Not master" error when reading without SlaveOkay bit
-----------------------------------------------------

Scenario: With TopologyType ReplicaSetWithPrimary, we read from a server we
thought was RSPrimary. Thus the slaveOk bit is not set.

The response's QueryFailure bit is set and the response document is:

    {$err: "not master and slaveOk=false"}

Outcome: The former primary's ServerType MUST become Unknown.
The TopologyType MUST change to ReplicaSetNoPrimary.
The client MUST NOT immediately re-check the former primary.

"Node is recovering" error reading with SlaveOkay bit
-----------------------------------------------------

Scenario: With TopologyType ReplicaSetWithPrimary, we read from a server we
thought was RSSecondary. Thus the slaveOk bit *is* set.

The response's QueryFailure bit is set and the response document is:

    {$err: "not master or secondary; cannot currently read from this replSet member"}

Outcome: The former secondary's ServerType MUST become Unknown.
The TopologyType MUST remain ReplicaSetWithPrimary.
A multi-threaded client MUST immediately re-check the former secondary,
a single-threaded client MUST NOT.

"Node is recovering" error from a write concern error
-----------------------------------------------------

Scenario: With TopologyType ReplicaSetWithPrimary, a write to the primary responds
with the following document:

    { ok: 1, writeConcernError: {code: 91, errmsg: "Replication is being shut down"} }

Outcome: The former primary's ServerType MUST become Unknown.
The TopologyType MUST change to ReplicaSetNoPrimary.
A multi-threaded client MUST immediately re-check the former secondary,
a single-threaded client MUST NOT.

Parsing "not master" and "node is recovering" errors
----------------------------------------------------

For all these example responses,
the client MUST mark the server "Unknown"
and store the error message in the ServerDescription's error field.

Clients MUST NOT depend on any particular field order in these responses.

getLastError
''''''''''''

GLE response after OP_INSERT on an arbiter, secondary, slave,
recovering member, or ghost:

    {ok: 1, err: "not master"}

`Possible GLE response in MongoDB 2.6`_ during failover:

    {ok: 1, err: "replicatedToNum called but not master anymore"}

Note that this error message contains "not master" but does not start with it.

.. _Possible GLE response in MongoDB 2.6: https://jira.mongodb.org/browse/SERVER-9617

Write command
'''''''''''''

Response to an "insert" command on an arbiter, secondary, slave,
recovering member, or ghost:

    {ok: 0, errmsg: "not master"}

Query with slaveOk bit
''''''''''''''''''''''

Response from an arbiter, recovering member, or ghost
when slaveOk is true:

    {$err: "not master or secondary; cannot currently read from this replSet member"}

The QueryFailure bit is set in responseFlags.

Query without slaveOk bit
'''''''''''''''''''''''''

Response from an arbiter, recovering member, ghost, or secondary
when slaveOk is false:

    {$err: "not master and slaveOk=false"}

The QueryFailure bit is set in responseFlags.

Count with slaveOk bit
''''''''''''''''''''''

Command response on an arbiter, recovering member, or ghost
when slaveOk is true:

    {ok: 0, errmsg: "node is recovering"}

Count without slaveOk bit
'''''''''''''''''''''''''

Command response on an arbiter, recovering member, ghost, or secondary
when slaveOk is false:

    {ok: 0, errmsg: "not master"}

Network error on monitoring connection
--------------------------------------

Non-timeout network error
'''''''''''''''''''''''''

Scenario:

Subscribe to `TopologyDescriptionChanged SDAM event`_ on the MongoClient.

Subsribe to `PoolCleared CMAP event`_ on the MongoClient.

Set a `failCommand fail point`_ on ``isMaster`` command
with ``closeConnection: true`` parameter.

Perform a server scan manually or wait for the driver to scan the server.

Outcome:

A TopologyDescriptionChangedEvent must have been published with the server's
address and new description set to Unknown.

A PoolClearedEvent must have been published with the server's address.

Network timeout error
'''''''''''''''''''''

Scenario:

Subscribe to `TopologyDescriptionChanged SDAM event`_ on the MongoClient.

Subsribe to `PoolCleared CMAP event`_ on the MongoClient.

Mock a network timeout error on the monitoring connection.

Perform a server scan manually or wait for the driver to scan the server.

Outcome:

A TopologyDescriptionChangedEvent must have been published with the server's
address and new description set to Unknown.

A PoolClearedEvent must have been published with the server's address.

.. _failCommand fail point: https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point
.. _TopologyDescriptionChanged SDAM event: https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring-monitoring.rst#events
.. _PoolCleared CMAP event: https://github.com/mongodb/specifications/blob/master/source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst#events

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

Parsing "not master" and "node is recovering" errors
----------------------------------------------------

For all these example responses,
the client MUST mark the server "Unknown"
and store the error message in the ServerDescription's error field.
Multi-threaded or asynchronous clients MUST check the server soon;
single-threaded clients MUST mark the TopologyDescription "stale".

Clients MUST NOT depend on any particular field order in these responses.

getLastError
''''''''''''

GLE response after OP_INSERT on an arbiter, secondary, slave,
recovering member, or ghost:

    {ok: 1, err: "not master"}

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

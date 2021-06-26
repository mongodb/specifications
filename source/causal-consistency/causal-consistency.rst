================================
Causal Consistency Specification
================================

:Spec Title: Causal Consistency Specification (See the registry of specs)
:Spec Version: 1.0
:Author: Robert Stam
:Spec Lead: A\. Jesse Jiryu Davis
:Advisory Group: Jeremy Mikola, Jeff Yemin, Misha Tyulene, A. Jesse Jiryu Davis
:Approver(s): A\. Jesse Jiryu Davis, Jeff Yemin, Bernie Hackett, David Golden, Matt Broadstone, Andy Schwerin, Kal Manassiev, Eliot
:Informed: drivers@, Bryan Reinero, Christopher Hendel
:Status: Accepted (Could be Draft, Accepted, Rejected, Final, or Replaced)
:Type: Standards
:Minimum Server Version: 3.6 (The minimum server version this spec applies to)
:Last Modified: 17-Nov-2017

.. contents::

--------

Abstract
========

Version 3.6 of the server introduces support for causal consistency.
This spec builds upon the Sessions Specification to define how an application
requests causal consistency and how a driver interacts with the server
to implement causal consistency.

Definitions
===========

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
-----

Causal consistency
    A property that guarantees that an application can read its own writes and that
    a later read will never observe a version of the data that is older than an
    earlier read.

ClientSession
    The driver object representing a client session and the operations that can be
    performed on it.

Cluster time
    The current cluster time. The server reports its view of the current cluster
    time in the ``$clusterTime`` field in responses from the server and the driver
    participates in distributing the current cluster time to all nodes (called
    "gossipping the cluster time") by sending the highest ``$clusterTime`` it has seen
    so far in messages it sends to mongos servers. The current cluster time is a
    logical time, but is digitally signed to prevent malicious clients from
    propagating invalid cluster times. Cluster time is only used in replica sets
    and sharded clusters.

Logical time
    A time-like quantity that can be used to determine the order in which events
    occurred. Logical time is represented as a BsonTimestamp.

MongoClient
    The root object of a driver's API. MAY be named differently in some drivers.

MongoCollection
    The driver object representing a collection and the operations that can be
    performed on it. MAY be named differently in some drivers.

MongoDatabase
    The driver object representing a database and the operations that can be
    performed on it. MAY be named differently in some drivers.

Operation time
    The logical time at which an operation occurred. The server reports the
    operation time in the response to all commands, including error responses. The
    operation time by definition is always less than or equal to the cluster time.
    Operation times are tracked on a per ``ClientSession`` basis, so the ``operationTime``
    of each ``ClientSession`` corresponds to the time of the last operation performed
    in that particular ``ClientSession``.

ServerSession
    The driver object representing a server session.

Session
    A session is an abstract concept that represents a set of sequential
    operations executed by an application that are related in some way. This
    specification defines how sessions are used to implement causal
    consistency.

Unacknowledged writes
    Unacknowledged writes are write operations that are sent to the server without
    waiting for a reply acknowledging the write. See the "Unacknowledged Writes"
    section below for information on how unacknowledged writes interact with
    causal consistency.

Specification
=============

An application requests causal consistency by creating a ``ClientSession``
with options that specify that causal consistency is desired. An
application then passes the session as an argument to methods in the
``MongoDatabase`` and ``MongoCollection`` classes. Any operations performed against
that session will then be causally consistent.

Naming variations
=================

This specification defines names for new methods and types. To the extent
possible you SHOULD use these names in your driver. However, where your
driver's and/or language's naming conventions differ you SHOULD continue to use
them instead. For example, you might use ``StartSession`` or ``start_session`` instead
of ``startSession``.

High level summary of the API changes for causal consistency
============================================================

Causal consistency is built on top of client sessions.

Applications will start a new client session for causal consistency like
this:

.. code:: typescript

    options = new SessionOptions(causalConsistency = true);
    session = client.startSession(options);

All read operations performed using this session will now be causally
consistent.

If no value is provided for ``causalConsistency`` and snapshot reads are not requested
a value of true is implied. See the ``causalConsistency`` section.

MongoClient changes
===================

There are no API changes to ``MongoClient`` to support causal consistency.
Applications indicate whether they want causal consistency by setting the
``causalConsistency`` field in the options passed to the ``startSession`` method.

SessionOptions changes
======================

``SessionOptions`` change summary

.. code:: typescript

    class SessionOptions {
        Optional<bool> causalConsistency;

        // other options defined by other specs
    }

In order to support causal consistency a new property named
``causalConsistency`` is added to ``SessionOptions``. Applications set
``causalConsistency`` when starting a client session to indicate
whether they want causal consistency. All read operations performed
using that client session are then causally consistent.

Each new member is documented below.

causalConsistency
-----------------

Applications set ``causalConsistency`` when starting a session to
indicate whether they want causal consistency.

Note that the ``causalConsistency`` property is optional. The default value of
this property is ``not supplied``. If no value is supplied for
``causalConsistency`` the value will be inherited. Currently it is inherited
from the global default which is defined to be true. In the future it *might*
be inherited from client settings.

Causal consistency is provided at the session level by tracking the ``clusterTime``
and ``operationTime`` for each session. In some cases an application may wish
subsequent operations in one session to be causally consistent with operations
that were executed in a different session. In that case the application can call
the ``advanceClusterTime`` and ``advanceOperationTime`` methods in ``ClientSession`` to
advance the ``clusterTime`` and ``operationTime`` of one session to the ``clusterTime`` and
``operationTime`` from another session.

ClientSession changes
=====================

``ClientSession`` changes summary

.. code:: typescript

    interface ClientSession {
        Optional<BsonTimestamp> operationTime;

        void advanceOperationTime(BsonTimestamp operationTime);

        // other members as defined in other specs
    }

Each new member is documented below.

operationTime
-------------

This property returns the operation time of the most recent operation performed
using this session. If no operations have been performed using this session the value will be
null unless ``advanceOperationTime`` has been called.
This value will also be null when the cluster does not report
operation times.

advanceOperationTime
--------------------

This method advances the ``operationTime`` for a session. If the new
``operationTime`` is greater than the session's current ``operationTime`` then the
session's ``operationTime`` MUST be advanced to the new ``operationTime``. If the
new ``operationTime`` is less than or equal to the session's current
``operationTime`` then the session's ``operationTime`` MUST NOT be changed.

Drivers MUST NOT attempt to validate the supplied ``operationTime``. While the
server requires that ``operationTime`` be less than or equal to ``clusterTime``
we don't want to check that when ``advanceOperationTime`` is called. This
allows an application to call ``advanceClusterTime`` and
``advanceOperationTime`` in any order, or perhaps to not call
``advanceClusterTime`` at all and let the ``clusterTime`` that is sent to the
server be implied by the ``clusterTime`` in ``MongoClient``.

MongoDatabase changes
=====================

There are no additional API changes to ``MongoDatabase`` beyond those specified in
the Sessions Specification. All ``MongoDatabase`` methods that talk to the server
have been overloaded to take a session parameter. If that session was started
with ``causalConsistency = true`` then all operations using that session will
be causally consistent.

MongoCollection changes
=======================

There are no additional API changes to ``MongoCollection`` beyond those specified
in the Sessions Specification. All ``MongoCollection`` methods that talk to the
server have been overloaded to take a session parameter. If that session was
started with ``causalConsistency = true`` then all operations using that
session will be causally consistent.

Server Commands
===============

There are no new server commands related to causal consistency. Instead,
causal consistency is implemented by:

1. Saving the ``operationTime`` returned by 3.6+ servers for all operations in a
   property of the ``ClientSession`` object. The server reports the ``operationTime``
   whether the operation succeeded or not and drivers MUST save the ``operationTime``
   in the ``ClientSession`` whether the operation succeeded or not.

2. Passing that ``operationTime`` in the ``afterClusterTime`` field of the ``readConcern`` field
   for subsequent causally consistent read operations (for all commands that
   support a ``readConcern``)

3. Gossiping clusterTime (described in the Driver Session Specification)

Server Command Responses
========================

To support causal consistency the server returns the ``operationTime`` in
responses it sends to the driver (for both read and write operations).

.. code:: typescript

    {
        ok : 1 or 0,
        ... // the rest of the command reply
        operationTime : <BsonTimestamp>
        $clusterTime : <BsonDocument> // only in deployments that support cluster times
    }

The ``operationTime`` MUST be stored in the ``ClientSession`` to later be passed as the
``afterClusterTime`` field of the ``readConcern`` field in subsequent read operations. The
``operationTime`` is returned whether the command succeeded or not and MUST be
stored in either case.

Drivers MUST examine all responses from the server for the presence of an
``operationTime`` field and store the value in the ``ClientSession``.

When connected to a standalone node command replies do not include an
``operationTime`` field. All operations against a standalone node are causally
consistent automatically because there is only one node.

When connected to a deployment that supports cluster times the command response also includes a field
called ``$clusterTime`` that drivers MUST use to gossip the cluster time. See the
Sessions Specification for details.

Causally consistent read commands
=================================

For causal consistency the driver MUST send the ``operationTime`` saved in
the ``ClientSession`` as the value of the ``afterClusterTime`` field of the
``readConcern`` field:

.. code:: typescript

    {
        find : <string>, // or other read command
        ... // the rest of the command parameters
        readConcern :
        {
            level : ..., // from the operation's read concern (only if specified)
            afterClusterTime : <BsonTimestamp>
        }
    }

For the lists of commands that support causally consistent reads, see `ReadConcern`_ spec.

.. _ReadConcern: https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#read-concern/ 

The driver MUST merge the ``ReadConcern`` specified for the operation with the
``operationTime`` from the ``ClientSession`` (which goes in the ``afterClusterTime`` field)
to generate the combined ``readConcern`` to send to the server. If the level
property of the read concern for the operation is null then the driver MUST NOT
include a ``level`` field alongside the ``afterClusterTime`` of the ``readConcern``
value sent to the
server. Drivers MUST NOT attempt to verify whether the server supports causally
consistent reads or not for a given read concern level. The server will return
an error if a given level does not support causal consistency.

The Read and Write Concern specification states that when a user has not specified a
``ReadConcern`` or has specified the server's default ``ReadConcern``, drivers MUST
omit the ``ReadConcern`` parameter when sending the command. For causally
consistent reads this requirement is modified to state that when the
``ReadConcern`` parameter would normally be omitted drivers MUST send a ``ReadConcern``
after all because that is how the ``afterClusterTime`` value is sent to the server.

The Read and Write Concern Specification states that drivers MUST NOT add a
``readConcern`` field to commands that are run using a generic ``runCommand`` method.
The same is true for causal consistency, so commands that are run using ``runCommand``
MUST NOT have an ``afterClusterTime`` field added to them.

When executing a causally consistent read, the ``afterClusterTime`` field MUST be
sent when connected to a deployment that supports cluster times, and MUST NOT be sent
when connected to a deployment that does not support cluster times.

Unacknowledged writes
=====================

The implementation of causal consistency relies on the ``operationTime``
returned by the server in the acknowledgement of a write. Since unacknowledged
writes don't receive a response from the server (or don't wait for a response)
the ``ClientSession``'s ``operationTime`` is not updated after an unacknowledged write.
That means that a causally consistent read after an unacknowledged write cannot
be causally consistent with the unacknowledged write. Rather than prohibiting
unacknowledged writes in a causally consistent session we have decided to
accept this limitation. Drivers MUST document that causally consistent reads
are not causally consistent with unacknowledged writes.

Test Plan
=========

Below is a list of test cases to write.

Note: some tests are only relevant to certain deployments. For the purpose of deciding
which tests to run assume that any deployment that is version 3.6 or higher and is either a
replica set or a sharded cluster supports cluster times.

1.  When a ``ClientSession`` is first created the ``operationTime`` has no value
        * ``session = client.startSession()``
        * assert ``session.operationTime`` has no value

2.  | The first read in a causally consistent session must not send
    | ``afterClusterTime`` to the server (because the ``operationTime`` has not yet
    | been determined)
        * ``session = client.startSession(causalConsistency = true)``
        * ``document = collection.anyReadOperation(session, ...)``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command does not have an ``afterClusterTime``

3.  | The first read or write on a ``ClientSession`` should update the
    | ``operationTime`` of the ``ClientSession``, even if there is an error
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession() // with or without causal consistency``
        * ``collection.anyReadOrWriteOperation(session, ...) // test with errors also if possible``
        * capture the response sent from the server (using APM or other mechanism)
        * assert ``session.operationTime`` has the same value that is in the response from the server

4.  | A ``findOne`` followed by any other read operation (test them all) should
    | include the ``operationTime`` returned by the server for the first operation in
    | the ``afterClusterTime`` parameter of the second operation
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession(causalConsistency = true)``
        * ``collection.findOne(session, {})``
        * ``operationTime = session.operationTime``
        * ``collection.anyReadOperation(session, ...)``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command has an ``afterClusterTime`` field with a value of ``operationTime``

5.  | Any write operation (test them all) followed by a ``findOne`` operation should
    | include the ``operationTime`` of the first operation in the ``afterClusterTime``
    | parameter of the second operation, including the case where the first operation
    | returned an error
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession(causalConsistency = true)``
        * ``collection.anyWriteOperation(session, ...) // test with errors also where possible``
        * ``operationTime = session.operationTime``
        * ``collection.findOne(session, {})``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command has an ``afterClusterTime`` field with a value of ``operationTime``

6.  | A read operation in a ``ClientSession`` that is not causally consistent
    | should not include the ``afterClusterTime`` parameter in the command sent to the
    | server
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession(causalConsistency = false)``
        * ``collection.anyReadOperation(session, {})``
        * ``operationTime = session.operationTime``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command does not have an ``afterClusterTime`` field

7.  | A read operation in a causally consistent session against a deployment that does not support cluster times does
    | not include the ``afterClusterTime`` parameter in the command sent to the server
        * skip this test if connected to a deployment that does support cluster times
        * ``session = client.startSession(causalConsistency = true)``
        * ``collection.anyReadOperation(session, {})``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command does not have an ``afterClusterTime`` field

8.  | When using the default server ``ReadConcern`` the ``readConcern`` parameter in the
    | command sent to the server should not include a ``level`` field
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession(causalConsistency = true)``
        * configure ``collection`` to use default server ``ReadConcern``
        * ``collection.findOne(session, {})``
        * ``operationTime = session.operationTime``
        * ``collection.anyReadOperation(session, ...)``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command does not have a ```level`` field
        * assert that the command has a ``afterClusterTime`` field with a value of ``operationTime``

9.  | When using a custom ``ReadConcern`` the ``readConcern`` field in the command sent to
    | the server should be a merger of the ``ReadConcern`` value and the ``afterClusterTime``
    | field
        * skip this test if connected to a deployment that does not support cluster times
        * ``session = client.startSession(causalConsistency = true)``
        * configure collection to use a custom ReadConcern
        * ``collection.findOne(session, {})``
        * ``operationTime = session.operationTime``
        * ``collection.anyReadOperation(session, ...)``
        * capture the command sent to the server (using APM or other mechanism)
        * assert that the command has a ``level`` field with a value matching the custom readConcern
        * assert that the command has an ``afterClusterTime`` field with a value of ``operationTime``

10. | When an unacknowledged write is executed in a causally consistent
    | ``ClientSession`` the ``operationTime`` property of the ``ClientSession`` is
    | not updated
        * ``session = client.startSession(causalConsistency = true)``
        * configure the collection to use ``{ w : 0 }`` unacknowledged writes
        * ``collection.anyWriteOperation(session, ...)``
        * assert ``session.operationTime`` does not have a value

11. | When connected to a deployment that does not support cluster times messages sent to
    | the server should not include ``$clusterTime``
        * skip this test when connected to a deployment that does support cluster times
        * ``document = collection.findOne({})``
        * capture the command sent to the server
        * assert that the command does not include a ``$clusterTime`` field

12. | When connected to a deployment that does support cluster times messages sent to the server should
    | include ``$clusterTime``
        * skip this test when connected to a deployment that does not support cluster times
        * ``document = collection.findOne({})``
        * capture the command sent to the server
        * assert that the command includes a ``$clusterTime`` field

Motivation 
==========

To support causal consistency. Only supported with server version 3.6 or newer. 

Design Rationale
================

The goal is to modify the driver API as little as possible so that existing
programs that don't need causal consistency don't have to be changed.
This goal is met by defining a ``SessionOptions`` field that applications use to
start a ``ClientSession`` that can be used for causal consistency. Any
operations performed with such a session are then causally consistent.

The ``operationTime`` is tracked on a per ``ClientSession`` basis. This allows each
``ClientSession`` to have an ``operationTime`` that is sufficiently new to guarantee
causal consistency for that session, but no newer. Using an ``operationTime`` that
is newer than necessary can cause reads to block longer than necessary when
sent to a lagging secondary. The goal is to block for just long enough to
guarantee causal consistency and no longer.

Backwards Compatibility
=======================

The API changes to support sessions extend the existing API but do not
introduce any backward breaking changes. Existing programs that don't use
causal consistency continue to compile and run correctly.

Reference Implementation
========================

A reference implementation must be completed before any spec is given status
"Final", but it need not be completed before the spec is “Accepted”. While
there is merit to the approach of reaching consensus on the specification and
rationale before writing code, the principle of "rough consensus and running
code" is still useful when it comes to resolving many discussions of spec
details. A final reference implementation must include test code and
documentation.

Q&A
===

Changelog
=========

- 2017-09-13: Renamed "causally consistent reads" to "causal consistency"
- 2017-09-13: If no value is supplied for ``causallyConsistent`` assume true
- 2017-09-28: Remove remaining references to collections being associated with sessions
- 2017-09-28: Update spec to reflect that replica sets use $clusterTime also now
- 2017-10-04: Added advanceOperationTime
- 2017-10-05: How to handle default read concern
- 2017-10-06: advanceOperationTime MUST NOT validate operationTime
- 2017-11-17 : Added link to ReadConcern spec which lists commands that support readConcern

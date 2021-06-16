================================
Snapshot Reads Specification
================================

:Spec Title: Snapshot Reads Specification (See the registry of specs)
:Spec Version: 1.0
:Author: Boris Dogadov
:Advisors: Jeff Yemin, A. Jesse Jiryu Davis, Judah Schvimer
:Status: Draft (Could be Draft, Accepted, Rejected, Final, or Replaced)
:Type: Standards
:Minimum Server Version: 5.0 (The minimum server version this spec applies to)
:Last Modified: 15-Jun-2021

.. contents::

--------

Abstract
========

Version 5.0 of the server introduces support for readConcern level "snapshot" (non-speculative)
for read commands outside of transactions, including on secondaries.
This spec builds upon the Sessions Specification to define how an application
requests "snapshot" level readConcern and how a driver interacts with the server
to implement snapshot reads.

Definitions
===========

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
-----

ClientSession
    The driver object representing a client session and the operations that can be
    performed on it.

MongoClient
    The root object of a driver's API. MAY be named differently in some drivers.

MongoCollection
    The driver object representing a collection and the operations that can be
    performed on it. MAY be named differently in some drivers.

MongoDatabase
    The driver object representing a database and the operations that can be
    performed on it. MAY be named differently in some drivers.

ServerSession
    The driver object representing a server session.

Session
    A session is an abstract concept that represents a set of sequential
    operations executed by an application that are related in some way. This
    specification defines how sessions are used to implement snapshot reads.

Snapshot reads
    Reads with readconcern level ``snapshot`` that occur outside of transactions on
    both the primary and secondary nodes, including in sharded clusters.

Snapshot timestamp
    Snapshot timestamp, representing timestamp of the first read (find/aggregate operations) in the session.
    The server creates a cursor in response to a snapshot read command and 
    reports ``atClusterTime`` field in the cursor response. ``atClusterTime`` field represents the timestamp
    of the read and is guaranteed to be majority committed.

Specification
=============

An application requests snapshot reads by creating a ``ClientSession``
with options that specify that snapshot reads are desired. An
application then passes the session as an argument to methods in the
``MongoDatabase`` and ``MongoCollection`` classes. Read operations (find/aggregate/distinct) performed against
that session will be read from the same snapshot.

High level summary of the API changes for snapshot reads
========================================================

Snapshot reads are built on top of client sessions.

Applications will start a new client session for snapshot reads like
this:

.. code:: typescript

    options = new SessionOptions(isSnapshot = true);
    session = client.startSession(options);

All read operations performed using this session will be read from same snapshot.

If no value is provided for ``isSnapshot`` a value of false is
implied.

MongoClient changes
===================

There are no API changes to ``MongoClient`` to support snapshot reads.
Applications indicate whether they want snapshot reads by setting the
``isSnapshot`` field in the options passed to the ``startSession`` method.

SessionOptions changes
======================

``SessionOptions`` change summary

.. code:: typescript

    class SessionOptions {
        Optional<bool> isSnapshot;

        // other options defined by other specs
    }

In order to support snapshot reads a new property named
``isSnapshot`` is added to ``SessionOptions``. Applications set
``isSnapshot`` when starting a client session to indicate
whether they want snapshot reads. All read operations performed
using that client session will share the same snapshot.

Each new member is documented below.

isSnapshot
---------

Applications set ``isSnapshot`` when starting a session to
indicate whether they want snapshot reads.

Note that the ``isSnapshot`` property is optional. The default value of
this property is false.

Snapshot reads and causal consistency are mutually exclusive. Therefore if ``isSnapshot`` is set to true,
``causalConsistency`` property is set to false. Client MUST throw an Error if both ``isSnapshot`` and ``causalConsistency`` are set to true.
Snapshot reads are supported both on primaries and secondaries.

ClientSession changes
=====================

``ClientSession`` changes summary

.. code:: typescript

    interface ClientSession {
        Optional<BsonTimestamp> snapshotTimestamp;

        // other members as defined in other specs
    }

Each new member is documented below.

snapshotTimestamp
-------------------

This property returns the timestamp the first find/aggregate/distinct operation performed
using this session. If no operations that support the snapshot read concern have been performed
using this session the value will be null.

MongoDatabase changes
=====================

There are no additional API changes to ``MongoDatabase`` beyond those specified in
the Sessions Specification. All ``MongoDatabase`` methods that talk to the server
have been overloaded to take a session parameter. If that session was started
with ``isSnapshot = true`` then all read operations using that session will
will share the same snapshot.

MongoCollection changes
=======================

There are no additional API changes to ``MongoCollection`` beyond those specified
in the Sessions Specification. All ``MongoCollection`` methods that talk to the
server have been overloaded to take a session parameter. If that session was
started with ``isSnapshot = true`` then all operations using that
session will share the same snapshot.

ReadConcern changes
===================

``snapshot`` added to `ReadConcernLevel enumeration <../read-write-concern/read-write-concern.rst#read-concern>`_.`.

Server Commands
===============

There are no new server commands related to snapshot reads. Instead,
snapshot reads are implemented by:

1. Saving the ``atClusterTime`` returned by 5.0+ servers for the first find/aggregate operation in a
   property ``snapshotTimestamp`` of the ``ClientSession`` object. Drivers MUST save the ``atClusterTime``
   in the ``ClientSession`` object.

2. Passing that ``snapshotTimestamp`` in the ``atClusterTime`` field of the ``readConcern`` field
   for subsequent snapshot read operations (for find/aggregate/distinct commands).

Server Command Responses
========================

To support snapshot reads the server returns the ``atClusterTime`` in
cursor object it sends to the driver (for both find/aggregate commands).

.. code:: typescript

    {
        ok : 1 or 0,
        ... // the rest of the command reply
        cursor : {
            ... // the rest of the cursor reply
            atClusterTime : <BsonTimestamp>
        }
    }

The ``atClusterTime`` MUST be stored in the ``ClientSession`` to later be passed as the
``atClusterTime`` field of the ``readConcern`` with ``snapshot`` level field  in subsequent read operations.

Server Errors
=============
1. The server may reply to read commands with a ``SnapshotTooOld`` error if the client's ``atClusterTime`` value is not available in the server's history.
2. The server will return ``InvalidOptions`` error if both ``atClusterTime`` and ``afterClusterTime`` options are set to true.

Snapshot read commands
======================

For snapshot reads the driver MUST first obtain ``atClusterTime`` from cursor response of find/aggregate command,
by specifying ``readConcern`` with ``snapshot`` level field, and store it as ``snapshotTimestamp`` in 
``ClientSession`` object.

.. code:: typescript

    {
        find : <string>, // or other read command
        ... // the rest of the command parameters
        readConcern :
        {
            level : "snapshot"
        }
    }

For subsequent reads from same snapshot driver MUST send the ``snapshotTimestamp`` saved in
the ``ClientSession`` as the value of the ``atClusterTime`` field of the
``readConcern`` with ``snapshot`` level field:

.. code:: typescript

    {
        find : <string>, // or other read command
        ... // the rest of the command parameters
        readConcern :
        {
            level : "snapshot",
            afterClusterTime : <BsonTimestamp>
        }
    }

Lists of commands that support snapshot reads:

1. find
2. aggregate
3. distinct

Snapshot read commands errors
=============================

Drivers MUST NOT retry errors in SnapshotError category for snapshot reads if ``atClusterTime`` is supplied.

Test Plan
=========

Note: some tests are only relevant to certain deployments. For the purpose of deciding
which tests to run assume that any deployment that is version 5.0 or higher and is either a
replica set or a sharded cluster supports snapshot reads.
The server ``minSnapshotHistoryWindowInSeconds`` parameter SHOULD be configured to match the test execution time.

1.  | The first read in a snapshot session must not send ``atClusterTime``
    | to the server (because the ``atClusterTime`` has not yet been determined)

    * ``session = client.startSession(isSnapshot = true)``
    * ``document = collection.anyReadOperation(session, ...)``
    * capture the command sent to the server (using APM or other mechanism).
    * assert that the command does not have an ``atClusterTime``.

2.  | Subsequent snapshot reads on a ``ClientSession`` should read from the snapshot of the first read in that session.
    | Test SHOULD introduce two variations one for primaries and additional for secondary reads

    * ``session1 = client.startSession(isSnapshot = true)``
    * ``session2 = client.startSession(isSnapshot = true)``
    * ``readBeforeUpdateSession1 = collection.anyReadOrOperation(session1, ...)``
    * ``collection.anyUpdateOpertation(...)``
    * ``readBeforeUpdateSession2 = collection.anyReadOrOperation(session2, ...)``
    * ``collection.anyUpdateOpertation(...)``
    * ``readAfterUpdateSession1 = collection.anyReadOrOperation(session1, ...)``
    * ``readAfterUpdateSession2 = collection.anyReadOrOperation(session2, ...)``
    * | Assert that `readBeforeUpdateSession1` is equivalent to `readAfterUpdateSession1` and 
      | `readBeforeUpdateSession2` to `readAfterUpdateSession2`.

3.  | Snapshot reads that fail with ``SnapshotError`` are not retried.
    | This test is OPTIONAL as it requires setting ``session.snapshotTimestamp``
    | which is not part of the public API

    * ``session = client.startSession(isSnapshot = true)``
    * ``session.snapshotTimestamp = 0``
    * ``collection.anyReadOrOperation(session1, ...)``
    * Assert that only single read command was issued.

4.  | A read operation in a ``ClientSession`` that is not snapshot read
    | should not include the ``atClusterTime`` parameter in the command sent to the server

    * ``session = client.startSession(isSnapshot = false)``
    * ``collection.anyReadOperation(session, {})``
    * ``operationTime = session.operationTime``
    * capture the command sent to the server (using APM or other mechanism).
    * assert that the command does not have an ``atClusterTime`` field.

Motivation 
==========

To support snapshot reads. Only supported with server version 5.0+ or newer.

Design Rationale
================

The goal is to modify the driver API as little as possible so that existing
programs that don't need snapshot reads don't have to be changed.
This goal is met by defining a ``SessionOptions`` field that applications use to
start a ``ClientSession`` that can be used for snapshot reads. Alternative explicit approach of
obtaining ``atClusterTime`` from ``cursor`` object and passing it to readconcern object was considered initially.
Session based approach was chosen as it aligns better with the existing API, and requires minimal API changes.
Future extensibility for snapshot reads would be better served by session based approach, as no API changes will be required.

Backwards Compatibility
=======================

The API changes to support sessions extend the existing API but do not
introduce any backward breaking changes. Existing programs that don't use
snapshot reads continue to compile and run correctly.

Reference Implementation
========================

A reference implementation must be completed before any spec is given status
"Final", but it need not be completed before the spec is “Accepted”. C# driver will 
provide the reference implementation.
While there is merit to the approach of reaching consensus on the specification and
rationale before writing code, the principle of "rough consensus and running
code" is still useful when it comes to resolving many discussions of spec
details. A final reference implementation must include test code and
documentation.

Q&A
===

Changelog
=========

:2021-06-15: Initial version.

=============================
Driver Sessions Specification
=============================

:Spec Title: Driver Sessions Specification (See the registry of specs)
:Spec Version: 1.0
:Author: Robert Stam
:Spec Lead: A\. Jesse Jiryu Davis
:Advisory Group: Jeremy Mikola, Jeff Yemin, Samantha Ritter
:Approver(s): A\. Jesse Jiryu Davis, Jeff Yemin, Bernie Hackett, David Golden, Eliot
:Informed: drivers@, Bryan Reinero, Christopher Hendel
:Status: Accepted (Could be Draft, Accepted, Rejected, Final, or Replaced)
:Type: Standards
:Minimum Server Version: 3.6 (The minimum server version this spec applies to)
:Last Modified: 19-Sep-2017

.. contents::

--------

Abstract
========

Version 3.6 of the server introduces the concept of logical sessions for
clients. A session is an abstract concept that represents a set of sequential
operations executed by an application that are related in some way. This
specification is limited to how applications start and end sessions. Other
specifications define various ways in which sessions are used (e.g. causally
consistent reads, retriable writes, or transactions).

This specification also discusses how drivers participate in distributing the
cluster time throughout a deployment, a process known as "gossipping the
cluster time". While gossipping the cluster time is somewhat orthogonal to
sessions, any driver that implements sessions MUST also implement gossipping
the cluster time, so it is included in this specification.

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
    The driver object representing a client session and the operations that can
    be performed on it. Depending on the language a driver is written in this
    might be an interface or a class. See also ``ServerSession``.

Deployment
    A set of servers that are all part of a single MongoDB cluster. We avoid the
    word "cluster" because some people interpret "cluster" to mean "sharded cluster".

MongoClient
    The root object of a driver's API. MAY be named differently in some drivers.

MongoCollection
    The driver object representing a collection and the operations that can be
    performed on it. MAY be named differently in some drivers.

MongoDatabase
    The driver object representing a database and the operations that can be
    performed on it. MAY be named differently in some drivers.

ServerSession
    The driver object representing a server session. This type is an
    implementation detail and does not need to be public. See also
    ``ClientSession``.

Server session ID
    A server session ID is a token used to identify a particular server
    session. A driver can ask the server for a session ID using the
    ``startSession`` command or it can generate one locally (see Generating a
    Session ID locally).

Session
    A session is an abstract concept that represents a set of sequential
    operations executed by an application that are related in some way. Other
    specifications define the various ways in which operations can be related,
    but examples include causally consistent reads and retryable writes.

Topology
    The current configuration and state of a deployment. 

Specification
=============

Drivers currently have no concept of a session. The driver API will be expanded
to provide a way for applications to start and end sessions and to execute
operations in the context of a session. The goal is to expand the API in a way
that introduces no backward breaking changes. Existing applications that don't
use sessions don't need to be changed, and new applications that don't need
sessions can continue to be written using the existing API.

To use sessions an application will call new (or overloaded) methods that take
a session parameter.

Naming variations
=================

This specification defines names for new methods and types. To the extent
possible, these names SHOULD be used by drivers. However, where a driver and/or
language's naming conventions differ, those naming conventions SHOULD be used.
For example, a driver might name a method ``StartSession`` or ``start_session`` instead
of ``startSession``, or might name a type ``client_session`` instead of ``ClientSession``.

High level summary of the API changes for sessions
==================================================

This section is just a high level summary of the new API. Details are provided
further on.

Applications start a new session like this:

.. code:: typescript

    options = new SessionOptions(...);
    session = client.startSession(options);

The ``SessionOptions`` will be individually defined in several other
specifications. It is expected that the set of ``SessionOptions`` will grow over
time as sessions are used for new purposes.

Applications use a session by passing it as an argument to operation methods.
For example:

.. code:: typescript

    collection.InsertOne(session, ...)
    collection.UpdateOne(session, ...)

Applications end a session like this:

.. code:: typescript

    session.endSession()

While this specification does not deal with multi-document transactions (which
don't even exist yet), it is expected that when they are implemented they will
be based upon sessions. We can speculate that in the future we might have some
additional transaction-related methods for sessions such as:

.. code:: typescript

    transaction = session.beginTransaction()
    transaction.commit()
    transaction.abort()

However, multi-document transactions are out of scope for this specification.

MongoClient changes
===================

``MongoClient`` interface summary

.. code:: typescript

    class SessionOptions {
        // various other options as defined in other specifications
    }

    interface MongoClient {
        ClientSession startSession(SessionOptions options);

        // other existing members of MongoClient
    }

Each new member is documented below.

startSession
------------

The ``startSession`` method starts a new ``ClientSession`` with the provided options.

It MUST NOT be possible to change the options provided to ``startSession`` after
``startSession`` has been called. This can be accomplished by making the
``SessionOptions`` class immutable or using some equivalent mechanism that is
idiomatic for your language.

It is valid to call ``startSession`` with no options set. This will result in a
``ClientSession`` that has no effect on the operations performed in the context of
that session, other than to include a session ID in commands sent to the
server.

The ``SessionOptions`` MAY be a strongly typed class in some drivers, or MAY be a
loosely typed dictionary in other drivers. Drivers MUST define ``SessionOptions``
in such a way that new options can be added in a backward compatible way (it is
acceptable for backward compatibility to be at the source level).

A ``ClientSession`` MUST be associated with a ``ServerSession`` at the time
``startSession`` is called. As an implementation optimization drivers SHOULD reuse
``ServerSession`` instances across multiple ``ClientSession`` instances subject to the rule that a server
session MUST NOT be used by two ``ClientSession`` instances at the same time (see the Server
Session Pool section).

``startSession`` MUST report an error if sessions are not supported by the
deployment (see How to Check Whether a Deployment Supports Sessions).

Authentication
~~~~~~~~~~~~~~

When using authentication, using a session requires that only a single user be
authenticated. Drivers that still support authenticating multiple users at once
MAY continue to do so, but MUST NOT allow sessions to be used under such
circumstances.

If ``startSession`` is called when multiple users are authenticated drivers MUST
raise an error with the error message "Cannot call startSession when multiple
users are authenticated."

If a driver allows authentication to be changed on the fly (presumably few
still do) the driver MUST either prevent ``ClientSession`` instances from being used with a
connection that doesn't have matching authentication or MUST return an error if
such use is attempted.

ClientSession
=============

``ClientSession`` instances are not thread safe. They can only be used by one
thread at a time.

Drivers MUST document the thread-safety limitations of sessions. Drivers MUST
NOT attempt to detect simultaneous use by multiple threads (see Q&A for the
rationale).

ClientSession interface summary

.. code:: typescript

    interface ClientSession {
        MongoClient client;
        SessionOptions options;
        BsonDocument sessionId;

        void endSession();
    }

While it is not part of the public API, a ``ClientSession`` also has a private (or
internal) reference to a ``ServerSession``.

Each member is documented below.

client
------

This property returns the ``MongoClient`` that was used to start this
``ClientSession``.

options
-------

This property returns the ``SessionOptions`` that were used to start this
``ClientSession``.

sessionId
---------

This property returns the session ID of this session. Note that if server
sessions are pooled, different ``ClientSession`` instances will have the same session ID,
but never at the same time.

endSession
----------

This method ends a ``ClientSession``.

In languages that have idiomatic ways of disposing of resources, drivers SHOULD
support that in addition to or instead of ``endSession``. For example, in the .NET
driver ``ClientSession`` would implement ``IDisposable`` and the application could
choose to call ``session.Dispose`` or put the session in a using statement instead
of calling ``session.endSession``. If your language has an idiomatic way of
disposing resources you MAY choose to implement that in addition to or instead
of ``endSession``, whichever is more idiomatic for your language.

A driver MUST allow multiple calls to ``endSession`` (or ``Dispose``). All calls after
the first one are ignored.

Conceptually, calling ``endSession`` implies ending the corresponding server
session (by calling the ``endSessions`` command). As an implementation detail
drivers SHOULD cache server sessions for reuse (see Server Session Pool).

Once a ``ClientSession`` has ended, drivers MUST report an error if any operations
are attempted with that ``ClientSession``.

ServerSession
=============

A ``ServerSession`` is the driver object that tracks a server session. This object
is an implementation detail and does not need to be public. Drivers may store
this information however they choose; this data structure is defined here
merely to describe the operation of the server session pool.

ServerSession interface summary

.. code:: typescript

    interface ServerSession {
        BsonDocument sessionId;
        DateTime lastUse;
    }

sessionId
---------

This property returns the server session ID.

lastUse
-------

The driver MUST update the value of this property with the current DateTime
every time the server session ID is sent to the server. This allows the driver
to track with reasonable accuracy the server's view of when a server session
was last used.

Creating a ServerSession
------------------------

When a driver needs to create a new ``ServerSession`` instance the only information
it needs is the session ID to use for the new session. It can either get the
session ID from the server by running the ``startSession`` command, or it can
generate it locally.

In either case, the lastUse field of the ``ServerSession`` MUST be set to the
current time when the ``ServerSession`` is created.

Generating a session ID locally
-------------------------------

Running the ``startSession`` command to get a session ID for a new session requires
a round trip to the server. As an optimization the server allows drivers to
generate new session IDs locally and to just start using them. When a server
sees a new session ID that it has never seen before it simply assumes that it
is a new session.

A session ID is a ``BsonDocument`` that has the following form:

.. code:: typescript

    { id : <UUID> }

Where the UUID is encoded as a BSON binary value of subtype 4.

The id field of the session ID is a version 4 UUID that must comply with the
format described in RFC 4122. Section 4.4 describes an algorithm for generating
correctly-versioned UUIDs from a pseudo-random number generator.

If a driver is unable to generate a version 4 UUID it MAY instead run the
``startSession`` command and let the server generate the session ID.

MongoDatabase changes
=====================

All ``MongoDatabase`` methods that talk to the server SHOULD be overloaded to take
a new session parameter. When sending commands to the server, the session ID
MUST be included so that the server can associate the operation with a session
ID.

When overloading methods to take a session parameter, the session parameter
SHOULD be the first parameter. If overloading is not possible for your
language, it MAY be in a different position or MAY be embedded in an options
structure.

Methods that have a session parameter MUST check that the session argument is
not null and was created by the same ``MongoClient`` that this ``MongoDatabase`` came
from and report an error if they do not match.

When an existing ``MongoDatabase`` method that does not take a session is called,
the driver MUST check whether the deployment supports sessions (See How to
Check Whether a Deployment Supports Session). If sessions are supported, the
driver MUST behave as if a new ``ClientSession`` was started just for this one
operation and ended immediately after this operation completes. The actual
implementation will likely involve calling ``client.startSession``, but that is not
required by this spec.

The motivation for using an implied ``ClientSession`` for all methods that don't
already take a session parameter is to make sure that all commands that are
sent to the server are tagged with a session ID. This improves the ability of
an operations team to monitor (and kill if necessary) long running operations.
Tagging an operation with a session ID is specially useful if a deployment wide
operation needs to be killed.

MongoCollection changes
=======================

All ``MongoCollection`` methods that talk to the server SHOULD be overloaded to
take a new session parameter. When sending commands to the server, the session
ID MUST be included so that the server can associate the operation with a
session ID.

When overloading methods to take a session parameter, the session parameter
SHOULD be the first parameter. If overloading is not possible for your
language, it MAY be in a different position or MAY be embedded in an options
structure.

Methods that have a session parameter MUST check that the session argument is
not null and was created by the same ``MongoClient`` that this ``MongoCollection`` came
from and report an error if they do not match.

When an existing ``MongoCollection`` method that does not take a session is called,
the driver MUST check whether the deployment supports sessions (See How to
Check Whether a Deployment Supports Session). If sessions are supported, the
driver MUST behave as if a new ``ClientSession`` was started just for this one
operation and ended immediately after this operation completes. The actual
implementation will likely involve calling ``client.startSession``, but that is not
required by this spec.

Sessions and Cursors
====================

When an operation using a session returns a cursor, all subsequent ``GETMORE``
commands for that cursor MUST be run using the same session ID.

If a driver decides to run a ``KILLCURSORS`` command on the cursor, it also MUST be
run using the same session ID. See the Exceptions below for when it is permissible to not
include a session ID in a ``KILLCURSORS`` command.

How to Check Whether a Deployment Supports Sessions
===================================================

A driver can determine whether a deployment supports sessions by checking
whether the ``logicalSessionTimeoutMinutes`` property of the ``TopologyDescription``
has a value or not. If it has a value the deployment supports sessions.
However, in order for this determination to be valid, the driver MUST be
connected to at least one server. Therefore, the detailed steps to determine
whether sessions are supported are: 

1. If the ``TopologyDescription`` indicates that the driver is not connected to
any servers, a driver must do a server selection for any server. Server
selection will either time out or result in a ``TopologyDescription`` that
includes at least one connected server

2. Having verified in step 1 that the ``TopologyDescription`` includes at least
one connected server a driver can now determine whether sessions are supported
by inspecting the ``logicalSessionTimeoutMinutes`` property

Sending the session ID to the server on all commands
====================================================

When connected to a server that supports sessions a driver MUST append the
session ID to every command it sends to the server (with the exceptions noted
in the following section). It does this by adding a
top level ``lsid`` field to the command sent to the server. A driver MUST do this
without modifying any data supplied by the application (e.g. the command
document passed to runCommand).:

.. code:: typescript

    { commandName: ..., lsid : { id : <UUID> } }

Exceptions to sending the session ID to the server on all commands
==================================================================

There are some exceptions to the rule that a driver MUST append the session ID to
every command it sends to the server.

A driver MUST NOT append a session ID to any command sent during the process of
opening and authenticating a connection.

A driver MAY omit a session ID in isMaster commands sent solely for the purposes
of monitoring the state of a deployment.

A driver MAY omit a session ID in ``KILLCURSORS`` commands intended to reap cursors
that have gone out of scope.

Server Commands
===============

startSession
------------

The ``startSession`` server command has the following format:

.. code:: typescript

    { startSession : 1, $clusterTime : ... }

The ``$clusterTime`` field should only be sent when gossipping the cluster time. See the
section "Gossipping the cluster time" for information on ``$clusterTime``.

The server response has the following format:

.. code:: typescript

    {
        ok : 1,
        id : <BsonDocument>,
    }

In case of an error, the server response has the following format:

.. code:: typescript

    { ok : 0, errmsg : "...", code : NN }

When connected to a replica set the ``startSession`` command MUST be sent to the
primary if the primary is available. The ``startSession`` command MAY be sent to a
secondary if there is no primary available at the time the ``startSession`` command
needs to be run.

Drivers SHOULD generate session IDs locally if possible instead of running the
``startSession`` command, since running the command requires a network round trip.

endSessions
-----------

The ``endSessions`` server command has the following format:

.. code:: typescript

    { endSessions : 1, ids : [ id1, id2, … ], $clusterTime : ... }

The ``$clusterTime`` field should only be sent when gossipping the cluster time. See the
section of "Gossipping the cluster time" for information on ``$clusterTime``.

The server response has the following format:

.. code:: typescript

    { ok : 1 }

In case of an error, the server response has the following format:

.. code:: typescript

    { ok : 0, errmsg : "...", code : NN }

Drivers MUST ignore any errors returned by the ``endSessions`` command.

Drivers that do not implement a server session pool MUST run the ``endSessions``
command when the ``ClientSession.endSession`` method is called. Drivers that do
implement a server session pool SHOULD run the ``endSessions`` command once when
the ``MongoClient`` instance is shut down. If the number of sessions is very large
the ``endSessions`` command SHOULD be run multiple times to end 10,000 sessions at
a time (in order to avoid creating excessively large commands).

When connected to a sharded cluster the ``endSessions`` command can be sent to any
mongos. When connected to a replica set the ``endSessions`` command MUST be sent to
the primary if the primary is available, otherwise it MUST be sent to any
available secondary.

Server Session Pool
===================

Conceptually, each ``ClientSession`` can be thought of as having a new
corresponding ``ServerSession``. However, starting a server session might require a
round trip to the server (which can be avoided by generating the session ID
locally) and ending a session requires a separate round trip to the server.
Drivers can operate more efficiently and put less load on the server if they
cache ``ServerSession`` instances for reuse. To this end drivers SHOULD implement a server
session pool containing ``ServerSession`` instances available for reuse. A
``ServerSession`` pool MUST belong to a ``MongoClient`` instance and have the same
lifetime as the ``MongoClient`` instance.

If a driver has a server session pool, then when a new ``ClientSession`` is started
it MUST attempt to acquire a server session from the server session pool. See
the algorithm below for the steps to follow when attempting to acquire a
``ServerSession`` from the server session pool.

Note that ``ServerSession`` instances acquired from the server session pool might have as
little as one minute left before becoming stale and being discarded server
side. Drivers MUST document that if an application waits more than one minute
after calling ``startSession`` to perform operations with that session it risks
getting errors due to the server session going stale before it was used.

A server session is considered stale by the server when it has not been used
for a certain amount of time. The default amount of time is 30 minutes, but
this value is configurable on the server. Servers that support sessions will
report this value in the ``logicalSessionTimeoutMinutes`` field of the reply
to the ``ismaster`` command. The smallest reported timeout is recorded in the
``logicalSessionTimeoutMinutes`` property of the ``TopologyDescription``. See the
Server Discovery And Monitoring specification for details.

If a driver has a server session pool, then when a ``ClientSession`` is ended it
MUST return the server session to the server session pool. See the algorithm
below for the steps to follow when returning a ``ServerSession`` instance to the server
session pool.

The server session pool has no maximum size. The pool only shrinks when a
server session is acquired for use or discarded.

If a driver has a server session pool, then when a ``MongoClient`` instance is
closed the driver MUST proactively inform the server that the pooled server
sessions will no longer be used by sending one or more ``endSessions`` commands to the
server.

The server session pool is modeled as a double ended queue. The algorithms
below require the ability to add and remove ``ServerSession`` instances from the front of
the queue and to inspect and possibly remove ``ServerSession`` instances from the back of
the queue. The front of the queue holds ``ServerSession`` instances that have been released
recently and should be the first to be reused. The back of the queue holds
``ServerSession`` instances that have not been used recently and that potentially will be
discarded if they are not used again before they expire.

Algorithm to acquire a ServerSession instance from the server session pool
--------------------------------------------------------------------------

1. If the server session pool is empty create a new ``ServerSession`` and use it

2. Otherwise remove a ``ServerSession`` from the front of the queue and examine it:
    * If it has at least one minute left before becoming stale use this ``ServerSession``
    * If it has less than one minute left before becoming stale discard it (let it be garbage collected) and return to step 1.

Algorithm to return a ServerSession instance to the server session pool
-----------------------------------------------------------------------

1. Before returning a server session to the pool a driver MUST first check the
   server session pool for server sessions at the back of the queue that are about
   to expire (meaning they will expire in less than one minute). A driver MUST
   stop checking server sessions once it encounters a server session that is not
   about to expire. Any server sessions found that are about to expire are removed
   from the end of the queue and discarded (or allowed to be garbage collected)

2. Then examine the server session that is being returned to the pool and:
    * If it won't expire for at least one minute add it to the front of the queue
    * If it will expire in less than one minute discard it (let it be garbage collected)

Gossipping the cluster time
===========================

Drivers MUST gossip the cluster time when connected to a deployment that uses
cluster times.

Gossipping the cluster time is a process in which the driver participates in
distributing the logical cluster time in a deployment. Drivers learn the
current cluster time (from a particular server's perspective) in responses
they receive from servers. Drivers in turn forward the highest cluster
time they have seen so far to any server they subsequently send commands
to.

A driver detects that it MUST participate in gossipping the cluster time when it sees
a $clusterTime in a response received from a server.

Receiving the current cluster time
----------------------------------

Drivers MUST examine all responses to server
commands to see if they contain a top level field named ``$clusterTime`` formatted
as follows:

.. code:: typescript

    {
        ...
        $clusterTime : {
            clusterTime : <BsonTimestamp>,
            signature : {
                hash : <BsonBinaryData>,
                keyId : <BsonInt64>
            }
        },
        ...
    }

Whenever a driver receives a cluster time from a server it MUST compare it to
the current highest seen cluster time for the deployment. If the new cluster time
is higher than the highest seen cluster time it MUST become the new highest
seen cluster time. Two cluster times are compared using only the BsonTimestamp
value of the ``clusterTime`` embedded field (be sure to include both the timestamp
and the increment of the BsonTimestamp in the comparison). The signature field
does not participate in the comparison.

Sending the highest seen cluster time
-------------------------------------

Whenever a driver sends a command to a server it MUST include the highest
seen cluster time in a top level field called ``$clusterTime``, in the same format
as it was received in (but see Gossipping with mixed server versions below).

How to compute the $clusterTime to send to a server
---------------------------------------------------

When starting a ``ClientSession``, applications can optionally initialize the
causal consistency properties of the ``ClientSession`` by setting the
``initialClustertime`` (and ``initialOperationTime``) properties of
``SessionOptions``. If these values are not valid they can cause errors. In
order to protect itself a driver must use these values only with the
``ClientSession`` in which they are defined. Only ``$clusterTime`` values that come
directly from a server should be allowed to propagate to the ``MongoClient``.

The safe way to compute the ``$clusterTime`` to send to a server is:

1. when the ``ClientSession`` is first started its ``clusterTime`` is set to
``initialClusterTime``

2. when the driver sends ``$clusterTime`` to the server it should send the
greater of the ``ClientSession`` ``clusterTime`` and the ``MongoClient``
``clusterTime` (either one could be null)

3. when the driver receives a ``$clusterTime`` from the server it should update
both the ``ClientSession`` and the ``MongoClient`` ``clusterTime``

This sequence ensures that if the ``initialClusterTime`` is invalid only that
one session will be affected. The ``MongoClient`` ``clusterTime`` is only
updated with ``$clusterTime`` values known to be valid because they were
received directly from a server.

Tracking the highest seen cluster time does not require checking the deployment topology or the server version
--------------------------------------------------------------------------------------------------------------

Drivers do not need to check the deployment topology or the server version they
are connected to in order to track the highest seen ``$clusterTime``. They simply
need to check for the presence of the ``$clusterTime`` field in responses received
from servers.

Gossipping with mixed server versions
-------------------------------------

Drivers MUST check that the server they are sending a command to supports
``$clusterTime`` before adding ``$clusterTime`` to the command. A server supports
``$clusterTime`` when the ``maxWireVersion`` >= 6.

This supports the (presumably short lived) scenario where not all servers have
been upgraded to 3.6.

Test Plan
=========

1. Pool is LIFO.
    * This test applies to drivers with session pools. 
    * Call ``MongoClient.startSession`` twice to create two sessions, let us call them ``A`` and ``B``. 
    * Call ``A.endSession``, then ``B.endSession``. 
    * Call ``MongoClient.startSession``: the resulting session must have the same session ID as ``B``. 
    * Call ``MongoClient.startSession`` again: the resulting session must have the same session ID  as ``A``.

2. ``$clusterTime`` in commands
    * Turn ``heartbeatFrequencyMS`` up to a very large number.
    * Register a command-started and a command-succeeded APM listener. 
    * Send a ``ping`` command to the server with the generic ``runCommand`` method. 
    * Assert that the command passed to the command-started listener includes ``$clusterTime`` if and only if ``maxWireVersion`` >= 6.
    * Record the ``$clusterTime``, if any, in the reply passed to the command-succeeded APM listener.
    * Send another ``ping`` command.
    * Assert that ``$clusterTime`` in the command passed to the command-started listener, if any, equals the ``$clusterTime`` in the previous server reply. (Turning ``heartbeatFrequencyMS`` up prevents an intervening heartbeat from advancing the ``$clusterTime`` between these final two steps.)

    Repeat for:
        * An aggregate command from the ``aggregate`` helper method
        * A find command from the ``find`` helper method
        * An insert command from the ``insert_one`` helper method

3. Test that session argument is for the right client
    * Create ``client1`` and ``client2``
    * Get ``database`` from ``client1``
    * Get ``collection`` from ``database``
    * Start ``session`` from ``client2``
    * Call ``collection.insertOne(session,...)``
    * Assert that an error was reported because ``session`` was not started from ``client1``

    Repeat for:
        * All methods that take a session parameter.

4. Test that no further operations can be performed using a session after ``endSession`` has been called
    * Start a ``session``
    * End the ``session``
    * Call ``collection.InsertOne(session, ...)``
    * Assert that the proper error was reported

    Repeat for:
        * All methods that take a session parameter.

    If your driver implements a platform dependent idiomatic disposal pattern, test
    that also (if the idiomatic disposal pattern calls ``endSession`` it would be
    sufficient to only test the disposal pattern since that ends up calling
    ``endSession``).

Motivation 
==========

Drivers currently have no concept of a session. The driver API needs to be
extended to support sessions.

Design Rationale
================

The goal is to modify the driver API in such a way that existing programs that
don't use sessions continue to compile and run correctly. This goal is met by
defining new methods (or overloads) that take a session parameter. An
application does not need to be modified unless it wants to take advantage of
the new features supported by sessions.

Backwards Compatibility
=======================

The API changes to support sessions extend the existing API but do not
introduce any backward breaking changes. Existing programs that don't use
sessions continue to compile and run correctly.

Reference Implementation (always required)
==========================================

A reference implementation must be completed before any spec is given status
"Final", but it need not be completed before the spec is “Accepted”. While
there is merit to the approach of reaching consensus on the specification and
rationale before writing code, the principle of "rough consensus and running
code" is still useful when it comes to resolving many discussions of spec
details. A final reference implementation must include test code and
documentation.

The C and C# drivers will do initial POC implementations.

Future work (optional)
======================

Use this section to discuss any possible work for a future spec. This could
cover issues where no consensus could be reached but that don’t block this
spec, changes that were rejected due to unclear use cases, etc.

Open questions
==============

Q&A
===

Q: Why do we say drivers MUST NOT attempt to detect unsafe multi-threaded use of ``ClientSession``?
    Because doing so would provide an illusion of safety. It doesn't make these
    instances thread safe. And even if when testing an application no such exceptions
    are encountered, that doesn't prove anything. The application might still be
    using the instances in a thread-unsafe way and just didn't happen to do so during
    a test run. The final argument is that checking this would require overhead
    that doesn't provide any clear benefit. 

Change log
==========

2017-09-29 Add an exception to the rule that ``KILLCURSORS`` commands always require a session id
2017-09-13 If causalConsistency option is ommitted assume true
2017-09-16 Omit session ID when opening and authenticating a connection
2017-09-18 Drivers MUST gossip the cluster time when they see a $clusterTime
2017-09-19 How to safely use initialClusterTime

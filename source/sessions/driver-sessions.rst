=============================
Driver Sessions Specification
=============================

:Status: Accepted
:Minimum Server Version: 3.6

.. contents::

--------

Abstract
========

Version 3.6 of the server introduces the concept of logical sessions for
clients. A session is an abstract concept that represents a set of sequential
operations executed by an application that are related in some way. This
specification is limited to how applications start and end sessions. Other
specifications define various ways in which sessions are used (e.g. causally
consistent reads, retryable writes, or transactions).

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

Explicit session
    A session that was started explicitly by the application by calling ``startSession``
    and passed as an argument to an operation.

MongoClient
    The root object of a driver's API. MAY be named differently in some drivers.

Implicit session
    A session that was started implicitly by the driver because the application
    called an operation without providing an explicit session.

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

Unacknowledged writes
    Unacknowledged writes are write operations that are sent to the server
    without waiting for a reply acknowledging the write. See the "When using
    unacknowledged writes" section below for information on how unacknowledged
    writes interact with sessions.

Network error
    Any network exception writing to or reading from a socket (e.g. a socket
    timeout or error).

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

    options = new SessionOptions(/* various settings */);
    session = client.startSession(options);

The ``SessionOptions`` will be individually defined in several other
specifications. It is expected that the set of ``SessionOptions`` will grow over
time as sessions are used for new purposes.

Applications use a session by passing it as an argument to operation methods.
For example:

.. code:: typescript

    collection.InsertOne(session /* etc. */)
    collection.UpdateOne(session /* etc. */)

Applications end a session like this:

.. code:: typescript

    session.endSession()

This specification does not deal with multi-document transactions, which
are covered in `their own specification <../transactions/transactions.rst>`_.

MongoClient changes
===================

``MongoClient`` interface summary

.. code:: java

    class SessionOptions {
      // various other options as defined in other specifications
    }

    interface MongoClient {
      ClientSession startSession(SessionOptions options);
      // other existing members of MongoClient
    }

Each new member is documented below.

While it is not part of the public API, ``MongoClient`` also needs a private
(or internal) ``clusterTime`` member (containing either a BSON document or
null) to record the highest ``clusterTime`` observed in a deployment (as
described below in `Gossipping the cluster time`_).

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
``startSession`` is called. As an implementation optimization drivers MUST reuse
``ServerSession`` instances across multiple ``ClientSession`` instances subject
to the rule that a server session MUST NOT be used by two ``ClientSession``
instances at the same time (see the Server Session Pool section). Additionally,
a ``ClientSession`` may only ever be associated with one ``ServerSession`` for
its lifetime.

Drivers MUST NOT check for session support in `startSession`. Instead, if sessions 
are not supported, the error MUST be reported the first time the session is used
for an operation (See `How to Check Whether a Connection Supports Sessions`_).

Explicit vs implicit sessions
-----------------------------

An explicit session is one started explicitly by the application by calling
``startSession``. An implicit session is one started implicitly by the driver
because the application called an operation without providing an explicit
session. Internally, a driver must be able to distinguish between explicit and
implicit sessions, but no public API for this is necessary because an
application will never see an implicit session.

The motivation for starting an implicit session for all methods that don't
take an explicit session parameter is to make sure that all commands that are
sent to the server are tagged with a session ID. This improves the ability of
an operations team to monitor (and kill if necessary) long running operations.
Tagging an operation with a session ID is specially useful if a deployment wide
operation needs to be killed.

Authentication
--------------

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

``ClientSession`` instances are not thread safe or fork safe. They can only be
used by one thread or process at a time.

Drivers MUST document the thread-safety and fork-safety limitations of sessions.
Drivers MUST NOT attempt to detect simultaneous use by multiple threads or
processes (see Q&A for the rationale).

ClientSession interface summary:

.. code:: java

    interface ClientSession {
        MongoClient client;
        Optional<BsonDocument> clusterTime;
        SessionOptions options;
        BsonDocument sessionId;

        void advanceClusterTime(BsonDocument clusterTime);
        void endSession();
    }

While it is not part of the public API, a ``ClientSession`` also has a private
(or internal) reference to a ``ServerSession``.

Each member is documented below.

client
------

This property returns the ``MongoClient`` that was used to start this
``ClientSession``.

clusterTime
-----------

This property returns the most recent cluster time seen by this session. If no
operations have been executed using this session this value will be null unless
``advanceClusterTime`` has been called. This value will also be null when a
cluster does not report cluster times.

When a driver is gossiping the cluster time it should send the more recent
``clusterTime`` of the ``ClientSession`` and the ``MongoClient``.

options
-------

This property returns the ``SessionOptions`` that were used to start this
``ClientSession``.

sessionId
---------

This property returns the session ID of this session. Note that since ``ServerSessions``
are pooled, different ``ClientSession`` instances can have the same session ID,
but never at the same time.

advanceClusterTime
------------------

This method advances the ``clusterTime`` for a session. If the new
``clusterTime`` is greater than the session's current ``clusterTime`` then the
session's ``clusterTime`` MUST be advanced to the new ``clusterTime``. If the
new ``clusterTime`` is less than or equal to the session's current
``clusterTime`` then the session's ``clusterTime`` MUST NOT be changed.

This method MUST NOT advance the ``clusterTime`` in ``MongoClient`` because we
have no way of verifying that the supplied ``clusterTime`` is valid. If the
``clusterTime`` in ``MongoClient`` were set to an invalid value all future
operations with this ``MongoClient`` would result in the server returning an
error. The ``clusterTime`` in ``MongoClient`` should only be advanced with a
``$clusterTime`` received directly from a server.

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

.. code:: java

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

    interface SessionId {
      id: UUID
    }

Where the UUID is encoded as a BSON binary value of subtype 4.

The id field of the session ID is a version 4 UUID that must comply with the
format described in RFC 4122. Section 4.4 describes an algorithm for generating
correctly-versioned UUIDs from a pseudo-random number generator.

If a driver is unable to generate a version 4 UUID it MAY instead run the
``startSession`` command and let the server generate the session ID.

MongoDatabase changes
=====================

All ``MongoDatabase`` methods that talk to the server MUST send a session ID
with the command when connected to a deployment that supports sessions so that
the server can associate the operation with a session ID.

New database methods that take an explicit session
--------------------------------------------------

All ``MongoDatabase`` methods that talk to the server SHOULD be overloaded to
take an explicit session parameter. (See `why is session an explicit parameter?`_.)

When overloading methods to take a session parameter, the session parameter
SHOULD be the first parameter. If overloading is not possible for your
language, it MAY be in a different position or MAY be embedded in an options
structure.

Methods that have a session parameter MUST check that the session argument is
not null and was created by the same ``MongoClient`` that this ``MongoDatabase`` came
from and report an error if they do not match.

Existing database methods that start an implicit session
--------------------------------------------------------

When an existing ``MongoDatabase`` method that does not take a session is called,
the driver MUST behave as if a new ``ClientSession`` was started just for this one
operation and ended immediately after this operation completes. The actual
implementation will likely involve calling ``client.startSession``, but that is not
required by this spec. Regardless, please consult the startSession section to
replicate the required steps for creating a session.
The driver MUST check for session support, but only after the connection is checked out
(See `How to Check Whether a Connection Supports Sessions`_) and MUST NOT consume a server  
session id until after the connection is checked out and session support is confirmed.

MongoCollection changes
=======================

All ``MongoCollection`` methods that talk to the server MUST send a session ID
with the command when connected to a deployment that supports sessions so that
the server can associate the operation with a session ID.

New collection methods that take an explicit session
----------------------------------------------------

All ``MongoCollection`` methods that talk to the server, with the exception of
`estimatedDocumentCount`, SHOULD be overloaded to take an explicit session
parameter. (See `why is session an explicit parameter?`_.)

When overloading methods to take a session parameter, the session parameter
SHOULD be the first parameter. If overloading is not possible for your
language, it MAY be in a different position or MAY be embedded in an options
structure.

Methods that have a session parameter MUST check that the session argument is
not null and was created by the same ``MongoClient`` that this ``MongoCollection`` came
from and report an error if they do not match.

The `estimatedDocumentCount` helper does not support an explicit session
parameter. The underlying command, `count`, is not supported in a transaction,
so supporting an explicit session would likely confuse application developers.
The helper returns an estimate of the documents in a collection and
causal consistency is unlikely to improve the accuracy of the estimate.

Existing collection methods that start an implicit session
----------------------------------------------------------

When an existing ``MongoCollection`` method that does not take a session is called,
the driver MUST behave as if a new ``ClientSession`` was started just for this one
operation and ended immediately after this operation completes. The actual
implementation will likely involve calling ``client.startSession``, but that is not
required by this spec. Regardless, please consult the startSession section to
replicate the required steps for creating a session.
The driver MUST check for session support, but only after the connection is checked out
(See `How to Check Whether a Connection Supports Sessions`_) and MUST NOT consume a server  
session id until after the connection is checked out and session support is confirmed.

Sessions and Cursors
====================

When an operation using a session returns a cursor, all subsequent ``GETMORE``
commands for that cursor MUST be run using the same session ID.

If a driver decides to run a ``KILLCURSORS`` command on the cursor, it also MAY be
run using the same session ID. See the Exceptions below for when it is permissible to not
include a session ID in a ``KILLCURSORS`` command.

Sessions and Connections
========================

To reduce the number of ``ServerSessions`` created, the driver MUST only obtain an implicit session's
``ServerSession`` after it successfully checks out a connection.
A driver SHOULD NOT attempt to release the acquired session before connection check in.

Explicit sessions MAY be changed to allocate a server session similarly.

How to Check Whether a Connection Supports Sessions
===================================================

A driver can determine whether a connection supports sessions by checking whether
the ``logicalSessionTimeoutMinutes`` property of the establishing handshake response has
a value or not. If it has a value, sessions are supported.

In the case of an explicit session, if sessions are not supported, the driver MUST raise an error.
In the case of an implicit session, if sessions are not supported, the driver MUST ignore the session.

Possible race condition when checking for session support
---------------------------------------------------------

There is a possible race condition that can happen between the time the
driver checks whether sessions are supported and subsequently sends a command
to the server:

* The server might have supported sessions at the time the connection was first
  opened (and reported a value for logicalSessionTimeoutMinutes in the initial
  response to the `handshake <https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst>`_),
  but have subsequently been downgraded to not support sessions. The server does
  not close the socket in this scenario, so the driver will conclude that
  the server at the other end of this connection supports sessions.

There is nothing that the driver can do about this race condition, and the server 
will just return an error in this scenario.

Sending the session ID to the server on all commands
====================================================

When connected to a server that supports sessions a driver MUST append the
session ID to every command it sends to the server (with the exceptions noted
in the following section). It does this by adding a
top level ``lsid`` field to the command sent to the server. A driver MUST do this
without modifying any data supplied by the application (e.g. the command
document passed to runCommand).:

.. code:: typescript

    interface ExampleCommandWithLSID {
      foo: 1;
      lsid: SessionId;
    }

Exceptions to sending the session ID to the server on all commands
==================================================================

There are some exceptions to the rule that a driver MUST append the session ID to
every command it sends to the server.

When opening and authenticating a connection
--------------------------------------------

A driver MUST NOT append a session ID to any command sent during the process of
opening and authenticating a connection.

When monitoring the state of a deployment
-----------------------------------------

A driver MAY omit a session ID in hello and legacy hello commands sent solely
for the purposes of monitoring the state of a deployment.

When sending a parallelCollectionScan command
---------------------------------------------

Sessions are designed for sequential operations and ``parallelCollectionScan``
is designed for parallel operation.  Because these are fundamentally
incompatible goals, drivers MUST NOT append session ID to the
``parallelCollectionScan`` command so that the resulting cursors have
no associated session ID and thus can be used in parallel.

When sending a killCursors command
----------------------------------

A driver MAY omit a session ID in ``killCursors`` commands for two reasons.
First, ``killCursors`` is only ever sent to a particular server, so operation teams
wouldn't need the ``lsid`` for cluster-wide killOp. An admin can manually kill the op with
its operation id in the case that it is slow. Secondly, some drivers have a background
cursor reaper to kill cursors that aren't exhausted and closed. Due to GC semantics,
it can't use the same ``lsid`` for ``killCursors`` as was used for a cursor's ``find`` and ``getMore``,
so there's no point in using any ``lsid`` at all.

When multiple users are authenticated and the session is implicit
-----------------------------------------------------------------

The driver MUST NOT send a session ID from an implicit session when multiple
users are authenticated. If possible the driver MUST NOT start an implicit
session when multiple users are authenticated. Alternatively, if the driver
cannot determine whether multiple users are authenticated at the point in time
that an implicit session is started, then the driver MUST ignore any implicit
sessions that subsequently end up being used on a connection that has multiple
users authenticated.

When using unacknowledged writes
--------------------------------

A session ID MUST NOT be used simultaneously by more than one operation. Since
drivers don't wait for a response for an unacknowledged write a driver would
not know when the session ID could be reused. In theory a driver could use a
new session ID for each unacknowledged write, but that would result in many
orphaned sessions building up at the server.

Therefore drivers MUST NOT send a session ID with unacknowledged writes under
any circumstances:

* For unacknowledged writes with an explicit session, drivers SHOULD raise an
  error.  If a driver allows users to provide an explicit session with an
  unacknowledged write (e.g. for backwards compatibility), the driver MUST NOT
  send the session ID.

* For unacknowledged writes without an explicit session, drivers SHOULD NOT use
  an implicit session.  If a driver creates an implicit session for
  unacknowledged writes without an explicit session, the driver MUST NOT send
  the session ID.

Drivers MUST document the behavior of unacknowledged writes for both explicit
and implicit sessions.

When wrapping commands in a ``$query`` field
--------------------------------------------

If the driver is wrapping the command in a ``$query`` field for non-OP_MSG messages in order to pass a readPreference to a
mongos (see `ReadPreference and Mongos <./find_getmore_killcursors_commands.rst#readpreference-and-mongos>`_),
the driver SHOULD NOT add the ``lsid`` as a top-level field, and MUST add the ``lsid`` as a field of the ``$query``

.. code:: typescript

    // Wrapped command:
    interface WrappedCommandExample {
      $query: {
        find: { foo: 1 }
      },
      $readPreference: {}
    }

    // Correct application of lsid
    interface CorrectLSIDUsageExample {
      $query: {
        find: { foo: 1 },
        lsid: SessionId
      },
      $readPreference: {}
    }

    // Incorrect application of lsid
    interface IncorrectLSIDUsageExample {
      $query: {
        find: { foo: 1 }
      },
      $readPreference: {},
      lsid: SessionId
    }


Server Commands
===============

startSession
------------

The ``startSession`` server command has the following format:

.. code:: typescript

    interface StartSessionCommand {
      startSession: 1;
      $clusterTime?: ClusterTime;
    }

The ``$clusterTime`` field should only be sent when gossipping the cluster time. See the
section "Gossipping the cluster time" for information on ``$clusterTime``.

The ``startSession`` command MUST be sent to the ``admin`` database.

The server response has the following format:

.. code:: typescript

    interface StartSessionResponse {
      ok: 1;
      id: BsonDocument;
    }

In case of an error, the server response has the following format:

.. code:: typescript

    interface StartSessionError {
      ok: 0;
      errmsg: string;
      code: number;
    }

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

    interface EndSessionCommand {
      endSessions: Array<SessionId>;
      $clusterTime?: ClusterTime;
    }

The ``$clusterTime`` field should only be sent when gossipping the cluster time. See the
section of "Gossipping the cluster time" for information on ``$clusterTime``.

The ``endSessions`` command MUST be sent to the ``admin`` database.

The server response has the following format:

.. code:: typescript

    interface EndSessionResponse {
      ok: 1;
    }

In case of an error, the server response has the following format:

.. code:: typescript

    interface EndSessionError {
      ok: 0;
      errmsg: string;
      code: number;
    }

Drivers MUST ignore any errors returned by the ``endSessions`` command.

The ``endSessions`` command MUST be run once when the ``MongoClient`` instance is shut down.
If the number of sessions is very large the ``endSessions`` command SHOULD be run
multiple times to end 10,000 sessions at a time (in order to avoid creating excessively large commands).

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
cache ``ServerSession`` instances for reuse. To this end drivers MUST
implement a server session pool containing ``ServerSession`` instances
available for reuse. A ``ServerSession`` pool MUST belong to a ``MongoClient``
instance and have the same lifetime as the ``MongoClient`` instance.

When a new implicit ``ClientSession`` is started it MUST NOT attempt to acquire a server
session from the server session pool immediately. When a new explicit ``ClientSession`` is started
it MAY attempt to acquire a server session from the server session pool immediately.
See the algorithm below for the steps to follow when attempting to acquire a ``ServerSession`` from the server session pool.

Note that ``ServerSession`` instances acquired from the server session pool might have as
little as one minute left before becoming stale and being discarded server
side. Drivers MUST document that if an application waits more than one minute
after calling ``startSession`` to perform operations with that session it risks
getting errors due to the server session going stale before it was used.

A server session is considered stale by the server when it has not been used
for a certain amount of time. The default amount of time is 30 minutes, but
this value is configurable on the server. Servers that support sessions will
report this value in the ``logicalSessionTimeoutMinutes`` field of the reply
to the hello and legacy hello commands. The smallest reported timeout is recorded in the
``logicalSessionTimeoutMinutes`` property of the ``TopologyDescription``. See the
Server Discovery And Monitoring specification for details.

When a ``ClientSession`` is ended it MUST return the server session to the server session pool.
See the algorithm below for the steps to follow when returning a ``ServerSession`` instance to the server
session pool.

The server session pool has no maximum size. The pool only shrinks when a
server session is acquired for use or discarded.

When a ``MongoClient`` instance is closed the driver MUST proactively inform the
server that the pooled server sessions will no longer be used by sending one or
more ``endSessions`` commands to the server.

The server session pool is modeled as a double ended queue. The algorithms
below require the ability to add and remove ``ServerSession`` instances from the front of
the queue and to inspect and possibly remove ``ServerSession`` instances from the back of
the queue. The front of the queue holds ``ServerSession`` instances that have been released
recently and should be the first to be reused. The back of the queue holds
``ServerSession`` instances that have not been used recently and that potentially will be
discarded if they are not used again before they expire.

An implicit session MUST be returned to the pool immediately following the completion of
an operation.  When an implicit session is associated with a cursor for use with ``getMore``
operations, the session MUST be returned to the pool immediately following a ``getMore``
operation that indicates that the cursor has been exhausted. In particular, it MUST not wait
until all documents have been iterated by the application or until the application disposes
of the cursor.  For language runtimes that provide the ability to attach finalizers to objects
that are run prior to garbage collection, the cursor class SHOULD return an implicit session
to the pool in the finalizer if the cursor has not already been exhausted.

If a driver supports process forking, the session pool needs to be cleared on
one side of the forked processes (just like sockets need to reconnect).
Drivers MUST provide a way to clear the session pool without sending
``endSessions``.  Drivers MAY make this automatic when the process ID changes.
If they do not, they MUST document how to clear the session pool wherever they
document fork support.  After clearing the session pool in this way, drivers
MUST ensure that sessions already checked out are not returned to the new pool.

If a driver has a server session pool and a network error is encountered when
executing any command with a ``ClientSession``, the driver MUST mark the
associated ``ServerSession`` as dirty. Dirty server sessions are discarded
when returned to the server session pool. It is valid for a dirty session to be
used for subsequent commands (e.g. an implicit retry attempt, a later command
in a bulk write, or a later operation on an explicit session), however, it MUST
remain dirty for the remainder of its lifetime regardless if later commands
succeed.

Algorithm to acquire a ServerSession instance from the server session pool
--------------------------------------------------------------------------

1. If the server session pool is empty create a new ``ServerSession`` and use it

2. Otherwise remove a ``ServerSession`` from the front of the queue and examine it:

   * If the driver is in load balancer mode, use this ``ServerSession``.
   * If it has at least one minute left before becoming stale use this ``ServerSession``
   * If it has less than one minute left before becoming stale discard it (let it be garbage collected) and return to step 1.

See the `Load Balancer Specification <../load-balancers/load-balancers.rst#session-expiration>`__
for details on session expiration.


Algorithm to return a ServerSession instance to the server session pool
-----------------------------------------------------------------------

1. Before returning a server session to the pool a driver MUST first check the
   server session pool for server sessions at the back of the queue that are about
   to expire (meaning they will expire in less than one minute). A driver MUST
   stop checking server sessions once it encounters a server session that is not
   about to expire. Any server sessions found that are about to expire are removed
   from the end of the queue and discarded (or allowed to be garbage collected)

2. Then examine the server session that is being returned to the pool and:

   * If this session is marked dirty (i.e. it was involved in a network error)
     discard it (let it be garbage collected)
   * If it will expire in less than one minute discard it
     (let it be garbage collected)
   * If it won't expire for at least one minute add it to the front of the queue

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
a ``$clusterTime`` in a response received from a server.

Receiving the current cluster time
----------------------------------

Drivers MUST examine all responses from the server
commands to see if they contain a top level field named ``$clusterTime`` formatted
as follows:

.. code:: typescript

  interface ClusterTime {
    clusterTime: Timestamp;
    signature: {
      hash: Binary;
      keyId: Int64;
    };
  }

  interface AnyServerResponse {
    // ... other properties ...
    $clusterTime: ClusterTime;
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

When sending ``$clusterTime`` to the server the driver MUST send the greater of
the ``clusterTime`` values from ``MongoClient`` and ``ClientSession``. Normally
a session's ``clusterTime`` will be less than or equal to the ``clusterTime``
in ``MongoClient``, but it could be greater than the ``clusterTime`` in
``MongoClient`` if ``advanceClusterTime`` was called with a ``clusterTime``
that came from somewhere else.

A driver MUST NOT use the ``clusterTime`` of a ``ClientSession`` anywhere else
except when executing an operation with this session. This rule protects the
driver from the scenario where ``advanceClusterTime`` was called with an
invalid ``clusterTime`` by limiting the resulting server errors to the one
session. The ``clusterTime`` of a ``MongoClient`` MUST NOT be advanced by any
``clusterTime`` other than a ``$clusterTime`` received directly from a server.

The safe way to compute the ``$clusterTime`` to send to a server is:

1. When the ``ClientSession`` is first started its ``clusterTime`` is set to
null.

2. When the driver sends ``$clusterTime`` to the server it should send the
greater of the ``ClientSession`` ``clusterTime`` and the ``MongoClient``
``clusterTime`` (either one could be null).

3. When the driver receives a ``$clusterTime`` from the server it should advance
both the ``ClientSession`` and the ``MongoClient`` ``clusterTime``. The ``clusterTime``
of a ``ClientSession`` can also be advanced by calling ``advanceClusterTime``.

This sequence ensures that if the ``clusterTime`` of a ``ClientSession`` is invalid only that
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

See the `README <tests/README.rst>`_ for tests.

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

Why do we say drivers MUST NOT attempt to detect unsafe multi-threaded or multi-process use of ``ClientSession``?
-----------------------------------------------------------------------------------------------------------------

Because doing so would provide an illusion of safety. It doesn't make these
instances thread safe. And even if when testing an application no such exceptions
are encountered, that doesn't prove anything. The application might still be
using the instances in a thread-unsafe way and just didn't happen to do so during
a test run. The final argument is that checking this would require overhead
that doesn't provide any clear benefit.

Why is session an explicit parameter?
-------------------------------------

A previous draft proposed that ClientSession would be a MongoClient-like object added to the object hierarchy::

  session = client.startSession(...)
  database = session.getDatabase(...) // database is associated with session
  collection = database.getCollection(...) // collection is associated with session
  // operations on collection implicitly use session
  collection.insertOne({})
  session.endSession()

The central feature of this design is that a MongoCollection (or database, or perhaps a GridFS object) is associated with a session, which is then an implied parameter to any operations executed using that MongoCollection.

This API was rejected, with the justification that a ClientSession does not naturally belong to the state of a MongoCollection. MongoCollection has up to now been a stable long-lived object that could be widely shared, and in most drivers it is thread safe. Once we associate a ClientSession with it, the MongoCollection object becomes short-lived and is no longer thread safe. It is a bad sign that MongoCollection's thread safety and lifetime vary depending on how its parent MongoDatabase is created.

Instead, we require users to pass session as a parameter to each function::

  session = client.startSession(...)
  database = client.getDatabase(...)
  collection = database.getCollection(...)
  // users must explicitly pass session to operations
  collection.insertOne(session, {})
  session.endSession()

Why does a network error cause the ``ServerSession`` to be discarded from the pool?
-----------------------------------------------------------------------------------

When a network error is encountered when executing an operation with a
``ClientSession``, the operation may be left running on the server. Re-using
this ``ServerSession`` can lead to parallel operations which violates the
rule that a session must be used sequentially. This results in multiple
problems:

#. killSessions to end an earlier operation would surprisingly also end a
   later operation.
#. An otherwise unrelated operation that just happens to use that same server
   session will potentially block waiting for the previous operation to
   complete. For example, a transactional write will block a subsequent
   transactional write.

Why do automatic retry attempts re-use a dirty implicit session?
----------------------------------------------------------------

The retryable writes spec requires that both the original and retry attempt
use the same server session. The server will block the retry attempt until the
initial attempt completes at which point the retry attempt will continue
executing.

For retryable reads that use an implicit session, drivers could choose to use a
new server session for the retry attempt however this would lose the
information that these two reads are related.

Why don't drivers run the endSessions command to cleanup dirty server sessions?
-------------------------------------------------------------------------------

Drivers do not run the endSessions command when discarding a dirty server
session because disconnects should be relatively rare and the server won't
normally accumulate a large number of abandoned dirty sessions. Any abandoned
sessions will be automatically cleaned up by the server after the
configured ``logicalSessionTimeoutMinutes``.


Why must drivers wait to consume a server session until after a connection is checked out?
------------------------------------------------------------------------------------------

The problem that may occur is when the number of concurrent application requests are larger than the number of available connections,
the driver may generate many more implicit sessions than connections.
For example with maxPoolSize=1 and 100 threads, 100 implicit sessions may be created.
This increases the load on the server since session state is cached in memory.
In the worst case this kind of workload can hit the session limit and trigger TooManyLogicalSessions.

In order to address this, drivers MUST NOT consume a server session id until after the connection is checked out.
This change will limit the number of "in use" server sessions to no greater than an application's maxPoolSize.

The language here is specific about obtaining a server session as opposed to creating the implicit session
to permit drivers to take an implementation approach where the implicit session creation logic largely remains unchanged.
Implicit session creation can be left as is, as long as the underlying server resource isn't allocated until it
is needed and, known it will be used, after connection checkout succeeds.

It is still possible that via explicit sessions or cursors, which hold on to the session they started with, a driver could over allocate sessions.
But those scenarios are extenuating and outside the scope of solving in this spec.

Why should drivers NOT attempt to release a serverSession before checking back in the operation's connection?
-------------------------------------------------------------------------------------------------------------

There are a variety of cases, such as retryable operations or cursor creating operations,
where a ``serverSession`` must remain acquired by the ``ClientSession`` after an operation is attempted.
Attempting to account for all these scenarios has risks that do not justify the potential guaranteed ``ServerSession`` allocation limiting.

Changelog
=========

:2017-09-13: If causalConsistency option is omitted assume true
:2017-09-16: Omit session ID when opening and authenticating a connection
:2017-09-18: Drivers MUST gossip the cluster time when they see a $clusterTime
:2017-09-19: How to safely use initialClusterTime
:2017-09-29: Add an exception to the rule that ``KILLCURSORS`` commands always require a session id
:2017-10-03: startSession and endSessions commands MUST be sent to the admin database
:2017-10-03: Fix format of endSessions command
:2017-10-04: Added advanceClusterTime
:2017-10-06: Added descriptions of explicit and implicit sessions
:2017-10-17: Implicit sessions MUST NOT be used when multiple users authenticated
:2017-10-19: Possible race conditions when checking whether a deployment supports sessions
:2017-11-21: Drivers MUST NOT send a session ID for unacknowledged writes
:2018-01-10: Note that MongoClient must retain highest clusterTime
:2018-01-10: Update test plan for drivers without APM
:2018-01-11: Clarify that sessions require replica sets or sharded clusters
:2018-02-20: Add implicit/explicit session tests
:2018-02-20: Drivers SHOULD error if unacknowledged writes are used with sessions
:2018-05-23: Drivers MUST not use session ID with parallelCollectionScan
:2018-06-07: Document that estimatedDocumentCount does not support explicit sessions
:2018-07-19: Justify why session must be an explicit parameter to each function
:2018-10-11: Session pools must be cleared in child process after fork
:2019-05-15: A ServerSession that is involved in a network error MUST be discarded
:2019-10-22: Drivers may defer checking if a deployment supports sessions until the first
:2021-04-08: Updated to use hello and legacy hello
:2021-04-08: Adding in behaviour for load balancer mode.
:2020-05-26: Simplify logic for determining sessions support
:2022-01-28: Implicit sessions MUST obtain server session after connection checkout succeeds
:2022-03-24: ServerSession Pooling is required and clarifies session acquisition bounding
:2022-06-13: Move prose tests to test README and apply new ordering
:2022-10-05: Remove spec front matter
:2023-02-24: Defer checking for session support until after connection checkout

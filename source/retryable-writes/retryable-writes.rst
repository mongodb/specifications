================
Retryable Writes
================

:Spec Title: Retryable Writes
:Spec Version: 1.0
:Author: Jeremy Mikola
:Lead: \A. Jesse Jiryu Davis
:Advisors: Robert Stam, Esha Maharishi, Samantha Ritter, and Kaloian Manassiev
:Status: Draft
:Type: Standards
:Minimum Server Version: 3.6
:Last Modified: 2017-07-25

.. contents::

--------

Abstract
========

MongoDB 3.6 will implement support for server sessions, which are shared
resources within a cluster identified by a session ID. Drivers compatible with
MongoDB 3.6 will also implement support for client sessions, which are always
associated with a server session and will allow for certain commands to be
executed within the context of a server session.

Additionally, MongoDB 3.6 will utilize server sessions to allow some write
commands to specify a transaction ID to enforce at-most-once semantics for the
write operation(s) and allow for retrying the operation if the driver fails to
obtain a command result (e.g. network error after a replica set failover). This
specification will outline how an API for retryable write operations will be
implemented in drivers. The specification will define an option to enable
retryable writes for an application and describe how a transaction ID will be
provided to write commands executed therein.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

Transaction ID
   The transaction ID identifies the transaction as part of which the command is
   running. In a write command where the client has requested retryable
   behavior, it is expressed by the top-level ``lsid`` and ``txnNum`` fields.
   The ``lsid`` component is the corresponding server session ID. which is a
   BSON value defined in the Driver Session specification. The ``txnNum``
   component is a monotonically increasing (per server session), positive 64-bit
   integer.

ClientSession
   Driver object representing a client session, which is defined in the Driver
   Session specification. This object is always associated with a server
   session; however, drivers will pool server sessions so that creating a
   ClientSession will not always entail creation of a new server session. The
   name of this object MAY vary across drivers.

Additional terms may be defined in the Driver Session specification.

Naming Deviations
-----------------

This specification defines the name for a new MongoClient option,
``retryWrites``. Drivers MUST use the defined name for the connection string
parameter to ensure portability of connection strings across applications and
drivers.

If drivers solicit MongoClient options through another mechanism (e.g. options
dictionary provided to the MongoClient constructor), drivers SHOULD use the
defined name but MAY deviate to comply with their existing conventions. For
example, a driver may use ``retry_writes`` instead of ``retryWrites``.

For other names in the spec (e.g. ``transactionId`` field for Command Monitoring
event objects), drivers SHOULD use the defined name but MAY deviate to comply
with their existing conventions.

MongoClient Configuration
-------------------------

This specification introduces the following client-level configuration option.

retryWrites
~~~~~~~~~~~

This boolean option determines whether retryable behavior will be applied to all
write operations executed within the MongoClient. This option MUST default to
false, which implies no change in write behavior.

This option MUST NOT be configurable at the level of a database object,
collection object, or at the level of an individual write operation.

Generating Transaction IDs
--------------------------

The server requires each retryable write operation to provide a unique
transaction ID in its command document. The transaction ID consists of a server
session ID and a monotonically increasing transaction number. The session ID is
obtained from the ClientSession object, which will have either been passed to
the write operation from the application or constructed internally for the
operation. Drivers will be responsible for maintaining a monotonically
increasing transaction number for each server session used by a ClientSession
object. Drivers MUST preserve the transaction number when reusing a server
session from the pool with a new ClientSession (this can be tracked as another
property on the driver’s object for the server session).

Drivers MUST ensure that each retryable write command specifies a transaction
number larger than any previously used transaction number for its session ID.

Since ClientSession objects are not thread safe and may only be used by one
thread at a time, drivers should not need to worry about race conditions when
incrementing the transaction number.

Behavioral Changes for Write Commands
-------------------------------------

Any helper method that takes a write concern parameter (see the `CRUD`_ and
`Read and Write Concern`_ specifications) MUST also accept an optional
ClientSession parameter. If a ClientSession parameter is specified by the
application, drivers MUST use it to generate the transaction ID for a retryable
write operation. Otherwise, drivers MUST internally construct a new
ClientSession for the sole purpose of generating a transaction ID. Any
internally constructed ClientSession SHOULD be destroyed as soon as the
operation is complete in its interactions with the server so that the
ClientSession may return its server session to the pool.

Drivers MUST automatically add a transaction ID to all write operations
executed within a MongoClient where retryable writes have been enabled. The
client MUST NOT check whether the specific write command supports retryability.
If the client provides a helper method for any of the "other commands that
write" specified in the Read and Write Concern specification, the method MUST
automatically add a transaction ID when executed within a MongoClient where
retryable writes have been enabled.

.. _CRUD: ../crud/crud.rst
.. _Read and Write Concern: ../read-write-concern/read-write-concern.rst

If your driver offers a generic command method on your database object, it MUST
NOT automatically add a transaction ID. The generic command method MUST NOT
check the user’s command document to determine if it is a write, nor check
whether the server is new enough to support a transaction ID for the command.
The method should simply send the user’s command document to the server as-is.

This specification does not affect write commands executed within a MongoClient
where retryable writes have not been enabled.

Constructing Write Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When constructing any write command that will be executed within a MongoClient
where retryable writes have been enabled, drivers MUST increment the transaction
number for the corresponding server session and include the server session ID
and transaction number in top-level ``lsid`` and ``txnNum`` fields,
respectively. ``lsid`` is a BSON value (discussed in the Driver Session
specification). ``txnNum`` MUST be an unsigned integer; the server will accept
32-bit (BSON type 0x10) or 64-bit (0x12) values.

The following example illustrates a possible write command for an
``updateOne()`` operation:

.. code:: typescript

  {
    update: "coll",
    lsid: { ... },
    txnNum: 100,
    updates: [
      { q: { x: 1 }, u: { $inc: { y: 1 } }, multi: false, upsert: false },
    ],
    ordered: true
  }

When constructing multiple write commands for a multi-statement write operation
(i.e. ``insertMany()`` and ``bulkWrite()``), drivers MUST increment the
transaction number for each command in the batch.

Retrying Write Commands
~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST NOT attempt to retry any write command that returns a response.

When a write command fails to return a response (e.g. network error), drivers
currently raise an error to the user. In the case of a multi-statement write
operation split across multiple write commands, such an error will also
interrupt execution of any additional write commands.

If a write command including a transaction ID fails to return a response on the
first attempt, the driver MUST update its topology according to the SDAM spec
(see: `Network error when reading or writing`_), reselect a writable server, and
execute the command again. Consider the following pseudo-code:

.. _Network error when reading or writing: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#network-error-when-reading-or-writing

.. code:: typescript

  function executeRetryableWrite(command) {
    server = selectServer("writable");

    if (server.getMaxWireVersion() < RETRYABLE_WIRE_VERSION) {
      throw new UnsupportedException();
    }

    try {
      return executeCommand(server, command);
    } catch (NetworkException e) {
      updateTopologyDescriptionForNetworkError(server, e);
    }

    server = selectServer("writable");

    // If the new server is too old, throw original network error
    if (server.getMaxWireVersion() < RETRYABLE_WIRE_VERSION) {
      throw e;
    }

    return executeCommand(server, command);
  }

When selecting a writable server for the first attempt of a retryable write
operation, drivers MUST raise a client-side error if the server’s maximum wire
version does not support retryable writes. If the server selected for a retry
attempt does not support retryable writes (e.g. mixed-version cluster), retrying
is not possible and drivers MUST raise the original network error to the user.

When retrying a write command, drivers MUST resend the command with the same
transaction ID. Drivers MAY resend the original wire protocol message (see:
`Can drivers resend the same wire protocol message on retry attempts?`_). If the
second attempt also fails, drivers MUST raise its corresponding error to the
user.

Supported Write Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

MongoDB 3.6 will support retryability for some, but not all, write operations.

Supported single-statement write operations include ``insertOne()``,
``updateOne()``, ``replaceOne()``, ``deleteOne()``, ``findOneAndDelete()``,
``findOneAndReplace()``, and ``findOneAndUpdate()``.

Supported multi-statement write operations include ``insertMany()`` and
``bulkWrite()`` where the ordered option is ``true`` and, in the case of
``bulkWrite()``, the requests parameter does not include ``UpdateMany`` or
``DeleteMany`` operations.

These methods above are defined in the `CRUD`_ specification.

Later versions of MongoDB may add support for additional write operations.

Unsupported Write Operations (client-side error)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When selecting a writable server for the first attempt of a retryable write
operation, drivers MUST raise a client-side error if the server’s maximum wire
version does not support retryable writes. It is still possible that a 3.6
server may not support retryable writes if the
``{setFeatureCompatibilityVersion: 3.6}`` admin command has not been run on the
cluster; however, that can only be reported as a server-side error (discussed
later).

Write commands specifying an unacknowledged write concern (i.e. ``{w: 0})`` are
not supported. Drivers MUST raise an error if an unacknowledged write concern
would be applied to any write command executed within a MongoClient where
retryable writes have been enabled.

Drivers MAY raise the error for an unacknowledged write concern eagerly instead
of waiting until a write operation is invoked. For example, drivers with an
immutable collection object, which also do not allow a write concern to be
specified on a per-operation basis, may prefer to raise an error at the time
the collection is instantiated with an unacknowledged write concern when
associated with a MongoClient where retryable writes have been enabled.

Unsupported Write Operations (server-side error)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write commands where a single statement might affect multiple documents will not
be initially supported by MongoDB 3.6, although this may change in the future.
This includes an `update`_ command where any statement in the updates sequence
specifies a ``multi`` option of ``true`` or a `delete`_ command where any
statement in the ``deletes`` sequence specifies a ``limit`` option of ``0``. In
the context of the `CRUD`_ specification, this includes the ``updateMany()`` and
``deleteMany()`` methods. Drivers MUST rely on the server to raise an error if a
multi-document write operations would be retried and is not supported.

.. _update: https://docs.mongodb.com/manual/reference/command/update/
.. _delete: https://docs.mongodb.com/manual/reference/command/delete/

Write commands containing multiple statements and unordered execution will not
be initially supported by MongoDB 3.6, although this may change in the future.
This includes an `insert`_, `update`_, or `delete`_ command where the
``ordered`` option is ``false``. In the context of the `CRUD`_ specification,
this includes the ``insertMany()`` and ``bulkWrite()`` methods. Drivers MUST
rely on the server to raise an error if a multi-statement write operation with
unordered execution would be retried and is not supported.

.. _insert: https://docs.mongodb.com/manual/reference/command/insert/

Write commands other than `insert`_, `update`_, `delete`_, or `findAndModify`_
will not be initially supported by MongoDB 3.6, although this may change in the
future. This includes, but is not limited to, an `aggregate`_ command using the
``$out`` pipeline operator. Drivers MUST rely on the server to raise an error if
a write command would be retried and is not supported.

.. _findAndModify: https://docs.mongodb.com/manual/reference/command/findAndModify/
.. _aggregate: https://docs.mongodb.com/manual/reference/command/aggregate/

Retryable write commands may not be supported at all in MongoDB 3.6 if the
``{setFeatureCompatibilityVersion: 3.6}`` admin command has not been run on the
cluster. Drivers cannot anticipate this scenario and MUST rely on the server to
raise an error if 3.6 feature compatibility is not enabled.

Logging Retry Attempts
======================

Drivers MAY choose to log retry attempts for write operations. This
specification does not define a format for such log messages.

Command Monitoring
==================

In accordance with the `Command Monitoring`_ specification, drivers MUST
guarantee that each ``CommandStartedEvent`` has either a correlating
``CommandSucceededEvent`` or ``CommandFailedEvent``. If the first attempt of a
retryable write operation fails to return a response, drivers MUST fire a
``CommandFailedEvent`` for the network error and fire a separate
``CommandStartedEvent`` when executing the subsequent retry attempt. Note that
the second ``CommandStartedEvent`` may have a different ``connectionId``, since
a writable server is reselected for the retry attempt.

.. _Command Monitoring: ../command-monitoring/command-monitoring.rst

The `Command Monitoring`_ specification states that the ``operationId`` field is
a driver-generated, 64-bit integer and may be “used to link events together such
as bulk write operations.” Drivers SHOULD NOT use this field to relay
information about a transaction ID. A bulk write operation may consist of
multiple write commands, each of which have a unique transaction ID.

Drivers MUST add an optional ``transactionId`` field to the
``CommandStartedEvent``, ``CommandSucceededEvent``, and
``CommandFailedEventdata`` data structures:

.. code:: typescript

  /**
   * Returns the transaction ID for the command. This is used to link
   * events together such as retryable write operations. OPTIONAL.
   *
   * If set, this should be a subset of the command document containing
   * only the lsid and txnNum fields.
   */
  transactionId: Document;

Drivers MUST set the ``transactionId`` field for write commands executed within
a MongoClient where retryable writes have been enabled.

Test Plan
=========

See the `README <tests/README.rst>`_ for tests.

At a high level, the following scenarios are covered by the test plan:

 * Test behavior for supported write operations.

   - Executing the same write operation (and transaction ID) multiple times
     should yield an identical write result.
   - Test at-most-once behavior by observing that subsequent executions of the
     same write operation do not incur further modifications to the collection
     data.
   - Exercise supported single-statement write operations (i.e. deleteOne,
     insertOne, replaceOne, updateOne, and findAndModify) executed within a
     client session where the ``retryWrites`` option is ``true``.
   - Exercise supported multi-statement insertMany and bulkWrite operations,
     which contain only supported single-statement write operations, executed
     within a client session where the ``retryable`` and ``ordered`` options are
     ``true``.

 * Test that unsupported API usage yields a client-side error

   - Unsupported write concerns: ``{w:0}`` (i.e fire-and-forget)

 * Test that unsupported write operations yield a server-side error

   - Unsupported write operations: updateMany and deleteMany
   - Unsupported write operations included within a bulkWrite

     + When ``ordered`` is ``true``, test that a sequence of supported write
       operations succeeds until an unsupported write operation is encountered
       and that the bulkWrite result indicates which writes succeeded and
       failed. Test cases where the bulkWrite consists of like operations
       executed in a single command (e.g. series of updateOne and updateMany) or
       as multiple commands (e.g. updateOne followed by deleteMany).

   - Unsupported execution order: insertMany or bulkWrite when ``ordered`` is
     ``false``
   - Unsupported write commands: aggregate with ``$out`` pipeline operator

If possible, drivers should test exceptional behavior for invalid transaction
IDs:

 * Transaction ID containing an invalid session ID (e.g. does not correlate with
   a valid server session)
 * Transaction ID containing an invalid transaction number (e.g. decremented
   from the previous transaction number)

Drivers may also be able to verify at-most-once semantics as described above by
testing their internal implementation (e.g. checking that transaction IDs are
added to outgoing commands).

Motivation for Change
=====================

Drivers currently have no API for specifying at-most-once semantics and
retryable behavior for write operations. The driver API needs to be extended to
support this behavior.

Design Rationale
================

The design of this specification piggy-backs that of the Driver Session
specification in that it modifies the driver API as little as possible to
introduce the concept of at-most-once semantics and retryable behavior for write
operations. A transaction ID will be included in all write commands executed
within the scope of a MongoClient where retryable writes have been enabled.

Drivers will rely on the server to yield an error if an unsupported write
operation would be retried and is not supported. This will free drivers from
having to maintain a list of supported write operations and also allow for
forward compatibility when future server versions begin to support retryable
behavior for additional write operations.

Backwards Compatibility
=======================

The API changes to support retryable writes extend the existing API but do not
introduce any backward breaking changes. Existing programs that do not make use
of retryable writes will continue to compile and run correctly.

Reference Implementation
========================

The C# and C drivers will provide reference implementations. JIRA links will be
added here at a later point.

Future Work
===========

Supporting at-most-once semantics and retryable behavior for updateMany and
deleteMany operations may become possible once the server implements support for
multi-document transactions.

A separate specification for retryable read operations could complement this
specification. Retrying read operations would not require client or server
sessions and could be implemented independently of retryable writes.

Q & A
=====

Why are write operations only retried once?
-------------------------------------------

The spec concerns itself with retrying write operations that fail to return a
response due to a network error, which may be classified as either a transient
error (e.g. dropped connection, replica set failover) or persistent outage. In
the case of a transient error, the driver will mark the server as “unknown” per
the `SDAM`_ spec. A subsequent retry attempt will allow the driver to rediscover
the primary within the designated server selection timeout period (30 seconds by
default). If server selection times out during this retry attempt, we can
reasonably assume that there is a persistent outage. In the case of a persistent
outage, multiple retry attempts are fruitless and would waste time. See
`How To Write Resilient MongoDB Applications`_ for additional discussion on this
strategy.

.. _SDAM: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst
.. _How To Write Resilient MongoDB Applications: https://emptysqua.re/blog/how-to-write-resilient-mongodb-applications/

What if the transaction number overflows?
-----------------------------------------

Since server sessions are pooled and session lifetimes are configurable on
the server, it is theoretically possible for the transaction number to overflow
if it reaches the limits of a signed 64-bit integer. The spec does not address
this scenario. Drivers may decide to handle this as they wish. For example, they
may raise a client-side error if a transaction number would overflow, eagerly
remove sessions with sufficiently high transactions numbers from the pool in an
attempt to limit such occurrences, or simply rely on the server to raise an
error when a transaction number is reused.

Why are unacknowledged write concerns unsupported?
--------------------------------------------------

The server does not consider the write concern when deciding if a write
operation supports retryable behavior. Technically, operations with an
unacknowledged write concern can specify a transaction ID and be retried.
However, the spec elects not to support unacknowledged write concerns due to
various ways that drivers may issue write operations with unacknowledged write
concerns.

When using ``OP_QUERY`` to issue a write command to the server, a command response
is always returned. A write command with an unacknowledged write concern (i.e.
``{w:0}``) will return a response of ``{ok:1}``. If a network error is
encountered attempting to read that response, the driver could attempt to retry
the operation by executing it again with the same transaction ID.

Some drivers fall back to legacy opcodes (e.g. ``OP_INSERT``) to execute write
operations with an unacknowledged write concern. In the future, ``OP_MSG`` may
allow the server to avoid returning any response for write operations sent with
an unacknowledged write concern. In both of these cases, there is no response
for which the driver might encounter a network error and decide to retry the
operation.

Rather than depend on an implementation detail to determine if retryable
behavior might apply, the spec has chosen to prohibit retryable behavior
outright for unacknowledged write concerns and guarantee a consistent user
experience across all drivers.

Why expose users to server-side errors for unsupported operations?
------------------------------------------------------------------

.. todo:: Determine how this should change. Do we end up using whitelists for
   supported operations (based on wire protocol verison) and avoid injecting
   transaction IDs on all write ops, or rely on the server to raise an error if
   unsupported ops would be retried? In both cases, it's possible for users to
   be unaware that some operations are not supported until some error in prod.
   Given the MongoClient-wide scope of retryWrites, we likely don't want to
   prohibit unsupported operations outright (either in the client API or by
   having the server raise an exception on the first attempt).

Several approaches that would shelter users from such errors were discussed.
Drivers could maintain a whitelist so that transaction IDs would only be added
to operations known to be supported by the server. Alternatively, the server
could change its behavior to ignore transaction IDs when an unsupported
operations is first attempted and only report an error if the operation was
retried (in this case, the unsupported error takes the place of what would
otherwise be a network error).

Ultimately, it was decided that immediate feedback should be a priority. Drivers
currently raise a client-side error if an update or delete specify a
``collation`` option that is not supported by the primary server rather than
have it be silently ignored. In the case of retryable writes, such errors
clearly inform the user that their code is not compatible with the current
server version. This forces the user to acknowledge exactly which operations are
supported during testing and avoids the chance of encountering an unexpected
"operation cannot be retried" error in production.

Lastly, the initial list of supported operations is already quite permissive.
Most `CRUD`_ operations are supported apart from ``updateMany()``,
``deleteMany()``, and ``aggregate()`` with ``$out``. Unordered bulk writes are
rare and other write operations (e.g. ``renameCollection``) are rarer still.

Why does the retryWrites MongoClient option default to false?
-------------------------------------------------------------

Retryable write operations are a first step towards the server supporting
transactions and multi-document writes. MongoDB 3.6 lacks support for retrying
some CRUD operations, such as ``updateMany()`` and
``deleteMany()``. Additionally, write commands other than ``insert``,
``update``, and ``delete`` are not supported at all.

Furthermore, we cannot know for sure what the server-side overhead will be for
executing write operations within sessions. As such, it would be prudent not to
introduce this feature by enabling it for all applications by default.

Can drivers resend the same wire protocol message on retry attempts?
--------------------------------------------------------------------

Since retry attempts entail sending the same command and transaction ID to the
server, drivers may opt to resend the same wire protocol message in order to
avoid constructing a new message and computing its checksum. The server will not
complain if it receives two messages with the same ``requestID``, as the field
is only used for logging and populating the ``responseTo`` field in its replies
to the client. That said, this approach may have implications for
`Command Monitoring`_, since the original write command and its retry attempt
may report the same requestID.

Changes
=======

2017-08-18: retryWrites is now a MongoClient option.

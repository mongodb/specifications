================
Retryable Writes
================

:Spec Title: Retryable Writes
:Spec Version: 1.0
:Author: Jeremy Mikola
:Lead: \A. Jesse Jiryu Davis
:Advisors: Robert Stam, Esha Maharishi, Samantha Ritter, and Kaloian Manassiev
:Status: Draft (awaiting reference implementation)
:Type: Standards
:Minimum Server Version: 3.6
:Last Modified: 2018-03-14

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
obtain a write result (e.g. network error or "not master" error after a replica
set failover). This specification will outline how an API for retryable write
operations will be implemented in drivers. The specification will define an
option to enable retryable writes for an application and describe how a
transaction ID will be provided to write commands executed therein.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

Transaction ID
   The transaction ID identifies the transaction as part of which the command is
   running. In a write command where the client has requested retryable
   behavior, it is expressed by the top-level ``lsid`` and ``txnNumber`` fields.
   The ``lsid`` component is the corresponding server session ID. which is a
   BSON value defined in the `Driver Session`_ specification. The ``txnNumber``
   component is a monotonically increasing (per server session), positive 64-bit
   integer.

   .. _Driver Session: ../sessions/driver-sessions.rst

ClientSession
   Driver object representing a client session, which is defined in the
   `Driver Session`_ specification. This object is always associated with a
   server session; however, drivers will pool server sessions so that creating a
   ClientSession will not always entail creation of a new server session. The
   name of this object MAY vary across drivers.

Retryable Error
   Any network exception or a write command response with an error indicating
   that the node is no longer a primary (e.g. "not master" or "node is
   recovering" errors). Such errors correspond to those discussed in the SDAM
   spec's section on `Error Handling`_.

   .. _Error Handling: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#error-handling

Additional terms may be defined in the `Driver Session`_ specification.

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

For any other names in the spec, drivers SHOULD use the defined name but MAY
deviate to comply with their existing conventions.

MongoClient Configuration
-------------------------

This specification introduces the following client-level configuration option.

retryWrites
~~~~~~~~~~~

This boolean option determines whether retryable behavior will be applied to all
supported write operations executed within the MongoClient. This option MUST
default to false, which implies no change in write behavior.

This option MUST NOT be configurable at the level of a database object,
collection object, or at the level of an individual write operation.

Requirements for Retryable Writes
---------------------------------

Supported Server Versions
~~~~~~~~~~~~~~~~~~~~~~~~~

Like sessions, retryable writes require a MongoDB 3.6 replica set or shard
cluster operating with feature compatibility version 3.6 (i.e. the
``{setFeatureCompatibilityVersion: 3.6}`` administrative command has been run on
the cluster). Drivers SHOULD verify server eligibility by ensuring that
``maxWireVersion`` is at least six, the ``logicalSessionTimeoutMinutes``
field is present in the server's ``isMaster`` response, and the server type is
not standalone.

If the server selected for the first attempt of a retryable write operation does
not support retryable writes, drivers MUST execute the write as if retryable
writes were not enabled. Drivers MUST NOT include a transaction ID in the write
command and MUST not retry the command under any circumstances.

In a sharded cluster, it is possible that mongos may appear to support retryable
writes but one or more shards in the cluster do not (e.g. replica set shard is
configured with feature compatibility version 3.4, a standalone is added as a
new shard). In these rare cases, a write command that fans out to a shard that
does not support retryable writes may partially fail and an error may be
reported in the write result from mongos (e.g. ``writeErrors`` array in the bulk
write result). This does not constitute a retryable error. Drivers MUST relay
such errors to the user.

Supported Write Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

MongoDB 3.6 will support retryability for some, but not all, write operations.

Supported single-statement write operations include ``insertOne()``,
``updateOne()``, ``replaceOne()``, ``deleteOne()``, ``findOneAndDelete()``,
``findOneAndReplace()``, and ``findOneAndUpdate()``.

Supported multi-statement write operations include ``insertMany()`` and
``bulkWrite()``. The ordered option may be ``true`` or ``false``. In the case of
``bulkWrite()``, the requests parameter may not include ``UpdateMany`` or
``DeleteMany`` operations.

These methods above are defined in the `CRUD`_ specification.

Later versions of MongoDB may add support for additional write operations.

Drivers MUST document operations that support retryable behavior and the
conditions for which retryability is determined (see:
`How will users know which operations are supported?`_). Drivers are not
required to exhaustively document all operations that do not support retryable
behavior.

Unsupported Write Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write commands specifying an unacknowledged write concern (e.g. ``{w: 0})``) do
not support retryable behavior. Drivers MUST NOT add a transaction ID to any
write command with an unacknowledged write concern executed within a MongoClient
where retryable writes have been enabled. Drivers MUST NOT retry these commands.

Write commands where a single statement might affect multiple documents will not
be initially supported by MongoDB 3.6, although this may change in the future.
This includes an `update`_ command where any statement in the updates sequence
specifies a ``multi`` option of ``true`` or a `delete`_ command where any
statement in the ``deletes`` sequence specifies a ``limit`` option of ``0``. In
the context of the `CRUD`_ specification, this includes the ``updateMany()`` and
``deleteMany()`` methods as well as ``bulkWrite()`` where the requests parameter
includes an ``UpdateMany`` or ``DeleteMany`` operation. Drivers MUST NOT add a
transaction ID to any single- or multi-statement write commands that include one
or more multi-document write operations. Drivers MUST NOT retry these commands
if they fail to return a response.

.. _update: https://docs.mongodb.com/manual/reference/command/update/
.. _delete: https://docs.mongodb.com/manual/reference/command/delete/

Write commands other than `insert`_, `update`_, `delete`_, or `findAndModify`_
will not be initially supported by MongoDB 3.6, although this may change in the
future. This includes, but is not limited to, an `aggregate`_ command using the
``$out`` pipeline operator. Drivers MUST NOT add a transaction ID to these
commands and MUST NOT retry these commands if they fail to return a response.

.. _insert: https://docs.mongodb.com/manual/reference/command/insert/
.. _findAndModify: https://docs.mongodb.com/manual/reference/command/findAndModify/
.. _aggregate: https://docs.mongodb.com/manual/reference/command/aggregate/

Implementing Retryable Writes
-----------------------------

Generating Transaction IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~

The server requires each retryable write operation to provide a unique
transaction ID in its command document. The transaction ID consists of a server
session ID and a monotonically increasing transaction number. The session ID is
obtained from the ClientSession object, which will have either been passed to
the write operation from the application or constructed internally for the
operation. Drivers will be responsible for maintaining a monotonically
increasing transaction number for each server session used by a ClientSession
object. Drivers that pool server sessions MUST preserve the transaction number
when reusing a server session from the pool with a new ClientSession (this can
be tracked as another property on the driver's object for the server session).

Drivers MUST ensure that each retryable write command specifies a transaction
number larger than any previously used transaction number for its session ID.

Since ClientSession objects are not thread safe and may only be used by one
thread at a time, drivers should not need to worry about race conditions when
incrementing the transaction number.

Behavioral Changes for Write Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST automatically add a transaction ID to all supported write commands
executed via a specific `CRUD`_ method (e.g. ``updateOne()``) or write command
method (e.g. ``executeWriteCommand()``) within a MongoClient where retryable
writes have been enabled and when the selected server supports retryable writes.

.. _CRUD: ../crud/crud.rst

If your driver offers a generic command method on your database object (e.g.
``runCommand()``), it MUST NOT check the user's command document to determine if
it is a supported write operation and MUST NOT automatically add a transaction
ID. The method should send the user's command document to the server as-is.

This specification does not affect write commands executed within a MongoClient
where retryable writes have not been enabled.

Constructing Write Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When constructing a supported write command that will be executed within a
MongoClient where retryable writes have been enabled, drivers MUST increment the
transaction number for the corresponding server session and include the server
session ID and transaction number in top-level ``lsid`` and ``txnNumber``
fields, respectively. ``lsid`` is a BSON value (discussed in the
`Driver Session`_ specification). ``txnNumber`` MUST be a positive 64-bit
integer (BSON type 0x12).

The following example illustrates a possible write command for an
``updateOne()`` operation:

.. code:: typescript

  {
    update: "coll",
    lsid: { ... },
    txnNumber: 100,
    updates: [
      { q: { x: 1 }, u: { $inc: { y: 1 } }, multi: false, upsert: false },
    ],
    ordered: true
  }

When constructing multiple write commands for a multi-statement write operation
(i.e. ``insertMany()`` and ``bulkWrite()``), drivers MUST increment the
transaction number for each supported write command in the batch.

Executing Retryable Write Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When selecting a writable server for the first attempt of a retryable write
command, drivers MUST allow a server selection error to propagate. In this case,
the caller is able to infer that no attempt was made.

If retryable writes is not enabled or the selected server does not support
retryable writes, drivers MUST NOT include a transaction ID in the command and
MUST attempt to execute the write command exactly once and allow any errors to
propagate. In this case, the caller is able to infer that an attempt was made.

If retryable writes are enabled and the selected server supports retryable
writes, drivers MUST add a transaction ID to the command. Drivers MUST only
attempt to retry a write command if the first attempt yields a retryable error.
Drivers MUST NOT attempt to retry a write command on any other error.

If the first attempt of a write command including a transaction ID encounters a
retryable error, the driver MUST update its topology according to the SDAM spec
(see: `Error Handling`_) and capture this original retryable error. Drivers
should then proceed with selecting a writable server for the retry attempt.

.. _Error Handling: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#error-handling

If the driver cannot select a server for the retry attempt or the selected
server does not support retryable writes, retrying is not possible and drivers
MUST raise the original retryable error. In both cases, the caller is able to
infer that an attempt was made.

If the retry attempt also fails, drivers MUST update their topology according to
the SDAM spec (see: `Error Handling`_). If an error would not allow the caller
to infer that an attempt was made (e.g. connection pool exception originating
from the driver), the original error should be raised. If the retry failed due
to another retryable error or some other error originating from the server, that
error should be raised instead as the caller can infer that an attempt was made
and the second error is likely more relevant (with respect to the current
topology state).

Drivers MUST NOT attempt to retry a write command with the same transaction ID
more than once.

Consider the following pseudo-code:

.. code:: typescript

  /**
   * Checks if a server supports retryable writes.
   */
  function isRetryableWritesSupported(server) {
    if (server.getMaxWireVersion() < RETRYABLE_WIRE_VERSION) {
      return false;
    }

    if ( ! server.hasLogicalSessionTimeoutMinutes()) {
      return false;
    }

    if (server.isStandalone()) {
      return false;
    }

    return true;
  }

  /**
   * Executes a write command in the context of a MongoClient where retryable
   * writes have been enabled. The session parameter may be an implicit or
   * explicit client session (depending on how the CRUD method was invoked).
   */
  function executeRetryableWrite(command, session) {
    /* Allow ServerSelectionException to propagate to our caller, which can then
     * assume that no attempts were made. */
    server = selectServer("writable");

    /* If the server does not support retryable writes, execute the write as if
     * retryable writes are not enabled. */
    if ( ! isRetryableWritesSupported()) {
      return executeCommand(server, command);
    }

    /* Incorporate lsid and txnNumber fields into the command document. These
     * values will be derived from the implicit or explicit session object. */
    retryableCommand = addTransactionIdToCommand(command, session);

    /* NetworkException and NotMasterException are both retryable errors. If
     * caught, remember the exception, update SDAM accordingly, and proceed with
     * retrying the operation. */
    try {
      return executeCommand(server, retryableCommand);
    } catch (NetworkException originalError) {
      updateTopologyDescriptionForNetworkError(server, originalError);
    } catch (NotMasterException originalError) {
      updateTopologyDescriptionForNotMasterError(server, originalError);
    }

    /* If we cannot select a writable server, do not proceed with retrying and
     * throw the original error. The caller can then infer that an attempt was
     * made and failed. */
    try {
      server = selectServer("writable");
    } catch (Exception ignoredError) {
      throw originalError;
    }

    /* If the server selected for retrying is too old, throw the original error.
     * The caller can then infer that an attempt was made and failed. This case
     * is very rare, and likely means that the cluster is in the midst of a
     * downgrade. */
    if ( ! isRetryableWritesSupported()) {
      throw originalError;
    }

    /* Allow any retryable error from the second attempt to propagate to our
     * caller, as it will be just as relevant (if not more relevant) than the
     * original error. For exceptions that originate from the driver (e.g. no
     * socket available from the connection pool), we should raise the original
     * error. Other exceptions originating from the server should be allowed to
     * propagate. */
    try {
      return executeCommand(server, retryableCommand);
    } catch (NetworkException secondError) {
      updateTopologyDescriptionForNetworkError(server, secondError);
      throw secondError;
    } catch (NotMasterException secondError) {
      updateTopologyDescriptionForNotMasterError(server, secondError);
      throw secondError;
    } catch (DriverException ignoredError) {
      throw originalError;
    }
  }

When retrying a write command, drivers MUST resend the command with the same
transaction ID. Drivers MAY resend the original wire protocol message (see:
`Can drivers resend the same wire protocol message on retry attempts?`_).

In the case of a multi-statement write operation split across multiple write
commands, a failed retry attempt will also interrupt execution of any additional
write operations in the batch (regardless of the ordered option). This is no
different than if a retryable error had been encountered without retryable
behavior enabled or supported by the driver. Drivers are encouraged to provide
access to an intermediary write result (e.g. BulkWriteResult, InsertManyResult)
through the BulkWriteException, in accordance with the `CRUD`_ specification.

Logging Retry Attempts
======================

Drivers MAY choose to log retry attempts for write operations. This
specification does not define a format for such log messages.

Command Monitoring
==================

In accordance with the `Command Monitoring`_ specification, drivers MUST
guarantee that each ``CommandStartedEvent`` has either a correlating
``CommandSucceededEvent`` or ``CommandFailedEvent``. If the first attempt of a
retryable write operation encounters a retryable error, drivers MUST fire a
``CommandFailedEvent`` for the retryable error and fire a separate
``CommandStartedEvent`` when executing the subsequent retry attempt. Note that
the second ``CommandStartedEvent`` may have a different ``connectionId``, since
a writable server is reselected for the retry attempt.

.. _Command Monitoring: ../command-monitoring/command-monitoring.rst

Each attempt of a retryable write operation SHOULD report a different
``requestId`` so that events for each attempt can be properly correlated with
one another.

The `Command Monitoring`_ specification states that the ``operationId`` field is
a driver-generated, 64-bit integer and may be "used to link events together such
as bulk write operations." Each attempt of a retryable write operation SHOULD
report the same ``operationId``; however, drivers SHOULD NOT use the
``operationId`` field to relay information about a transaction ID. A bulk write
operation may consist of multiple write commands, each of which may specify a
unique transaction ID.

Test Plan
=========

See the `README <tests/README.rst>`_ for tests.

At a high level, the test plan will cover the following scenarios for executing
supported write operations within a MongoClient where retryable writes have been
enabled:

* Executing the same write operation (and transaction ID) multiple times should
  yield an identical write result.
* Test at-most-once behavior by observing that subsequent executions of the same
  write operation do not incur further modifications to the collection data.
* Exercise supported single-statement write operations (i.e. deleteOne,
  insertOne, replaceOne, updateOne, and findAndModify).
* Exercise supported multi-statement insertMany and bulkWrite operations, which
  contain only supported single-statement write operations. Both ordered and
  unordered execution should be tested.

If possible, drivers should test that transaction IDs are never included in
commands for unsupported write operations:

* Write commands with unacknowledged write concerns (e.g. ``{w: 0}``)

* Unsupported single-statement write operations

  - ``updateMany()``
  - ``deleteMany()``

* Unsupported multi-statement write operations

  - ``bulkWrite()`` that includes ``UpdateMany`` or ``DeleteMany``

* Unsupported write commands

  - ``aggregate`` with ``$out`` pipeline operator

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

The design of this specification piggy-backs that of the `Driver Session`_
specification in that it modifies the driver API as little as possible to
introduce the concept of at-most-once semantics and retryable behavior for write
operations. A transaction ID will be included in all supported write commands
executed within the scope of a MongoClient where retryable writes have been
enabled.

Drivers expect the server to yield an error if a transaction ID is included in
an unsupported write command. This requires drivers to maintain a whitelist and
track which write operations support retryable behavior for a given server
version (see: `Why must drivers maintain a whitelist of supported
operations?`_).

While this approach will allow applications to take advantage of retryable write
behavior with minimal code changes, it also presents a documentation challenge.
Users must understand exactly what can and will be retried (see: `How will users
know which operations are supported?`_).

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

The spec concerns itself with retrying write operations that encounter a
retryable error (i.e. no response due to network error or a response indicating
that the node is no longer a primary). A retryable error may be classified as
either a transient error (e.g. dropped connection, replica set failover) or
persistent outage. In the case of a transient error, the driver will mark the
server as "unknown" per the `SDAM`_ spec. A subsequent retry attempt will allow
the driver to rediscover the primary within the designated server selection
timeout period (30 seconds by default). If server selection times out during
this retry attempt, we can reasonably assume that there is a persistent outage.
In the case of a persistent outage, multiple retry attempts are fruitless and
would waste time. See `How To Write Resilient MongoDB Applications`_ for
additional discussion on this strategy.

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

When using ``OP_QUERY`` to issue a write command to the server, a command
response is always returned. A write command with an unacknowledged write
concern (i.e. ``{w: 0}``) will return a response of ``{ok: 1}``. If a retryable
error is encountered (either a network error or "not master" response), the
driver could attempt to retry the operation by executing it again with the same
transaction ID.

Some drivers fall back to legacy opcodes (e.g. ``OP_INSERT``) to execute write
operations with an unacknowledged write concern. In the future, ``OP_MSG`` may
allow the server to avoid returning any response for write operations sent with
an unacknowledged write concern. In both of these cases, there is no response
for which the driver might encounter a retryable error and decide to retry the
operation.

Rather than depend on an implementation detail to determine if retryable
behavior might apply, the spec has chosen to not support retryable behavior
for unacknowledged write concerns and guarantee a consistent user experience
across all drivers.

Why must drivers maintain a whitelist of supported operations?
--------------------------------------------------------------

Requiring that drivers maintain a whitelist of supported write operations is
unfortunate. It both adds complexity to the driver's implementation and limits
the driver's ability to immediately take advantage of new server functionality
(i.e. the driver must be upgraded to support additional write operations).

Several other alternatives were discussed:

* The server could inform drivers which write operations support retryable
  behavior in its ``isMaster`` response. This would be a form of feature
  discovery, for which there is no established protocol. It would also add
  complexity to the connection handshake.
* The server could ignore a transaction ID on the first observed attempt of an
  unsupported write command and only yield an error on subsequent attempts. This
  would require the server to create a transaction record for unsupported writes
  to avoid the risk of applying a write twice and ensuring that retry attempts
  could be differentiated. It also poses a significant problem for sharding if a
  multi-document write does not reach all shards, since those shards would not
  know to create a transaction record.
* The driver could allow more fine-grained control retryable write behavior by
  supporting a ``retryWrites`` option on the database and collection objects.
  This would allow users to enable ``retryWrites`` on a MongoClient and disable
  it as needed to execute unsupported write operations, or vice versa. Since we
  expect the ``retryWrites`` option to become less relevant once transactions
  are implemented, we would prefer not to add the option throughout the driver
  API.

How will users know which operations are supported?
---------------------------------------------------

The initial list of supported operations is already quite permissive. Most
`CRUD`_ operations are supported apart from ``updateMany()``, ``deleteMany()``,
and ``aggregate()`` with ``$out``. Other write operations
(e.g. ``renameCollection``) are rare.

That said, drivers will need to clearly document exactly which operations
support retryable behavior. In the case ``bulkWrite()``, which may or may not
support retryability, drivers should discuss how elegibility is determined.

Why does the retryWrites MongoClient option default to false?
-------------------------------------------------------------

Retryable write operations are a first step towards the server supporting
transactions and multi-document writes. MongoDB 3.6 lacks support for retrying
some `CRUD`_ operations, such as ``updateMany()`` and ``deleteMany()``.
Additionally, write commands other than ``insert``, ``update``, ``delete``, and
``findAndModify`` are not supported at all.

Enabling retryability for write operations does incur some server-side overhead.
As such, it would be prudent not to enable this feature for all applications by
default and instead have applications opt in to the behavior. We may change this
default in the future if testing reveals the overhead to be sufficiently small.

Can drivers resend the same wire protocol message on retry attempts?
--------------------------------------------------------------------

Since retry attempts entail sending the same command and transaction ID to the
server, drivers may opt to resend the same wire protocol message in order to
avoid constructing a new message and computing its checksum. The server will not
complain if it receives two messages with the same ``requestId``, as the field
is only used for logging and populating the ``responseTo`` field in its replies
to the client. That said, this approach may have implications for
`Command Monitoring`_, since the original write command and its retry attempt
may report the same ``requestId``.

Changes
=======

2018-03-14: Clarify that retryable writes may fail with a FCV 3.4 shard.

2017-11-02: Drivers should not raise errors if selected server does not support
retryable writes and instead fall back to non-retryable behavior. In addition to
wire protocol version, drivers may check for ``logicalSessionTimeoutMinutes`` to
determine if a server supports sessions and retryable writes.

2017-10-26: Errors when retrying may be raised instead of the original error
provided they allow the user to infer that an attempt was made.

2017-10-23: Drivers must document operations that support retryability.

2017-10-23: Raise the original retryable error if server selection or wire
protocol checks fail during the retry attempt. Encourage drivers to provide
intermediary write results after an unrecoverable failure during a bulk write.

2017-10-18: Standalone servers do not support retryable writes.

2017-10-18: Also retry writes after a "not master" error.

2017-10-08: Renamed ``txnNum`` to ``txnNumber`` and noted that it must be a
64-bit integer (BSON type 0x12).

2017-08-25: Drivers will maintain a whitelist so that only supported write
operations may be retried. Transaction IDs will not be included in unsupported
write commands, irrespective of the ``retryWrites`` option.

2017-08-18: ``retryWrites`` is now a MongoClient option.

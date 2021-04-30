==============================
Client Side Operations Timeout
==============================

:Title: Client Side Operations Timeout
:Author: Divjot Arora
:Spec Lead: Jeff Yemin
:Approvers: Jeff Yemin, Clyde Bazile
:Advisory Group: Bernie Hackett, Jason Carey, Will Shulman
:Status: Accepted
:Type: Standards
:Minimum Server Version: 2.6
:Last Modified: November 24, 2020
:Version: 1.0.0

.. contents::

--------

Abstract
========

This specification outlines a new ``timeoutMS`` option to govern the amount
of time that a single operation can execute before control is returned to the
user. This timeout applies to all of the work done to execute the operation,
including but not limited to server selection, connection checkout, and
server-side execution.

META 
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”,
“SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this
document are to be interpreted as described in \`RFC 2119
<https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

min(a, b)
  Shorthand for "the minimum of a and b" where ``a`` and ``b`` are numeric
  values. For any cases where 0 means "infinite" (e.g. `timeoutMS`_),
  ``min(0, other)`` MUST evaluate to ``other``.

MongoClient Configuration
-------------------------

This specification introduces a new configuration option and deprecates some
existing options.

timeoutMS
~~~~~~~~~

This 64-bit integer option specifies the per-operation timeout value in
milliseconds. The default value is unset. Both unset and an explicit value of
0 mean infinite, though some client-side timeouts like
``serverSelectionTimeoutMS`` will still apply. Drivers MUST error if a
negative value is specified. This value MUST be configurable at the level of
a MongoClient, MongoDatabase, MongoCollection, or of a single operation.
However, if the option is specified at any level, it cannot be later changed
to unset. At each level, the value MUST be inherited from the previous level
if it is not explicitly specified. Additionally, some entities like
``ClientSession`` and ``GridFSBucket`` either inherit ``timeoutMS`` from
their parent entities or provide options to override it. The behavior for
these entities is described in individual sections of this specification.

Drivers for languages that provide an idiomatic API for expressing durations
of time (e.g. ``TimeSpan`` in .NET) MAY choose to leverage these APIs for the
``timeoutMS`` option rather than using int64. Drivers that choose to do so
MUST also follow the semantics for special values defined by those types.
Such drivers MUST also ensure that there is a way to explicitly set
``timeoutMS`` to ``infinite`` in the API.

See `timeoutMS cannot be changed to unset once it’s specified`_.

Backwards Breaking Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This specification deprecates many existing timeout options and introduces a
new exception type that is used to communicate timeout expiration. If drivers
need to make backwards-breaking changes to support ``timeoutMS``, the
backwards breaking behavior MUST be gated behind the presence of the
``timeoutMS`` option. If the ``timeoutMS`` option is not set, drivers MUST
continue to honor existing timeouts such as ``socketTimeoutMS``. Backwards
breaking changes include any changes to exception types thrown by stable API
methods or changes to timeout behavior. Drivers MUST document these changes.

In a subsequent major release, drivers SHOULD drop support for legacy timeout
behavior and only continue to support the timeout options that are not
deprecated by this specification. Once legacy options are removed, drivers
MUST make the backwards-breaking behavioral changes described in this
specification regardless of whether or not ``timeoutMS`` is set by the
application.

See the `Errors`_ section for explanations of the backwards-breaking changes
to error reporting.

Deprecations
~~~~~~~~~~~~

The following configuration timeout options MUST be deprecated in favor of
``timeoutMS``:

- ``socketTimeoutMS``

- ``waitQueueTimeoutMS``

- ``wTimeoutMS``

The following options for CRUD methods MUST be deprecated in favor of
``timeoutMS``:

- ``maxTimeMS``

- ``maxCommitTimeMS``

Timeout Behavior
----------------

The ``timeoutMS`` option specifies the best-effort maximum amount of time a
single operation can take before control is returned to the application.
Drivers MUST keep track of the remaining time before the timeout expires as
an operation progresses.

Operations
~~~~~~~~~~

The ``timeoutMS`` option applies to all operations defined in the following
specifications:

- `CRUD <./../crud/crud.rst>`__
- `Change Streams <../change-streams/change-streams.rst>`__
- `Client Side Encryption <../client-side-encryption/client-side-encryption.rst>`__
- `Enumerating Collections <../enumerate-collections.rst>`__
- `Enumerating Databases <../enumerate-databases.rst>`__
- `GridFS <../gridfs/gridfs-spec.rst>`__
- `Index Management <../index-management.rst>`__
- `Transactions <../transactions/transactions.rst>`__
- `Convenient API for Transactions <../transactions-convenient-api/transactions-convenient-api.rst>`__

In addition, it applies to all operations on cursor objects that may perform
blocking work (e.g. methods to iterate or close a cursor, any method that
reads documents from a cursor into an array, etc).

Validation and Overrides
~~~~~~~~~~~~~~~~~~~~~~~~

When executing an operation, drivers MUST ignore any deprecated timeout
options if ``timeoutMS`` is set on the operation or is inherited from the
collection/database/client levels. In addition to being set at these levels,
the timeout for an operation can also be expressed via an explicit
ClientSession (see `Convenient Transactions API`_). In this case, the timeout
on the session MUST be used as the ``timeoutMS`` value for the operation.
Drivers MUST raise a validation error if an explicit session with a timeout
is used and the ``timeoutMS`` option is set at the operation level for
operations executed as part of a ``withTransaction`` callback.

See `timeoutMS overrides deprecated timeout options`_.

Errors
~~~~~~

If the ``timeoutMS`` option is not set and support for deprecated timeout
options has not been dropped but a timeout is encountered (e.g. server
selection times out), drivers MUST continue to return existing errors. This
ensures that error-handling code in existing applications does not break
unless the user opts into using ``timeoutMS``.

If the ``timeoutMS`` option is set and the timeout expires, drivers MUST
abort all blocking work and return control to the user with an error. This
error MUST be distinguished in some way (e.g. custom exception type) to make
it easier for users to detect when an operation fails due to a timeout. If
the timeout expires during a blocking task, drivers MUST expose the
underlying error returned from the task from this new error type. The
stringified version of the new error type MUST include the stringified
version of the underlying error as a substring. For example, if server
selection expires and returns a ``ServerSelectionTimeoutException``, drivers
must allow users to access that exception from this new error type. If there
is no underlying error, drivers MUST add information about when the timeout
expiration was detected to the stringified version of the timeout error.

Error Transformations
`````````````````````

When using the new timeout error type, drivers MUST transform timeout errors
from external sources into the new error. One such error is the
``MaxTimeMSExpired`` server error. When checking for this error, drivers MUST
only check that the error code is 50 and MUST NOT check the code name or
error message. This error can be present in a top-level response document
where the ``ok`` value is 0, as part of an error in the ``writeErrors``
array, or in a nested ``writeConcernError`` document. For example, all three
of the following server responses would match this criteria:

.. code:: javascript

   {ok: 0, code: 50, codeName: "MaxTimeMSExpired", errmsg: "operation time limit exceeded"}

   {ok: 1, writeErrors: [{code: 50, codeName: "MaxTimeMSExpired", errmsg: "operation time limit exceeded"}]}

   {ok: 1, writeConcernError: {code: 50, codeName: "MaxTimeMSExpired"}}

Timeouts from other sources besides MongoDB servers MUST also be transformed
into this new exception type. These include socket read/write timeouts and
HTTP request timeouts.

Blocking Sections for Operation Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following pieces of operation execution are considered blocking:

#. Implicit session acquisition if an explicit session was not provided for the
   operation. This is only considered blocking for drivers that perform server
   selection to determine session support when acquiring implicit sessions.
#. Server selection
#. Connection checkout - If ``maxPoolSize`` has already been reached for the
   selected server, this is the amount of time spent waiting for a connection to
   be available.
#. Connection establishment - If the pool for the selected server is
   empty and a new connection is needed, the following pieces of connection
   establishment are considered blocking:

   #. TCP socket establishment

   #. TLS handshake

      #.  All messages sent over the socket as part of the TLS handshake

      #. OCSP verification - HTTP requests sent to OCSP responders.
      
   #. MongoDB handshake (i.e. initial connection ``isMaster``)

   #. Authentication

      #. SCRAM-SHA-1, SCRAM-SHA-256, PLAIN: Execution of the command required
         for the SASL conversation.

      #. GSSAPI: Execution of the commands required for the SASL conversation
         and requests to the KDC and TGS.

      #. MONGODB-AWS: Execution of the commands required for the SASL
         conversation and all HTTP requests to ECS and EC2 endpoints.

      #. MONGODB-X509: Execution of the commands required for the
         authentication conversation.

#. Client-side encryption

   #. Execution of ``listCollections`` commands to get collection schemas.

   #. Execution of ``find`` commands against the key vault collection to get
      encrypted data keys.

   #. Requests to non-local key management servers (e.g. AWS KMS) to decrypt
      data keys.

   #. Requests to mongocryptd servers.

#. Socket write to send a command to the server

#. Socket read to receive the server’s response

The ``timeoutMS`` option MUST apply to all blocking sections. Drivers MUST
document any exceptions. For example, drivers that do not have full control
over OCSP verification might not be able to set timeouts for HTTP requests to
responders and would document that OCSP verification could result in an
execution time greater than ``timeoutMS``.

Server Selection
~~~~~~~~~~~~~~~~

If ``timeoutMS`` is set, drivers MUST use ``min(serverSelectionTimeoutMS,
remaining timeoutMS)``, referred to as ``computedServerSelectionTimeout`` as
the timeout for server selection and connection checkout. The server selection
loop MUST fail with a timeout error once the timeout expires.

After a server has been selected, drivers MUST use the remaining
``computedServerSelectionTimeout`` value as the timeout for connection
checkout. If a new connection is required, ``min(connectTimeoutMS, remaining
computedServerSelectionTimeout)`` MUST be used as the timeout for TCP socket
establishment. Any network requests required to create or authenticate a
connection (e.g. HTTP requests to OCSP responders) MUST use
``min(operationTimeout, remaining computedServerSelectionTimeout)`` as a
timeout, where ``operationTimeout`` is the specified default timeout for the
network request. If there is no specified default, these operations MUST use
the remaining ``computedServerSelectionTimeout`` value. All commands sent
during the connection’s handshake MUST use the remaining
``computedServerSelectionTimeout`` as their ``timeoutMS`` value. Handshake
commands MUST also set timeouts per the `Command Execution`_ section.

If ``timeoutMS`` is not set and support for ``waitQueueTimeoutMS`` has not
been removed, drivers MUST continue to exhibit the existing timeout behavior
by honoring ``serverSelectionTimeoutMS`` for server selection and
``waitQueueTimeoutMS`` for connection checkout. If a new connection is
required, drivers MUST use ``connectTimeoutMS`` as the timeout for socket
establishment and ``socketTimeoutMS`` as the socket timeout for all handshake
commands.

See `serverSelectionTimeoutMS is not deprecated`_ and `connectTimeoutMS is
not deprecated`_.

Command Execution
~~~~~~~~~~~~~~~~~

If ``timeoutMS`` is set, drivers MUST append a ``maxTimeMS`` field to
commands executed against a MongoDB server using the 90th percentile RTT of
the selected server. Note that this value MUST be retrieved during server
selection using the ``servers`` field of the same `TopologyDescription
<../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#TopologyDescription>`__
that was used for selection before the selected server's description can be
modified. Otherwise, drivers may be subject to a race condition where a
server is reset to the default description (e.g. due to an error in the
monitoring thread) after it has been selected but before the RTT is
retrieved.

If the 90th percentile RTT of the selected server is less than the remaining
timeoutMS, the value of this field MUST be ``remaining timeoutMS - 90th
percentile RTT``. If not, drivers MUST return a timeout error without
attempting to send the message to the server. This is done to ensure that an
operation is not routed to the server if it will likely fail with a socket
timeout as that could cause connection churn. The ``maxTimeMS`` field MUST be
appended after all blocking work is complete.

After wire message construction, drivers MUST check for timeout before
writing the message to the server. If the timeout has expired or the amount
of time remaining is less than the selected server's 90th percentile RTT,
drivers MUST return the connection to the pool and raise a timeout exception.
Otherwise, drivers MUST set the connection’s write timeout to the remaining
``timeoutMS`` value before writing a message to the server. After the write
is complete, drivers MUST check for timeout expiration before reading the
server’s response. If the timeout has expired, the connection MUST be closed
and a timeout exception MUST be propagated to the application. If it has not,
drivers MUST set the connection’s read timeout to the remaining ``timeoutMS``
value. The timeout MUST apply to the aggregate of all reads done to receive a
server response, not to individual reads. If any read or write calls on the
socket fail with a timeout, drivers MUST transform the error into the new
timeout exception as described in the `Error Transformations`_ section.

If ``timeoutMS`` is not set and support for ``socketTimeoutMS`` has not been
removed, drivers MUST honor ``socketTimeoutMS`` as the timeout for socket
reads and writes.

See `maxTimeMS accounts for server RTT`_.

Batching
~~~~~~~~

If an operation must be sent to the server in multiple batches (e.g.
``collection.bulkWrite()``), the ``timeoutMS`` option MUST apply to the
entire operation, not to each individual batch.

Retryability
~~~~~~~~~~~~

If an operation requires a retry per the retryable reads or writes
specifications and ``timeoutMS`` is set to a non-zero value, drivers MUST
retry operations as many times as possible before the timeout expires or a
retry attempt returns a non-retryable error. Once the timeout expires, a
timeout error MUST be raised.

See `Why don’t drivers use backoff/jitter between retry attempts?`_.

Client Side Encryption
~~~~~~~~~~~~~~~~~~~~~~

If automatic client-side encryption or decryption is enabled, the remaining
``timeoutMS`` value MUST be used as the ``timeoutMS`` when executing
``listCollections`` commands to retrieve collection schemas, ``find``
commands to get data from the key vault, and any commands against
mongocryptd. It MUST also be used as the request timeout for HTTP requests
against KMS servers to decrypt data keys. When sending a command to
mongocryptd, drivers MUST NOT append a ``maxTimeMS`` field. This is to ensure
that a ``maxTimeMS`` field can be safely appended to the command after it has
been marked by mongocryptd and encrypted by libmongocrypt. To determine
whether or not the server is a mongocryptd, drivers MUST check that the
``iscryptd`` field in the server's description is ``true``.

For explicit encryption and decryption, the ``ClientEncryptionOpts`` options
type used to construct `ClientEncryption
<../client-side-encryption/client-side-encryption.rst#clientencryption>`_
instances MUST support a new ``timeoutMS`` option, which specifies the timeout
for all operations executed on the ``ClientEncryption`` object.

See `maxTimeMS is not added for mongocryptd`_.

Background Connection Pooling
-----------------------------

Connections created as part of a connection pool’s ``minPoolSize``
maintenance routine MUST use ``connectTimeoutMS`` as the timeout for
connection establishment. After the connection is established, if
``timeoutMS`` is set at the MongoClient level, it MUST be used as the timeout
for all commands sent as part of the MongoDB or authentication handshakes.
The timeout MUST be refreshed after each command. These commands MUST set
timeouts per the `Command Execution`_ section. If ``timeoutMS`` is not set,
drivers MUST continue to honor ``socketTimeoutMS`` as the socket timeout for
handshake and authentication commands.

Server Monitoring
-----------------

Drivers MUST NOT use ``timeoutMS`` for commands executed by the server
monitoring and RTT calculation threads.

See `Monitoring threads do not use timeoutMS`_.

Cursors
-------

For operations that create cursors, ``timeoutMS`` can either cap the lifetime
of the cursor or be applied separately to the original operation and all
``next`` calls. To support both of these use cases, these operations MUST
support a ``timeoutMode`` option. This option is an enum with possible values
``CURSOR_LIFETIME`` and ``ITERATION``. The default value depends on the type
of cursor being created. Drivers MUST error if ``timeoutMode`` is set and
``timeoutMS`` is not.

When applying the ``timeoutMS`` option to ``next`` calls on cursors, drivers
MUST ensure it applies to the entire call, not individual commands. For
drivers that send ``getMore`` requests in a loop when iterating tailable
cursors, the timeout MUST apply to the totality of all ``getMore``’s, not to
each one individually. If a resume is required for a ``next`` call on a
change stream, the timeout MUST apply to the entirety of the initial
``getMore`` and all commands sent as part of the resume attempt.

For ``close`` methods, drivers MUST allow ``timeoutMS`` to be overridden if
doing so is possible in the language.  If explicitly set for the operation,
it MUST be honored.  Otherwise, if ``timeoutMS`` was applied to the operation
that created the cursor, it MUST be refreshed for the ``killCursors`` command
if one is required.  Note that this means ``timeoutMS`` will be refreshed for
the ``close`` call even if the cursor was created with a ``timeoutMode`` of
``CURSOR_LIFETIME`` and the timeout associated with the cursor has expired.
The calculated timeout MUST apply to explicit ``close`` methods that can be
invoked by users as well as implicit destructors that are automatically
invoked when exiting resource blocks.

See `Cursor close() methods refresh timeoutMS`_.

Non-tailable Cursors
~~~~~~~~~~~~~~~~~~~~

For non-tailable cursors, the default value of ``timeoutMode`` is
``CURSOR_LIFETIME``. If ``timeoutMS`` is set, drivers MUST apply it to the
original operation and the lifetime of the created cursor. For example, if a
``find`` is executed at time ``T``, the ``find`` and all ``getMore``’s on the
cursor must finish by time ``T + timeoutMS``. When executing ``next`` calls
on the cursor, drivers MUST use the remaining timeout as the ``timeoutMS``
value for the operation but MUST NOT append a ``maxTimeMS`` field to
``getMore`` commands. If there are documents remaining in a previously
retrieved batch, the ``next`` method MUST return them even if the timeout has
expired and MUST only return a timeout error if a ``getMore`` is required.

If ``timeoutMode`` is set to ``ITERATION``, drivers MUST raise a client-side
error if the operation is an ``aggregate`` with a ``$out`` or ``$merge``
pipeline stage. If the operation is not an ``aggregate`` with ``$out`` or
``$merge``, drivers MUST honor the ``timeoutMS`` option for the initial
command but MUST NOT append a ``maxTimeMS`` field to the command sent to the
server. After the operation has executed, the original ``timeoutMS`` value
MUST also be applied to each ``next`` call on the created cursor. Drivers
MUST NOT append a ``maxTimeMS`` field to ``getMore`` commands.

See `Non-tailable cursor behavior`_.

Tailable Cursors
~~~~~~~~~~~~~~~~

Tailable cursors only support the ``ITERATION`` value for the ``timeoutMode``
option. This is the default value and drivers MUST error if the option is set
to ``CURSOR_LIFETIME``.

Tailable non-awaitData Cursors
``````````````````````````````

If ``timeoutMS`` is set, drivers MUST apply it separately to the original
operation and to all ``next`` calls on the resulting cursor but MUST NOT
append a ``maxTimeMS`` field to any commands.

Tailable awaitData Cursors
``````````````````````````

If ``timeoutMS`` is set, drivers MUST apply it to the original operation.
Drivers MUST also apply the original ``timeoutMS`` value to each ``next``
call on the resulting cursor but MUST NOT use it to derive a ``maxTimeMS``
value for ``getMore`` commands. Helpers for operations that create tailable
awaitData cursors MUST also support the ``maxAwaitTimeMS`` option. Drivers
MUST error if this option is set, ``timeoutMS`` is set to a non-zero value,
and ``maxAwaitTimeMS`` is greater than or equal to ``timeoutMS``. If this
option is set, drivers MUST use it as the ``maxTimeMS`` field on ``getMore``
commands.

See `Tailable cursor behavior`_ for rationale regarding both non-awaitData
and awaitData cursors.

Change Streams
~~~~~~~~~~~~~~

Driver ``watch`` helpers MUST support both ``timeoutMS`` and
``maxAwaitTimeMS`` options. Drivers MUST error if ``maxAwaitTimeMS`` is set,
``timeoutMS`` is set to a non-zero value, and ``maxAwaitTimeMS`` is greater
than or equal to ``timeoutMS``. These helpers MUST NOT support the
``timeoutMode`` option as change streams are an abstraction around
tailable-awaitData cursors, so they implicitly use ``ITERATION`` mode. If
set, drivers MUST apply the ``timeoutMS`` option to the initial ``aggregate``
operation. Drivers MUST also apply the original ``timeoutMS`` value to each
``next`` call on the change stream but MUST NOT use it to derive a
``maxTimeMS`` field for ``getMore`` commands. If the ``maxAwaitTimeMS``
option is set, drivers MUST use it as the ``maxTimeMS`` field on ``getMore``
commands.

If a ``next`` call fails with a timeout error, drivers MUST NOT invalidate
the change stream. The subsequent ``next`` call MUST perform a resume attempt
to establish a new change stream on the server. Any errors from the
``aggregate`` operation done to create a new change stream MUST be propagated
to the application. Drivers MUST document that users can either call ``next``
again or close the existing change stream and create a new one if a previous
``next`` call times out. The documentation MUST suggest closing and
re-creating the stream with a higher timeout if the timeout occurs before any
events have been received because this is a signal that the server is timing
out before it can finish processing the existing oplog.

See `Change stream behavior`_.

Sessions
--------

The `SessionOptions <../sessions/driver-sessions.rst#mongoclient-changes>`_
used to construct explicit `ClientSession
<../sessions/driver-sessions.rst#clientsession>`_ instances MUST accept a new
``defaultTimeoutMS`` option, which specifies the ``timeoutMS`` value for the
following operations executed on the session:

#. commitTransaction
#. abortTransaction
#. withTransaction
#. endSession

If this option is not specified for a ``ClientSession``, it MUST inherit the
``timeoutMS`` of its parent MongoClient.

Session checkout
~~~~~~~~~~~~~~~~

As noted in `Blocking Sections for Operation Execution`_, implicit session
checkout can be considered a blocking process for some drivers.  Such drivers
MUST apply the remaining ``timeoutMS`` value to this process when executing
an operation.  For explicit session checkout, drivers MUST apply the
``timeoutMS`` value of the MongoClient to the ``startSession`` call if set.
Drivers MUST NOT allow users to override ``timeoutMS`` for ``startSession``
operations.

See `timeoutMS cannot be overridden for startSession calls`_.

Convenient Transactions API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``timeoutMS`` is set, drivers MUST apply it to the entire
``withTransaction`` call. To propagate the timeout to the user-supplied
callback, drivers MUST store the timeout as a field on the ClientSession
object. This field SHOULD be private to ensure that a user can not modify it
while a ``withTransaction`` call is in progress. Drivers that cannot make
this field private MUST signal that the field should not be accessed or
modified by users if there is an idiomatic way to do so in the language (e.g.
underscore-prefixed variable names in Python) and MUST document that
modification of the field can cause unintended correctness issues for
applications. Drivers MUST document that the remaining timeout will not be
applied to callback operations that do not use the ClientSession. Drivers
MUST also document that overridding ``timeoutMS`` for operations executed
using the explict session inside the provided callback will result in a
client-side error, as defined in `Validation and Overrides`_. If the callback
returns an error and the transaction must be aborted, drivers MUST refresh
the ``timeoutMS`` value for the ``abortTransaction`` operation.

If ``timeoutMS`` is not set, drivers MUST continue to exhibit the existing
120 second timeout behavior. Drivers MUST NOT change existing implementations
to use ``timeoutMS=120000`` for this case.

See `withTransaction communicates timeoutMS via ClientSession`_ and
`withTransaction refreshes the timeout for abortTransaction`_.

GridFS API
----------

GridFS buckets MUST inherit ``timeoutMS`` from their parent MongoDatabase
instance and all methods in the GridFS Bucket API MUST support the
``timeoutMS`` option. For methods that create streams (e.g.
``open_upload_stream``), the option MUST cap the lifetime of the entire
stream. This MUST include the time taken by any operations executed during
stream construction, reads/writes, and close/abort calls. For example, if a
stream is created at time ``T``, the final ``close`` call on the stream MUST
finish all blocking work before time ``T + timeoutMS``. Methods that interact
with a user-provided stream (e.g. ``upload_from_stream``) MUST use
``timeoutMS`` as the timeout for the entire upload/download operation. If the
user-provided streams do not support timeouts, drivers MUST document that the
timeout for these methods may be breached if calls to interact with the
stream take longer than the remaining timeout. If ``timeoutMS`` is set, all
cursors created for GridFS API operations MUST internally set the
``timeoutMode`` option to ``CURSOR_LIFETIME``.

See `GridFS streams behavior`_.

RunCommand
----------

The behavior of ``runCommand`` is undefined if the provided command document
includes a ``maxTimeMS`` field and the ``timeoutMS`` option is set. Drivers
MUST document the behavior of ``runCommand`` for this case and MUST NOT
attempt to check the command document for the presence of a ``maxTimeMS``
field.

See `runCommand behavior`_.

Test Plan
=========

See the `README.rst
<https://github.com/divjotarora/specifications/blob/csot-tests/source/client-side-operations-timeout/tests/README.rst>`__
in the tests directory.

Motivation for Change
=====================

Users have many options to set timeouts for various parts of operation
execution including, but not limited to, ``serverSelectionTimeoutMS``,
``socketTimeoutMS``, ``connectTimeoutMS``, ``maxTimeMS``, and ``wTimeoutMS``.
As a result, users are often unsure which timeout to use. Because some of
these timeouts are additive, it is difficult to set a combination which
ensures control will be returned to the user after a specified amount of
time. To make timeouts more intuitive, changes are required to the drivers
API to deprecate some of the existing timeouts and add a new one to specify
the maximum execution time for an entire operation from start to finish.

In addition, automatically retrying reads and writes that failed due to
transient network blips or planned maintenance scenarios has improved
application resiliency but the original behavior of only retrying once still
allowed some errors to be propagated to applications. Supporting a timeout
for an entire operation allows drivers to retry operations multiple times
while still guaranteeing that an application can get back control once the
specified amount of time has elapsed.

Design Rationale
================

timeoutMS cannot be changed to unset once it’s specified
--------------------------------------------------------

If ``timeoutMS`` is specified at any level, it cannot be later changed to
unset at a lower level. For example, a user cannot do:

.. code:: python

   client = MongoClient(uri, timeoutMS=1000)
   db = client.database("foo", timeoutMS=None)

This is because drivers return existing exception types if ``timeoutMS`` is
not specified, but will return new exception types and use new timeout
behaviors if it is. Once the user has opted into this behavior, we should not
allow them to opt out of it at a lower level. If a user wishes to set the
timeout to infinite for a specific database, collection, or operation, they
can explicitly set ``timeoutMS`` to 0.

serverSelectionTimeoutMS is not deprecated
------------------------------------------

The original goal of the project was to expose a single timeout and deprecate
all others. This was not possible, however, because executing an operation
consists of two distinct parts. The first is selecting a server and checking
out a connection from its pool. This should have a default timeout because
failure to do this indicates that the deployment is not in a healthy state or
that there was a configuration error which prevents the driver from
successfully connecting. The second is server-side operation execution, which
cannot have a default timeout. Some operations finish in a few milliseconds,
while others can run for many hours. Adding a default would inevitably break
applications. To accomplish both of these goals, ``serverSelectionTimeoutMS``
was preserved and is used to timeout the client-side section of operation
execution.

connectTimeoutMS is not deprecated
----------------------------------

Similar to the reasoning for not deprecating ``serverSelectionTimeoutMS``,
socket establishment should have a default timeout because failure to create
a socket likely means that the target server is not healthy or there is a
network issue. To accomplish this, the ``connectTimeoutMS`` option is not
deprecated by this specification. Drivers also use ``connectTimeoutMS`` to
derive a socket timeout for monitoring connections, which are not subject to
timeoutMS.

timeoutMS overrides deprecated timeout options
----------------------------------------------

Applying both ``timeoutMS`` and a deprecated timeout option like
``socketTimeoutMS`` at the same time would lead to confusing semantics that
are difficult to document and understand. When first writing this
specification, we considered having drivers error in this situation to catch
mismatched timeouts as early as possible. However, because ``timeoutMS`` can
be set at any level, this behavior could lead to unanticipated runtime errors
if an application set ``timeoutMS`` for a specific operation and the
MongoClient used in production was configured with a deprecated timeout
option. To have clear semantics and avoid unexpected errors in applications, we
decided that ``timeoutMS`` should override deprecated timeout options.

maxTimeMS is not added for mongocryptd
--------------------------------------

The mongocryptd server annotates the provided command to indicate encryption
requirements and returns the marked up result. If the command sent to
mongocryptd contained ``maxTimeMS``, the final command sent to MongoDB would
contain two ``maxTimeMS`` fields: one added by the regular MongoClient and
another added by the mongocryptd client. To avoid this complication, drivers
do not add this field when sending commands to mongocryptd at all. Doing so
does not sacrifice any functionality because mongocryptd always runs on
localhost and does not perform any blocking work, so execution or network
timeouts cannot occur.

maxTimeMS accounts for server RTT
---------------------------------

When constructing a command, drivers use the ``timeoutMS`` option to derive a
value for the ``maxTimeMS`` command option and the socket timeout. The full
time to round trip a command is (network RTT + server-side execution time).
If both ``maxTimeMS`` and socket timeout were set to the same value, the
server would never be able to respond with a ``MaxTimeMSExpired`` error
because drivers would hit the socket timeout first and close the connection.
This would lead to connection churn if the specified timeout is too low. To
allow the server to gracefully error and avoid churn, drivers must account
for the network round trip in the ``maxTimeMS`` calculation.

Monitoring threads do not use timeoutMS
---------------------------------------

Using ``timeoutMS`` in the monitoring and RTT calculation threads would
require another special case in the code that derives ``maxTimeMS`` from
``timeoutMS`` because the awaitable ``isMaster`` requests sent to 4.4+
servers already have a ``maxAwaitTimeMS`` field. Adding ``maxTimeMS`` also
does not help for non-awaitable ``isMaster`` commands because we expect them
to execute quickly on the server. The Server Monitoring spec already mandates
that drivers set and dynamically update the read/write timeout of the
dedicated connections used in monitoring threads, so we rely on that to time
out commands rather than adding complexity to the behavior of ``timeoutMS``.

runCommand behavior
-------------------

The behavior of runCommand varies across drivers. If the provided command
document includes a ``maxTimeMS`` field and the ``timeoutMS`` option is set,
some drivers would overwrite the ``maxTimeMS`` field with the value derived
from ``timeoutMS``, while others would append a second ``maxTimeMS`` field,
which would cause a server error on versions 3.4+. To be prescriptive, we
could mandate that drivers raise a client-side error in this case, but this
would require a potentially expensive lookup in the command document. To
avoid this additional cost, drivers are only required to document the
behavior and suggest that ``timeoutMS`` be used instead of including a manual
``maxTimeMS`` field.

Why don’t drivers use backoff/jitter between retry attempts?
------------------------------------------------------------

Earlier versions of this specification proposed adding backoff and/or jitter
between retry attempts to avoid connection storming or overloading the
server, but we later deemed this unnecessary. If multiple concurrent
operations select the same server for a retry and its connection pool is
empty, we rely on the ``maxConnecting`` parameter introduced in DRIVERS-781
to rate limit new connection attempts, which mitigates the risk of connection
storms. Even if the new server has enough connections in its pool to service
the operations, recent server versions do very little resource-intensive work
until execution reaches the storage layer, which is already guarded by
read/write tickets, so we don’t expect the server to be overwhelmed. If we
later decide that adding jitter would be useful, it may be easier to do so in
the server itself via a ticket-based admission system earlier in the
execution stack.

Cursor close() methods refresh timeoutMS
----------------------------------------

If a cursor times out client-side (e.g. a non-tailable cursor created with
``timeoutMode=CURSOR_LIFETIME``), it’s imperative that drivers make a
good-faith effort to close the server-side cursor even though the timeout has
expired because failing to do so would leave resources open on the server for
a potentially long time. It was decided that ``timeoutMS`` will be refreshed
for ``close`` operations to allow the cursor to be killed server-side.

Non-tailable cursor behavior
----------------------------

There are two usage patterns for non-tailable cursors. The first is to read
documents from a cursor into an iterable object, either by explicitly
iterating the cursor in a loop or using a language construct like Python list
comprehensions. To supply a timeout for the entire process, drivers use
``timeoutMS`` to cap the execution time for the initial command and all
required ``getMore``’s. This use case also matches the server behavior; if
``maxTimeMS`` is set for an operation that creates a non-tailable cursor, the
server will use the time limit to cap the total server-side execution time
for future ``getMore``’s. Because this type of usage matches the server
behavior and is the more common case, this is the default behavior.

The second use case is batch processing, where the user takes advantage of
the lazy nature of cursors to process documents from a large collection. In
this case, the user does not want all documents from the collection to be in
an array because that would require too much memory. To accommodate this use
case, drivers support a new ``timeoutMode`` option. Users can set the value
for this option to ``ITERATION`` to have ``timeoutMS`` apply to the original
command and then separately to each ``next`` call. When this option is used,
drivers do not set ``maxTimeMS`` on the initial command to avoid capping the
cursor lifetime in the server.

Tailable cursor behavior
------------------------

Once a tailable cursor is created, it conceptually lives forever. Therefore,
it only makes sense to support ``timeoutMode=ITERATION`` for these cursors
and drivers error if ``timeoutMode=CURSOR_LIFETIME`` is specified.

There are two types of tailable cursors. The first, tailable non-awaitData
cursors, support ``maxTimeMS`` for the original command but not for any
``getMore`` requests. However, setting ``maxTimeMS`` on the original command
also incorrectly caps the server-side execution time for future ``getMore``’s
(`SERVER-51153 <http://jira.mongodb.org/browse/SERVER-51153>`__). This is
undesirable behavior because it does not match the guarantees made by
``timeoutMode=ITERATION``. To work around this, drivers honor ``timeoutMS``
for both the original operation and all ``getMore``’s but only use it to
derive client-side timeouts and do not append a ``maxTimeMS`` field to any
commands. The server-side execution time is enforced via socket timeouts.

The second type is tailable awaitData cursors. The server supports the
``maxTimeMS`` option for the original command. For ``getMore``’s, the option
is supported, but instead of limiting the server-side execution time, it
specifies how long the server should wait for new data to arrive if it
reaches the end of the capped collection and the batch is still empty. If no
new data arrives within that time limit, the server will respond with an
empty batch. For these cursors, drivers support both the ``timeoutMS`` and
``maxAwaitTimeMS`` options. The ``timeoutMS`` option is used to derive
client-side timeouts, while the ``maxAwaitTimeMS`` option is used as the
``maxTimeMS`` field for ``getMore`` commands. These values have distinct
meanings, so supporting both yields a more robust, albeit verbose, API.
Drivers error if ``maxAwaitTimeMS`` is greater than or equal to ``timeoutMS``
because in that case, ``getMore`` requests would not succeed if the batch was
empty: the server would wait for ``maxAwaitTimeMS``, but the driver would
close the socket after ``timeoutMS``.

Change stream behavior
----------------------

Change streams internally behave as tailable awaitData cursors, so the
behavior of the ``timeoutMS`` option is the same for both. The main
difference is that change streams are resumable and drivers automatically
perform resume attempts when they encounter transient errors. This allows
change streams to be resilient to timeouts. If ``timeoutMS`` expires during a
next call, drivers can’t auto-resume, but they can make sure the change
stream is not invalidated so the user can call next again. In this case, the
subsequent call would perform the resume without doing a ``getMore`` first.

withTransaction communicates timeoutMS via ClientSession
--------------------------------------------------------

Because the ``withTransaction`` API doesn’t allow drivers to plumb down the
remaining timeout into the user-provided callback, this spec requires the
remaining timeout to be stored on the ClientSession. Operations in the
callback that run under that ClientSession can then extract the timeout from
the session and apply it. To avoid confusing validation semantics, operations
error if there is a timeout on the session but also an overridden timeout for
the operation. It’s possible that the ability to communicate timeouts for a
block of operations via a ClientSession is useful as a general purpose API,
but we’ve decided to make it private until there are other known use cases.

withTransaction refreshes the timeout for abortTransaction
----------------------------------------------------------

If the user-provided callback to ``withTransaction`` times out, it could
leave a transaction running on the server. It’s imperative that drivers make
an effort to abort the open transaction because failing to do so could result
in the collections and databases affected by the transaction being locked for
a long period of time, which could cause applications to stall. Because
``timeoutMS`` has expired before drivers attempt to abort the transaction, we
require drivers to refresh it and apply the original value to the execution
of the ``abortTransaction`` operation. This can cause the entire
``withTransaction`` call to take up to ``2*timeoutMS``, but it was decided
that this risk is worthwhile given the importance of transaction cleanup.

GridFS streams behavior
-----------------------

Streams created by GridFS API operations (e.g. by ``open_upload_stream`` and
``open_download_stream``) present a challenge for this specification. These
types of streams execute multiple operations, but there can be artificial
gaps between operations if the application does not invoke the stream
functions for long periods of time. Generally, we expect users to upload or
download an entire file as quickly as possible, so we decided to have
``timeoutMS`` cap the lifetime of the created stream. The other option was to
apply the entire ``timeoutMS`` value to each operation executed by the
stream, but streams perform many hidden operations, so this approach could
cause an upload/download to take much longer than expected.

timeoutMS cannot be overridden for startSession calls
-----------------------------------------------------

In general, users can override ``timeoutMS`` at the level of a single
operation.  The ``startSession`` operation, however, only inherits
``timeoutMS`` from the MongoClient and does not allow the option to be
overridden.  This was a consious API design decision because drivers are
moving towards only supporting MongoDB versions 3.6 and higher, so sessions
will always be supported. Adding an override for ``startSession`` would
introduce a new knob and increase the API surface of drivers without providing
a significant benefit.


Future work
===========

Modify GridFS streams behavior via new options
----------------------------------------------

As explained in the design rationale, drivers use ``timeoutMS`` to cap the
entire lifetime of streams created by GridFS operations. If we find that users
are often encountering timeout errors when using these APIs due to the time
spent during non-MongoDB operations (e.g.  streaming data read from a GridFS
stream into another data store), we could consider toggling GridFS behavior
via an option similiar to ``timeoutMode`` for cursors. To avoid
backwards-breaking behavioral changes, the default would continue to cap the
stream lifetime but there could be another mode that refreshes the timeout
for each database operation. This would mimic using
``timeoutMode=ITERATION`` for cursors.


Changelog 
=========

===========
Run Command
===========

:Status: Accepted
:Minimum Server Version: N/A

.. contents::

--------

Abstract
========
This specification defines requirements and behaviors for drivers' run command and related APIs.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in `RFC 2119
<https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

-----
Terms
-----
Command
    A structure representing a BSON document that has a shape matching a supported MongoDB operation.

---------------------------
Implementation requirements
---------------------------

All drivers MAY offer the operations defined in the following sections.
This does not preclude a driver from offering more.

----------
Deviations
----------

Please refer to `The CRUD specification's Guidance <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#guidance>`_ on how APIs may deviate between languages.

Cursor iterating APIs MAY be offered via language syntax or predefined iterable methods.

--------------
``runCommand``
--------------

The following represents how a runCommand API SHOULD be exposed.

.. code:: typescript

    interface Database {
      /**
       * Takes an argument representing an arbitrary BSON document and executes it against the server.
       */
      runCommand(command: BSONDocument, options: RunCommandOptions): BSONDocument;
    }

    interface RunCommandOptions {
      /**
       * An optional readPreference setting to apply to server selection logic.
       * This value MUST be applied to the command document as the $readPreference global command argument if not set to primary.
       *
       * @defaultValue ReadPreference(mode: primary)
       *
       * @see https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#read-preference
       */
      readPreference?: ReadPreference;

      /**
       * An optional explicit client session.
       * The associated logical session id (`lsid`) the driver MUST apply to the command.
       *
       * @see https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#clientsession
       */
      session?: ClientSession;

      /**
       * An optional timeout option to govern the amount of time that a single operation can execute before control is returned to the user.
       * This timeout applies to all of the work done to execute the operation, including but not limited to server selection, connection checkout, and server-side execution.
       *
       * @ see https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst
       */
      timeoutMS?: number;
    }

RunCommand implementation details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RunCommand provides a way to access MongoDB server commands directly without requiring a driver to implement a bespoke helper.
The API is intended to take a document from a user and apply a number of common driver internal concerns before forwarding the command to a server.
A driver MUST not inspect the user's command, this includes checking for the fields a driver MUST attach to the command sent as described below.
Depending on a driver's BSON implementation this can result in these fields being overwritten or duplicated, a driver SHOULD document that using these fields has undefined behavior.
A driver MUST not modify the user's command, a clone SHOULD be created before the driver attaches any of the required fields to the command.

Drivers that have historically modified user input SHOULD strive to instead clone the input such that appended fields do not affect the user's input in their next major version.

OP_MSG
""""""

The ``$db`` global command argument MUST be set on the command sent to the server and it MUST equal the database name RunCommand was invoked on.

* See OP_MSG's section on `Global Command Arguments <https://github.com/mongodb/specifications/blob/master/source/message/OP_MSG.rst#global-command-arguments>`_

ReadPreference
""""""""""""""

For the purposes of server selection RunCommand MUST assume all commands are read operations.
To facilitate server selection the RunCommand operation MUST accept an optional ``readPreference`` option.

* See Server Selection's section on `Use of read preferences with commands <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#use-of-read-preferences-with-commands>`_

If the provided ReadPreference is NOT ``{mode: primary}``, the command sent MUST include the ``$readPreference`` global command argument.

* See OP_MSG's section on `Global Command Arguments <https://github.com/mongodb/specifications/blob/master/source/message/OP_MSG.rst#global-command-arguments>`_

Driver Sessions
"""""""""""""""

A driver's RunCommand MUST provide an optional session option to support explicit sessions and transactions.
If a session is not provided the driver MUST attach an implicit session if the connection supports sessions.
Drivers MUST NOT attempt to check the command document for the presence of an ``lsid``.

Every ClientSession has a corresponding logical session ID representing the server-side session ID.
The logical session ID MUST be included under ``lsid`` in the command sent to the server without modifying user input.

* See Driver Sessions' section on `Sending the session ID to the server on all commands <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#sending-the-session-id-to-the-server-on-all-commands>`_

The command sent to the server MUST gossip the ``$clusterTime`` if cluster time support is detected.

* See Driver Sessions' section on `Gossipping the cluster time <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#gossipping-the-cluster-time>`_

Transactions
""""""""""""

If RunCommand is used within a transaction the read preference MUST be sourced from the transaction's options.
The command sent to the server MUST include the transaction specific fields, summarized as follows:

* If ``runCommand`` is executing within a transaction:

  * ``autocommit`` - The autocommit flag MUST be set to false.
  * ``txnNumber`` - MUST be set.

* If ``runCommand`` is the first operation of the transaction:

  * ``startTransaction`` - MUST be set to true.
  * ``readConcern`` - MUST be set to the transaction's read concern if it is NOT the default.

* See `Generic RunCommand helper within a transaction <https://github.com/mongodb/specifications/blob/master/source/transactions/transactions.rst#generic-runcommand-helper-within-a-transaction>`_ in the Transactions specification.

ReadConcern and WriteConcern
""""""""""""""""""""""""""""

RunCommand MUST NOT support read concern and write concern options.
Drivers MUST NOT attempt to check the command document for the presence of a ``readConcern`` and ``writeConcern`` field.

Additionally, unless executing within a transaction, RunCommand MUST NOT set the ``readConcern`` or ``writeConcern`` fields in the command document.
For example, default values MUST NOT be inherited from client, database, or collection options.

If the user-provided command document already includes ``readConcern`` or ``writeConcern`` fields, the values MUST be left as-is.

* See Read Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method>`_
* See Write Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method-1>`_

Retryability
""""""""""""

All commands executed via RunCommand are non-retryable operations.
Drivers MUST NOT inspect the command to determine if it is a write and MUST NOT attach a ``txnNumber``.

* See Retryable Reads' section on `Unsupported Read Operations <https://github.com/mongodb/specifications/blob/master/source/retryable-reads/retryable-reads.rst#unsupported-read-operations>`_
* See Retryable Writes' section on `Behavioral Changes for Write Commands <https://github.com/mongodb/specifications/blob/master/source/retryable-writes/retryable-writes.rst#behavioral-changes-for-write-commands>`_

Stable API
""""""""""

The command sent MUST attach stable API fields as configured on the MongoClient.

* See Stable API's section on `Generic Command Helper Behaviour <https://github.com/mongodb/specifications/blob/master/source/versioned-api/versioned-api.rst#generic-command-helper>`_

Client Side Operations Timeout
""""""""""""""""""""""""""""""

RunCommand MUST provide an optional ``timeoutMS`` option to support client side operations timeout.
Drivers MUST NOT attempt to check the command document for the presence of a ``maxTimeMS`` field.
Drivers MUST document the behavior of RunCommand if a ``maxTimeMS`` field  is already set on the command (such as overwriting the command field).

* See Client Side Operations Timeout's section on `runCommand <https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst#runcommand>`_
* See Client Side Operations Timeout's section on `runCommand behavior <https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst#runcommand-behavior>`_


--------------------
``runCursorCommand``
--------------------

The following represents how a runCursorCommand API may be exposed.

.. code:: typescript

    interface Db {
      /**
       * Takes an argument representing an arbitrary BSON document and executes it against the server.
       */
      runCursorCommand(command: BSONDocument, options: RunCursorCommandOptions): RunCommandCursor;
    }

    interface RunCursorCommandOptions extends RunCommandOptions {
      /**
       * For operations that create cursors, timeoutMS can either cap the lifetime of the cursor or be applied separately to the original operation and all next calls.
       * To support both of these use cases, these operations MUST support a timeoutMode option.
       *
       * @defaultValue 'CURSOR_LIFETIME'
       *
       * @see https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst
       */
      timeoutMode?: 'ITERATION' | 'CURSOR_LIFETIME';

      /**
       * Identifies the type of cursor this is.
       *
       * A tailable cursor can receive empty ``nextBatch`` arrays in getMore responses.
       * However, subsequent ``getMore`` operations may return documents if new data has become available.
       *
       * A tailableAwait cursor is an enhancement where instead of dealing with empty responses the server will block until data become available.
       *
       * @defaultValue NON_TAILABLE
       */
      cursorType: NON_TAILABLE | TAILABLE | TAILABLE_AWAIT;
    }

RunCursorCommand implementation details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RunCursorCommand provides a way to access MongoDB server commands that return a cursor directly without requiring a driver to implement a bespoke cursor implementation.
The API is intended to be built upon RunCommand and take a document from a user and apply a number of common driver internal concerns before forwarding the command to a server.
A driver can expect that the result from running this command will return a document with a ``cursor`` field and MUST provide the caller with a language native abstraction to continue iterating the results from the server.

High level RunCursorCommand steps:

* If no session is provided by the caller, create a ClientSession
* Create a local Cursor instance
* Run the cursor creating command provided by the caller
* Store the ``firstBatch``, ``ns``, and ``id`` from the server's response as well as which server the operation was executed on
* When the current batch has been fully iterated, using the same server the initial command was executed on execute a ``getMore``
* Store the results of the getMore's ``nextBatch`` and update the cursor's ``id``
* Continue executing ``getMore`` commands until the cursor is exhausted

Driver Sessions
"""""""""""""""

A driver MUST create an implicit ClientSession if none is provided and it MUST be attached for the duration of the cursor's lifetime.
All ``getMore`` commands constructed for this cursor MUST send the same ``lsid`` used on the initial command.
A cursor is exhausted when the server reports a cursor is equal to zero.
When the cursor is exhausted the client session MUST be ended and the server session returned to the pool as early as possible rather than waiting for a caller to completely iterate the final batch.

Server Selection
""""""""""""""""

RunCursorCommand MUST support a ``readPreference`` option that MUST be used to determine server selection.
The selected server MUST be used for subsequent ``getMore`` commands.

Load Balancers
""""""""""""""

When in ``loadBalanced`` mode, a driver MUST pin the connection the initial operation was executed on and reuse it for subsequent ``getMore`` operations.

* See Load Balancer's section on `Behaviour With Cursors <https://github.com/mongodb/specifications/blob/master/source/load-balancers/load-balancers.rst#behaviour-with-cursors>`_

Iterating the Cursor
""""""""""""""""""""

Drivers MUST provide an API, typically, a method named ``next()``, that returns one document per invocation.
If the cursor's batch is empty and the cursor id is nonzero, the driver MUST perform a ``getMore`` operation.

Executing GetMores
""""""""""""""""""

The cursor API returned to the caller MUST offer a way to configure ``batchSize``, ``maxTimeMS``, and ``comment`` that are sent on the ``getMore`` command.

.. code:: typescript

  interface GetMore {
    /** Set to the nonzero cursor id */
    getMore: int64;
    /** Set to the namespace returned by the initial command response */
    collection: string;
    /**
     * User configurable document count for the batch returned for this getMore.
     * Only attached to command document if nonzero.
     */
    batchSize?: int23;
    /**
     * User configurable time limit enforced by the server.
     */
    maxTimeMS?: int23;
    /**
     * User configurable comment that can be used to identify the operation in logs.
     * This can be any BSON value.
     */
    comment?: BSONValue;
  }

The driver's cursor MUST update its ``id`` and ``ns``, as well as store the ``nextBatch`` from every getMore response.

Tailable and TailableAwait
""""""""""""""""""""""""""

By default most cursors are non-tailable, for example, a find that exhausts when all results for the filter have been satisfied.
MongoDB also supports creating cursors that "tail" or follow the target namespace for new data.
Querying capped collections and change streams are some examples of tailable cursor use cases.
A tailable cursor can receive ``getMore`` responses with an empty ``nextBatch`` array, this does not indicate that the cursor has been exhausted.

In addition to considering a cursor tailable, an ``awaitData`` flag may be sent on the initial command.
This will request that the server block responding to the ``getMore`` immediately and instead rely on the ``maxTimeMS`` field of the ``getMore`` (or server default).
If the time does expire an empty batch will be returned and the driver MUST issue another ``getMore``.

It is up to the user to construct their initial command with ``awaitData`` and ``tailable`` flags as well as inform RunCursorCommand of the ``cursorType`` that should be constructed.
Requesting a ``cursorType`` that does not align with the fields sent to the server on the initial command SHOULD be documented as undefined behavior.

Resource Cleanup
""""""""""""""""

Drivers MUST provide an explicit mechanism for releasing the cursor resources, typically a ``.close()`` method.
If the cursor id is nonzero a KillCursors operation MUST be attempted, the result of the operation SHOULD be ignored.
The ClientSession associated with the cursor MUST be ended and the ServerSession returned to the pool.

* See Driver Sessions' section on `When sending a killCursors command <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#when-sending-a-killcursors-command>`_

Client Side Operations Timeout
""""""""""""""""""""""""""""""

As with RunCommand if the initial command has a ``maxTimeMS`` and CSOT settings are provided the behavior is undefined and drivers MUST NOT inspect the document to detect this.
Drivers SHOULD not allow both a ``getMore`` ``maxTimeMS`` setting to be provided and CSOT settings.
Drivers MUST document that attempting to set both can have undefined behavior and is not supported.

When ``timeoutMS`` and ``timeoutMode`` are provided the driver MUST support timeout functionality as described in the CSOT specification.

* See Client Side Operations Timeout's section on `Cursors <https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst#cursors>`_

Changelog
=========

:2023-04-24: Add runCursorCommand API specification.
:2023-04-20: Add run command specification.

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
       * @see ../server-selection/server-selection.md#read-preference
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

* See Server Selection's section on `Use of read preferences with commands <../server-selection/server-selection.md#use-of-read-preferences-with-commands>`_

If the provided ReadPreference is NOT ``{mode: primary}`` and the selected server is NOT a standalone, the command sent MUST include the ``$readPreference`` global command argument.

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

* See `Generic RunCommand helper within a transaction <../transactions/transactions.md#generic-runcommand-helper-within-a-transaction>`_ in the Transactions specification.

ReadConcern and WriteConcern
""""""""""""""""""""""""""""

RunCommand MUST NOT support read concern and write concern options.
Drivers MUST NOT attempt to check the command document for the presence of a ``readConcern`` and ``writeConcern`` field.

Additionally, unless executing within a transaction, RunCommand MUST NOT set the ``readConcern`` or ``writeConcern`` fields in the command document.
For example, default values MUST NOT be inherited from client, database, or collection options.

If the user-provided command document already includes ``readConcern`` or ``writeConcern`` fields, the values MUST be left as-is.

* See Read Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method>`__
* See Write Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method-1>`__

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

* See Client Side Operations Timeout's section on `runCommand <../client-side-operations-timeout/client-side-operations-timeout.md#runcommand>`_
* See Client Side Operations Timeout's section on `runCommand behavior <../client-side-operations-timeout/client-side-operations-timeout.md#runcommand-behavior>`_


--------------------
``runCursorCommand``
--------------------

Drivers MAY expose a runCursorCommand API with the following syntax.

.. code:: typescript

    interface Database {
      /**
       * Takes an argument representing an arbitrary BSON document and executes it against the server.
       */
      runCursorCommand(command: BSONDocument, options: RunCursorCommandOptions): RunCommandCursor;
    }

    interface RunCursorCommandOptions extends RunCommandOptions {
      /**
       * This option is an enum with possible values CURSOR_LIFETIME and ITERATION.
       * For operations that create cursors, timeoutMS can either cap the lifetime of the cursor or be applied separately to the original operation and all subsequent calls.
       * To support both of these use cases, these operations MUST support a timeoutMode option.
       *
       * @defaultValue CURSOR_LIFETIME
       *
       * @see https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst
       */
      timeoutMode?: ITERATION | CURSOR_LIFETIME;

      /**
       * See the `cursorType` enum defined in the crud specification.
       * @see https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read
       *
       * Identifies the type of cursor this is for client side operations timeout to properly apply timeoutMode settings.
       *
       * A tailable cursor can receive empty `nextBatch` arrays in `getMore` responses.
       * However, subsequent `getMore` operations may return documents if new data has become available.
       *
       * A tailableAwait cursor is an enhancement where instead of dealing with empty responses the server will block until data becomes available.
       *
       * @defaultValue NON_TAILABLE
       */
      cursorType?: CursorType;
    }

    /**
     * The following are the configurations a driver MUST provide to control how getMores are constructed.
     * How the options are controlled should be idiomatic to the driver's language.
     * See Executing ``getMore`` Commands.
     */
    interface RunCursorCommandGetMoreOptions {
      /** Any positive integer is permitted. */
      batchSize?: int;
      /** Any non-negative integer is permitted. */
      maxTimeMS?: int;
      comment?: BSONValue;
    }

RunCursorCommand implementation details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RunCursorCommand provides a way to access MongoDB server commands that return a cursor directly without requiring a driver to implement a bespoke cursor implementation.
The API is intended to be built upon RunCommand and take a document from a user and apply a number of common driver internal concerns before forwarding the command to a server.
A driver can expect that the result from running this command will return a document with a ``cursor`` field and MUST provide the caller with a language native abstraction to continue iterating the results from the server.
If the response from the server does not include a ``cursor`` field the driver MUST throw an error either before returning from ``runCursorCommand`` or upon first iteration of the cursor.

High level RunCursorCommand steps:

* Run the cursor creating command provided by the caller and retain the ClientSession used as well as the server the command was executed on.
* Create a local cursor instance and store the ``firstBatch``, ``ns``, and ``id`` from the response.
* When the current batch has been fully iterated, execute a ``getMore`` using the same server the initial command was executed on.
* Store the ``nextBatch`` from the ``getMore`` response and update the cursor's ``id``.
* Continue to execute ``getMore`` commands as needed when the caller empties local batches until the cursor is exhausted or closed (i.e. ``id`` is zero).

Driver Sessions
"""""""""""""""

A driver MUST create an implicit ClientSession if none is provided and it MUST be attached for the duration of the cursor's lifetime.
All ``getMore`` commands constructed for this cursor MUST send the same ``lsid`` used on the initial command.
A cursor is considered exhausted or closed when the server reports its ``id`` as zero.
When the cursor is exhausted the client session MUST be ended and the server session returned to the pool as early as possible rather than waiting for a caller to completely iterate the final batch.

* See Drivers Sessions' section on `Sessions and Cursors <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#sessions-and-cursors>`_

Server Selection
""""""""""""""""

RunCursorCommand MUST support a ``readPreference`` option that MUST be used to determine server selection.
The selected server MUST be used for subsequent ``getMore`` commands.

Load Balancers
""""""""""""""

When in ``loadBalanced`` mode, a driver MUST pin the connection used to execute the initial operation, and reuse it for subsequent ``getMore`` operations.

* See Load Balancer's section on `Behaviour With Cursors <https://github.com/mongodb/specifications/blob/master/source/load-balancers/load-balancers.rst#behaviour-with-cursors>`_

Iterating the Cursor
""""""""""""""""""""

Drivers MUST provide an API, typically, a method named ``next()``, that returns one document per invocation.
If the cursor's batch is empty and the cursor id is nonzero, the driver MUST perform a ``getMore`` operation.

Executing ``getMore`` Commands
""""""""""""""""""""""""""""""

The cursor API returned to the caller MUST offer an API to configure ``batchSize``, ``maxTimeMS``, and ``comment`` options that are sent on subsequent ``getMore`` commands.
If it is idiomatic for a driver to allow setting these options in ``RunCursorCommandOptions``, the driver MUST document that the options only pertain to ``getMore`` commands.
A driver MAY permit users to change ``getMore`` field settings at any time during the cursor's lifetime and subsequent ``getMore`` commands MUST be constructed with the changes to those fields.
If that API is offered drivers MUST write tests asserting ``getMore`` commands are constructed with any updated fields.

* See Find, getMore and killCursors commands' section on `GetMore <https://github.com/mongodb/specifications/blob/master/source/find_getmore_killcursors_commands.rst#getmore>`_

Tailable and TailableAwait
""""""""""""""""""""""""""

* **See first:** Find, getMore and killCursors commands's section on `Tailable cursors <https://github.com/mongodb/specifications/blob/master/source/find_getmore_killcursors_commands.rst#tailable-cursors>`_

It is the responsibility of the caller to construct their initial command with ``awaitData`` and ``tailable`` flags **as well as** inform RunCursorCommand of the ``cursorType`` that should be constructed.
Requesting a ``cursorType`` that does not align with the fields sent to the server on the initial command SHOULD be documented as undefined behavior.

Resource Cleanup
""""""""""""""""

Drivers MUST provide an explicit mechanism for releasing the cursor resources, typically a ``.close()`` method.
If the cursor id is nonzero a KillCursors operation MUST be attempted, the result of the operation SHOULD be ignored.
The ClientSession associated with the cursor MUST be ended and the ServerSession returned to the pool.

* See Driver Sessions' section on `When sending a killCursors command <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#when-sending-a-killcursors-command>`_
* See Find, getMore and killCursors commands' section on `killCursors <https://github.com/mongodb/specifications/blob/master/source/find_getmore_killcursors_commands.rst#killcursors>`_

Client Side Operations Timeout
""""""""""""""""""""""""""""""

RunCursorCommand MUST provide an optional ``timeoutMS`` option to support client side operations timeout.
Drivers MUST NOT attempt to check the command document for the presence of a ``maxTimeMS`` field.
Drivers MUST document the behavior of RunCursorCommand if a ``maxTimeMS`` field is already set on the command.
Drivers SHOULD raise an error if both ``timeoutMS`` and the ``getMore``-specific ``maxTimeMS`` option are specified (see: `Executing getMore Commands`_).
Drivers MUST document that attempting to set both options can have undefined behavior and is not supported.

When ``timeoutMS`` and ``timeoutMode`` are provided the driver MUST support timeout functionality as described in the CSOT specification.

* See Client Side Operations Timeout's section on `Cursors <../client-side-operations-timeout/client-side-operations-timeout.md#cursors>`_

Changelog
=========

:2023-05-10: Add runCursorCommand API specification.
:2023-05-08: ``$readPreference`` is not sent to standalone servers
:2023-04-20: Add run command specification.

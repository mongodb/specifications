===========
Run Command
===========

:Title: Run Command
:Status: Implementing
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
       * The associated logical session id (`lsid`) MUST be applied to the command.
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

Deviations
^^^^^^^^^^

* Drivers MAY rename their API to match the language syntax.

RunCommand implementation details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RunCommand provides a way to access MongoDB server commands directly without requiring a driver to implement a bespoke helper.
The API is intended to take a document from a user and apply a number of common driver internal concerns before forwarding the command to a server.
In general, a driver SHOULD avoid inspecting or modifying the user's command document in an effort to remain forward compatible with any potential server commands.

Drivers that have historically modified user input SHOULD strive to instead clone the input such that appended fields do not affect the user's input.

OP_MSG
""""""

The ``$db`` global command argument MUST be set on the command sent to the server and it MUST equal the database name the runCommand API was invoked on.

* See OP_MSG's section on `Global Command Arguments <https://github.com/mongodb/specifications/blob/master/source/message/OP_MSG.rst#global-command-arguments>`_

ReadPreference
""""""""""""""

A driver's runCommand implementation MUST assume all commands are read operations.
To facilitate server selection the runCommand operation MUST accept an optional Read Preference option.

* See Server Selection's section on `Use of read preferences with commands <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#use-of-read-preferences-with-commands>`_

If the provided ReadPreference is NOT ``{mode: primary}``, the command sent MUST include the ``$readPreference`` global command argument.

* See OP_MSG's section on `Global Command Arguments <https://github.com/mongodb/specifications/blob/master/source/message/OP_MSG.rst#global-command-arguments>`_

Driver Sessions
"""""""""""""""

A driver's runCommand API MUST provide an optional session option to support explicit sessions and transactions.
If a session is not provided the driver MUST attach an implicit session if the selected server supports sessions.

Every ClientSession has a corresponding Logical Session ID representing the server-side session ID.
The Logical Session ID MUST be included under ``lsid`` in the command sent to the server without modifying user input.

* See Driver Sessions' section on `Sending the session ID to the server on all commands <https://github.com/mongodb/specifications/blob/master/source/sessions/driver-sessions.rst#sending-the-session-id-to-the-server-on-all-commands>`_

Transactions
""""""""""""

If runCommand is used within a transaction the read preference MUST be sourced from the transaction's options.
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

Additionally, unless executing within a transaction, the RunCommand operation MUST NOT set the ``readConcern`` or ``writeConcern`` fields in the command document. For example, default values MUST NOT be inherited from client, database, or collection options.

If the user-provided command document already includes ``readConcern`` or ``writeConcern`` fields, the values MUST be left as-is.

* See Read Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method>`_
* See Write Concern's section on `Generic Command Method <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#generic-command-method-1>`_

Retryability
""""""""""""

All commands passed to runCommand are considered non-retryable reads.
Drivers MUST NOT inspect the command to determine if it is a write and MUST NOT attach a ``txnNumber``.

* See Retryable Reads' section on `Unsupported Read Operations <https://github.com/mongodb/specifications/blob/master/source/retryable-reads/retryable-reads.rst#unsupported-read-operations>`_
* See Retryable Writes' section on `Behavioral Changes for Write Commands <https://github.com/mongodb/specifications/blob/master/source/retryable-writes/retryable-writes.rst#behavioral-changes-for-write-commands>`_

Stable API
""""""""""

The command sent MUST attach stable API fields as configured on the MongoClient.

* See Stable API's section on `Generic Command Helper Behaviour <https://github.com/mongodb/specifications/blob/master/source/versioned-api/versioned-api.rst#generic-command-helper>`_

Client Side Operations Timeout
""""""""""""""""""""""""""""""

A driver's runCommand API MUST provide an optional ``timeoutMS`` option to support client side operations timeout.
Drivers MUST NOT attempt to check the command document for the presence of a ``maxTimeMS`` field.
Drivers MUST document the behavior of runCommand if a ``maxTimeMS`` field  is already set on the command (such as overwriting the command field).

* See Client Side Operations Timeout's section on `runCommand <https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst#runcommand>`_
* See Client Side Operations Timeout's section on `runCommand behavior <https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.rst#runcommand-behavior>`_

Changelog
=========

:2023-03-28: Add run command specification.

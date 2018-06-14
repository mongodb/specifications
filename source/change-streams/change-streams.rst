==============
Change Streams
==============

:Title: Change Streams
:Author: Matt Broadstone
:Advisory Group: David Golden, A. Jesse Jiryu Davis
:Approvers: Jeff Yemin, A. Jesse Jiryu Davis, Bernie Hackett, David Golden, Eliot
:Status: Accepted
:Type: Standards
:Minimum Server Version: 3.6
:Last Modified: December 13, 2017
:Version: 1.5.1

.. contents::

--------

Abstract
========

As of version 3.6 of the MongoDB server a new ``$changeStream`` pipeline stage is supported in the aggregation framework.  Specifying this stage first in an aggregation pipeline allows users to request that notifications are sent for all changes to a particular collection.  This specification defines the means for creating change streams in drivers, as well as behavior during failure scenarios.

Specification
=============

-----------
Definitions
-----------

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
-----

Resumable Error
^^^^^^^^^^^^^^^

An error is considered resumable if it meets any of the following criteria:

- any error encountered which is not a server error (e.g. a timeout error or
  network error)

- *any* server error response from a getMore command excluding those
  containing the following error codes

  .. list-table::
    :header-rows: 1

    * - Error Name
      - Error Code
    * - Interrupted
      - 11601
    * - CappedPositionLost
      - 136
    * - CursorKilled
      - 237

- a server error response with an error message containing the substring "not
  master" or "node is recovering"

An error on an aggregate command is not a resumable error. Only errors on a
getMore command may be considered resumable errors.

The criteria for resumable errors is similar to the discussion in the SDAM
spec's section on `Error Handling`_, but includes additional error codes. See
`What do the additional error codes mean?`_ for the reasoning behind these
additional errors.

.. _Error Handling: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#error-handling

--------
Guidance
--------

For naming and deviation guidance, see the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#naming>`_.

--------------------
Server Specification
--------------------

Response Format
---------------

If the aggregation with ``$changeStream`` specified completes successfully, the resultant stream will deliver documents in the following format:

.. code:: typescript

  {
    /**
     * The id functions as an opaque token for use when resuming an interrupted
     * change stream.
     */
    _id: Document;

    /**
     * Describes the type of operation represented in this change notification.
     */
    operationType: "insert" | "update" | "replace" | "delete" | "invalidate";

    /**
     * Contains two fields: “db” and “coll” containing the database and
     * collection name in which the change happened.
     */
    ns: Document;

    /**
     * Only present for ops of type ‘insert’, ‘update’, ‘replace’, and
     * ‘delete’.
     *
     * For unsharded collections this contains a single field, _id, with the
     * value of the _id of the document updated.  For sharded collections,
     * this will contain all the components of the shard key in order,
     * followed by the _id if the _id isn’t part of the shard key.
     */
    documentKey: Optional<Document>;

    /**
     * Only present for ops of type ‘update’.
     *
     * Contains a description of updated and removed fields in this
     * operation.
     */
    updateDescription: Optional<UpdateDescription>;

    /**
     * Always present for operations of type ‘insert’ and ‘replace’. Also
     * present for operations of type ‘update’ if the user has specified ‘updateLookup’
     * in the ‘fullDocument’ arguments to the ‘$changeStream’ stage.
     *
     * For operations of type ‘insert’ and ‘replace’, this key will contain the
     * document being inserted, or the new version of the document that is replacing
     * the existing document, respectively.
     *
     * For operations of type ‘update’, this key will contain a copy of the full
     * version of the document from some point after the update occurred. If the
     * document was deleted since the updated happened, it will be null.
     */
    fullDocument: Document | null;

  }

  class UpdateDescription {
    /**
     * A document containing key:value pairs of names of the fields that were
     * changed, and the new value for those fields.
     */
    updatedFields: Document;

    /**
     * An array of field names that were removed from the document.
     */
    removedFields: Array<String>;
  }

**NOTE:** The above format is provided for illustrative purposes, and is subject to change without warning.

----------
Driver API
----------

.. code:: typescript

  interface ChangeStream extends Iterable<Document> {
    /**
     * The resume token (_id) of the document the iterator last returned
     */
    private resumeToken: Document;

    /**
     * The pipeline of stages to append to an initial ``$changeStream`` stage
     */
    private pipeline: Array<Document>;

    /**
     * The options provided to the initial ``$changeStream`` stage
     */
    private options: ChangeStreamOptions;

    /**
     * The read preference for the initial change stream aggregation, used
     * for server selection during an automatic resume.
     */
    private readPreference: ReadPreference;
  }

  interface Collection {
    /**
     * @returns a change stream on a specific collection.
     */
    watch(pipeline: Document[], options: Optional<ChangeStreamOptions>): ChangeStream;
  }

  interface Database {
    /**
     * Allows a client to observe all changes in a database.
     * Excludes system collections.
     * @returns a change stream on all collections in a database
     * @since 4.0
     * @see https://docs.mongodb.com/manual/reference/system-collections/
     */
    watch(pipeline: Document[], options: Optional<ChangeStreamOptions>): ChangeStream;
  }

  interface MongoClient {
    /**
     * Allows a client to observe all changes in a cluster.
     * Excludes system collections.
     * Excludes the "config", "local", and "admin" databases.
     * @since 4.0
     * @returns a change stream on all collections in all databases in a cluster
     * @see https://docs.mongodb.com/manual/reference/system-collections/
     */
    watch(pipeline: Document[], options: Optional<ChangeStreamOptions>): ChangeStream;
  }

  class ChangeStreamOptions {
    /**
     * Allowed values: ‘default’, ‘updateLookup’.  Defaults to ‘default’.  When set to
     * ‘updateLookup’, the change notification for partial updates will include both
     * a delta describing the changes to the document, as well as a copy of the entire
     * document that was changed from some time after the change occurred.  For forward
     * compatibility, a driver MUST NOT raise an error when a user provides an unknown
     * value. The driver relies on the server to validate this option.
     *
     * @note this is an option of the `$changeStream` pipeline stage.
     */
    fullDocument: string = ‘default’;

    /**
     * Specifies the logical starting point for the new change stream.
     *
     * @note this is an option of the `$changeStream` pipeline stage.
     */
    resumeAfter: Optional<Document>;

    /**
     * The maximum amount of time for the server to wait on new documents to satisfy
     * a change stream query.
     *
     * This is the same field described in FindOptions in the CRUD spec.
     * @see https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read
     * @note this option is an alias for `maxTimeMS`, used on `getMore` commands
     * @note this is an aggregation command option
     */
    maxAwaitTimeMS: Optional<Int64>;

    /**
     * The number of documents to return per batch.
     *
     * This option is sent only if the caller explicitly provides a value. The
     * default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate
     * @note this is an aggregation command option
     */
    batchSize: Optional<Int32>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The
     * default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate
     * @note this is an aggregation command option
     */
    collation: Optional<Document>;

    /**
     * The change stream will only provides changes that occurred after the
     * specified timestamp. Any command run against the server will return
     * an operation time that can be used here. The default value is an
     * operation time obtained from the server before the change stream was created.
     * @since 4.0
     * @see https://docs.mongodb.com/manual/reference/method/db.runCommand/
     * @note this is an option of the `$changeStream` pipeline stage.
     */
    startAtOperationTime: Optional<Timestamp>;
  }

**NOTE:** The set of ``ChangeStreamOptions`` may grow over time.

Helper Method
-------------

The driver API consists of a ``ChangeStream`` type, as well as three helper methods. All helpers MUST return a ``ChangeStream`` instance. Implementers MUST document that helper methods are preferred to running a raw aggregation with a ``$changeStream`` stage, for the purpose of supporting resumability.

The helper methods must construct an aggregation command with a REQUIRED initial ``$changeStream`` stage.  A driver MUST NOT throw a custom exception if multiple ``$changeStream`` stages are present (e.g. if a user also passed ``$changeStream`` in the pipeline supplied to the helper), as the server will return an error.

The helper methods MUST determine a read concern for the operation in accordance with the `Read and Write Concern specification <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#via-code>`_.  The initial implementation of change streams on the server requires a “majority” read concern or no read concern.  Drivers MUST document this requirement.  Drivers SHALL NOT throw an exception if any other read concern is specified, but instead should depend on the server to return an error.

The stage has the following shape:

.. code:: typescript

  { $changeStream: ChangeStreamOptions }

The first parameter of the helpers specifies an array of aggregation pipeline stages which MUST be appended to the initial stage. Drivers MUST support an empty pipeline. Languages which support default parameters MAY specify an empty array as the default value for this parameter. Drivers SHOULD otherwise make specification of a pipeline as similar as possible to the `aggregate <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read>`_ CRUD method.

Additionally, implementors MAY provide a form of these methods which require no parameters, assuming no options and no additional stages beyond the initial ``$changeStream`` stage:

.. code:: python

  for change in db.collection.watch():
      print(change)

Presently change streams support only a subset of available aggregation stages:

- ``$match``
- ``$project``
- ``$addFields``
- ``$replaceRoot``
- ``$redact``

A driver MUST NOT throw an exception if any unsupported stage is provided, but instead depend on the server to return an error.

The aggregate helper methods MUST have no new logic related to the ``$changeStream`` stage. Drivers MUST be capable of handling `TAILABLE_AWAIT <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read>`_  cursors from the aggregate command in the same way they handle such cursors from find.

``Collection.watch`` helper
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a ``ChangeStream`` on a specific collection

Command syntax:

.. code:: typescript

    {
      aggregate: 'collectionName'
      pipeline: [{$changeStream: {...}}, ...],
      ...
    }

``Database.watch`` helper
^^^^^^^^^^^^^^^^^^^^^^^^^

:since: 4.0

Returns a ``ChangeStream`` on all collections in a database.

Command syntax:

.. code:: typescript

    {
      aggregate: 1
      pipeline: [{$changeStream: {...}}, ...],
      ...
    }

``MongoClient.watch`` helper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:since: 4.0

Returns a ``ChangeStream`` on all collections in all databases in a cluster

Command syntax:

.. code:: typescript

    {
      aggregate: 1
      pipeline: [{$changeStream: {allChangesForCluster: true, ...}}, ...],
      ...
    }

The helper MUST run the command against the `admin` database

ChangeStream
------------

A ``ChangeStream`` is an abstraction of a `TAILABLE_AWAIT <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read>`_ cursor, with support for resumability.  Implementors MAY choose to implement a ``ChangeStream`` as an extension of an existing tailable cursor implementation.  If the ``ChangeStream`` is implemented as a type which owns a tailable cursor, then the implementor MUST provide a method to close the change stream, as well as satisfy the requirements of extending ``Iterable<Document>``.

A change stream MUST track the last resume token returned by the iterator to the user, caching it locally for use in future attempts to resume.  A driver MUST raise an error on the first response received without a resume token (e.g. the user has removed it with a pipeline stage), and close the change stream.  The error message SHOULD resemble “Cannot provide resume functionality when the resume token is missing”.

A change stream MUST attempt to resume a single time if it encounters any resumable error.  A change stream MUST NOT attempt to resume on any other type of error, with the exception of a “not master” server error.  If a driver receives a “not master” error (for instance, because the primary it was connected to is stepping down), it will treat the error as a resumable error and attempt to resume.

In addition to tracking the most recently delivered resume token, change streams MUST also track the read preference specified when the change stream was created. In the event of a resumable error, a change stream MUST perform server selection with the original read preference before attempting to resume.

Single Server Topologies
^^^^^^^^^^^^^^^^^^^^^^^^

Presently, change streams cannot be initiated on single server topologies as they do not have an oplog.  Drivers MUST NOT throw an exception in this scenario, but instead rely on an error returned from the server.  This allows for the server to seamlessly introduce support for this in the future, without need to make changes in driver code.

startAtOperationTime
^^^^^^^^^^^^^^^^^^^^

:since: 4.0

``startAtOperationTime`` specifies that a change stream will only return changes that occurred at or after the specified ``Timestamp``.

The server expects ``startAtOperationTime`` as a BSON Timestamp

.. code:: typescript

    {
      ts: Timestamp;
    }

Drivers MUST allow users to specify a ``startAtOperationTime`` option in the ``Collection.watch`` and ``Database.watch`` helpers. They MUST allow users to specify this value as a raw ``Timestamp``.

``startAtOperationTime`` and ``resumeAfter`` are mutually exclusive; if both ``startAtOperationTime`` and ``resumeAfter`` are set, the server will return an error. Drivers MUST NOT throw a custom error, and MUST defer to the server error.

If neither ``startAtOperationTime`` nor ``resumeAfter`` are specified, and the max wire version is >= ``7`` drivers SHOULD set a default ``startAtOperationTime`` using the ``MongoClient`` field ``lastOperationTime`` (see `Causal Consistency <../causal-consistency/causal-consistency.rst#mongoclient-changes>`_.

If the ``lastOperationTime`` is not available, ``startAtOperationTime`` MAY be omitted. If this is the case, then the ``ChangeStream`` MUST save the ``operationTime`` value returned from the server in response to the initial aggregation call issued by the change stream.

resumeAfter
^^^^^^^^^^^

``resumeAfter`` is used to resume a changeStream that has been stopped to ensure that only changes starting with the log entry immediately *after* the provided token will be returned. If the resume token specified does not exist, the server will return an error. 

Resume Process
^^^^^^^^^^^^^^

Once a ``ChangeStream`` has encountered a resumable error, it MUST attempt to resume one time. The process for resuming MUST follow these steps:

- Perform server selection.
- Connect to selected server.
- If the ``ChangeStream`` has not received any changes, and ``resumeAfter`` is not specified, and the max wire version is >= ``7``:

    - The driver MUST execute the known aggregation command.
    - The driver MUST specify the ``startAtOperationTime`` key set to the original timestamp used in the initial aggregation command.
    - The driver MUST NOT set a ``resumeAfter`` key.
    - In this case, the ``ChangeStream`` will return all changes that occurred after the specified ``startAtOperationTime``.
- Else:

    - The driver MUST execute the known aggregation command.
    - The driver MUST specify a ``resumeAfter`` with the last known ``resumeToken``.
    - The driver MUST NOT set a ``startAtOperationTime``.
    - If a ``startAtOperationTime`` key was part of the original aggregation command, the driver MUST remove it.
    - In this case, the ``ChangeStream`` will return notifications starting with the oplog entry immediately *after* the provided token.

If the server supports sessions, the resume attempt MUST use the same session as the previous attempt's command.

A driver SHOULD attempt to kill the cursor on the server on which the cursor is opened during the resume process, and MUST NOT attempt to kill the cursor on any other server.


Notes and Restrictions
^^^^^^^^^^^^^^^^^^^^^^

**1. `fullDocument: updateLookup` can result in change documents larger than 16MB**

There is a risk that if there is a large change to a large document, the full document and delta might result in a document larger than the 16MB limitation on BSON documents.  If that happens the cursor will be closed, and a server error will be returned.

**2. Users can remove the resume token with aggregation stages**

It is possible for a user to specify the following stage:

.. code:: javascript

    { $project: { _id: 0 } }

Similar removal of the resume token is possible with the ``$redact`` and ``$replaceRoot`` stages.  While this is not technically illegal, it makes it impossible for drivers to support resumability.  Users may explicitly opt out of resumability by issuing a raw aggregation with a ``$changeStream`` stage.

Rationale
=========

-------------------
Why Helper Methods?
-------------------

Change streams are a first class concept similar to CRUD or aggregation; the fact that they are initiated via an aggregation pipeline stage is merely an implementation detail.  By requiring drivers to support top-level helper methods for this feature we not only signal this intent, but also solve a number of other potential problems:

Disambiguation of the result type of this special-case aggregation pipeline (``ChangeStream``), and an ability to control the behaviors of the resultant cursor

More accurate support for the concept of a maximum time the user is willing to wait for subsequent queries to complete on the resultant cursor (``maxAwaitTimeMs``)

Finer control over the options pertaining specifically to this type of operation, without polluting the already well-defined ``AggregateOptions``

Flexibility for future potentially breaking changes for this feature on the server

------------------------------------------------------------------
Why are ChangeStreams required to retry once on a resumable error?
------------------------------------------------------------------

User experience is of the utmost importance. Errors not originating from the server are generally network errors, and network errors can be transient.  Attempting to resume an interrupted change stream after the initial error allows for a seamless experience for the user, while subsequent network errors are likely to be an outage which can then be exposed to the user with greater confidence.

---------------------------------------------------
Why do we allow access to the resume token to users
---------------------------------------------------

Imagine a scenario in which a user wants to process each change to a collection **at least once**, but the application crashes during processing.  In order to overcome this failure, a user might use the following approach:

.. code:: python

  resumeToken = None
  localChange = getChangeFromLocalStorage()
  if localChange:
    processChange(localChange)
    resumeToken = localChange['_id']

  try:
      for change in db.collection.watch([...], resumeAfter=resumeToken):
          persistToLocalStorage(change)
          processChange(change)
  except Exception:
      log.error("...")

In this case the current change is always persisted locally, including the resume token, such that on restart the application can still process the change while ensuring that the change stream continues from the right logical time in the oplog.  It is the application's responsibility to ensure that ``processChange`` is idempotent, this design merely makes a reasonable effort to process each change **at least** once.

-------------------------------------------------------
Why is there no example of the desired user experience?
-------------------------------------------------------

The specification used to include this overspecified example of the "desired user experience":

.. code:: python

  try:
      for change in db.collection.watch(...):
          print(change)
  except Exception:
      # We know for sure it's unrecoverable:
      log.error("...")

It was decided to remove this example from the specification for the following reasons:

- Tailable + awaitData cursors behave differently in existing supported drivers.
- There are considerations to be made for languages that do not permit interruptible I/O (such as Java), where a change stream which blocks forever in a separate thread would necessitate killing the thread.
- There is something to be said for an API that allows cooperation by default. The model in which a call to next only blocks until any response is returned (even an empty batch), allows for interruption and cooperation (e.g. interaction with other event loops).

----------------------------------------
What do the additional error codes mean?
----------------------------------------

The `CursorKilled` or `Interrupted` error implies implies some other actor killed the cursor.

The `CappedPositionLost` error implies falling off of the back of the oplog,
so resuming is impossible.

-----------------------------------------------------------------------------------------
Why do we need to send a default ``startAtOperationTime`` in the ``$changeStream`` stage?
-----------------------------------------------------------------------------------------

``startAtOperationTime`` allows a user to create a change stream that does not return
results until a later point in time. However, it has the added benefit of allowing
a change stream to resume and receive all changes that it may have missed since it's first
creation.

For example:

- A client creates a ``ChangeStream``, and calls ``watch``
- The ``ChangeStream`` sends out the initial ``aggregate`` call, and receives a response
with no initial values.
- The client's network is partitioned from the server, causing the client's ``getMore`` to time out
- Changes occur on the server.
- The network is unpartitioned
- The client attempts to resume the ``ChangeStream``

In the above example, not sending ``startAtOperationTime`` will result in the change stream missing
the changes that occurred while the server and client are partitioned. By sending ``startAtOperationTime``,
the server will know to include changes from that previous point in time.

Test Plan
=========

See `tests/README.rst <tests/README.rst>`_

Backwards Compatibility
=======================

There should be no backwards compatibility concerns.


Reference Implementations
=========================

 - NODE (NODE-1055)
 - PYTHON (PYTHON-1338)
 - RUBY (RUBY-1228)

Changelog
=========
+------------+------------------------------------------------------------+
| 2017-08-03 | Initial commit                                             |
+------------+------------------------------------------------------------+
| 2017-08-07 | Fixed typo in command format                               |
+------------+------------------------------------------------------------+
| 2017-08-16 | Added clarification regarding Resumable errors             |
+------------+------------------------------------------------------------+
| 2017-08-16 | Fixed formatting of resume process                         |
+------------+------------------------------------------------------------+
| 2017-08-22 | Clarified killing cursors during resume process            |
+------------+------------------------------------------------------------+
| 2017-09-06 | Remove `desired user experience` example                   |
+------------+------------------------------------------------------------+
| 2017-09-21 | Clarified that we need to close the cursor on missing token|
+------------+------------------------------------------------------------+
| 2017-09-26 | Clarified that change stream options may be added later    |
+------------+------------------------------------------------------------+
| 2017-11-06 | Defer to Read and Write concern spec for determining a read|
|            | concern for the helper method.                             |
+------------+------------------------------------------------------------+
| 2017-12-13 | Default read concern is also accepted, not just "majority".|
+------------+------------------------------------------------------------+
| 2018-04-17 | Clarified that the initial aggregate should not be retried.|
+------------+------------------------------------------------------------+
| 2018-04-18 | Added helpers for Database and MongoClient,                |
|            | and added ``startAtClusterTime`` option.                   |
+------------+------------------------------------------------------------+
| 2018-05-24 | Changed ``startatClusterTime`` to ``startAtOperationTime`` |
+------------+------------------------------------------------------------+

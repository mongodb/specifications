.. role:: javascript(code)
  :language: javascript

=======================================
Find, getMore and killCursors commands.
=======================================

:Spec: 137
:Version: 1.3
:Title: Find, getMore and killCursors commands
:Author: Christian Kvalheim
:Lead: Christian Kvalheim
:Advisors: \Anna Herlihy, Robert Stam
:Status: Accepted
:Type: Standards
:Minimum Server Version: 3.2
:Last Modified: October 21, 2015

.. contents::

Abstract
========

The Find, GetMore and KillCursors commands in MongoDB 3.2 or later replace the use of the legacy OP_QUERY, OP_GET_MORE and OP_KILL_CURSORS wire protocol messages. This specification lays out how drivers should interact with the new commands when compared to the legacy wire protocol level messages.

Definitions
===========

Meta
----

The keywords "MUST", “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119`_.

.. _RFC 2119: https://www.ietf.org/rfc/rfc2119.txt

Terms
-----

Document
^^^^^^^^

::

  The term Document refers to the implementation in the driver's language of a BSON document.

Command
^^^^^^^

::

  A BSON document containing the fields making up a MongoDB server command.

Wire Protocol
^^^^^^^^^^^^^

::

  The binary protocol used to talk with MongoDB over a socket. It’s made up by the OP_QUERY, OP_GET_MORE, OP_KILL_CURSORS, OP_INSERT, OP_UPDATE and OP_DELETE.

Guidance
========

Documentation
-------------

The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.

The CRUD API MUST be implemented using the find, getMore and optionally killCursors commands if the **isMaster** command returns **maxWireVersion >= 4**.

Commands
========

find
----

The **find** command replaces the query functionality of the OP_QUERY wire protocol message but cannot execute queries against special collections. Unlike the legacy OP_QUERY wire protocol message, the **find** command cannot be used to execute other commands.

.. code:: javascript

    {
      "find": <string>,
      "filter": { ... },
      "sort": { ... },
      "projection": { ... },
      "hint": { ... }|<string>,
      "skip": <int64>,
      "limit": <int64>,
      "batchSize": <int64>,
      "singleBatch": <bool>,
      "comment": <string>,
      "maxScan": <int32>,
      "maxTimeMS": <int32>,
      "max": { ... },
      "min": { ... },
      "returnKey": <bool>,
      "showRecordId": <bool>,
      "snapshot": <bool>,
      "tailable": <bool>,
      "oplogReplay": <bool>,
      "noCursorTimeout": <bool>,
      "awaitData": <bool>,
      "allowPartialResults": <bool>,
      "readConcern": { ...}
    }

The accepted parameters are described in the table below.  Parameters marked "Req" are required by the server and MUST be included in the command.  Parameters marked "Def" define the default values assumed by the server if the parameter is omitted].

.. list-table:: Find command parameters
   :widths: 15 15 15 15 15 30
   :header-rows: 1

   * - Parameter
     - Req
     - Def.
     - Type
     - CRUD API Mapping
     - Description
   * - find
     - X
     -
     - String
     -
     - Its argument MUST be a string specifying the name of the collection
   * - filter
     - X
     -
     - Doc.
     - filter
     - The query predicate.
   * - sort
     -
     -
     - Doc.
     - FindOptions.sort
     - If specified, then the result set will be sorted accordingly. The document is in expected to be in ordered form.
   * - projection
     -
     -
     - Doc.
     - FindOptions.projection
     - If provided it specifies the inclusion or exclusion of fields in the returned documents.
   * - hint
     -
     -
     - Doc.
       String
     - modifiers.$hint
     - If specified, then the query system will only consider plans using the hinted index.

       If the driver provides a document, it takes the following format

       { field1: <-1/1>, ... fieldN: <-1/1> }

       If the driver provides a string, it is the name of the index to use as the hint.  For an index specification {a: 1} this might take the form of the string a_1.
   * - skip
     -
     - 0
     - int64
     - FindOptions.skip
     - Specifies the starting point for the returned documents.
   * - limit
     -
     -
     - int64
     - FindOptions.limit
     - A limit of 0 has the same meaning as the absence of a limit.
   * - batchSize
     -
     -
     - int64
     - FindOptions.batchSize
     - batchSize specifies the maximum number of documents returned in a find or getMore command.
   * - singleBatch
     -
     - false
     - Bool
     -
     - If true, then the server will return a single batch up to the maximum server message size, and then close the ClientCursor. The client cannot issue any OP_GET_MORE messages or getMore commands.
   * - comment
     -
     -
     - String
     - FindOptions.comment
     - The comment meta-operator makes it possible to attach a comment to a query.
   * - maxScan
     -
     -
     - Int32 >= 0
     - modifiers.$maxScan
     - Constrains the query to only scan the specified number of documents when fulfilling the query.
   * - maxTimeMS
     -
     -
     - Int32 >= 0
     - FindOptions.maxTimeMS
     - Specifies a cumulative time limit in milliseconds for processing operations on the cursor
   * - max
     -
     -
     - Doc.
     - modifiers.$max
     - Specify a max value to specify the exclusive upper bound for a specific index in order to constrain the results of find(). The max specifies the upper bound for all keys of a specific index in order.

       The specified document takes the form of

       { field1: <max value>, ... fieldN: <max valueN> }
   * - min
     -
     -
     - Doc.
     - modifiers.$min
     - Specify a min value to specify the inclusive lower bound for a specific index in order to constrain the results of find(). The min specifies the lower bound for all keys of a specific index in order.

       The specified document takes the form of

       { field1: <min value>, ... fieldN: <min valueN> }
   * - returnKey
     -
     -
     - Bool
     - modifiers.$returnKey
     - Only return the index field or fields for the results of the query. If returnKey is set to true and the query does not use an index to perform the read operation, the returned documents will not contain any fields.
   * - showRecordId
     -
     -
     - Bool
     - modifiers.$showDiskLoc
     - The showRecordId field returns the internal MongoDB record id for each document returned by the query.
   * - snapshot
     -
     -
     - Bool
     - modifiers.$snapshot
     - The snapshot operator prevents the cursor from returning a document more than once because an intervening write operation.
   * - tailable
     -
     -
     - Bool
     - Set if FindOptions.cursorType is either CursorType.TAILABLE or CursorType.TAILABLE_AWAIT
     - Specify that find command MUST return a tailable cursor.

       Can only only be used if the find command is operating over a capped collections.
   * - oplogReplay
     -
     -
     - Bool
     - FindOptions.oplogReply
     - Internal replication use only.
   * - noCursorTimeout
     -
     -
     - Bool
     - FindOptions.noCursorTimeout
     - The server normally times out idle cursors after an inactivity period (10 minutes) to prevent excess memory use. Set this option to prevent that.
   * - awaitData
     -
     -
     - Bool
     - Set if FindOptions.cursorType is CursorType.TAILABLE_AWAIT
     - If True awaitData MUST have tailable. maxTimeMS on getMore can be used to control the amount of time the cursor waits for new documents before returning an empty result.
   * - allowPartialResults
     -
     -
     - Bool
     - FindOptions.allowPartialResults
     - Get partial results from a mongos if some shards are down (instead of throwing an error).

       Drivers MUST NOT send this field if the topology type is not 'Sharded'
   * - readConcern
     -
     -
     - Doc
     - N/A

       MAY be set on CRUD specification (see readConcern specification for details)
     - Allows driver to specify if the query should be performed against a specific snapshot view of the documents in a collection. (N.B. this is not the same as the "snapshot" option, above.)

       The readConcern option takes the following document specification.
       {
         level: "[majority|local]",
       }

       level: “local” is the default, if no level is explicitly specified.
       level: “local” means to do a read with no snapshot; this is the behavior of reads in 3.0 and prior versions of MongoDB.
       level: “majority” means to do a read from the latest committed snapshot known to the server  (which could be stale).


For a successful command, the document returned from the server has the following format:

.. code:: javascript

    {
      "cursor": {
        "id": <int64>,
        "ns": <string>,
        "firstBatch": [
          ...
        ]
      },
      "ok": 1
    }

Special Collection names
^^^^^^^^^^^^^^^^^^^^^^^^

The find command **does not support querying on system collections**, so if drivers are using any system collections instead of the inprog, killop, unlock, etc. commands they SHOULD default to using the old-style OP_QUERY.

Any driver that provides helpers for any of the special collections below SHOULD use the replacement commands if **ismaster.maxWireVersion >= 4** or higher.

.. list-table:: Special Collection Names
   :widths: 15 30
   :header-rows: 1

   * - Special collection name
     - Replacement Command
   * - $cmd.sys.inprog
     - currentOp
   * - $cmd.sys.unlock
     - fsyncUnlock
   * - <database>.system.indexes
     - listIndexes
   * - <database>.system.namespaces
     - listCollections

Exhaust
^^^^^^^

The **find** command does not support the exhaust flag from **OP_QUERY**. Drivers that support exhaust MUST fallback to existing **OP_QUERY** wire protocol messages.

Interactions with OP_QUERY
^^^^^^^^^^^^^^^^^^^^^^^^^^

When sending a find operation as a find command rather than a legacy **OP_QUERY** find only the **slaveOk** flag is honored of the flags available in the **flag** field on the wire protocol.

For the **find**, **getMore** and **killCursors** commands the **numberToReturn** field SHOULD be -1. To execute **find** commands against a secondary the driver MUST set the **slaveOk** bit for the **find** command to successfully execute.

The **slaveOk** flag SHOULD not be set for all follow-up **getMore** and **killCursors** commands. The cursor on the server keeps the original **slaveOk** value first set on the **find** command.

More detailed information about the interaction of the **slaveOk** with **OP_QUERY** can be found in the Server Selection Spec `Passing a Read Preference`_.

.. _Passing a Read Preference: https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#passing-read-preference-to-mongos

Behavior of Limit, skip and batchSize
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The new **find** command has different semantics to the existing 3.0 and earlier **OP_QUERY** wire protocol message. The **limit** field is a hard limit on the total number of documents returned by the cursor no matter what **batchSize** is provided.

Once the limit on the cursor has been reached the server will destroy the cursor and return a **cursorId** of **0** in the **OP_REPLY**. This differs from existing **OP_QUERY** behavior where there is no server side concept of limit and where the driver **MUST** keep track of the limit on the client side and **MUST** send a **OP_KILLCURSORS** wire protocol message when it limit is reached.

When setting the **batchSize** on the **find** and **getMore** command the value MUST be based on the cursor limit calculations specified in the `CRUD`_ specification. 

In the following example the **limit** is set to **4** and the **batchSize** is set to **3** the following commands are executed.

.. code:: javascript

    {find: ..., batchSize:3}
    {getMore: ..., batchSize:1}

.. _CRUD: https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#id16

If there are not enough documents in the cursor to fulfill the **limit** defined, the cursor runs to exhaustion and is closed, returning a cursorId of 0 to the client.

Below are are some examples of using **limit**, **skip** and **batchSize**.

We have 100 documents in the collection **t**. We execute the following **find** command in the shell.

.. code:: javascript

    var b = db.runCommand({find:"t", limit:20, batchSize:10});

    db.runCommand({getMore:b.cursor.id, collection:"t", batchSize:20});

The **find** command executes and returns the first 10 results. The **getMore** command returns the final 10 results reaching the **limit** of 20 documents.

The **skip** option works in the same way as the current **OP_QUERY** starting the cursor after skipping **n** number of documents of the query.

.. code:: javascript

    var b = db.runCommand({find:"t", limit:20, batchSize:10, skip:85});

    db.runCommand({getMore:b.cursor.id, collection:"t", batchSize:20});

The **find** command returns the documents 86-95 and the **getMore** returns the last 5 documents.

Mapping OP_QUERY behavior to the find command limit and batchSize fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The way that limit, batchSize and singleBatch are defined for the find command differs from how these were specified in OP_QUERY and the CRUD spec.  The following  mappings from legacy definitions MUST be performed for the find command.

.. list-table:: Limit and batchSize
   :widths: 15 15 30
   :header-rows: 1

   * - Value
     - Translates to
     - Description
   * - limit < 0
     - limit = Math.abs(limit)
       singleBatch = true
     - Negative values for limit is not allowed
   * - limit == 0
     - Omit limit from command
     - Returns all document available for the query.
   * - limit > 0
     - N/A
     -
   * - batchSize < 0
     - batchSize = Math.abs(batchSize)
       singleBatch= true
     - Negative values for batchSize is not allowed
   * - batchSize == 0
     - Omit batchSize from command
     - Allow server to apply the default batchSize.
   * - batchSize > 0
     - N/A
     -

Special handling of limit < 0 and batchSize < 0
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If both **limit** and **batchSize** are negative the values should be handled in the following way.

.. list-table:: Limit and batchSize both negative
   :widths: 15 15 30
   :header-rows: 1

   * - Value
     - Translates to
     - Description
   * - limit <= batchSize
     - limit = Math.abs(limit)
       batchSize = Math.abs(limit)
       singleBatch = true
     - No special treatment needed
   * - limit > batchSize
     - limit = Math.abs(limit)
       batchSize = Math.abs(limit)
       singleBatch = true
     - No special treatment needed

BatchSize of 1
^^^^^^^^^^^^^^

In 3.2 a batchSize of 1 means return a single document for the find command and it will not destroy the cursor after the first batch of documents are returned. Given a query returning 4 documents the number of commands issues will be.

1. **find** command with batchSize=1
2. **getMore** command with batchSize=1
3. **getMore** command with batchSize=1
4. **getMore** command with batchSize=1

The driver **SHOULD NOT attempt to emulate the behavior seen in 3.0 or earlier** as the new find command enables the user expected behavior of allowing the first result to contain a single document when specifying batchSize=1.

Tailable cursors
^^^^^^^^^^^^^^^^

Tailable cursors have some fundamental changes compared to the existing **OP_QUERY** implementation. To create a tailable cursor you execute the following command:

.. code:: javascript

    var b = db.runCommand({ find:"t", tailable: true });

To create a tailable cursor with **tailable** and **awaitData**, execute the following command:

.. code:: javascript

    var b = db.runCommand({ find:"t", tailable: true, awaitData: true });

If **maxTimeMS** is not set in FindOptions, the driver SHOULD refrain from setting **maxTimeMS** on the **find** or **getMore** commands issued by the driver and allow the server to use its internal default value for **maxTimeMS**.

Semantics of maxTimeMS for a Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the case of  a **non-tailable cursor query** OR **a tailable cursor query with awaitData == false**, the driver MUST set maxTimeMS on the **find** command and MUST NOT set maxTimeMS on the **getMore** command.

In the case of **a tailable cursor with awaitData == true** the driver MUST provide a Cursor level option named **maxAwaitTimeMS** (See CRUD specification for details). The **maxTimeMS** option on the **getMore** command MUST be set to the value of the option **maxAwaitTimeMS**. If no **maxAwaitTimeMS** is specified, the driver SHOULD not set **maxTimeMS** on the **getMore** command. 

getMore
-------

The **getMore** command replaces the **OP_GET_MORE** wire protocol message. The query flags passed to OP_QUERY for a getMore command MUST be slave_ok=True when sent to a secondary. The OP_QUERY namespace MUST be the same as for the **find** and **killCursors** commands. The command takes the following object.

.. code:: javascript

    {
      "getMore": <int64>,
      "collection": <string>,
      "batchSize": <int64>,
      "maxTimeMS": <int32>
    }

The accepted parameters are described in the table below.

.. list-table:: getMore command parameters
   :widths: 15 15 15 30
   :header-rows: 1

   * - Parameter
     - Req
     - Type
     - Description
   * - getMore
     - X
     - int64
     - Specifies the cursorid of the ClientCursor that this getMore should exercise.
   * - collection
     - X
     - String
     - The name of the collection on which the query is operating.
   * - batchSize
     - X
     - Int32
     - Indicates how many results should be returned in the next batch to the client. Errors if zero or negative.
   * - maxTimeMS
     -
     - Int32
     - If not set, the server defaults to it’s internal maxTimeMS setting.

       Please see the "Semantics of maxTimeMS" section for more details.

The **batchSize** MUST be an int32 larger than 0. If **batchSize** is equal to 0 it must be omitted. If **batchSize** is less than 0 it must be turned into a positive integer using **Math.abs** or equivalent function in your language.

On success, the getMore command will return the following:

.. code:: javascript

    {
      "cursor": {
        "id": <int64>,
        "ns": <string>,
        "nextBatch": [
          ...
        ]
      },
      "ok": 1
    }

killCursors
-----------

The **killCursors** command replaces the **OP_KILL_CURSORS** wire protocol message. The OP_QUERY namespace MUST be the same as for the **find** and **getMore** commands. The **killCursors** command is optional to implement in **MongoDB 3.2**.

.. code:: javascript

    {
      "killCursors": <string>,
      "cursors": [
        <cursor id 1>
        <cursor id 2>,
        …
        <cursor id n>
      ]
    }

The accepted parameters are described in the table below. The query flags passed to OP_QUERY for a killCursors command MUST be slave_ok=True when sent to a secondary.

.. list-table:: killCursors command parameters
   :widths: 15 15 15 30
   :header-rows: 1

   * - Parameter
     - Req
     - Type
     - Description
   * - killCursors
     - X
     - String
     - The collection name used in the find command that created this cursor.
   * - cursors
     - X
     - Array of int64’s
     - An array of one or more cursorId’s

The command response will be as follows:

.. code:: javascript

    {
      "cursorsKilled": [
        <cursor id 1>
        <cursor id 2>,
        …
        <cursor id n>
      ],
      "cursorsNotFound": [
        <cursor id 1>
        <cursor id 2>,
        …
        <cursor id n>
      ],
      "cursorsAlive": [
        <cursor id 1>
        <cursor id 2>,
        …
        <cursor id n>
      ],
      ok: 1
    }

The **cursorsAlive** array contain cursors that were not possible to kill. The information SHOULD be ignored by the driver.

Difference from 3.0 OP_KILL_CURSORS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One of the differences with the new **killCursors** command compared to the **OP_KILL_CURSORS** wire protocol message is that the **killCursors** command returns a response while the **OP_KILL_CURSORS** wire protocol does not.

The **OP_REPLY** message has the following general structure.

.. code:: javascript

    struct {
        int32     messageLength;  // total message size, including
                                  // this

        int32     requestID;      // identifier for this message

        int32     responseTo;     // requestID from the original
                                  // request(used in reponses from db)

        int32     opCode;         // request type - see table below

        int32     responseFlags;  // bit vector - see details below

        int64     cursorID;       // cursor id if client needs to do
                                  // get more's

        int32     startingFrom;   // where in the cursor this reply is
                                  // starting

        int32     numberReturned; // number of documents in the reply

        document* documents;      // documents
    }

For the **find**, **getMore** and **killCursors** MongoDB returns a single document meaning **numberReturned** is set to **1**. This is in contrast to MongoDB 3.0 and earlier where a **OP_QUERY** query will set **numberReturned** to >= 0.

A driver MUST deserialize the command result and extract the **firstBatch** and **nextBatch** arrays for the **find** and **getMore** commands to access the returned documents.

The result from the **killCursors** command MAY be safely ignored.

If the driver supports returning **raw** BSON buffers instead of deserialized documents there might be a need to be able to partially deserialize documents to be able to efficiently provide the behavior in comparison to existing **OP_QUERY** queryresults.

Errors
======

The **find** and **getMore** commands will report errors using the standard mechanism: an "ok: 0" field paired with “errmsg” and “code” fields. See below for example error responses:

.. code:: shell

    > db.runCommand({find: "t", sort: {padding: -1}})

.. code:: javascript

    {
      "errmsg" : "exception: Executor error: Overflow sort stage buffered data usage of 41630570 bytes exceeds internal limit of 33554432 bytes",
      "code" : 28616,
      "ok" : 0
    }

.. code:: shell

    > db.runCommand({find: "t", foo: "bar"})

.. code:: javascript

    {
      "ok" : 0,
      "errmsg" : "Failed to parse: { find: \"t\", foo: \"bar\" }. Unrecognized field 'foo'.",
      "code" : 2
    }

Like other commands, the find and getMore commands will not use the OP_REPLY response flags. `OP_REPLY Documentation`_

.. _OP_REPLY Documentation: http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-reply

FAQ
===

Changes in error handling for 3.2 tailable cursor
-------------------------------------------------

Tailable cursors pointing to documents in a capped collection that get overwritten will return a zero document result in MongoDB 3.0 or earlier but will return an error in MongoDB 3.2

Explain command
---------------

There is no equivalent of the $explain modifier in the find command. The driver MUST use the **explain** command. Information about the command can be found in the `Explain command reference`_.

.. _Explain command reference: http://docs.mongodb.org/manual/reference/command/explain/

ReadPreference and Mongos
-------------------------

The **find** command does not include a readPreference field. To pass a readPreference to a **mongos** use the **$readPreference** field and format your command as.

.. code:: javascript

    {$query: {find: ‘.....}, $readPreference: {}}

This format is general for all commands when executing against a Mongos proxy.

More in depth information about passing read preferences to Mongos can be found in the Server Selection Specification `Server Selection Specification`_.

.. _Server Selection Specification: https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#passing-read-preference-to-mongos

Changes
=======
2015-09-30 slaveOk flag must be set to true on **getMore** and **killCursors** commands to make drivers have same behavior as for OP_GET_MORE and OP_KILL_CURSORS.

2015-10-13 added guidance on batchSize values as related to the **getMore** command. SlaveOk flag SHOULD not be set on getMore and killCursors commands. Introduced maxAwaitTimeMS option for setting maxTimeMS on getMore commands when the cursor is a tailable cursor with awaitData set.

2015-10-21 If no **maxAwaitTimeMS** is specified, the driver SHOULD not set **maxTimeMS** on the **getMore** command. 

2016-08-15 Changed $explain modifier to MUST use explain command from SHOULD.

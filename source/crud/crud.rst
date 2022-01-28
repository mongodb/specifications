.. role:: javascript(code)
  :language: javascript

===============
Driver CRUD API
===============

:Spec: 110
:Title: Driver CRUD API
:Authors: Craig Wilson
:Advisors: Jeremy Mikola, Jeff Yemin
:Status: Approved
:Type: Standards
:Minimum Server Version: 2.6
:Last Modified: 2022-01-??

.. contents::

--------

Abstract
========

The CRUD API defines a set of related methods and structures defining a driver's API. As not all languages/frameworks have the same abilities, parts of the spec may or may not apply. These sections have been called out.


Specification
=============

This specification is about `Guidance`_ in 3 areas related to the CRUD API as well as a specification for the API itself. It does not define implementation details and provides room and flexibility for the idioms and differences in languages and frameworks.


-----------
Definitions
-----------

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.


Terms
-----

Collection
  The term ``interface Collection`` will be seen in most of the sections. Each driver will likely have a class or interface defined for the concept of a collection. Operations appearing inside the ``interface Collection`` are required operations to be present on a driver's concept of a collection.

Iterable
  The term ``Iterable`` will be seen as a return type from some of the `Read`_ methods. Its use is as that of a sequence of items. For instance, ``collection.find({})`` returns a sequence of documents that can be iterated over.


--------
Guidance
--------

Documentation
-------------

The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.


Operations
----------

All drivers MUST offer the operations defined in the following sections. This does not preclude a driver from offering more.


Operation Parameters
--------------------

All drivers MUST offer the same options for each operation as defined in the following sections. This does not preclude a driver from offering more. A driver SHOULD NOT require a user to specify optional parameters, denoted by the Optional<> signature. Unless otherwise specified, optional values should not be sent to the server.

~~~~~~~~~~
Deviations
~~~~~~~~~~

A non-exhaustive list of acceptable deviations are as follows:

* Using named parameters instead of an options hash. For instance, ``collection.find({x:1}, sort: {a: -1})``.

* When using an ``Options`` class, if multiple ``Options`` classes are structurally equatable, it is permissible to consolidate them into one with a clear name. For instance, it would be permissible to use the name ``UpdateOptions`` as the options for ``UpdateOne`` and ``UpdateMany``.

* Using a fluent style builder for find or aggregate:

  .. code:: typescript

    collection.find({x: 1}).sort({a: -1}).skip(10);

  When using a fluent-style builder, all options should be named rather than inventing a new word to include in the pipeline (like options). Required parameters are still required to be on the initiating method.

  In addition, it is imperative that documentation indicate when the order of operations is important. For instance, skip and limit in find is order irrelevant where skip and limit in aggregate is not.


Naming
------

All drivers MUST name operations, objects, and parameters as defined in the following sections.

Deviations are permitted as outlined below.


~~~~~~~~~~
Deviations
~~~~~~~~~~

When deviating from a defined name, an author should consider if the altered name is recognizable and discoverable to the user of another driver.

A non-exhaustive list of acceptable naming deviations are as follows:

* Using "batchSize" as an example, Java would use "batchSize" while Python would use "batch_size". However, calling it "batchCount" would not be acceptable.
* Using "maxTimeMS" as an example, .NET would use "MaxTime" where it's type is a TimeSpan structure that includes units. However, calling it "MaximumTime" would not be acceptable.
* Using "FindOptions" as an example, Javascript wouldn't need to name it while other drivers might prefer to call it "FindArgs" or "FindParams". However, calling it "QueryOptions" would not be acceptable.
* Using "isOrdered" rather than "ordered". Some languages idioms prefer the use of "is", "has", or "was" and this is acceptable.


Timeouts
--------

Drivers MUST enforce timeouts for all operations per the `Client Side
Operations Timeout
<../client-side-operations-timeout/client-side-operations-timeout.rst>`__
specification. All operations that return cursors MUST support the timeout
options documented in the `Cursors
<../client-side-operations-timeout/client-side-operations-timeout.rst#Cursors>`__
section of that specification.

---
API
---

Read
----

.. note::

    The term Iterable<T> is used below to indicate many of T. This spec is flexible on what that means as different drivers will have different requirements, types, and idioms.

.. code:: typescript

  interface Collection {

    /**
     * Runs an aggregation framework pipeline.
     *
     * Note: $out and $merge are special pipeline stages that cause no results
     * to be returned from the server. As such, the iterable here would never
     * contain documents. Drivers MAY setup a cursor to be executed upon
     * iteration against the output collection such that if a user were to
     * iterate the return value, results would be returned.
     *
     * Note: result iteration should be backed by a cursor. Depending on the implementation,
     * the cursor may back the returned Iterable instance or an iterator that it produces.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    aggregate(pipeline: Document[], options: Optional<AggregateOptions>): Iterable<Document>;

    /**
     * Gets the number of documents matching the filter.
     *
     * **This method is DEPRECATED and should not be implemented in new drivers.**
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
       @deprecated 4.0
     */
    count(filter: Document, options: Optional<CountOptions>): Int64;

    /**
     * Count the number of documents in a collection that match the given
     * filter. Note that an empty filter will force a scan of the entire
     * collection. For a fast count of the total documents in a collection
     * see estimatedDocumentCount.
     *
     * See "Count API Details" section below.
     */
    countDocuments(filter: Document, options: Optional<CountOptions>): Int64;

    /**
     * Gets an estimate of the count of documents in a collection using collection metadata.
     *
     * See "Count API Details" section below.
     */
    estimatedDocumentCount(options: Optional<EstimatedDocumentCountOptions>): Int64;

    /**
     * Finds the distinct values for a specified field across a single collection.
     *
     * Note: the results are backed by the "values" array in the distinct command's result
     * document. This differs from aggregate and find, where results are backed by a cursor.
     *
     * @see https://docs.mongodb.com/manual/reference/command/distinct/
     */
    distinct(fieldName: string, filter: Document, options: Optional<DistinctOptions>): Iterable<any>;

    /**
     * Finds the documents matching the model.
     *
     * Note: The filter parameter below equates to the $query meta operator. It cannot
     * contain other meta operators like $maxScan. However, do not validate this document
     * as it would be impossible to be forwards and backwards compatible. Let the server
     * handle the validation.
     *
     * Note: If $explain is specified in the modifiers, the return value is a single
     * document. This could cause problems for static languages using strongly typed entities.
     *
     * Note: result iteration should be backed by a cursor. Depending on the implementation,
     * the cursor may back the returned Iterable instance or an iterator that it produces.
     *
     * @see https://docs.mongodb.com/manual/core/read-operations-introduction/
     */
    find(filter: Document, options: Optional<FindOptions>): Iterable<Document>;

  }

  interface Database {

    /**
     * Runs an aggregation framework pipeline on the database for pipeline stages
     * that do not require an underlying collection, such as $currentOp and $listLocalSessions.
     *
     * Note: result iteration should be backed by a cursor. Depending on the implementation,
     * the cursor may back the returned Iterable instance or an iterator that it produces.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/#dbcmd.aggregate
     */
    aggregate(pipeline: Document[], options: Optional<AggregateOptions>): Iterable<Document>;

  }

  class AggregateOptions {

    /**
     * Enables writing to temporary files. When set to true, aggregation stages
     * can write data to the _tmp subdirectory in the dbPath directory.
     *
     * This option is sent only if the caller explicitly provides a value. The default
     * is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    allowDiskUse: Optional<Boolean>;

    /**
     * The number of documents to return per batch.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * If specified, drivers SHOULD apply this option to both the original aggregate command and subsequent
     * getMore operations on the cursor.
     *
     * Drivers MUST NOT specify a batchSize of zero in an aggregate command that includes an $out or $merge stage,
     * as that will prevent the pipeline from executing. Drivers SHOULD leave the cursor.batchSize command option
     * unset in an aggregate command that includes an $out or $merge stage.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    batchSize: Optional<Int32>;

    /**
     * If true, allows the write to opt-out of document level validation. This only applies
     * when the $out or $merge stage is specified.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    collation: Optional<Document>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * The maximum amount of time for the server to wait on new documents to satisfy a tailable cursor
     * query.
     *
     * This options only applies to aggregations which return a TAILABLE_AWAIT cursor. Drivers
     * SHOULD always send this value, if the cursor is not a TAILABLE_AWAIT cursor the server will
     * ignore it.
     *
     * @note this option is an alias for maxTimeMS, used on getMore commands
     * @note this option is not set on the aggregate command
     */
    maxAwaitTimeMS: Optional<Int64>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions between 3.6 and 4.2 only support string as comment,
     * and providing a non-string type will result in a server-side error.
     * Older server versions do not support comment for aggregate command at all,
     * and providing one will result in a server-side error.
     *
     * Any comment set on a aggregate command is inherited by any subsequent
     * getMore commands run on the same cursor.id returned from the
     * aggregate command. Therefore, drivers MUST NOT attach the comment
     * to subsequent getMore commands on a cursor.
     */
    comment: Optional<any>;

    /**
     * The index to use for the aggregation. The hint does not apply to $lookup and $graphLookup stages.
     * Specify either the index name as a string or the index key pattern. If specified,
     * then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see http://docs.mongodb.com/manual/reference/command/aggregate/
     */
    hint: Optional<(String | Document)>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/aggregate/
     */
    let: Optional<Document>;
  }

  class CountOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum number of documents to count.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     */
    limit: Optional<Int64>;

    /**
     * The maximum amount of time to allow the operation to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     */
    maxTimeMS: Optional<Int64>;

    /**
     * The number of documents to skip before counting.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     */
    skip: Optional<Int64>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for count command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class EstimatedDocumentCountOptions {

    /**
     * The maximum amount of time to allow the operation to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     */
    maxTimeMS: Optional<Int64>;
  }

  class DistinctOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/distinct/
     */
    collation: Optional<Document>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/distinct/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for distinct command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  enum CursorType {
    /**
     * The default value. A vast majority of cursors will be of this type.
     */
    NON_TAILABLE,
    /**
     * Tailable means the cursor is not closed when the last data is retrieved.
     * Rather, the cursor marks the final object’s position. You can resume
     * using the cursor later, from where it was located, if more data were
     * received. Like any “latent cursor”, the cursor may become invalid at
     * some point (CursorNotFound) – for example if the final object it
     * references were deleted.
     *
     * @see https://docs.mongodb.com/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    TAILABLE,
    /**
     * Combines the tailable option with awaitData, as defined below.
     *
     * Use with TailableCursor. If we are at the end of the data, block for a
     * while rather than returning no data. After a timeout period, we do return
     * as normal. The default is true.
     *
     * @see https://docs.mongodb.com/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    TAILABLE_AWAIT
  }

  class FindOptions {

    /**
     * Enables writing to temporary files on the server. When set to true, the server
     * can write temporary data to disk while executing the find operation.
     *
     * This option is sent only if the caller explicitly provides a value. The default
     * is to not send a value.
     *
     * This option is only supported by servers >= 4.4. Older servers >= 3.2 will report an error for using this option.
     * For servers < 3.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    allowDiskUse: Optional<Boolean>;

    /**
     * Get partial results from a mongos if some shards are down (instead of throwing an error).
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, the Partial wire protocol flag is used and defaults to false.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    allowPartialResults: Optional<Boolean>;

    /**
     * The number of documents to return per batch.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this is combined with limit to create the wire protocol numberToReturn value.
     * If specified, drivers SHOULD apply this option to both the original query operation and subsequent
     * getMore operations on the cursor.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    batchSize: Optional<Int32>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    collation: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 only support string as comment,
     * and providing a non-string type will result in a server-side error.
     *
     * Any comment set on a find command is inherited by any subsequent
     * getMore commands run on the same cursor.id returned from the
     * find command. Therefore, drivers MUST NOT attach the comment
     * to subsequent getMore commands on a cursor.
     */
    comment: Optional<any>;

    /**
     * Indicates the type of cursor to use. This value includes both
     * the tailable and awaitData options.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, the AwaitData and Tailable wire protocol flags are used and default to false.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    cursorType: Optional<CursorType>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum number of documents to return.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this is combined with batchSize to create the wire protocol numberToReturn value.
     *
     * A negative limit implies that the caller has requested a single batch of results. For servers >= 3.2, singleBatch
     * should be set to true and limit should be converted to a positive value. For servers < 3.2, the wire protocol
     * numberToReturn value may be negative.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    limit: Optional<Int64>;

    /**
     * The exclusive upper bound for a specific index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    max: Optional<Document>;

    /**
     * The maximum amount of time for the server to wait on new documents to satisfy a tailable cursor
     * query. This only applies to a TAILABLE_AWAIT cursor. When the cursor is not a TAILABLE_AWAIT cursor,
     * this option is ignored.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as maxTimeMS does not exist in the OP_GET_MORE wire protocol.
     *
     * Note: This option is specified as "maxTimeMS" in the getMore command and not provided as part of the
     * initial find command.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    maxAwaitTimeMS: Optional<Int64>;

    /**
     * Maximum number of documents or index keys to scan when executing the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     * @deprecated 4.0
     */
    maxScan: Optional<Int64>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * The inclusive lower bound for a specific index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    min: Optional<Document>;

    /**
     * The server normally times out idle cursors after an inactivity period (10 minutes)
     * to prevent excess memory use. Set this option to prevent that.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, the NoCursorTimeout wire protocol flag is used and defaults to false.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    noCursorTimeout: Optional<Boolean>;

    /**
     * Enables optimization when querying the oplog for a range of ts values
     *
     * Note: this option is intended for internal replication use only.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, the OplogReplay wire protocol flag is used and defaults to false.
     * For servers >= 4.4, the server will ignore this option if set (see: SERVER-36186).
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     * @deprecated 4.4
     */
    oplogReplay: Optional<Boolean>;

    /**
     * Limits the fields to return for all matching documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    projection: Optional<Document>;

    /**
     * If true, returns only the index keys in the resulting documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    returnKey: Optional<Boolean>;

    /**
     * Determines whether to return the record identifier for each document. If true, adds a field $recordId to the returned documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    showRecordId: Optional<Boolean>;

    /**
     * The number of documents to skip before returning.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this is a wire protocol parameter that defaults to 0.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    skip: Optional<Int64>;

    /**
     * Prevents the cursor from returning a document more than once because of an intervening write operation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     * @deprecated 4.0
     */
    snapshot: Optional<Boolean>;

    /**
     * The order in which to return matching documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    sort: Optional<Document>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/find/
     */
    let: Optional<Document>;
  }

~~~~~~~~~~~~~~~~~
Count API Details
~~~~~~~~~~~~~~~~~

MongoDB drivers provide two helpers for counting the number of documents in a
collection, estimatedDocumentCount and countDocuments. The names were chosen
to make it clear how they behave and exactly what they do. The
estimatedDocumentCount helper returns an estimate of the count of documents
in the collection using collection metadata, rather than counting the
documents or consulting an index. The countDocuments helper counts the
documents that match the provided query filter using an aggregation pipeline.

The count() helper is deprecated. It has always been implemented using the
``count`` command. The behavior of the count command differs depending on the
options passed to it and may or may not provide an accurate count. When
no query filter is provided the count command provides an estimate using
collection metadata. Even when provided with a query filter the count
command can return inaccurate results with a sharded cluster `if orphaned
documents exist or if a chunk migration is in progress <https://docs.mongodb.com/manual/reference/command/count/#behavior>`_.
The countDocuments helper avoids these sharded cluster problems entirely
when used with MongoDB 3.6+, and when using ``Primary`` read preference with
older sharded clusters.

~~~~~~~~~~~~~~~~~~~~~~
estimatedDocumentCount
~~~~~~~~~~~~~~~~~~~~~~

On server versions greater than or equal to 4.9.0 (wire version 12 or higher),
the estimatedDocumentCount function is implemented using the ``$collStats``
aggregate pipeline stage with ``$group`` to gather results from multiple shards.
As documented above, the only supported option is maxTimeMS::

  pipeline = [
    { '$collStats': { 'count': {} } },
    { '$group': { '_id': 1, 'n': { '$sum': '$count' } } }
  ]

Similar to the count command, the estimated count of documents is returned
in the ``n`` field. Implementations can assume that the document containing
the single result of the aggregation pipeline is contained in the first batch of
the server's reply to the aggregate command. It is not necessary to execute a getMore
operation to ensure that the result is available.

In the event this aggregation is run against a non-existent namespace, a NamespaceNotFound(26)
error will be returned during execution. Drivers MUST interpret the server error code 26 as
a ``0`` count.

For server versions less than 4.9.0 (wire version 11 or under), the estimatedDocumentCount
function is implemented using the ``count`` command with no query filter, skip,
limit, or other options that would alter the results. Once again, the only supported
option is maxTimeMS.

~~~~~~~~~~~~~~
countDocuments
~~~~~~~~~~~~~~

The countDocuments function is implemented using the ``$group`` aggregate
pipeline stage with ``$sum``. Applications must be required to pass a value
for filter, but an empty document is supported::

  pipeline = [{'$match': filter}]
  if (skip) {
    pipeline.push({'$skip': skip})
  }
  if (limit) {
    pipeline.push({'$limit': limit})
  }
  pipeline.push({'$group': {'_id': 1, 'n': {'$sum': 1}}})

The count of documents is returned in the ``n`` field, similar to the ``count``
command. countDocuments options other than filter, skip, and limit are added as
options to the ``aggregate`` command.

In the event this aggregation is run against an empty collection, an empty
array will be returned with no ``n`` field. Drivers MUST interpret this result
as a ``0`` count.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Combining Limit and Batch Size for the Wire Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The OP_QUERY wire protocol only contains a numberToReturn value which drivers must calculate to get expected limit and batch size behavior. Subsequent calls to OP_GET_MORE should use the user-specified batchSize or default to 0. If the result is larger than the max Int32 value, an error MUST be raised as the computed value is impossible to send to the server. Below is pseudo-code for calculating numberToReturn for OP_QUERY.

.. code:: typescript

  function calculateFirstNumberToReturn(options: FindOptions): Int32 {
    Int32 numberToReturn;
    Int32 limit = options.limit || 0;
    Int32 batchSize = options.batchSize || 0;

    if (limit < 0) {
      numberToReturn = limit;
    }
    else if (limit == 0) {
      numberToReturn = batchSize;
    }
    else if (batchSize == 0) {
      numberToReturn = limit;
    }
    else if (limit < batchSize) {
      numberToReturn = limit;
    }
    else {
      numberToReturn = batchSize;
    }

    return numberToReturn;
  }

Because of this anomaly in the wire protocol, it is up to the driver to enforce the user-specified limit. Each driver MUST keep track of how many documents have been iterated and stop iterating once the limit has been reached. When the limit has been reached, if the cursor is still open, a driver MUST kill the cursor.

~~~~~~~~~~~~~~~~~~~~~~~~~~
Database-level aggregation
~~~~~~~~~~~~~~~~~~~~~~~~~~

The server supports several collection-less aggregation source stages like ``$currentOp`` and ``$listLocalSessions``. The database aggregate command requires a collection name of 1 for collection-less source stages. Drivers support for database-level aggregation will allow users to receive a cursor from these collection-less aggregation source stages.

Write
-----

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Insert, Update, Replace, Delete, and Bulk Writes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: typescript

  interface Collection {

    /**
     * Executes multiple write operations.
     *
     * An error MUST be raised if the requests parameter is empty.
     *
     * For servers < 3.4, if a collation was explicitly set for any request, an error MUST be raised
     * and no documents sent.
     *
     * NOTE: see the FAQ about the previous bulk API and how it relates to this.
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     * @see https://docs.mongodb.com/manual/reference/command/insert/
     * @see https://docs.mongodb.com/manual/reference/command/update/
     * @throws InvalidArgumentException if requests is empty
     * @throws BulkWriteException
     */
    bulkWrite(requests: WriteModel[], options: Optional<BulkWriteOptions>): BulkWriteResult;

    /**
     * Inserts the provided document. If the document is missing an identifier,
     * the driver should generate one.
     *
     * @see https://docs.mongodb.com/manual/reference/command/insert/
     * @throws WriteException
     */
    insertOne(document: Document, options: Optional<InsertOneOptions>): InsertOneResult;

    /**
     * Inserts the provided documents. If any documents are missing an identifier,
     * the driver should generate them.
     *
     * An error MUST be raised if the documents parameter is empty.
     *
     * Note that this uses the bulk insert command underneath and should not
     * use OP_INSERT.
     *
     * @see https://docs.mongodb.com/manual/reference/command/insert/
     * @throws InvalidArgumentException if documents is empty
     * @throws BulkWriteException
     */
    insertMany(documents: Iterable<Document>, options: Optional<InsertManyOptions>): InsertManyResult;

    /**
     * Deletes one document.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     * @throws WriteException
     */
    deleteOne(filter: Document, options: Optional<DeleteOptions>): DeleteResult;

    /**
     * Deletes multiple documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     * @throws WriteException
     */
    deleteMany(filter: Document, options: Optional<DeleteOptions>): DeleteResult;

    /**
     * Replaces a single document.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     * @throws WriteException
     */
    replaceOne(filter: Document, replacement: Document, options: Optional<ReplaceOptions>): UpdateResult;

    /**
     * Updates one document.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     * @throws WriteException
     */
    updateOne(filter: Document, update: (Document | Document[]), options: Optional<UpdateOptions>): UpdateResult;

    /**
     * Updates multiple documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     * @throws WriteException
     */
    updateMany(filter: Document, update: (Document | Document[]), options: Optional<UpdateOptions>): UpdateResult;
  }

  class BulkWriteOptions {

    /**
     * If true, when a write fails, return without performing the remaining
     * writes. If false, when a write fails, continue with the remaining writes, if any.
     * Defaults to true.
     */
    ordered: Boolean;

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using OP_INSERT, OP_UPDATE, or OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for write operations,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class InsertOneOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using OP_INSERT, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for insert command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class InsertManyOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using OP_INSERT, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * If true, when an insert fails, return without performing the remaining
     * writes. If false, when a write fails, continue with the remaining writes, if any.
     * Defaults to true.
     */
    ordered: Boolean;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for insert command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class UpdateOptions {

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.2. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;


    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/update/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for update command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class ReplaceOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.2. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/update/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for update command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class DeleteOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    hint: Optional<(String | Document)>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/delete/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for delete command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }


Bulk Write Models
~~~~~~~~~~~~~~~~~

.. code:: typescript

  interface WriteModel {
    // marker interface for writes that can be batched together.
  }

  class InsertOneModel implements WriteModel {

    /**
     * The document to insert.
     *
     * @see https://docs.mongodb.com/manual/reference/command/insert/
     */
    document: Document;
  }

  class DeleteOneModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    filter: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    hint: Optional<(String | Document)>;
  }

  class DeleteManyModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    filter: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_DELETE or OP_MSG, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    hint: Optional<(String | Document)>;
  }

  class ReplaceOneModel implements WriteModel {

    /**
     * The filter to limit the replaced document.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    filter: Document;

    /**
     * The document with which to replace the matched document.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    replacement: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.2. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }

  class UpdateOneModel implements WriteModel {

    /**
     * The filter to limit the updated documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    filter: Document;

    /**
     * A document or pipeline containing update operators.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    update: (Document | Document[]);

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.2. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }

  class UpdateManyModel implements WriteModel {

    /**
     * The filter to limit the updated documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    filter: Document;

    /**
     * A document or pipeline containing update operators.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    update: (Document | Document[]);

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.2. Older servers >= 3.4 will report an error for using this option.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_UPDATE, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using OP_MSG and servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }


Write Results
~~~~~~~~~~~~~

The acknowledged property is defined for languages/frameworks without a sufficient optional type. Hence, a driver may choose to return an Optional<BulkWriteResult> such that unacknowledged writes don't have a value and acknowledged writes do have a value.

.. note::
    If you have a choice, consider providing the acknowledged member and raising an error if the other fields are accessed in an unacknowledged write. Instead of users receiving a null reference exception, you have the opportunity to provide an informative error message indicating the correct way to handle the situation. For instance, "The insertedCount member is not available when the write was unacknowledged. Check the acknowledged member to avoid this error."

Any result class with all parameters marked NOT REQUIRED is ultimately NOT REQUIRED as well. For instance, the ``InsertOneResult`` has all NOT REQUIRED parameters and is therefore also NOT REQUIRED allowing a driver to use "void" as the return value for the ``insertOne`` method.

.. code:: typescript

  class BulkWriteResult {

    /**
     * Indicates whether this write result was acknowledged. If not, then all
     * other members of this result will be undefined.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    acknowledged: Boolean;

    /**
     * Number of documents inserted.
     */
    insertedCount: Int64;

    /**
     * Map of the index of the operation to the id of the inserted document.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    insertedIds: Map<Int64, any>;

    /**
     * Number of documents matched for update.
     */
    matchedCount: Int64;

    /**
     * Number of documents modified.
     */
    modifiedCount: Int64;

    /**
     * Number of documents deleted.
     */
    deletedCount: Int64;

    /**
     * Number of documents upserted.
     */
    upsertedCount: Int64;

    /**
     * Map of the index of the operation to the id of the upserted document.
     */
    upsertedIds: Map<Int64, any>;

  }

  class InsertOneResult {

    /**
     * Indicates whether this write result was acknowledged. If not, then all
     * other members of this result will be undefined.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    acknowledged: Boolean;

    /**
     * The identifier that was inserted. If the server generated the identifier, this value
     * will be null as the driver does not have access to that data.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    insertedId: any;

  }

  class InsertManyResult {

    /**
     * Indicates whether this write result was acknowledged. If not, then all
     * other members of this result will be undefined.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    acknowledged: Boolean;

    /**
     * Map of the index of the inserted document to the id of the inserted document.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    insertedIds: Map<Int64, any>;

  }

  class DeleteResult {

    /**
     * Indicates whether this write result was acknowledged. If not, then all
     * other members of this result will be undefined.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    acknowledged: Boolean;

    /**
     * The number of documents that were deleted.
     */
    deletedCount: Int64;

  }

  class UpdateResult {

    /**
     * Indicates whether this write result was acknowledged. If not, then all
     * other members of this result will be undefined.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    acknowledged: Boolean;

    /**
     * The number of documents that matched the filter.
     */
    matchedCount: Int64;

    /**
     * The number of documents that were modified.
     */
    modifiedCount: Int64;

    /**
     * The number of documents that were upserted.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property so long as
     * it is always possible to infer whether an upsert has taken place. Since
     * the "_id" of an upserted document could be null, a null "upsertedId" may
     * be ambiguous in some drivers. If so, this field can be used to indicate
     * whether an upsert has taken place.
     */
    upsertedCount: Int64;

    /**
     * The identifier of the inserted document if an upsert took place.
     */
    upsertedId: any;

  }

~~~~~~~~~~~~~~
Error Handling
~~~~~~~~~~~~~~

Defined below are error and exception types that should be reported from the
various write methods. Since error types across languages would be impossible to
reconcile, the below definitions represent the fields and names for the
information that should be present. Structure isn't important as long as the
information is available.

Drivers SHOULD report errors however they report other server errors: by raising
an exception, returning "false" and populating an error struct, or another idiom
that is consistent with other server errors.

WriteConcernError
~~~~~~~~~~~~~~~~~

.. code:: typescript

  class WriteConcernError {

    /**
     * An integer value identifying the write concern error. Corresponds to the
     * "writeConcernError.code" field in the command response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A document identifying the write concern setting related to the error.
     * Corresponds to the "writeConcernError.errInfo" field in the command
     * response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    details: Document;

    /**
     * A description of the error. Corresponds to the
     * "writeConcernError.errmsg" field in the command response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    message: String;

  }

Drivers MUST construct a ``WriteConcernError`` from a server reply as follows:

- Set ``code`` to ``writeConcernError.code``.
- Set ``message`` to ``writeConcernError.errmsg`` if available.
- Set ``details`` to ``writeConcernError.errInfo`` if available. Drivers MUST NOT parse inside ``errInfo``.

See `writeConcernError Examples </source/read-write-concern/read-write-concern.rst#writeconcernerror-examples>`_
in the Read/Write Concern spec for examples of how a server represents write
concern errors in replies.

WriteError
~~~~~~~~~~

Write errors for ``insert``, ``update``, and ``delete`` commands are reported as
objects within a ``writeErrors`` array field in the command response. Drivers
MUST construct a ``WriteError`` from a server reply as follows (where
``writeErrors[]`` refers to a particular element in the array):

- Set ``code`` to ``writeErrors[].code``.
- Set ``message`` to ``writeErrors[].errmsg`` if available.
- Set ``details`` to ``writeErrors[].errInfo`` if available. Drivers MUST NOT parse inside ``errInfo``.

For single-statement writes (i.e. ``insertOne``, ``updateOne``, ``updateMany``,
``replaceOne``, ``deleteOne``, and ``deleteMany``), a single write error may be
reported in the array and ``writeErrors[0].index`` will be zero.

For multi-statement writes (i.e. ``insertMany`` and ``bulkWrite``), potentially
many write errors may be reported in the array and the ``index`` property will
be set accordingly. Since the reported ``index`` is specific to each command,
drivers MUST adjust the index accordingly for ``BulkWriteError.index``.

.. code:: typescript

  class WriteError {

    /**
     * An integer value identifying the write error. Corresponds to the
     * "writeErrors[].code" field in the command response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A document providing more information about the write error (e.g. details
     * pertaining to document validation). Corresponds to the
     * "writeErrors[].errInfo" field in the command response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    details: Document;

    /**
     * A description of the error. Corresponds to the "writeErrors[].errmsg"
     * field in the command response.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    message: String;

  }

  class BulkWriteError : WriteError {

    /**
     * The index of the request that errored. This is derived in part from the
     * "writeErrors[].index" field in the command response; however, drivers
     * MUST adjust the index accordingly for bulk writes that execute multiple
     * writes commands.
     */
    index: Int32;

    /**
     * The request that errored.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    request: Optional<WriteModel>;

  }

  /**
   * NOTE: Only one of writeConcernError or writeError will be populated at a time. Your driver must present the offending
   * error to the user.
   */
  class WriteException {

    /**
     * The error that occurred on account of write concern failure.
     */
    writeConcernError: Optional<WriteConcernError>;

    /**
     * The error that occurred on account of a non-write concern failure.
     */
    writeError: Optional<WriteError>;

  }

  class BulkWriteException {

    /**
     * The requests that were sent to the server.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    processedRequests: Optional<Iterable<WriteModel>>;

    /**
     * The requests that were not sent to the server.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    unprocessedRequests: Optional<Iterable<WriteModel>>;

    /**
     * The intermediary write result for any operations that succeeded before
     * the bulk write was interrupted.
     *
     * NOT REQUIRED: Drivers may choose to not provide this property.
     */
    writeResult: Optional<BulkWriteResult>;

    /**
     * The error that occured on account of write concern failure. If the error was a Write Concern related, this field must be present.
     */
    writeConcernError: Optional<WriteConcernError>;

    /**
     * The error that occured on account of a non-write concern failure. This might be empty if the error was a Write Concern related error.
     */
    writeErrors: Optional<Iterable<BulkWriteError>>;

  }


~~~~~~~~~~~~~~~
Find And Modify
~~~~~~~~~~~~~~~

.. code:: typescript

  interface Collection {

    /**
     * Finds a single document and deletes it, returning the original. The document to return may be null.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndDelete(filter: Document, options: Optional<FindOneAndDeleteOptions>): Document;

    /**
     * Finds a single document and replaces it, returning either the original or the replaced
     * document. The document to return may be null.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndReplace(filter: Document, replacement: Document, options: Optional<FindOneAndReplaceOptions>): Document;

    /**
     * Finds a single document and updates it, returning either the original or the updated
     * document. The document to return may be null.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndUpdate(filter: Document, update: (Document | Document[]), options: Optional<FindOneAndUpdateOptions>): Document;

  }

  enum ReturnDocument {
    /**
     * Indicates to return the document before the update, replacement, or insert occured.
     */
     BEFORE,
    /**
     * Indicates to return the document after the update, replacement, or insert occured.
     */
     AFTER
  }

  class FindOneAndDeleteOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 4.2 will report an error for using this option.
     * For servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes and servers < 4.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Limits the fields to return for all matching documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * Note: this option is mapped to the "fields" findAndModify command option.
     *
     * @see https://docs.mongodb.com/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for findAndModify command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class FindOneAndReplaceOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 4.2 will report an error for using this option.
     * For servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes and servers < 4.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Limits the fields to return for all matching documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * Note: this option is mapped to the "fields" findAndModify command option.
     *
     * @see https://docs.mongodb.com/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * When ReturnDocument.After, returns the replaced or inserted document rather than the original.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * Note: this option is mapped to the "new" findAndModify boolean field. ReturnDocument.Before represents false,
     * and ReturnDocument.After represents true.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    returnDocument: Optional<ReturnDocument>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

    /**
     * When true, findAndModify creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    upsert: Optional<Boolean>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for findAndModify command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

  class FindOneAndUpdateOptions {

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a true value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern.
     * If specified, then the query system will only consider plans using the hinted index.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 4.4. Older servers >= 4.2 will report an error for using this option.
     * For servers < 4.2, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes and servers < 4.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * NOTE: This option is deprecated in favor of timeoutMS.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Limits the fields to return for all matching documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * Note: this option is mapped to the "fields" findAndModify command option.
     *
     * @see https://docs.mongodb.com/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * When ReturnDocument.After, returns the replaced or inserted document rather than the original.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * Note: this option is mapped to the "new" findAndModify boolean field. ReturnDocument.Before represents false,
     * and ReturnDocument.After represents true.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    returnDocument: Optional<ReturnDocument>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    upsert: Optional<Boolean>;

    /**
     * Map of parameter names and values. Values must be constant or closed
     * expressions that do not reference document fields. Parameters can then be
     * accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * This option is only supported by servers >= 5.0. Older servers >= 2.6 (and possibly earlier) will report an error for using this option.
     *
     * @see http://docs.mongodb.com/manual/reference/command/findAndModify/
     */
    let: Optional<Document>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     *
     * The comment can be any valid BSON type for server versions 4.4 and above.
     * Server versions prior to 4.4 do not support comment for findAndModify command,
     * and providing one will result in a server-side error.
     */
    comment: Optional<any>;
  }

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Update vs. Replace Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``update`` family of operations require that the update document parameter MUST have only atomic modifiers. In practice, this means that introspection needs to happen on that document to enforce this. However, it is enough to only check the first element in the document. If it begins with a ``$`` sign and the rest of the document's elements do not, the server will throw an error. Note that it is required that an update document have at least one atomic modifier.

The ``replace`` family of operations require that the replacement document parameter MUST NOT begin with an atomic modifier. In practice, this means that introspection needs to happen on that document to enforce this. However, it is enough to only check the first element in the document. If it does not begin with a ``$`` sign but an element later on does, the server will throw an error.


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Aggregation Pipelines with Write Stages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section discusses special considerations for aggregation pipelines that
contain write stages (e.g. ``$out``, ``$merge``).


Returning a cursor on the output collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As noted in the documentation for the ``aggregate`` helper earlier in this
document, ``$out`` and ``$merge`` are special pipeline stages that cause no
results to be returned from the server. As such, drivers MAY setup a cursor to
be executed upon iteration against the output collection and return that instead
of an iterable that would otherwise have no results.

Drivers that do so for ``$merge`` MAY remind users that such a cursor may return
more documents than were written by the aggregation (e.g. documents that existed
in the collection prior to ``$merge`` being executed).


Read preferences and server selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section is only applicable if an explicit (i.e. per-operation) or inherited
(e.g. from a Collection) read preference is available and it is *not* a primary
read preference (i.e. ``{ "mode": "primary" }``).

Historically, only primaries could execute an aggregation pipeline with ``$out``
or ``$merge`` and drivers never considered a read preference for the operation.
As of ``featureCompatibilityVersion`` 4.4, secondaries can now execute pipelines
with ``$out`` or ``$merge``. Since drivers do not track
``featureCompatibilityVersion``, the decision to consider a read preference for
such a pipeline will depend on the wire version(s) of the server(s) to which the
driver is connected.

If there are one or more available servers and one or more of those servers is
pre-5.0 (i.e. wire version < 13), drivers MUST NOT use the available read
preference and MUST instead select a server using a primary read preference.

Otherwise, if there are either no available servers, all available servers are
5.0+ (i.e. wire version >= 13), or the topology type is LoadBalanced (we can
assume the backing mongos is 5.0+), drivers MUST use the available read
preference.

Drivers SHOULD augment their
`server selection algorithm <..../server-selection/server-selection.rst#server-selection-algorithm>`_
such that this logic can be enforced within a single server selection attempt.

Drivers MUST discern the read preference used to select a server for the
operation, which SHALL be used for specifying the
`$readPreference global command argument <../message/OP_MSG.rst#global-command-arguments>`_
and
`passing read preference to mongos and load balancers <../server-selection/server-selection.rst#passing-read-preference-to-mongos-and-load-balancers>`_
(if applicable).


Test Plan
=========

See the `README <tests/README.rst>`_ for tests.


Motivation
==========

Current drivers have chosen slightly different names and semantics for the same operations and options. In addition, not all drivers offer all the same operations and methods. As such, it is difficult to transition from driver to driver making the jobs of polyglot developers, documentation authors, and support engineers more difficult.


Backwards Compatibility
=======================

This spec should be mostly backwards compatible as it is very lenient. Drivers finding a backwards compatibility problem should attempt to work around it using an acceptable deviation. In rare cases, a driver may need to break backwards compatibility. This should be done in accordance with a versioning scheme indicating that a backwards compatible break may have occured in conjunction with release documentation and warnings.


Reference Implementation
========================

See Test Plan


Related Terminology
===================

If a driver needs to refer to items in the following list, the below are the accepted forms of those terms and deviations from the Naming section are still permissible.

* Read Preference: readPreference
* Read Concern: readConcern
* Write Concern: writeConcern


Q & A
=====

Q: Why do the names of the fields differ from those defined in the MongoDB manual?
  Documentation and commands often refer to same-purposed fields with different names making it difficult to have a cohesive API. In addition, occasionally the name was correct at one point and its purpose has expanded to a point where the initial name doesn't accurately describe its current function.

  In addition, responses from the servers are sometimes cryptic and used for the purposes of compactness. In these cases, we felt the more verbose form was desirable for self-documentation purposes.

Q: Where is read preference?
  Read preference is about selecting a server with which to perform a read operation, such as a query, a count, or an aggregate. Since all operations defined in this specification are performed on a collection, it's uncommon that two different read operations on the same collection would use a different read preference, potentially getting out-of-sync results. As such, the most natural place to indicate read preference is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose this selection filter to a user per operation for various reasons.  As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.

Q: Where is read concern?
  Read concern is about indicating how reads are handled. Since all operations defined in this specification are performed on a collection, it's uncommon that two different read operations on the same collection would use a different read concern, potentially causing mismatched and out-of-sync data. As such, the most natural place to indicate read concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose read concern to a user per operation for various reasons. As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.

Q: Where is write concern?
  Write concern is about indicating how writes are acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different write operations on the same collection would use a different write concern, potentially causing mismatched and out-of-sync data. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it. See the `Read/Write Concern specification </source/read-write-concern/read-write-concern.rst>`_ for the API of constructing a read/write concern and associated API.

  However, it might be that a driver needs to expose write concern to a user per operation for various reasons. As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.

Q: How do I throttle unacknowledged writes now that write concern is no longer defined on a per operation basis?
  Some users used to throttle unacknowledged writes by using an acknowledged write concern every X number of operations. Going forward, the proper way to handle this is by using the bulk write API.

Q: What is the logic for adding "One" or "Many" into the method and model names?
  If the maximum number of documents affected can only be one, we added "One" into the name. This makes it explicit that the maximum number of documents that could be affected is one vs. infinite.

  In addition, the current API exposed by all our drivers has the default value for "one" or "many" set differently for update and delete. This generally causes some issues for new developers and is a minor annoyance for existing developers. The safest way to combat this without introducing discrepencies between drivers/driver versions or breaking backwards compatibility was to use multiple methods, each signifying the number of documents that could be affected.

Q: Speaking of "One", where is ``findOne``?
  If your driver wishes to offer a ``findOne`` method, that is perfectly fine. If you choose to implement ``findOne``, please keep to the naming conventions followed by the ``FindOptions`` and keep in mind that certain things don't make sense like limit (which should be -1), tailable, awaitData, etc...

Q: What considerations have been taken for the eventual merging of query and the aggregation framework?
  In the future, it is probable that a new query engine (QE) will look very much like the aggregation framework. Given this assumption, we know that both ``find`` and ``aggregate`` will be renderable in QE, each maintaining their ordering guarantees for full backwards compatibility.

  Hence, the only real concern is how to initiate a query using QE. While ``find`` is preferable, it would be a backwards breaking change. It might be decided that ``find`` is what should be used, and all drivers will release major revisions with this backwards breaking change. Alternatively, it might be decided that another initiator would be used.

Q: Didn't we just build a bulk API?
  Yes, most drivers did just build out a bulk API (fluent-bulk-api). While unfortunate, we felt it better to have the bulk api be consistent with the rest of the methods in the CRUD family of operations. However, the fluent-bulk-api is still able to be used as this change is non-backwards breaking. Any driver which implemented the fluent bulk API should deprecate it and drivers that have not built it should not do so.

Q: What about explain?
  Explain has been determined to be not a normal use-case for a driver. We'd like users to use the shell for this purpose. However, explain is still possible from a driver. For find, it can be passed as a modifier. Aggregate can be run using a runCommand method passing the explain option. In addition, server 3.0 offers an explain command that can be run using a runCommand method.

Q: Where did modifiers go in FindOptions?
  MongoDB 3.2 introduced the find command. As opposed to using the general "modifiers" field any longer, each relevant option is listed explicitly. Some options, such as "tailable" or "singleBatch" are not listed as they are derived from other fields. Upgrading a driver should be a simple procedure of deprecating the "modifiers" field and introducing the new fields. When a collision occurs, the explicitly specified field should override the value in "modifiers".

Q: Where is ``save``?
  Drivers have historically provided a ``save`` method, which was syntactic sugar for upserting or inserting a document based on whether it contained an identifier, respectively. While the ``save`` method may be convenient for interactive environments, such as the shell, it was intentionally excluded from the CRUD specification for language drivers for several reasons. The ``save`` method promotes a design pattern of "fetch, modify, replace" and invites race conditions in application logic. Additionally, the split nature of ``save`` makes it difficult to discern at a glance if application code will perform an insert or potentially dangerous full-document replacement. Instead of relying on ``save``, application code should know whether document already has an identifier and explicitly call ``insertOne`` or ``replaceOne`` with the ``upsert`` option.

Q: Where is ``useCursor`` in AggregateOptions?
  Inline aggregation results are no longer supported in server 3.5.2+. The `aggregate command <https://docs.mongodb.com/manual/reference/command/aggregate/>`_ must be provided either the ``cursor`` document or the ``explain`` boolean. AggregateOptions does not define an ``explain`` option. If a driver does support an ``explain`` option, the ``cursor`` document should be omitted if ``explain`` is ``true``. Otherwise a ``cursor`` document must be added to the ``aggregate`` command. Regardless, ``useCursor`` is no longer needed. Removing ``useCursor`` is a backwards breaking change, so drivers should first deprecate this option in a minor release, and remove it in a major release.

Q: Where is ``singleBatch`` in FindOptions?
  Drivers have historically allowed users to request a single batch of results (after which the cursor is closed) by specifying a negative value for the ``limit`` option. For servers < 3.2, a single batch may be requested by specifying a negative value in the ``numberToReturn`` wire protocol field. For servers >= 3.2, the ``find`` command defines ``limit`` as a non-negative integer option but introduces a ``singleBatch`` boolean option. Rather than introduce a ``singleBatch`` option to FindOptions, the spec preserves the existing API for ``limit`` and instructs drivers to convert negative values accordingly for servers >= 3.2.

Q: Why are client-side errors raised for some unsupported options?
  Server versions before 3.4 were inconsistent about reporting errors for unrecognized command options and may simply ignore them, which means a client-side error is the only way to inform users that such options are unsupported. For unacknowledged writes using OP_MSG, a client-side error is necessary because the server has no chance to return a response (even though a 3.6+ server is otherwise capable of reporting errors for unrecognized options). For unacknowledged writes using legacy opcodes (i.e. OP_INSERT, OP_UPDATE, and OP_DELETE), the message body has no field with which to express these options so a client-side error is the only mechanism to inform the user that such options are unsupported. The spec does not explicitly refer to unacknowledged writes using OP_QUERY primarily because a response document is always returned and drivers generally would not consider using OP_QUERY precisely for that reason.

Changes
=======

* 2022-01-??: Add comment attribute to all helpers.
* 2022-01-19: Deprecate the maxTimeMS option and require that timeouts be applied per the client-side operations timeout spec.
* 2022-01-14: Add let to ReplaceOptions
* 2021-11-10: Revise rules for applying read preference for aggregations with $out and $merge.
* 2021-11-10: Add let to FindOptions, UpdateOptions, DeleteOptions, FindOneAndDeleteOptions, FindOneAndReplaceOptions, FindOneAndUpdateOptions
* 2021-09-28: Support aggregations with $out and $merge on 5.0+ secondaries
* 2021-08-31: Allow unacknowledged hints on write operations if supported by server (reverts previous change).
* 2021-06-02: Introduce WriteError.details and clarify WriteError construction
* 2021-06-01: Add let to AggregateOptions
* 2021-01-21: Update estimatedDocumentCount to use $collStats stage for servers >= 4.9
* 2020-04-17: Specify that the driver must raise an error for unacknowledged hints on any write operation, regardless of server version.
* 2020-03-19: Clarify that unacknowledged update, findAndModify, and delete operations with a hint option should raise an error on older server versions.
* 2020-03-06: Added hint option for DeleteOne, DeleteMany, and FindOneAndDelete operations.
* 2020-01-24: Added hint option for findAndModify update/replace operations.
* 2020-01-17: Add allowDiskUse to FindOptions.
* 2020-01-14: Deprecate oplogReplay option for find command
* 2020-01-10: Clarify client-side error reporting for unsupported options
* 2020-01-10: Error if hint specified for unacknowledged update using OP_UPDATE or OP_MSG for servers < 4.2
* 2019-10-28: Removed link to old language examples.
* 2019-09-26: Added hint option for update commands.
* 2019-06-07: Consistent treatment for aggregate $merge and $out stages
* 2019-05-01: Specify a document or pipeline for commands with updates in server 4.2+.
* 2019-02-20: Mark the request field of BulkWriteError as NOT REQUIRED
* 2018-11-30: Specify maxAwaitTimeMS in AggregateOptions
* 2018-11-15: Aggregate commands with an $out stage should not specify batchSize
* 2018-10-25: Note how results are backed for aggregate, distinct, and find operations
* 2018-07-25: Added upsertedCount to UpdateResult.
* 2018-06-07: Deprecated the count helper. Added the estimatedDocumentCount and countDocuments helpers.
* 2018-03-05: Deprecate snapshot option
* 2018-03-01: Deprecate maxScan query option.
* 2018-02-06: Note that batchSize in FindOptions and AggregateOptions should also apply to getMore.
* 2018-01-26: Only send bypassDocumentValidation option if it's true, don't send false.
* 2017-10-23: Allow BulkWriteException to provide an intermediary write result.
* 2017-10-17: Document negative limit for FindOptions.
* 2017-10-09: Bumped minimum server version to 2.6 and removed references to older versions in spec and tests.
* 2017-10-09: Prohibit empty insertMany() and bulkWrite() operations.
* 2017-10-09: Split UpdateOptions and ReplaceOptions. Since replaceOne() previously used UpdateOptions, this may have BC implications for drivers using option classes.
* 2017-10-05: Removed useCursor option from AggregateOptions.
* 2017-09-26: Added hint option to AggregateOptions.
* 2017-09-25: Added comment option to AggregateOptions.
* 2017-08-31: Added arrayFilters to bulk write update models.
* 2017-06-29: Remove requirement of using OP_KILL_CURSOR to kill cursors.
* 2017-06-27: Added arrayFilters to UpdateOptions and FindOneAndUpdateOptions.
* 2017-06-26: Added FAQ entry for omission of save method.
* 2017-05-12: Removed extra "collation" option added to several bulk write models.
* 2017-01-09: Removed modifiers from FindOptions and added in all options.
* 2017-01-09: Changed the value type of FindOptions.skip and FindOptions.limit to Int64 with a note related to calculating batchSize for opcode writes.
* 2017-01-09: Reworded description of how default values are handled and when to send certain options.
* 2016-09-23: Included collation option in the bulk write models.
* 2016-08-05: Added in collation option.
* 2015-11-05: Typos in comments about bypassDocumentValidation
* 2015-10-16: Added maxAwaitTimeMS to FindOptions.
* 2015-10-01: Moved bypassDocumentValidation into BulkWriteOptions and removed it from the individual write models.
* 2015-09-16: Added bypassDocumentValidation.
* 2015-09-16: Added readConcern notes.
* 2015-06-17: Added limit/batchSize calculation logic.

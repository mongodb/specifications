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
:Last Modified: October 9, 2017

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
     * Note: $out is a special pipeline stage that causes no results to be returned
     * from the server. As such, the iterable here would never contain documents. Drivers
     * MAY setup a cursor to be executed upon iteration against the $out collection such
     * that if a user were to iterate a pipeline including $out, results would be returned.
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    aggregate(pipeline: Document[], options: Optional<AggregateOptions>): Iterable<Document>;

    /**
     * Gets the number of documents matching the filter.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    count(filter: Document, options: Optional<CountOptions>): Int64;

    /**
     * Finds the distinct values for a specified field across a single collection.
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
     * @see https://docs.mongodb.com/manual/core/read-operations-introduction/
     */
    find(filter: Document, options: Optional<FindOptions>): Iterable<Document>;

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
     *
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    batchSize: Optional<Int32>;

    /**
     * If true, allows the write to opt-out of document level validation. This only applies
     * when the $out stage is specified.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
     * @see https://docs.mongodb.com/manual/reference/command/aggregate/
     */
    maxTimeMS: Optional<Int64>;
    
    /**
     * Enables users to specify an arbitrary string to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * @see http://docs.mongodb.com/manual/reference/command/aggregate/
     */
    comment: Optional<String>;

    /**
     * The index to use for the aggregation. The hint does not apply to $lookup and $graphLookup stages.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see http://docs.mongodb.com/manual/reference/command/aggregate/ 
     */
    hint: Optional<(String | Document)>;
  }

  class CountOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    collation: Optional<Document>;

    /**
     * The index to use.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum number of documents to count.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    limit: Optional<Int64>;

    /**
     * The maximum amount of time to allow the query to run.

     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * The number of documents to skip before counting.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/count/
     */
    skip: Optional<Int64>;
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
     * @see https://docs.mongodb.com/manual/reference/command/distinct/
     */
    maxTimeMS: Optional<Int64>;
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
     * Attaches a comment to the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
     */
    comment: Optional<String>;

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
     * The index to use.
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
     */
    maxScan: Optional<Int64>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
     * Internal replication use only - driver should not set
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, the OplogReplay wire protocol flag is used and defaults to false.
     *
     * @see https://docs.mongodb.com/manual/reference/command/find/
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
  }

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

Write
-----

~~~~~
Basic
~~~~~

.. code:: typescript

  interface Collection {

    /**
     * Sends a batch of writes to the server at the same time.
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
    updateOne(filter: Document, update: Document, options: Optional<UpdateOptions>): UpdateResult;

    /**
     * Updates multiple documents.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     * @throws WriteException
     */
    updateMany(filter: Document, update: Document, options: Optional<UpdateOptions>): UpdateResult;
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
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;
  }

  class InsertOneOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;
  }

  class InsertManyOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * If true, when an insert fails, return without performing the remaining
     * writes. If false, when a write fails, continue with the remaining writes, if any.
     * Defaults to true.
     */
    ordered: Boolean;
  }

  class UpdateOptions {

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }

  class ReplaceOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.2, this option is ignored and not sent as document validation is not available.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }

  class DeleteOptions {

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;
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
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;
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
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/delete/
     */
    collation: Optional<Document>;
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
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

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
     * A document containing update operators.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    update: Update;

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

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
     * A document containing update operators.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    update: Update;

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.4, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    collation: Optional<Document>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;
  }


Results
~~~~~~~

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
     * The identifier of the inserted document if an upsert took place.
     */
    upsertedId: any;

  }


Error Handling
~~~~~~~~~~~~~~

Below are defined the exceptions that should be thrown from the various write methods. Since exceptions across languages would be impossible to reconcile, the below definitions represent the fields and names for the information that should be present. Structure isn't important as long as the information is available.

.. note::
    The actual implementation of correlating, merging, and interpreting write errors from the server is not defined here. This spec is solely about the API for users.

.. code:: typescript

  class WriteConcernError {

    /**
     * An integer value identifying the write concern error.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A document identifying the write concern setting related to the error.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    details: Document;

    /**
     * A description of the error.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    message: String;

  }

  class WriteError {

    /**
     * An integer value identifying the error.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A description of the error.
     *
     * @see https://docs.mongodb.com/manual/reference/method/WriteResult/
     */
    message: String;

  }

  class BulkWriteError : WriteError {

    /**
     * The index of the request that errored.
     */
    index: Int32;

    /**
     * The request that errored.
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
    findOneAndUpdate(filter: Document, update: Document, options: Optional<FindOneAndUpdateOptions>): Document;

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
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
  }

  class FindOneAndReplaceOptions {

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
     * The maximum amount of time to allow the query to run.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
  }

  class FindOneAndUpdateOptions {

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     * For servers < 3.6, the driver MUST raise an error if the caller explicitly provides a value.
     * For unacknowledged writes using opcodes, the driver MUST raise an error if the caller explicitly provides a value.
     *
     * @see https://docs.mongodb.com/manual/reference/command/update/
     */
    arrayFilters: Optional<Array<Document>>;

    /**
     * If true, allows the write to opt-out of document level validation.
     *
     * This option is sent only if the caller explicitly provides a value. The default is to not send a value.
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
     * The maximum amount of time to allow the query to run.
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
  }

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Update vs. Replace Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``update`` family of operations require that the update document parameter MUST have only atomic modifiers. In practice, this means that introspection needs to happen on that document to enforce this. However, it is enough to only check the first element in the document. If it begins with a ``$`` sign and the rest of the document's elements do not, the server will throw an error. Note that it is required that an update document have at least one atomic modifier.

The ``replace`` family of operations require that the replacement document parameter MUST NOT begin with an atomic modifier. In practice, this means that introspection needs to happen on that document to enforce this. However, it is enough to only check the first element in the document. If it does not begin with a ``$`` sign but an element later on does, the server will throw an error.


Test Plan
======================================

See the `README <tests/README.rst>`_ for tests.

In addition, we have constructed some example usages in different languages that show how different implementations are able to conform to the specification and still look and feel idiomatic to a user.

* `C++ <examples/cpp/usage_example.cpp>`_
* `Javascript <examples/javascript/usage_example.js>`_
* `Java <examples/java/src/main/java/examples/MongoCollectionUsageExample.java>`_
* `Node <examples/node/usage_example.js>`_
* `PHP <examples/php/usage_example.php>`_


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
  Write concern is about indicating how writes are acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different write operations on the same collection would use a different write concern, potentially causing mismatched and out-of-sync data. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it.

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

Changes
=======

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

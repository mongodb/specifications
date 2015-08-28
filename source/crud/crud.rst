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
:Minimum Server Version: 2.4
:Last Modified: June 17, 2015

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

* When using an ``Options`` class, if multiple ``Options`` classes are structurally equatable, it is permissible to consolidate them into one with a clear name. For instance, it would be permissible to use the name ``UpdateOptions`` as the options for ``UpdateOne``, ``UpdateMany``, and ``ReplaceOne``.

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
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */
    aggregate(pipeline: Document[], options: Optional<AggregateOptions>): Iterable<Document>;

    /**
     * Gets the number of documents matching the filter.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    count(filter: Document, options: Optional<CountOptions>): Int64;

    /**
     * Finds the distinct values for a specified field across a single collection. 
     *
     * @see http://docs.mongodb.org/manual/reference/command/distinct/
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
     * @see http://docs.mongodb.org/manual/core/read-operations-introduction/
     */
    find(filter: Document, options: Optional<FindOptions>): Iterable<Document>;

  }

  class AggregateOptions {

    /**
     * Enables writing to temporary files. When set to true, aggregation stages 
     * can write data to the _tmp subdirectory in the dbPath directory.
     * The default is no value: the driver sends no "allowDiskUse" option to the
     * server with the "aggregate" command.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    allowDiskUse: Optional<Boolean>;

    /**
     * The number of documents to return per batch. 
     *
     * For servers < 2.6, this option is ignored as aggregation cursors are not available.
     * The default is no value: the driver sends no "batchSize" option to the server with
     * the "aggregate" command, thus accepting the server default batch size.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    batchSize: Optional<Int32>;

    /**
     * If true, allows the write to opt-out of document level validation. This only applies
     * when the $out stage is specified. If $out is not specified, this option should
     * be ignored.
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * The maximum amount of time to allow the query to run.
     * The default is no value: the driver sends no "maxTimeMS" option to the
     * server with the "aggregate" command.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    maxTimeMS: Optional<Int64>;

    /**
     * Indicates whether the command will request that the server provide results using a cursor.
     *
     * For servers < 2.6, this option is ignored as aggregation cursors are not available.
     * For servers >= 2.6, this option allows users to turn off cursors if necessary to aid in mongod/mongos upgrades.
     * The default value is true: the driver sends "cursor: {}" to the server with the "aggregate" command
     * by default.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */
    useCursor: Optional<Boolean>;

  }

  class CountOptions {

    /**
     * The index to use. The default is no hint.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    hint: Optional<(String | Document)>;

    /**
     * The maximum number of documents to count. The default is no limit.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    limit: Optional<Int64>;

    /**
     * The maximum amount of time to allow the query to run.
     * The default is no maxTimeMS.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * The number of documents to skip before counting. The default is no skip.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    skip: Optional<Int64>;

  }

  class DistinctOptions {

    /**
     * The maximum amount of time to allow the query to run.
     * The default is no maxTimeMS.
     *
     * @see http://docs.mongodb.org/manual/reference/command/distinct/
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
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    TAILABLE,
    /**
     * Combines the tailable option with awaitData, as defined below.
     *
     * Use with TailableCursor. If we are at the end of the data, block for a
     * while rather than returning no data. After a timeout period, we do return
     * as normal. The default is true.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    TAILABLE_AWAIT
  }

  class FindOptions {

    /**
     * Get partial results from a mongos if some shards are down (instead of throwing an error).
     *
     * The default in servers >= 3.2 is no value: no "allowPartialResults" option is sent with
     * the "find" command.
     *
     * In servers < 3.2, the Partial OP_QUERY flag defaults to false.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    allowPartialResults: Optional<Boolean>;
    
    /**
     * The number of documents to return per batch.
     *
     * This is combined with limit to create the OP_QUERY numberToReturn value.
     *
     * The default is no value: the driver accepts the server default batch size.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.batchSize/
     */ 
    batchSize: Optional<Int32>;

    /**
     * Attaches a comment to the query. If $comment also exists
     * in the modifiers document, the comment field overwrites $comment.
     * The default is no comment.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/meta/comment/
     */ 
    comment: Optional<String>;

    /**
     * Indicates the type of cursor to use. This value includes both
     * the tailable and awaitData options.
     *
     * The default in servers >= 3.2 is no value: no "awaitData" or "tailable"
     * option is sent with the "find" command.
     *
     * In servers < 3.2, the AwaitData OP_QUERY flag and the Tailable OP_QUERY
     * flag default to false.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    cursorType: Optional<CursorType>;

    /**
     * The maximum number of documents to return.
     *
     * This is combined with batchSize to create the OP_QUERY numberToReturn value.
     *
     * The default is no limit.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.limit/
     */
    limit: Optional<Int32>;

    /**
     * The maximum amount of time to allow the query to run. If $maxTimeMS also exists
     * in the modifiers document, the maxTimeMS field overwrites $maxTimeMS.
     * The default is no maxTimeMS.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/meta/maxTimeMS/
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Meta-operators modifying the output or behavior of a query.
     * The default is no modifers.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/query-modifier/
     */
    modifiers: Optional<Document>;

    /**
     * The server normally times out idle cursors after an inactivity period (10 minutes) 
     * to prevent excess memory use. Set this option to prevent that.
     *
     * The default in servers >= 3.2 is no value: no "noCursorTimeout" option is sent with
     * the "find" command.
     *
     * In servers < 3.2, the NoCursorTimeout OP_QUERY flag defaults to false.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    noCursorTimeout: Optional<Boolean>;

    /**
     * Internal replication use only - driver should not set
     *
     * The default in servers >= 3.2 is no value: no "oplogReplay" option is sent with
     * the "find" command.
     *
     * In servers < 3.2, the OplogReplay OP_QUERY flag defaults to false.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    oplogReplay: Optional<Boolean>;

    /** 
     * Limits the fields to return for all matching documents.
     * The default is no projection.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results/
     */
    projection: Optional<Document>;

    /**
     * The number of documents to skip before returning.
     *
     * In servers < 3.2, this is a wire protocol parameter that defaults to 0.
     *
     * The default in servers >= 3.2 is no skip: no "skip" option is sent with
     * the "find" command.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.skip/
     */
    skip: Optional<Int32>;

    /**
     * The order in which to return matching documents. If $orderby also exists
     * in the modifiers document, the sort field overwrites $orderby.
     * The default is no sort.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.sort/
     */ 
    sort: Optional<Document>;
  }

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Combining Limit and Batch Size for the Wire Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The OP_QUERY wire protocol only contains a numberToReturn value which drivers must calculate to get expected limit and batch size behavior. Subsequent calls to OP_GETMORE should use the user-specified batchSize or default to 0. Below is pseudo-code for calculating numberToReturn for OP_QUERY.

.. code:: typescript

  function calculateFirstNumberToReturn(FindOptions options) {
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

Because of this anomaly in the wire protocol, it is up to the driver to enforce the user-specified limit. Each driver MUST keep track of how many documents have been iterated and stop iterating once the limit has been reached. When the limit has been reached, if the cursor is still open, a driver MUST send the OP_KILLCURSORS wire protocol message.

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
     * NOTE: see the FAQ about the previous bulk API and how it relates to this.
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     * @see http://docs.mongodb.org/manual/reference/command/update/
     * @throws BulkWriteException
     */
    bulkWrite(requests: WriteModel[], options: Optional<BulkWriteOptions>): BulkWriteResult;

    /**
     * Inserts the provided document. If the document is missing an identifier,
     * the driver should generate one.
     *
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     * @throws WriteException
     */
    insertOne(document: Document, options: Optional<InsertOneOptions>): InsertOneResult;

    /**
     * Inserts the provided documents. If any documents are missing an identifier,
     * the driver should generate them.
     *
     * Note that this uses the bulk insert command underneath and should not
     * use OP_INSERT. This will be slow on < 2.6 servers, so document
     * your driver appropriately.
     *
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     * @throws BulkWriteException
     */
    insertMany(Iterable<Document> documents, options: Optional<InsertManyOptions>): InsertManyResult;

    /**
     * Deletes one document.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     * @throws WriteException
     */
    deleteOne(filter: Document): DeleteResult; 

    /**
     * Deletes multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     * @throws WriteException
     */
    deleteMany(filter: Document): DeleteResult;

    /**
     * Replaces a single document.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/update/
     * @throws WriteException
     */
    replaceOne(filter: Document, replacement: Document, options: Optional<UpdateOptions>): UpdateResult; 

    /**
     * Updates one document.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/update/
     * @throws WriteException
     */
    updateOne(filter: Document, update: Document, options: Optional<UpdateOptions>): UpdateResult;

    /**
     * Updates multiple documents.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/update/
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

  }

  class InsertOneOptions {

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

  }

  class InsertManyOptions {

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * If true, when an insert fails, return without performing the remaining 
     * writes. If false, when a write fails, continue with the remaining writes, if any. 
     * Defaults to true.
     */
    ordered: Boolean;

  }

  class UpdateOptions

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;

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
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     */
    document: Document;

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;
  }

  class DeleteOneModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     */
    filter: Document;

  }

  class DeleteManyModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     */
    filter: Document;

  }

  class ReplaceOneModel implements WriteModel {

    /**
     * The filter to limit the replaced document.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document;

    /**
     * The document with which to replace the matched document.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    replacement: Document;

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;

  }

  class UpdateOneModel implements WriteModel {
    
    /**
     * The filter to limit the updated documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document;

    /**
     * A document containing update operators.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    update: Update;

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Optional<Boolean>;

  }

  class UpdateManyModel implements WriteModel {
    
    /**
     * The filter to limit the updated documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document;

    /**
     * A document containing update operators.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    update: Update;

    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
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
     * Indicates whether this write result was ackowledged. If not, then all
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
     * Indicates whether this write result was ackowledged. If not, then all
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
     * Indicates whether this write result was ackowledged. If not, then all
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
     * Indicates whether this write result was ackowledged. If not, then all
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
     * Indicates whether this write result was ackowledged. If not, then all
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
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A document identifying the write concern setting related to the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    details: Document;

    /**
     * A description of the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    message: String;

  }

  class WriteError {

    /**
     * An integer value identifying the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    code: Int32;

    /**
     * A description of the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
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
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndDelete(filter: Document, options: Optional<FindOneAndDeleteOptions>): Document;

    /**
     * Finds a single document and replaces it, returning either the original or the replaced
     * document. The document to return may be null.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndReplace(filter: Document, replacement: Document, options: Optional<FindOneAndReplaceOptions>): Document;

    /**
     * Finds a single document and updates it, returning either the original or the updated
     * document. The document to return may be null.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
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
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Optional<Int64>;

    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

  }

  class FindOneAndReplaceOptions {
    
    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Optional<Int64>;

    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * When ReturnDocument.After, returns the replaced or inserted document rather than the original.
     * Defaults to ReturnDocument.Before.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    returnDocument: Optional<ReturnDocument>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

    /**
     * When true, findAndModify creates a new document if no document matches the query. The
     * default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    upsert: Optional<Boolean>;

  }

  class FindOneAndUpdateOptions {
    
    /**
     * If true, allows the write to opt-out of document level validation. 
     * 
     * On servers >= 3.2, the default is to not send a value. no 
     * "bypassDocumentValidation" option is sent with the "insert" command.
     *
     * On servers < 3.2, this option is ignored.
     */
    bypassDocumentValidation: Optional<Boolean>;
    
    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Optional<Int64>;
    
    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Optional<Document>;

    /**
     * When ReturnDocument.After, returns the updated or inserted document rather than the original.
     * Defaults to ReturnDocument.Before.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    returnDocument: Optional<ReturnDocument>;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Optional<Document>;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
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

Q: Why do the names of the fields differ from those defined on docs.mongodb.org?
  Documentation and commands often refer to same-purposed fields with different names making it difficult to have a cohesive API. In addition, occasionally the name was correct at one point and its purpose has expanded to a point where the initial name doesn't accurately describe its current function.

  In addition, responses from the servers are sometimes cryptic and used for the purposes of compactness. In these cases, we felt the more verbose form was desirable for self-documentation purposes.


Q: Where is read preference?
  Read preference is about selecting a server with which to perform a read operation, such as a query, a count, or an aggregate. Since all operations defined in this specification are performed on a collection, it's uncommon that two different read operations on the same collection would use a different read preference, potentially getting out-of-sync results. As such, the most natural place to indicate read preference is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose this selection filter to a user per operation for various reasons.  As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.

Q: Where is read concern?
  Read concern is about indicating how reads are handled. Since all operations defined in this specification are performed on a collection, it's uncommon that two different read operations on the same collection would use a different read cocnern, potentially causing mismatched and out-of-sync data. As such, the most natural place to indicate read concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose read concern to a user per operation for various reasons. As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.


Q: Where is write concern?
  Write concern is about indicating how writes are acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different write operations on the same collection would use a different write concern, potentially causing mismatched and out-of-sync data. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose write concern to a user per operation for various reasons. As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.


Q: How do I throttle unacknowledged writes now that write concern is longer defined on a per operation basis?
  Some users used to throttle unacknowledged writes by using a write concern every X number of operations. The proper way to handle this on >= 2.6 servers is to use the bulk write API. Users working with servers < 2.6 should manually send a ``getLastError`` command every X number of operations if the driver does not support write concerns per operation.


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
  Explain has been determined to be not a normal use-case for a driver. We'd like users to use the shell for this purpose. However, explain is still possible from a driver. For find, it can be passed as a modifier. Aggregate can be run using a runCommand method passing the explain option. In addition, server 2.8 offers an explain command that can be run using a runCommand method.

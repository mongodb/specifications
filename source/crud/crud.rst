.. role:: javascript(code)
  :language: javascript

===============
Driver CRUD API
===============

:Spec: 110
:Title: Driver CRUD API
:Authors: Craig Wilson
:Advisors: Tyler Brock, Jeremy Mikola, Jeff Yemin
:Status: Approved
:Type: Standards
:Minimum Server Version: 2.4
:Last Modified: Mar. 2, 2015

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

All drivers MUST offer the same options for each operation as defined in the following sections. This does not preclude a driver from offering more. The options parameter is optional. A driver SHOULD NOT require a user to specify optional parameters.

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
    aggregate(pipeline: Document[], options: AggregateOptions): Iterable<Document>;

    /**
     * Gets the number of documents matching the filter.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    count(filter: Document, options: CountOptions): Int64;

    /**
     * Finds the distinct values for a specified field across a single collection. 
     *
     * @see http://docs.mongodb.org/manual/reference/command/distinct/
     */
    distinct(fieldName: string, filter: Document, options: DistinctOptions): Iterable<any>;

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
    find(filter: Document, options: FindOptions): Iterable<Document>;

  }

  class AggregateOptions {

    /**
     * Enables writing to temporary files. When set to true, aggregation stages 
     * can write data to the _tmp subdirectory in the dbPath directory. The
     * default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    allowDiskUse: Boolean;

    /**
     * The number of documents to return per batch.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    batchSize: Int32;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    maxTimeMS: Int64;

    /**
     * Indicates if the results should be provided as a cursor. 
     *
     * The default for this value depends on the version of the server. 
     * - Servers >= 2.6 will use a default of true. 
     * - Servers < 2.6 will use a default of false. 
     * 
     * As with any other property, this value can be changed.
     *
     * @see http://docs.mongodb.org/manual/reference/command/aggregate/
     */ 
    useCursor: Boolean;

  }

  class CountOptions {

    /**
     * The index to use.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    hint: (String | Document);

    /**
     * The maximum number of documents to count.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    limit: Int64;

    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    maxTimeMS: Int64;

    /**
     * The number of documents to skip before returning the documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/count/
     */
    skip: Int64;

  }

  class DistinctOptions {

    /**
     * The maximum amount of time to allow the query to run. The default is infinite.
     *
     * @see http://docs.mongodb.org/manual/reference/command/distinct/
     */
    maxTimeMS: Int64;

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
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    allowPartialResults: Boolean;
    
    /**
     * The number of documents to return per batch.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.batchSize/
     */ 
    batchSize: Int32;

    /**
     * Attaches a comment to the query. If $comment also exists
     * in the modifiers document, the comment field overwrites $comment.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/meta/comment/
     */ 
    comment: String;

    /**
     * Indicates the type of cursor to use. This value includes both
     * the tailable and awaitData options.
     * The default is NON_TAILABLE.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    cursorType: CursorType;

    /**
     * The maximum number of documents to return.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.limit/
     */
    limit: Int32;

    /**
     * The maximum amount of time to allow the query to run. If $maxTimeMS also exists
     * in the modifiers document, the maxTimeMS field overwrites $maxTimeMS.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/meta/maxTimeMS/
     */
    maxTimeMS: Int64;

    /**
     * Meta-operators modifying the output or behavior of a query.
     *
     * @see http://docs.mongodb.org/manual/reference/operator/query-modifier/
     */
    modifiers: Document;

    /**
     * The server normally times out idle cursors after an inactivity period (10 minutes) 
     * to prevent excess memory use. Set this option to prevent that.
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    noCursorTimeout: Boolean;

    /**
     * Internal replication use only - driver should not set
     *
     * @see http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-query
     */
    oplogReplay: Boolean;

    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results/
     */
    projection: Document;

    /**
     * The number of documents to skip before returning.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.skip/
     */
    skip: Int32;

    /**
     * The order in which to return matching documents. If $orderby also exists
     * in the modifiers document, the sort field overwrites $orderby.
     *
     * @see http://docs.mongodb.org/manual/reference/method/cursor.sort/
     */ 
    sort: Document;
  }


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
    bulkWrite(requests: WriteModel[], options: BulkWriteOptions): BulkWriteResult;

    /**
     * Inserts the provided document. If the document is missing an identifier,
     * the driver should generate one.
     *
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     * @throws WriteException
     */
    insertOne(document: Document): InsertOneResult;

    /**
     * Inserts the provided documents. If any documents are missing an identifier,
     * the driver should generate them.
     *
     * Note that this uses the bulk insert command underneath and should not
     * use OP_INSERT. This will be slow on < 2.6 servers, so document
     * your driver appropriately.
     *
     * @see http://docs.mongodb.org/manual/reference/command/insert/
     * @throws WriteException
     */
    insertMany(Iterable<Document> documents, options: InsertManyOptions): InsertManyResult;

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
    replaceOne(filter: Document, replacement: Document, options: UpdateOptions): UpdateResult; 

    /**
     * Updates one document.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/update/
     * @throws WriteException
     */
    updateOne(filter: Document, update: Document, options: UpdateOptions): UpdateResult;

    /**
     * Updates multiple documents.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/update/
     * @throws WriteException
     */
    updateMany(filter: Document, update: Document, options: UpdateOptions): UpdateResult;

  }

  class BulkWriteOptions {

    /**
     * If true, when a write fails, return without performing the remaining 
     * writes. If false, when a write fails, continue with the remaining writes, if any. 
     * Defaults to true.
     */
    ordered: Boolean;

  }

  class InsertManyOptions {

    /**
     * If true, when an insert fails, return without performing the remaining 
     * writes. If false, when a write fails, continue with the remaining writes, if any. 
     * Defaults to true.
     */
    ordered: Boolean;

  }

  class UpdateOptions

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Boolean optional;

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
    document: Document required;

  }

  class DeleteOneModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     */
    filter: Document required;

  }

  class DeleteManyModel implements WriteModel {

    /**
     * The filter to limit the deleted documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/delete/
     */
    filter: Document required;

  }

  class ReplaceOneModel implements WriteModel {

    /**
     * The filter to limit the replaced document.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document required;

    /**
     * The document with which to replace the matched document.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    replacement: Document required;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Boolean optional;

  }

  class UpdateOneModel implements WriteModel {
    
    /**
     * The filter to limit the updated documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document required;

    /**
     * A document containing update operators.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    update: Update required;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Boolean optional;

  }

  class UpdateManyModel implements WriteModel {
    
    /**
     * The filter to limit the updated documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    filter: Document required;

    /**
     * A document containing update operators.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    update: Update required;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/update/
     */
    upsert: Boolean optional;

  }


Results
~~~~~~~

Unlike the models, the optional and required designations are for the implementer to decide how best their users should consume these results. For instance, the acknowledged property is defined for languages/frameworks without a sufficient optional type. Hence, a driver may choose to return an Optional<BulkWriteResult> such that unacknowledged writes don't have a value and acknowledged writes do have a value. 

.. note::
    If you have a choice, consider providing the acknowledged member and raising an error if the other fields are accessed in an unacknowledged write. Instead of users receiving a null reference exception, you have the opportunity to provide an informative error message indicating the correct way to handle the situation. For instance, "The insertedCount member is not available when the write was unacknowledged. Check the acknowledged member to avoid this error."

Finally, any result class with all optional parameters is ultimately optional as well. For instance, the ``InsertOneResult``, since it has all optional parameters, is also optional which allows for a driver to use "void" as the return value for the ``insertOne`` method.

.. code:: typescript
  
  class BulkWriteResult {

    /**
     * Indicates whether this write result was ackowledged. If not, then all
     * other members of this result will be undefined.
     */
    acknowledged: Boolean optional;

    /**
     * Number of documents inserted.
     */
    insertedCount: Int64 required;

    /**
     * Map of the index of the operation to the id of the inserted document.
     */
    insertedIds: Map<Int64, any> optional;

    /**
     * Number of documents matched for update.
     */
    matchedCount: Int64 required;

    /**
     * Number of documents modified.
     */
    modifiedCount: Int64 required;

    /**
     * Number of documents deleted.
     */
    deletedCount: Int64 required;

    /**
     * Number of documents upserted.
     */
    upsertedCount: Int64 required;

    /**
     * Map of the index of the operation to the id of the upserted document.
     */
    upsertedIds: Map<Int64, any> required;

  }

  class InsertOneResult {

    /**
     * Indicates whether this write result was ackowledged. If not, then all
     * other members of this result will be undefined.
     */
    acknowledged: Boolean optional;

    /**
     * The identifier that was inserted. If the server generated the identifier, this value
     * will be null as the driver does not have access to that data.
     */
    insertedId: any optional;

  }

  class InsertManyResult {

    /**
     * Indicates whether this write result was ackowledged. If not, then all
     * other members of this result will be undefined.
     */
    acknowledged: Boolean optional;

    /**
     * Map of the index of the inserted document to the id of the inserted document.
     */
    insertedIds: Map<Int64, any> optional;

  }

  class DeleteResult {

    /**
     * Indicates whether this write result was ackowledged. If not, then all
     * other members of this result will be undefined.
     */
    acknowledged: Boolean optional;

    /**
     * The number of documents that were deleted.
     */
    deletedCount: Int64 required;

  }

  class UpdateResult {

    /**
     * Indicates whether this write result was ackowledged. If not, then all
     * other members of this result will be undefined.
     */
    acknowledged: Boolean optional;

    /**
     * The number of documents that matched the filter.
     */
    matchedCount: Int64 required;

    /**
     * The number of documents that were modified.
     */
    modifiedCount: Int64 required;

    /**
     * The identifier of the inserted document if an upsert took place.
     */
    upsertedId: any required;

  }


Error Handling
~~~~~~~~~~~~~~

Below are defined the exceptions that should be thrown from the various write methods. Since exceptions across languages would be impossible to reconcile, the below definitions represent the fields and names for the information that should be present. Structure isn't important as long as the information is available.

.. note::
    The actual implementation of correlating, merging, and interpreting write errors from the server is not defined here. This spec is solely about the API for users.

.. code:: typescript

  /**
   * NOTE: Only one of writeConcernError or writeError will be populated at a time. Your driver must present the offending
   * error to the user.
   */
  class WriteException {

    /**
     * The error that occurred on account of write concern failure.
     */ 
    writeConcernError: WriteConcernError optional;

    /**
     * The error that occurred on account of a non-write concern failure.
     */
    writeError: WriteError optional;

  }

  class WriteConcernError {

    /**
     * An integer value identifying the write concern error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    code: Int32 required;

    /**
     * A document identifying the write concern setting related to the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    details: Document required;

    /**
     * A description of the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    message: String required;

  }

  class WriteError {

    /**
     * An integer value identifying the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    code: Int32 required;

    /**
     * A description of the error.
     *
     * @see http://docs.mongodb.org/manual/reference/method/WriteResult/
     */
    message: String required;

  }

  class BulkWriteException {

    /**
     * The requests that were sent to the server.
     */
    processedRequests: Iterable<WriteModel> optional;

    /**
     * The requests that were not sent to the server.
     */
    unprocessedRequests: Iterable<WriteModel> optional;

    /**
     * The error that occured on account of write concern failure. If the error was a Write Concern related, this field must be present.
     */ 
    writeConcernError: WriteConcernError optional;

    /**
     * The error that occured on account of a non-write concern failure. This might be empty if the error was a Write Concern related error.
     */
    writeErrors: Iterable<BulkWriteError> required;

  }

  class BulkWriteError : WriteError {

    /**
     * The index of the request that errored.
     */
    index: Int32 required;

    /**
     * The request that errored.
     */
    request: WriteModel optional;

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
    findOneAndDelete(filter: Document, options: FindOneAndDeleteOptions): Document;

    /**
     * Finds a single document and replaces it, returning either the original or the replaced
     * document. The document to return may be null.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndReplace(filter: Document, replacement: Document, options: FindOneAndReplaceOptions): Document;

    /**
     * Finds a single document and updates it, returning either the original or the updated
     * document. The document to return may be null.
     * 
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     * @throws WriteException
     */
    findOneAndUpdate(filter: Document, update: Document, options: FindOneAndUpdateOptions): Document;

  }

  enum ReturnDocument {
    /**
     * Indicates to return the document before the update, replacement, or insert occured.
     */
     Before,
    /**
     * Indicates to return the document after the update, replacement, or insert occured.
     */
     After
  }

  class FindOneAndDeleteOptions {
    
    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Int64 optional;

    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Document optional;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Document optional;

  }

  class FindOneAndReplaceOptions {
    
    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Int64 optional;

    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Document optional;

    /**
     * When ReturnDocument.After, returns the replaced or inserted document rather than the original.
     * Defaults to ReturnDocument.Before.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    returnDocument: ReturnDocument optional;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Document optional;

    /**
     * When true, findAndModify creates a new document if no document matches the query. The
     * default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    upsert: Boolean optional;

  }

  class FindOneAndUpdateOptions {
    
    /**
     * The maximum amount of time to allow the query to run.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */ 
    maxTimeMS: Int64 optional;
    
    /** 
     * Limits the fields to return for all matching documents.
     *
     * @see http://docs.mongodb.org/manual/tutorial/project-fields-from-query-results
     */
    projection: Document optional;

    /**
     * When ReturnDocument.After, returns the updated or inserted document rather than the original.
     * Defaults to ReturnDocument.Before.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    returnDocument: ReturnDocument optional;

    /**
     * Determines which document the operation modifies if the query selects multiple documents.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    sort: Document optional;

    /**
     * When true, creates a new document if no document matches the query. The default is false.
     *
     * @see http://docs.mongodb.org/manual/reference/command/findAndModify/
     */
    upsert: Boolean optional;

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


Q & A
=====

Q: Why do the names of the fields differ from those defined on docs.mongodb.org?
  Documentation and commands often refer to same-purposed fields with different names making it difficult to have a cohesive API. In addition, occasionally the name was correct at one point and its purpose has expanded to a point where the initial name doesn't accurately describe its current function.

  In addition, responses from the servers are sometimes cryptic and used for the purposes of compactness. In these cases, we felt the more verbose form was desirable for self-documentation purposes.


Q: Where is read preference?
  Read preference is about selecting a server with which to perform a read operation, such as a query, a count, or an aggregate. Since all operations defined in this specification are performed on a collection, it's uncommon that two different read operations on the same collection would use a different read preference, potentially getting out-of-sync results. As such, the most natural place to indicate read preference is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose this selection filter to a user per operation for various reasons.  As noted before, it is permitted to specify this, along with other driver-specific options, in some alternative way.


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

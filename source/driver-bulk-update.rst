Bulk API Spec
=============

:Authors: Christian Kvalheim
:Status: Deprecated
:Type: Standards
:Last Modified: October 9, 2015

.. contents::

Changes from previous versions
------------------------------

Deprecated in favor of the *Driver CRUD API*.

v0.7
~~~~
* Clarify that "writeConcernErrors" field is plural

v0.6
~~~~
* First public version of the specification.
* Merged in Test Cases from QA tickets
* Specification cleanup and increased precision

v0.5
~~~~
* Specification cleanup and increased precision
* Suggested Error handling for languages using commonly raising exceptions
* Narrowed writeConcern reporting requirement

v0.4
~~~~
* Renamed nUpdated to nMatched as to reflect that it's the number of matched documents not the number of modified documents.


Bulk Operation Builder
----------------------

Starting a bulk operation can be done in two ways.

.. code:: javascript

    initializeUnorderedBulkOp()     -> Bulk   - Initialize an unordered bulk
    initializeOrderedBulkOp()       -> Bulk   - Initialize an ordered bulk

Operations Possible On Bulk Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Available operations follow the fluent API for insert, update and
remove.

.. code:: javascript

    /**
     * Update one document matching the selector
     */
    bulk.find({a : 1}).updateOne({$inc : { x : 1 }});

    /**
     * Update all documents matching the selector
     */
    bulk.find({a : 2}).update({$inc : { x : 2 }});

    /**
     * Update all documents
     * Note that find() is prohibited; the query is required
     */
    bulk.find({}).update({$inc : { x : 2 }});

    /**
     * Replace entire document (update with whole doc replace)
     */
    bulk.find({a : 3}).replaceOne({ x : 3 });

    /**
     * Update one document matching the selector or upsert
     */
    bulk.find({a : 1}).upsert().updateOne({$inc : { x : 1 }});

    /**
     * Update all documents matching the selector or upsert
     */
    bulk.find({a : 2}).upsert().update({$inc : { x : 2 }});

    /**
     * Replaces a single document matching the selector or upsert
     */
    bulk.find({a : 3}).upsert().replaceOne({ x : 3 });

    /**
     * Remove a single document matching the selector
     */
    bulk.find({a : 4}).removeOne();

    /**
     * Remove all documents matching the selector
     */
    bulk.find({a : 5}).remove();

    /**
     * Remove all documents
     * Note that find() is prohibited; the query is required
     */
    bulk.find({}).remove();

    /**
     * Insert a document
     */
    bulk.insert({ x : 4 });

    /**
     * Execute the bulk operation, with an optional writeConcern
     * overwriting the default w:1. A descriptive error should be
     * raised if execute is called more than once or before any
     * operations have been added.
     */
    writeConcern = { w: 1, wtimeout: 100 }
    bulk.execute(writeConcern);

Current shell implementation
----------------------------
The shell implementation serves as a guide only. One main difference between the shell implementation and a proper driver implementation 
is that unordered bulk operations are not optimized by re-ordering the writes; only the execution semantics are kept correct. 
You can find it here:

https://github.com/mongodb/mongo/blob/master/src/mongo/shell/bulk_api.js

If you need more information about the actual write command you can find the specification at the following location

https://github.com/mongodb/specifications/blob/master/source/server_write_commands.rst

Modes of Execution
------------------
The write commands have a new option called **ordered** that is a boolean. **ordered** replaces **continueOnError** but with slightly different semantics.

### ordered = true
If the driver sets **ordered = true** all operations will be executed serially in the write command and the operation will abort on the first error. So given the 3 following operations.

.. code:: javascript

    bulk.insert({a:1})
    bulk.insert({a:2})
    bulk.find({a:2}).update({$set: {a:1}}) // Clashes with unique index
    bulk.find({a:1}).remove()

With **ordered = true** the bulk operation will terminate after the update as it errors out. With **ordered = true** the driver will receive only a single error.

### ordered = false
If the driver sets **ordered = false** all operations might be applied in parallel by the server. The server will execute all the operations and return all errors created by the operations. So given the 4 following operations.

.. code:: javascript

    bulk.insert({a:1})
    bulk.insert({a:2})
    bulk.find({a:2}).update({$set: {a:1}}) // Might clash with unique index
    bulk.find({a:3}).remove
    bulk.find({a:2}.update({$set: {a:1}}) // Might clash with unique index

Due to the write operations potentially happening concurrently there is no way to determine the final state of the bulk operation above. If **insert({a:1})** happens before the two updates we will get 2 duplicate key index errors from the two update operations. If one of the updates happen first the insert will error out. By setting **ordered** to false we are trading off guaranteed order of execution for increased parallelization.

Ordered Bulk Operations
-----------------------

To start the ordered bulk operation call.

.. code:: javascript

    initializeOrderedBulkOp() -> bulk

The ordered bulk operation guarantees the order of writes for a mixed set of operations. This means the driver needs to ensure that all operations are performed in the order they were added.

Consider the following set of operations:

.. code:: javascript

    var bulk = db.c.initializeOrderedBulkOp()
    bulk.insert({a : 1})
    bulk.insert({a : 2})
    bulk.insert({a : 3})
    bulk.find({a : 2}).upsert().updateOne({$set : { a : 4 }});
    bulk.find({a : 1}).removeOne();
    bulk.insert({a : 5})
    bulk.execute({w : 1})

This will generate the following sequence of writes to the server.

1. Insert write command
2. Update write command
3. Remove write command
4. Insert write command

One thing to note is that if a write command goes over the maximum number of documents or maxBSONMessageSize for an individual write command it needs to be split into multiple as for unordered bulks.

.. NOTE::
  **ContinueOnError** Ordered operations are synonymous with
  continueOnError = false. There is no way to specify a different
  value for continueOnError.

Unordered Bulk Operations
-------------------------

To start the unordered bulk operation call:

.. code:: javascript

    initializeUnorderedBulkOp() -> bulk

The unordered bulk operation does not guarantee order of execution of any added write operations. If you have the following code.

.. code:: javascript

    var bulk = db.c.initializeUnorderedBulkOp()
    bulk.insert({_id : 1})
    bulk.find({_id : 2}).updateOne({$inc : { x : 1 }});
    bulk.find({_id : 3}).removeOne();
    bulk.insert({_id : 4})
    bulk.find({_id : 5}).updateOne({$inc : { x : 1 }});
    bulk.find({_id : 6}).removeOne();
    bulk.execute({w:1})

Internally the driver will execute 3 write commands. One each for the inserts, updates and removes. It's important to note that the write commands could be executed in any order.

.. NOTE::
  **ContinueOnError** Unordered operations are synonymous with
  continueOnError = true. There is no way to specify a different
  value for continueOnError.


Request Size Limits
-------------------

Supporting unlimited batch sizes poses two problems - the BSONObj internal size limit is 16 MiB + small overhead (for commands), and a small write operation may have a much larger response.  In order to ensure a batch can be correctly processed, two limits must be respected.

Both of these limits can be found using hello or legacy hello:

* ``maxBsonObjectSize`` : currently 16 MiB, this is the maximum size of writes (excepting command overhead)
  that should be sent to the server.  Documents to be inserted, query documents for updates and 
  deletes, and update expression documents must be <= this size.

  Batches containing more than one insert, update, or delete must be less than ``maxBsonObjectSize``.
  Note that this means a single-item batch can exceed ``maxBsonObjectSize``.  The additional overhead of
  the command itself is guaranteed not to trigger an error from the server, except in the case of 
  `SERVER-12305 <https://jira.mongodb.org/browse/SERVER-12305>`_.

* ``maxWriteBatchSize`` : currently 1000, this is the maximum number of inserts, updates, or deletes that 
  can be included in a write batch.  If more than this number of writes are included, the server cannot
  guarantee space in the response document to reply to the batch. 

If the batch is too large in size or bytes, the command may fail. The bulk API should ensure that this does not happen by splitting a batch into multiple batches of the same type if any of the limits are hit.


On Bulk Execution
-----------------

A descriptive error should be raised if ``execute`` is called more than once.

A descriptive error should be raise if ``execute`` is called before any operations have been added.


Possible Implementation
-----------------------

One possible solution for serialization of bulk operations is to serialize some preamble and then to incrementally serialize and append each document to the collected message. The command wrapper has the array argument last so that the programmer can append to it. As you incrementally serialize, first check the collected size plus the incremental size.

If it is less than maxBsonObjectSize (incorporate additional headroom for your implementation), you can safely append and the message will be accepted by the server. If it exceeds maxBsonObjectSize, you should "finish" (without appending, updating the BSON array and document sizes) and execute the collected message. A new write command message will be serialized.

The un-appended incremental serialization from before will be appended on the new message. Continue incremental serialization, appending, and execution as above until the bulk operation is completed. Your implementation may need additional headroom for whatever is not already in the preamble, e.g., write concern, finish bytes, etc.

There are two maximum write command sizes a driver needs to take into account. The first one is **maxBsonObjectSize** that defines the maximum size of a single write command. The current tolerance is **maxBsonObjectSize** + 16K. If the driver sends a message that overflows this tolerance the server will respond with an error. 

The second value is the **maxWriteBatchSize** value which specifies the maximum number of operations allowed in a single write command. In 2.6 this is currently set to **1000** operations. If the driver sends a write command with more than **maxWriteBatchSize** operations in it, the server will error out.

To avoid these errors the driver needs to split write commands if they overflow the two cases into one or more new write commands.

On Errors
=========

It's important to understand the way the processing of commands happens on the server to understand the possible error scenarios. Let's look at the processing pipeline.

Validate BSON/Auth -> Write Operations -> Apply Write Concern

The first step will abort the operation completely with no changes applied to Mongo. An error at this stage will be top level an will mean no attempt was made to process the command. This also uniquely sets **ok** to **0**.

.. code:: javascript

  {
    "ok" : 0,
    "code" : 13,
    "errmsg": "Authentication error"
  }

If the first step passes with no errors there might be a command level error such as a duplicate key error. This is a write error and will return an error results containing the **writeErrors** field.

.. code:: javascript

  {
    "ok" : 1,
    "n" : 0,
    "writeErrors" : [
      {
        "index" : 0,
        "code" : 11000,
        "errmsg" : "DuplicateKey insertDocument :: caused by :: 11000 E11000 duplicate key error index: test.test.$a_1  dup key: { : 1 }"
      }
    ],
  }

In the case of an **ordered** bulk operation you'll only ever get a single write error as the execution of the command will stop at the first error. In an **unordered** bulk operation you might have more than one.

The last step of applying the write concern can also cause an error. Given a write concern **{w:5, wtimeout:1000}** where there is only 3 servers in the replicaset, the write concern can never be fulfilled and will return an error. An example server response might be:

.. code:: javascript

  {
    "ok" : 1,
    "n" : 1,
    "writeConcernError" : {
      "code" : 64,
      "errmsg" : "...."
    }
  }

Notice how write concern is just a single error for the whole command. Getting a writeConcernError does not mean the items were not applied, it means the write concern could not be fulfilled. In the example above **n** is still **1**.

It's fair to consider the server response field **writeErrors** to be hard errors while **writeConcernError** is a soft error.

Merging Results
===============

Handling errors
---------------
Handling the merging of errors is most easily expressed with some examples.

Handling Write Errors
~~~~~~~~~~~~~~~~~~~~~

Consider the following following bulk write operation:

.. code:: javascript

  collection.ensureIndex({a:1}, {unique:true})
  var bulk = collection.initializeOrderedBulkOp()
  bulk.insert({a:1})
  bulk.insert({a:2})
  bulk.find({a:2}).upsert().update({$set:{a:1}})
  bulk.insert({a:3})
  bulk.execute()

This operation will only execute the three first operations (the first two inserts and an upsert)
before stopping due to a duplicate key error. The merged result would look something like this:

.. code:: javascript

  {
    "nInserted" : 2,
    "nUpserted" : 0,
    "nMatched" : 0,
    "nModified" : 0,
    "nRemoved" : 1,
    "upserted" : [ ]
    "writeErrors" : [
      {
        "index" : 2,
        "code" : 11000,
        "errmsg" : "DuplicateKey insertDocument :: caused by :: 11000 E11000 duplicate key error index: test.test.$a_1  dup key: { : 1 }"
      }
    ]
    "writeConcernErrors": []
  }

In this situation the client should throw a single error and stop processing.

Handling Write Concern Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write concern is applied after the server side execution of the write operations.

This means that replication failure or other forms of writeConcernErrors should not affect the execution of the batch
but simply serve as an indication that the write concern has not been met.

If there is no write concern error the bulk result's "writeConcernErrors" array is empty.

When the bulk operation is implemented using legacy opcodes, no server error
code is available. The server's getlasterror response is like:

.. code:: javascript

  {
    "ok" : 1,
    "wtimeout": true,
    "err": "timeout"
  }

In this case the driver must construct a writeConcernErrors array containing one error document with code 64,
and the "err" field from the getlasterror response as the errmsg.

An example with "w: 5" and fewer than 5 replicas:

.. code:: javascript

  var bulk = collection.initializeOrderedBulkOp()
  bulk.insert({a:1})
  bulk.execute({w:5, wtimeout:1})

The expected result from these operations are.

.. code:: javascript

  {
    "nInserted" : 1,
    "nUpserted" : 0,
    "nMatched" : 0,
    "nModified" : 0,
    "nRemoved" : 0,
    "upserted" : [ ]
    "writeErrors" : [ ],
    "writeConcernErrors": [{
      "code": 64,
      "waiting for replication timed out",
    }]
  }

.. note:: The example output is from MongoDB 2.6. In MongoDB 2.4 the driver supplies the error code 64, and the error message is "timeout". Starting in MongoDB 3.0, the writeConcernError code is 100 and the message is "Not enough data-bearing nodes".

General rule of handling errors
-------------------------------

1. A top level error means the whole command failed and should cause a command failure error.
2. For unordered bulk operations all write Errors should be rewritten and merged together.
3. For ordered bulk operations the returned write Error should be rewritten and returned.
4. Write Concern errors should not halt the processing of **ordered** bulk operations.

Merging write errors
--------------------

A bulk operation might involve multiple write commands.  Each write command could potentially return write errors and/or a write concern error. Each error in the **writeErrors** array contains an index pointing to the original document position in the write command document that caused it.

Consider the following bulk operation

.. code:: javascript

    collection.ensureIndex({a:1}, {unique:true})
    var bulk = db.c.initializeOrderedBulkOp()
    bulk.insert({a:1})
    bulk.insert({a:2})
    bulk.find({a:2}).updateOne({$set : { a : 1 }});
    bulk.find({a:4}).removeOne();
    bulk.execute({w:1})

The operation

.. code:: javascript

    bulk.find({a:2}).updateOne({$set : { a : 1 }});

causes an error

.. code:: javascript

  {
    "ok" : 1,
    "nModified" : 0,
    "n" : 0,
    "writeErrors" : [
      {
        "index" : 0,
        "code" : 11000,
        "errmsg" : "DuplicateKey insertDocument :: caused by :: 11000 E11000 duplicate key error index: test.test.$a_1  dup key: { : 1 }"
      }
    ]
  }

In the returned result, the **index** variable of the error points to document **0** from the update where it failed during execution. However in the original chain of operations the **update** operation is the third (**index 2**). To correctly correlate the errors to the user-provided order we need to rewrite the error to point to the correct index so the user can identify what document caused the error. So in this the error aspect of the final result will look like.

.. code:: javascript

  {
    "ok" : 1,
    "nModified" : 0,
    "n" : 2,
    "writeErrors" : [
      {
        "index" : 2,
        "code" : 11000,
        "errmsg" : "DuplicateKey insertDocument :: caused by :: 11000 E11000 duplicate key error index: test.test.$a_1  dup key: { : 1 }"
      }
    ]
  }

Notice the **index: 2** correctly pointing to the original document.

To correctly handle the merging the driver needs to keep track of the original indexes and how they map to the errors returned by the write commands. There might be a need to keep an index in memory to be able to correctly handle the mapping.

Write concern errors
--------------------

Each writeConcernError document received from a server operation (either a write command or legacy write) is appended to the bulk result's "writeConcernErrors" array:

.. code:: javascript

    var bulk = db.c.initializeOrderedBulkOp()
    bulk.insert({a:1})
    bulk.insert({a:2})
    bulk.find({a:1}).remove()
    bulk.execute({w:5, wtimeout:100})

The outcome on MongoDB 2.6 with fewer than 5 replicas is similar to:

.. code:: javascript

  {
    "nInserted" : 2,
    "nUpserted" : 0,
    "nMatched" : 0,
    "nModified" : 0,
    "nRemoved" : 1,
    "upserted" : [ ]
    "writeErrors" : [ ],
    "writeConcernErrors": [{
      "code": 64,
      "waiting for replication timed out",
    }, {
      "code": 64,
      "waiting for replication timed out",
    }]
  }

If there is no write concern error the bulk result's "writeConcernErrors" array is empty.

.. note:: Previous versions of this spec were ambiguous about reporting writeConcernErrors. Some clients include a singular field "writeConcernError" in bulk results; the singular form is now deprecated and an array called "writeConcernErrors" is required.

Handling upserts
----------------

When performing updates with upsert true the write command might return an upserted field. If it's a single document update command that causes an upsert it will look like.

.. code:: javascript
    
    {
        ok: 1
      , nModified: 0
      , n: 1      
      , upserted: {index:0, _id:ObjectId(".....")}
    }

On the other hand if we are upserting a series of documents the **upserted**  field will contain an array of the results. Given an update command that causes 2 upserts the result will look like.

.. code:: javascript

    {
        ok: 1
      , nModified: 0
      , n: 2
      , upserted: [
          {index:0, _id:ObjectId(".....")}
        , {index:1, _id:ObjectId(".....")}
      ]
    }

As in the case of errors the driver needs to rewrite the indexes for the upserted values to merge the results together into the final result so they reflect the initial order of the updates in the user specified batch.

Reporting Errors
================

Exceptions
----------

Depending on the language and platform there are different semantics on how to raise errors. For languages that usually raise exceptions it's recommended that an exception be raised when an ordered bulk operation fails.

Given the following scenario

.. code:: javascript

  collection.ensureIndex({a:1}, {unique:true})
  var bulk = collection.initializeOrderedBulkOp()
  bulk.insert({a:1})
  bulk.insert({a:1})
  bulk.execute({w:5, wtimeout:1})

In languages where the rule is to report errors by throwing an exception the duplicate insert should cause an exception to be raised when execute is called.

In the case of an unordered bulk operation the exception should be raised after the bulk has finished executing. It's important to differentiate between a **write** error and **write concern** error if exceptions are used to differentiate between the **hard** error of a write error and the **soft** error caused by a write concern error.

Callbacks
---------

Callback based languages or platform should return a results object containing the aggregated state of the bulk operations. Some platforms like Node.js supports callbacks with the format **function(err, object)**. In this case the result object should be returned as the err field if it contains any errors, only returning in the object field if no write or write concern errors happened.

Results Object
==============

The shell and **Node.js** implements the result as a custom object wrapping the results. This is to simplify the access to the internal state of the merged results. It serves mostly as an example as different languages might implement the results differently depending on their chosen error mechanism. F.ex it might make sense to throw an exception if the command fails at the authentication stage versus a duplicate key error on one of the operations in a bulk operation.

It keeps track of several aggregated values

========= =============================================================
field     description
========= =============================================================
nInserted Number of inserted documents
nUpserted Number of upserted documents
nMatched  Number of documents matched for update
nModified Number of documents actually changed by update
nRemoved  Number of documents removed
========= =============================================================

nMatched is equivalent to the "n" field in the getLastError response after a legacy update. nModified is quite different from "n". nModified is incremented only when an update operation actually changes a document.

For example, if a document has `x: 1` and we update it with `{$set: {x: 1}}`, nModified is not incremented for that document.

The WriteError's are wrapped in their own wrapper that also contains the operation that caused the error to happen. Similarly the WriteConcernError is a simple wrapper around the result to ensure it's read only.

A client may optionally provide a method to merge writeConcernErrors into one, analogous to how mongos does.

.. code:: javascript

  var WRITE_CONCERN_ERROR = 64;

  /**
   * Wraps the error
   */
  var WriteError = function(err) {
    if(!(this instanceof WriteError)) return new WriteError(err);

    // Define properties
    defineReadOnlyProperty(this, "code", err.code);
    defineReadOnlyProperty(this, "index", err.index);
    defineReadOnlyProperty(this, "errmsg", err.errmsg);

    //
    // Define access methods
    this.getOperation = function() {
      return err.op;
    }
  }

  /**
   * Wraps a write concern error
   */
  var WriteConcernError = function(err) {
    if(!(this instanceof WriteConcernError)) return new WriteConcernError(err);

    // Define properties
    defineReadOnlyProperty(this, "code", err.code);
    defineReadOnlyProperty(this, "errmsg", err.errmsg);
  }

  /**
   * Wraps the result for the commands
   */
  var BulkWriteResult = function(bulkResult) {
    // Define properties
    defineReadOnlyProperty(this, "ok", bulkResult.ok);
    defineReadOnlyProperty(this, "nInserted", bulkResult.nInserted);
    defineReadOnlyProperty(this, "nUpserted", bulkResult.nUpserted);
    defineReadOnlyProperty(this, "nMatched", bulkResult.nMatched);
    defineReadOnlyProperty(this, "nModified", bulkResult.nModified);
    defineReadOnlyProperty(this, "nRemoved", bulkResult.nRemoved);

    //
    // Define access methods
    this.getUpsertedIds = function() {
      return bulkResult.upserted;
    }

    this.getUpsertedIdAt = function(index) {
      return bulkResult.upserted[index];
    }

    this.getRawResponse = function() {
      return bulkResult;
    }

    this.hasWriteErrors = function() {
      return bulkResult.writeErrors.length > 0;
    }

    this.getWriteErrorCount = function() {
      return bulkResult.writeErrors.length;
    }

    this.getWriteErrorAt = function(index) {
      if(index < bulkResult.writeErrors.length) {
        return bulkResult.writeErrors[index];
      }
      return null;
    }

    this.hasWriteConcernError = function() {
      return bulkResult.writeConcernErrors.length > 0;
    }

    //
    // Determine if we have any errors
    this.hasErrors = function() {
      return this.hasWriteErrors() || this.hasWriteConcernError();
    }

    //
    // Get all errors
    this.getWriteErrors = function() {
      return bulkResult.writeErrors;
    }

    this.getWriteConcernError = function() {
      if(bulkResult.writeConcernErrors.length == 0) {
        return null;
      } else if(bulkResult.writeConcernErrors.length == 1) {
        // Return the error
        bulkResult.writeConcernErrors[0];
      } else {

        // Combine the errors
        var errmsg = "";
        for(var i = 0; i < bulkResult.writeConcernErrors.length; i++) {
          var err = bulkResult.writeConcernErrors[i];
          if (i != 0) {
            errmsg = errmsg + " and ";
          }

          errmsg = errmsg + '"' + err.errmsg + '"';
        }

        return new WriteConcernError({ errmsg : errmsg, code : WRITE_CONCERN_ERROR });
      }
    }

    this.isOK = function() {
      return bulkResult.ok == 1;
    }
  }

Pre 2.6 Support
===============

The batch API is required to work with pre **2.6**. This means detecting in the driver if the server supports the new write commands and downgrading to existing **OP_INSERT/OP_UPDATE/OP_REMOVE** if it does not.

Legacy servers don't report nModified for updates, and it is impossible for the driver to simulate it: nModified must be equal to the number of documents that are actually different after an update, but legacy servers only report the number of documents matched. The driver must therefore set the result's nModified field to null, or omit the field, when it executes a bulk operation against a legacy server. In static languages where nModified is an integer-type property on bulk results, an exception must be thrown if a user accesses the nModified property after executing a bulk operation on a legacy server.

One important aspect to keep in mind is that the existing **bulk** insert operation cannot be used as you need to retrieve the **getLastError** results for each individual operation. Thus the driver must execute inserts one by one.

Another important aspect to keep in mind is that a replication error can be signaled several ways by the **getLastError** result. The following error codes for the field code are an indicator of a replication error.

========= =============================================================
Code      Description
========= =============================================================
50        Operation exceeded time limit.
13475     Operation exceeded time limit.
16986     Operation exceeded time limit.
16712     Operation exceeded time limit.
========= =============================================================

Thee are also some some errors only detectable by inspecting the **errmsg** field.

====================  =============================================================
ErrMsg                Description
====================  =============================================================
exceeded time limit   Operation exceeded time limit.
execution terminated  Operation exceeded time limit.
====================  =============================================================

If an error does not return a code the driver can set the returned value to **8** (unknown error).  A BSON serializing error should be marked with **22** (illegal BSON).

There are some codes that don't match up between the **2.6** and existing servers. The suggestion is to not attempt to rewrite these errors as it will make the code very brittle. Some slight differences in error codes
and error messages between the write commands and the legacy operations are acceptable.

nModified
---------

The 2.6 server includes "nModified" in its response to an "update" command. The server increments nModified only when an "update" command has actually changed a document.
For example, if a document already has `x: 1` and you update it with `{$set: {x: 1}}`,
nModified is not incremented.
nModified is impossible to simulate with OP_UPDATE, which returns only "n",
the number of matched documents.

**Legacy writes**: The result of a bulk operation that uses legacy opcodes must set
nModified to NULL, or omit the field.
If your language is constrained such that you must include the field,
then user code should get an exception when accessing the field if you're talking to a legacy server.

**Mixed-version sharded cluster**:
When a client executes an "update" command on a 2.6 mongos,
and mongos executes it against some 2.4 mongods,
mongos omits nModified from the response, or sets nModified to NULL.
(We don't yet know which: `SERVER-13001`_)
If the client does a series of "update" commands within the same bulk operation against the same mongos,
some responses could include nModified and some won't,
depending on which mongods the mongos sent the operation to.
The driver algorithm for merging results, when using write commands, in pseudocode:

.. code:: javascript

    full_result = {
        "writeErrors": [],
        "writeConcernErrors": [],
        "nInserted": 0,
        "nUpserted": 0,
        "nMatched": 0,
        "nModified": 0,
        "nRemoved": 0,
        "upserted": [],
    }

    for each server response in all bulk operations' responses:
        if the operation is an update:
            if the response has a non-NULL nModified:
                if full_result has a non-NULL nModified:
                    full_result['nModified'] += response['nModified']
            else:
                # If any call does not return nModified we can't report
                # a valid final count so omit the field completely.
                remove nModified from full_result, or set to NULL

.. _SERVER-13001: https://jira.mongodb.org/browse/SERVER-13001

Questions & Answers
===================
**Question:** I'm writing my own driver should I support legacy downgrading.
**Answer:** Legacy downgrading is explained to help people support pre 2.6 servers but is not mandated for anything but the official drivers.

**Answer:** Changes where made to GLE in 2.6 that makes the error reporting more consistent. Downgrading will only correctly work against 2.4.X or earlier.

**Question:** My downgrading code breaks with 2.6

**Answer:** Changes where made to GLE in 2.6 that makes the error reporting more consistent. Downgrading will only correctly work against 2.4.X or earlier.

**Question:** Will there be any way for a user to set the number of wire operations a bulk operation will take (for debugging purposes).

**Answer:** No.

**Question:** Will there be support for .explain() with the bulk
interface?

**Answer:** Not for 2.6. It may be added with a later release along with
server support for mixed operations in a single bulk command

**Question:** The definition for unordered introduces indeterminism to the operation.
For example, what is the state of the collection after:

.. code:: javascript

    var bulk = db.c.initializeBulkOp()
    bulk.insert({_id : 1, x : 1})
    bulk.find({_id : 1}).updateOne({$inc : { x : 1 }});
    bulk.find({_id : 1}).removeOne();
    bulk.execute({w:1})

You could end up with either {_id : 1, x : 1}, {_id : 1, x : 2}, or no document at all,
depending on the order that the operations are performed in.

**Answer:** This is by design and definition. If the order matters then don't use an unordered bulk operation. No order will be defined or respected in an unordered operation.

**Question:** What should the driver do when an **ordered** bulk command is split into multiple write commands and an error happens?

**Answer:** If it's an **ordered** bulk command that is split into multiple write commands the driver should not send any remaining write commands after encountering the first error.

**Question:** What should the driver do when an **unordered** bulk command is split into multiple write commands and an error happens?

**Answer:** It's important to note that if the command is an **unordered** bulk command and it's split into multiple write command it should continue processing all the write commands even if there are errors.

**Question:** Does the driver need to merge errors from split write commands?

**Answer:** Yes

**Question:** Is find() with no argument allowed?

**Answer:** No, a selector is required for find() in the Bulk API.

**Question:** Is find({}) with an empty selector allowed?

**Answer:** Yes, updating or removing all documents using find({}) is allowed.

**Question:** My unordered bulk operation got split into multiple batches that all reported a write concern error. Should I report all of the write concern errors ?

**Answer:** Yes, combined into an array called "writeConcernErrors".

Detailed Test Cases
===================

These Test cases in this section serve the purpose of helping you validate the correctness of your **Bulk API** implementation.

INSERT
------

Test Case 1:
    Dynamic languages: raise error if wrong arg type
        initializeUnorderedBulkOp().insert('foo') throws a reasonable error
        
        initializeUnorderedBulkOp().insert([{}, {}]) throws a reasonable error: we can’t do a bulk insert with an array
        
        Same for initializeOrderedBulkOp().

Test Case 2:
    Insert not allowed with find({}):
        initializeUnorderedBulkOp().find({}).insert({}) is a type error.
        
        Same for initializeOrderedBulkOp().    

Test Case 3:
    Key validation, no $-prefixed keys allowed:
        batch = initializeUnorderedBulkOp().insert({$key: 1})
        
        bulk.execute() throws reasonable error (server does the validation)
        
        Same for initializeOrderedBulkOp().

Test Case 4:
    Inserting a document succeeds and returns 'nInserted’ of 1:
        Empty collection.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.insert({_id: 1})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 1,
                "nUpserted" : 0,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        Collection contains only {_id: 1}.
        
        Same for initializeOrderedBulkOp().

Test Case 5:
    The driver generates _id client-side for inserted documents:
        Empty collection.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.insert({})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 1,
                "nUpserted" : 0,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

            _id = collection.findOne()._id
            // pid = bytes 7 and 8 (counting from zero) of _id, as big-endian unsigned short
            pid == my PID

        Alternatively, just watch the server log or mongosniff and manually verify the _id was sent to the server.

        Same for initializeOrderedBulkOp().

Test Case 6:
    Insert doesn’t accept an array of documents:
        initializeUnorderedBulkOp().insert([{}, {}]) throws

        Same for initializeOrderedBulkOp().  

FIND
----

Test Case 1:
    Dynamic languages: find() with no args is prohibited:
        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find() raises error immediately

        Same for initializeOrderedBulkOp().

UPDATE
------

Test Case 1:
    Dynamic languages: raise error if wrong arg type
        .. code:: javascript

            initializeUnorderedBulkOp().find({}).update('foo') throws a reasonable error

        Same for initializeOrderedBulkOp().

Test Case 2:
    Dynamic languages: Update requires find() first:
        .. code:: javascript

            initializeUnorderedBulkOp().update({$set: {x: 1}}) is a type error

        Same for initializeOrderedBulkOp().

Test Case 3:
    Key validation, all top-level keys must be $-operators:
        These throw errors, even without calling execute():

        .. code:: javascript

            initializeUnorderedBulkOp().find({}).update({key: 1})
            initializeUnorderedBulkOp().find({}).update({key: 1, $key: 1})

        Same for initializeOrderedBulkOp().

Test Case 4:
    update() updates all matching documents, and reports nMatched correctly:
        Collection has {key: 1}, {key: 2}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({}).update({$set: {x: 3}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 2,
                "nModified" : 2,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.
        
        Collection has:
            .. code:: javascript

                {key: 1, x: 3}
                {key: 2, x: 3}

        Same for initializeOrderedBulkOp().

Test Case 5:
    update() only affects documents that match the preceding find():
        Collection has {key: 1}, {key: 2}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).update({$set: {x: 1}})
            batch.find({key: 2}).update({$set: {x: 2}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 2,
                "nModified" : 2,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        Collection has:
            .. code:: javascript

                {key: 1, x: 1}
                {key: 2, x: 2}

UPDATE_ONE
----------

Test Case 1:
    Dynamic languages: raise error if wrong arg type
        initializeUnorderedBulkOp().find({}).updateOne('foo') throws a reasonable error

        Same for initializeOrderedBulkOp().

Test Case 2:
    Dynamic languages: Update requires find() first:
        initializeUnorderedBulkOp().updateOne({$set: {x: 1}}) is a type error

        Same for initializeOrderedBulkOp().

Test Case 3:
    Key validation:
        These throw errors; all top-level keys must be $-operators:

        .. code:: javascript

            initializeUnorderedBulkOp().find({}).updateOne({key: 1})
            initializeUnorderedBulkOp().find({}).updateOne({key: 1, $key: 1})

        Same for initializeOrderedBulkOp().

Test Case 4:
    Basic:
        Collection has {key: 1}, {key: 2}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({}).updateOne({}, {$set: {key: 3}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 1,
                "nModified" : 1,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        .. code:: javascript

            collection.find({key: 3}).count() == 1.

        Same for initializeOrderedBulkOp().

REPLACE
-------

Test Case 1:
    Dynamic languages: There is no replace.
        initializeUnorderedBulkOp().find({}).replace() is a type error

        Same for initializeOrderedBulkOp().

REPLACE_ONE
-----------

Test Case 1:
    Dynamic languages: raise error if wrong arg type
        initializeUnorderedBulkOp().find({}).replaceOne('foo') throws a reasonable error

        Same for initializeOrderedBulkOp().

Test Case 2:
    Dynamic languages: replaceOne requires find() first:
        initializeUnorderedBulkOp().replaceOne({key: 1}) is a type error

        Same for initializeOrderedBulkOp().

Test Case 3:
    Key validation:
        These throw errors; no top-level keys can be $-operators:

        .. code:: javascript

            initializeUnorderedBulkOp().find({}).replaceOne({$key: 1})
            initializeUnorderedBulkOp().find({}).replaceOne({$key: 1, key: 1})

        Same for initializeOrderedBulkOp().

Test Case 4:
    If find() matches multiple documents, replaceOne() replaces exactly one of them:
        Collection has {key: 1}, {key: 1}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).replaceOne({key: 3})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 1,
                "nModified" : 1,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        .. code:: javascript
    
            collection.distinct('key') == [1, 3].

        Same for initializeOrderedBulkOp().

UPSERT-UPDATE
-------------

Test Case 1:
    upsert() requires find() first:
        initializeOrderedBulkOp().upsert() is a type error

        upsert().update() upserts a document, and doesn’t affect non-upsert updates in the same bulk operation. 'nUpserted’ is set:

        Empty collection.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).update({$set: {x: 1}})  // not an upsert
            batch.find({key: 2}).upsert().update({$set: {x: 2}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 1,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 0,
                "upserted" : [{ "index" : 1, "_id" : ObjectId(...)}]
            }

        nModified is NULL or omitted if legacy server.
        
        collection has only {_id: ObjectId(...), key: 2, x: 2}.

        Repeat the whole batch. Now nMatched == 1, nUpserted == 0.

        Same for initializeOrderedBulkOp().

Test Case 2:
    upsert().update() updates all matching documents:
        Collection starts with {key: 1}, {key: 1}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).upsert().update({$set: {x: 1}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 2,
                "nModified" : 2,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.
        
        collection has only {key: 1, x: 1}, {key: 1, x: 1}.

        Same for initializeOrderedBulkOp().

        We can upsert() a 16 MiB document—the driver can make a command document slightly larger than the max document size.

        Empty collection.
        
        .. code:: javascript

            var bigstring = “string of length 16 MiB - 30 bytes”
            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).upsert().update({$set: {x: bigstring}})
            batch.execute() succeeds.

        Same for initializeOrderedBulkOp().

UPSERT-UPDATE_ONE
-----------------

Test Case 1:
    upsert().updateOne() upserts a document, and doesn’t affect non-upsert updateOnes in the same bulk operation. 'nUpserted’ is set:
        Empty collection.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).updateOne({$set: {x: 1}})  // not an upsert
            batch.find({key: 2}).upsert().updateOne({$set: {x: 2}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 1,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 0,
                "upserted" : [{ "index" : 1, "_id" : ObjectId(...)} ]
            }

        nModified is NULL or omitted if legacy server.

        collection contains only {key: 2, x: 2}.

        Same for initializeOrderedBulkOp().

Test Case 2:
    upsert().updateOne() only updates one matching document:
        Collection starts with {key: 1}, {key: 1}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).upsert().updateOne({$set: {x: 1}})
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 1,
                "nModified" : 1,
                "nRemoved" : 0,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        collection has only {key: 1, x: 1}, {key: 1}.

UPSERT-REPLACE_ONE
------------------

Test Case 1:
    upsert().replaceOne() upserts a document, and doesn’t affect non-upsert replaceOnes in the same bulk operation. 'nUpserted’ is set:
        Empty collection.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).replaceOne({x: 1})  // not an upsert
            batch.find({key: 2}).upsert().replaceOne({x: 2})

            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 1,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 0,
                "upserted" : [{ "index" : 1, "_id" : ObjectId(...)}  ]
            }

        nModified is NULL or omitted if legacy server.
        
        collection contains {x: 2}.

        Same for initializeOrderedBulkOp().

Test Case 2:
    upsert().replaceOne() only replaces one matching document:
        Collection starts with {key: 1}, {key: 1}.

        .. code:: javascript

          batch = initializeUnorderedBulkOp()
          batch.find({key: 1}).upsert().replaceOne({x: 1})
          batch.execute() == {
              "writeErrors" : [ ],
              "writeConcernErrors" : [ ],
              "nInserted" : 0,
              "nUpserted" : 0,
              "nMatched" : 1,
              "nModified" : 1,
              "nRemoved" : 0,
              "upserted" : []
          }

        nModified is NULL or omitted if legacy server.

        collection has only {x: 1}, {key: 1}.

REMOVE
------

Test Case 1:
    remove() requires find() first:
        initializeUnorderedBulkOp().remove() is a type error

        Same for initializeOrderedBulkOp().

Test Case 1:
    Remove() with empty selector removes all documents:
        Collection starts with {key: 1}, {key: 1}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({}).remove()
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 2,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        Collection is now empty.

        Same for initializeOrderedBulkOp().

Test Case 2:
    Remove() with empty selector removes only matching documents:
        Collection starts with {key: 1}, {key: 2}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({key: 1}).remove()
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 1,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        Collection contains only {key: 2}.

        Same for initializeOrderedBulkOp().

REMOVE_ONE
----------

Test Case 1:
    removeOne() requires find() first:
        initializeUnorderedBulkOp().removeOne() is a type error

        Same for initializeOrderedBulkOp().

Test Case 2:
    If several documents match find(), removeOne() removes one:
        Collection has {key: 1}, {key: 1}.

        .. code:: javascript

            batch = initializeUnorderedBulkOp()
            batch.find({}).removeOne()
            batch.execute() == {
                "writeErrors" : [ ],
                "writeConcernErrors" : [ ],
                "nInserted" : 0,
                "nUpserted" : 0,
                "nMatched" : 0,
                "nModified" : 0,
                "nRemoved" : 1,
                "upserted" : [ ]
            }

        nModified is NULL or omitted if legacy server.

        collection.count() == 1.

        Same for initializeOrderedBulkOp().

MIXED OPERATIONS, UNORDERED
---------------------------
nMatched, nModified, nUpserted, nInserted, nRemoved are properly counted with an unordered bulk operation. The list of upserted documents is returned, with upserts’ indexes correctly rewritten.
Collection contains {a: 1}, {a: 2}.

.. code:: javascript

    batch = initializeUnorderedBulkOp()
    batch.find({a: 1}).update({$set: {b: 1}})
    batch.find({a: 2}).remove()
    batch.insert({a: 3})
    batch.find({a: 4}).upsert().updateOne({$set: {b: 4}})
    result = batch.execute()

    result['nMatched'] == 1
    result['nModified'] == 1 // (nModified is NULL or omitted if legacy server.)
    result['nUpserted'] == 1
    result['nInserted'] == 1
    result['nRemoved'] == 1

    result['upserted'].length == 1 and result['upserted'][0]['index'] == 3.
    result['upserted'][0]['_id'] is an ObjectId.

MIXED OPERATIONS, ORDERED
-------------------------
nMatched, nModified, nUpserted, nInserted, nRemoved are properly counted with an unordered bulk operation. The list of upserted documents is returned, with upserts’ indexes correctly rewritten.

Empty collection.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({a: 1})
    batch.find({a: 1}).updateOne({$set: {b: 1}})
    batch.find({a: 2}).upsert().updateOne({$set: {b: 2}})
    batch.insert({a: 3})
    batch.find({a: 3}).remove()
    result = batch.execute()

    result['nInserted'] == 2
    result['nUpserted'] == 1
    result['nMatched'] == 1
    result['nModified'] == 1 (nModified is NULL or omitted if legacy server.)
    result['nRemoved'] == 1

    result['upserted'].length == 1 and result['upserted'][0]['index'] == 2.
    result['upserted'][0]['_id'] is an ObjectId.

MIXED OPERATIONS, AUTH
----------------------
Verify that auth failures are handled gracefully, especially in conjunction with other errors, such as write concern or normal write errors.

Example: Using user defined roles (UDR) create a user who can do insert but not remove and run an ordered batch performing both of these operations. 

An ordered batch is expected to stop executing when the error is encountered, then raise the appropriate authentication error. If there have been write concern errors they may be lost. The behavior of an unordered batch is unspecified in the face of auth failure.

UNORDERED BATCH WITH ERRORS
---------------------------
nMatched, nModified, nUpserted, nInserted, nRemoved are properly counted with an unordered bulk operation that includes a write error. The list of upserted documents is returned, with upserts’ indexes correctly rewritten.

Empty collection, unique index on 'a’.

.. code:: javascript

    batch = initializeUnorderedBulkOp()
    batch.insert({b: 1, a: 1})
    // one or two of these upserts fails:
    batch.find({b: 2}).upsert().updateOne({$set: {a: 1}})
    batch.find({b: 3}).upsert().updateOne({$set: {a: 2}})
    batch.find({b: 2}).upsert().updateOne({$set: {a: 1}})
    batch.insert({b: 4, a: 3})
    // this and / or the first insert fails:
    batch.insert({b: 5, a: 1})

    batch.execute() should raise an error with some details:
    error_details['nInserted'] == 2
    error_details['nUpserted'] == 1
    nMatched, nModified, nRemoved are 0.
    (nModified is NULL or omitted if legacy server.)

    error_details['upserted'].length == 1
    error_details['upserted'][0]['index'] == 2
    error_details['upserted'][0]['_id'] is an ObjectId
    error_details['writeErrors'].length == 3
    collection.distinct('a') == [1, 2, 3]

ORDERED BATCH WITH ERRORS
-------------------------
nMatched, nModified, nUpserted, nInserted, nRemoved are properly counted with an ordered bulk operation that includes a write error. The list of upserted documents is returned, with upserts’ indexes correctly rewritten.

Empty collection, unique index on 'a’.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({b: 1, a: 1})
    batch.find({b: 2}).upsert().updateOne({$set: {a: 1}})
    batch.find({b: 3}).upsert().updateOne({$set: {a: 2}})
    batch.find({b: 2}).upsert().updateOne({$set: {a: 1}})  // will fail
    batch.insert({b: 4, a: 3})
    batch.insert({b: 5, a: 1})

    batch.execute() should raise an error with some details:
    nUpserted, nMatched, nModified, nRemoved are 0
    error_details['nInserted'] == 1
    error_details['writeErrors'].length == 1
    error = error_details['writeErrors'][0]
    error['code'] == 11000
    error['errmsg'] is a string.
    error['index'] == 1
    error['op'] == {q: {b: 2}, u: {$set: {a: 1}}, upsert: true}
    collection.count() == 1  // subsequent inserts weren’t attempted

BATCH SPLITTING: maxBsonObjectSize
----------------------------------
More than 16 MiB worth of inserts are split into multiple messages, and error indexes are rewritten. An unordered batch continues on error and returns the error after all messages are sent.

Empty collection.

.. code:: javascript

    // Verify that the driver splits inserts into 16-MiB messages:
    batch = initializeOrderedBulkOp()
    for (i = 0; i < 6; i++) {
    batch.insert({_id: i, a: '4 MiB STRING'});
    }

    batch.insert({_id: 0})  // will fail
    batch.insert({_id: 100})

    batch.execute() fails with error details

    error_details['nInserted'] == 6
    error_details['writeErrors'].length == 1
    error = error_details['writeErrors'][0]
    error['code'] == 11000  // duplicate key
    error['errmsg'] is a string.
    error['index'] == 6  // properly rewritten error index

    collection.count() == 6

Same for initializeUnorderedBulkOp, except:

.. code:: javascript

    error_details['nInserted'] == 7
    collection.count() == 7

BATCH SPLITTING: maxWriteBatchSize
----------------------------------
More than 1000 documents to be inserted, updated, or removed are split into multiple messages, and error indexes are rewritten. An unordered batch continues on error and returns the error after all messages are sent. Similar test to the maxBsonObjectSize test. Note the server doesn’t yet enforce the maxWriteBatchSize limit, so incorrect code will appear to succeed.

RE-RUNNING A BATCH
------------------
A batch can only be executed once.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({})
    batch.execute()
    batch.execute() a second time raises reasonable error.

Same for initializeUnorderedBulkOp().

EMPTY BATCH
-----------
execute() throws if the batch is empty.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.execute() with no operations raises a reasonable error.

Same for initializeUnorderedBulkOp().

NO JOURNAL
----------
Attempting the 'j’ write concern with a write command on mongod 2.6 is an error if mongod is started with --nojournal. This applies to bulk operations with mongod 2.4 as well, even though it returns {ok: 1, jnote: "journaling not enabled on this server"}; the driver must detect this message and turn it into an error.

mongod started with --nojournal.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({})
    batch.execute({j: 1}) raises error.

Same for initializeUnorderedBulkOp().

W > 1 AGAINST STANDALONE
------------------------
On both 2.4 and 2.6, attempting write concern w > 1 against a non-replica-set mongod is an error.

Standalone mongod.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({})
    batch.execute({w: 2}) raises error.

Same for initializeUnorderedBulkOp().

WTIMEOUT PLUS DUPLICATE KEY ERROR
---------------------------------
A single unordered batch can report both writeErrors and writeConcernErrors.

2-node replica set.

Empty collection.

.. code:: javascript

    batch = initializeUnorderedBulkOp()   
    batch.insert({_id: 1})
    batch.insert({_id: 1})
    batch.execute({w: 3, wtimeout: 1}) raises error with details.
    error_details['nInserted'] == 1
    error_details['writeErrors'].length == 1
    error_details['writeErrors'][0]['index'] == 1
    // code 64, "timed out" in 2.4
    // code 64, "waiting for replication timed out" in 2.6
    // code 100, "Not enough data-bearing nodes" in 3.0
    error_details['writeConcernErrors'][0]['code'] either 64 or 100
    error_details['writeConcernErrors'][0]['errmsg'] not empty

WTIMEOUT WITH MULTIPLE OPERATIONS
---------------------------------
Multiple write concern errors are all reported.

2-node replica set.

Empty collection.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({_id: 1})
    batch.find({}).remove()
    batch.execute({w: 3, wtimeout: 1}) raises error with details.
    error_details['nInserted'] == 1
    error_details['nRemoved'] == 1
    error_details['writeErrors'].length == 0
    // code 64, "timed out" in 2.4
    // code 64, "waiting for replication timed out" in 2.6
    // code 100, "Not enough data-bearing nodes" in 3.0

    wc_errors = error_details['writeConcernErrors']
    wc_errors.length == 2
    for (i = 0; i < 2; i++) {
      wc_errors[i]['code'] either 64 or 100
      wc_errors[i]['errmsg'] is not empty
    }

W = 0
-----
A batch with w: 0 doesn’t report write errors.

Empty collection.

.. code:: javascript

    batch = initializeOrderedBulkOp()
    batch.insert({_id: 1})
    batch.insert({_id: 1})
    batch.execute({w: 0}) raises no error.
    collection.count() == 1.

Same for initializeUnorderedBulkOp(), except collection.count() == 2.

FAILOVER WITH MIXED VERSIONS
----------------------------
The driver detects when the primary’s max wire protocol version increases or decreases, and the driver correctly switches between using write commands and using legacy write operations.

2-node replica set. One node runs 2.4, the other runs 2.6.

.. code:: javascript

    client = MongoReplicaSetClient()
    // Switch primary:
    client.admin.command({replSetStepDown: 5})  // can’t be primary for 5 seconds

    batch = client.db.collection.initializeOrderedBulkOp()
    batch.insert({_id: 1})
    batch.execute() should succeed

sleep 6 seconds

.. code:: javascript

    // Switch back to original primary
    client.admin.command({replSetStepDown: 5})
    batch = client.db.collection.initializeOrderedBulkOp()
    batch.insert({_id: 2}).execute() should succeed

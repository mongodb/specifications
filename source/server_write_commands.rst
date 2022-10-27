============================
Write Commands Specification
============================

:Status: Accepted
:Minimum Server Version: 2.6

.. contents::

--------

Goals
-----

* Method to do writes (insert/update/delete) that declares the write concern up front
* Support for batch operations
* As efficient as possible
* getLastError is disallowed after anything except old style write ops

Non-Goals
---------

* We're not specifying nor building any generic mechanism for feature discovery here
* We're not specifying nor building any generic way to be backwards compatible

Requests Format
---------------

We use a very similar request format for all insert, update, and delete commands, described
below. A request contains parameters on how to apply the batch items and, of course, the batch
items themselves.

Generic Fields
~~~~~~~~~~~~~~

* ``<write op>``: mandatory, with a string type, where <write op> can be ``insert``,
  ``update``, or ``delete`` and the content string is a valid collection name against which the
  write should be directed.  The <write op> must be the first key in the document.

    example: ::

      db.runCommand{ { update: "users", ...

* ``writeConcern``: optional, with a valid write concern BSONObj type, which contains the
  journaling, replication, and/or time out parameters that will be used at the end of the batch
  application. The default write concern for a mongod server can be set as a replica set
  configuration option, or if there is no replica set default the fallback is ``{ w: 1 }``.

    example: ::

      ..., writeConcern: { w: 2 }, ...

  Note that the write concern will be issued at the end of the batch application.
  
  We also support the "unusual" write concern: ``{ w : 0 }``, which means the user is uninterested
  in the result of the write at this time.  In this protocol, there is no provision to ignore the
  response packet.  The protocol, however, sends a very condensed response when it sees that 
  write concern (e.g. omits everything but the ``ok`` field).

* ``ordered``: optional, with a boolean type. If true, applies the batch's items in the same
  order the items appear, ie. sequentially.  If ``ordered`` is false, the server applies the 
  batch items in no particular order -- possibly, in parallel.  The default value is true, 
  sequential.

    example: ::

     ..., ordered: false, ...
     
* ``metadata``: RESERVED FOR MONGOS USE, future use.

* ``failFast``: NOT YET USED, RESERVED FOR FUTURE USE.  Optional, with a boolean type.  If false, allows
  the batch to continue processing even if some elements in the batch have errors.  If true, 
  the batch will stop on first error(s) it detects (write concern will not be applied).  Defaults
  to true for ordered batches, and false for unordered batches.

Batch Items Format
~~~~~~~~~~~~~~~~~~

We describe the array of batch items to be applied according to which type of write operation
we'd like to perform.

.. _insert:

* For inserts, ``documents`` array: mandatory, with an array of objects type. Objects must be
  valid for insertion.

    example: ::

     { insert: "coll",
       documents: [ <obj>, <obj>, ... ],
       ...
     }

.. _update:

* For updates, an ``updates`` array: mandatory, with an array of update objects type. Update
  objects must contain the query expression ``q``, an update expression ``u`` fields, and,
  optionally, a boolean ``multi`` if several documents may be changed, and a boolean ``upsert``
  if updates can become inserts. Both optional fields default to false.

    example: ::

      { update: "coll",
        updates: [
            { q : <query>, u : <update>, multi : <multi>, upsert : <upsert> },
            ...
        ],
        ...
      }

.. _delete:

* for deletes a ``deletes`` array: mandatory, with an array of delete object type. A delete

    example: ::

      { delete: "coll",
        deletes : [
            { q : <query>, limit : <num> },
            ...
        ],
        ...
      }

  Note that, to avoid accidentally deleting more documents than intended, we force the ``limit``
  field to be present all the time. When all documents that satisfy ``q`` should be
  deleted set ``limit`` to zero, as opposed to being omitted.

  Note: The only valid values for ``limit`` is 1 and 0.

Request Size Limits
~~~~~~~~~~~~~~~~~~~

Supporting unlimited batch sizes poses two problems - the BSONObj internal size limit is 16 MiB + 16 KiB
(for command overhead), and a small write operation may have a much larger response.  In order to
ensure a batch can be correctly processed, two limits must be respected.

Both of these limits can be found using hello():

* ``maxBsonObjectSize`` : currently 16 MiB, this is the maximum size of writes (excluding command overhead)
  that should be sent to the server.  Documents to be inserted, query documents for updates and
  deletes, and update expression documents must be <= this size.  Once these documents have been
  assembled into a write command the total size may exceed ``maxBsonObjectSize`` by a maximum of
  16 KiB, allowing users to insert documents up to ``maxBsonObjectSize``.

* ``maxWriteBatchSize`` : this is the maximum number of inserts, updates, or deletes that 
  can be included in a write batch.  If more than this number of writes are included, the server cannot
  guarantee space in the response document to reply to the batch.

If the batch is too large in size or bytes, the command may fail.

Response Format
---------------

There are two types of responses to any command:

- a ``command failure``, which indicates the command itself did not complete successfully.  Example
  command failures include failure to authorize, failure to parse, operation aborted by user,
  and unexpected errors during execution (these should be very rare).
   
- successful command execution, which for write commands may include write errors.

Command Failure Fields
~~~~~~~~~~~~~~~~~~~~~~

All commands have the same format when they fail unexpectedly:

``{ ok : 0, code : <error code>, errmsg : <human-readable string> }``

When a batch write command fails this way, like other commands, no guarantees are made about the
state of the writes which were sent.  Particular error codes may indicate more about what occurred,
but those codes are outside the scope of this spec.

General Response Fields
~~~~~~~~~~~~~~~~~~~~~~~

Again, like other commands, batch write commands return ``{ ok : 1, ... }`` when they complete
successfully.  Importantly, successful execution of a batch write command may include reporting of
unsuccessful writes (write errors) and write concern application (write concern error).

The main body of a successful response is below:

.. _ok:

* ``ok``: Mandatory field, (double)"1" if operation was executed. Does not mean successfully.
  For example, duplicate key error will still set ok = 1

.. _n:

* ``n``: Mandatory field, with a positive numeric type or zero. This field contains the aggregated 
  number of documents successfully affected by the entire write command. This includes the number of
  documents inserted, upserted, updated, and deleted.  We do not report on the individual number of 
  documents affected by each batch item. If the application would wish so, then the application 
  should issue one-item batches.

.. _writeErrors:

* ``writeErrors``: Optional field, an array of write errors. For every batch write that had an error, there
  is one BSON error document in the array describing the error.
  (See the `Error Document`_ section.)

.. _writeConcernError:

* ``writeConcernError``: Optional field, which may contain a BSON error document indicating an error occurred while
  applying the write concern (or an error indicating that the write concern was not applied).
  (See the `Error Document`_ section.)

Situational Fields
~~~~~~~~~~~~~~~~~~

We use the fields above for all responses, regardless of the request type. But some
request types require additional response information, as described below.

.. _nModified:

* ``nModified``: Optional field, with a positive numeric type or zero.  Zero is the default value.  This
  field is only and always present for batch updates.  ``nModified`` is the physical number of documents
  affected by an update, while ``n`` is the logical number of documents matched by the update's query.
  For example, if we have 100 documents like ::
  
    { bizName: "McD", employees: ["Alice", "Bob", "Carol"] }
    
  and we are adding a single new employee using $addToSet for each business document, ``n`` is useful to
  ensure all businesses have been updated, and ``nModified`` is useful to know which businesses actually
  added a new employee.

.. _upserted:

* ``upserted``: Optional field, with an array type.  If any upserts occurred in the batch,
  the array contains a BSON document listing the ``index`` and ``_id`` of the newly 
  upserted document in the database.

.. _lastOp:

* ``lastOp``: MONGOD ONLY.  Optional field, with a timestamp type, indicating the latest opTime on the
  server after all documents were processed.

* ``electionId``: MONGOD ONLY. Optional ObjectId field representing the last primary election Id.

Error Document
~~~~~~~~~~~~~~

For a write error or a write concern error, the following fields will appear in the error
document:

.. _code:

* ``code``: Mandatory field with integer format.  Contains a numeric code corresponding to a certain
  type of error.

.. _errInfo:

* ``errInfo``: Optional field, with a BSONObj format.  This field contains structured information
  about an error that can be processed programmatically. For example, if a request returns with a
  shard version error, we may report the proper shard version as a sub-field here. For another example,
  if a write concern timeout occurred, the information previously reported on ``wtimeout`` would be
  reported here.
  The format of this field depends on the code above.

.. _errmsg:

* ``errmsg``: Mandatory field, containing a human-readable version of the error.

.. _index:

* ``index``: WRITE ERROR ONLY.  The index of the erroneous batch item relative to request batch order.
  Batch items indexes start with 0.


Examples
--------

Successful case
~~~~~~~~~~~~~~~

Note that ok: 1 by itself does **not** mean that an insert, update, or delete was executed
successfully,
just that the batch was processed successfully.
``ok``: 1 merely means "all operations executed".
``n`` reports how many items from that batch were affected by the operation.

Insert
------

  Request: ::

    { insert: "coll", documents: [ {a: 1} ] }

  Response: ::

    { "ok" : 1, "n" : 1 }


  Request: ::

    { insert: "coll", documents: [ {a: 1}, {b: 2}, {c: 3}, {d: 4} ] }

  Response: ::

    { "ok" : 1, "n" : 4 }


Delete
------

  Request: ::

    { delete: "coll", deletes: [ { q: {b: 2}, limit: 1} ] }

  Response: ::

    { "ok" : 1, "n" : 1 }


  Request: ::

    {
        delete: "coll",
        deletes:
        [
            {
                q: {a: 1},
                limit: 0
            },
            {
                q: {c: 3},
                limit: 1
            }
        ]
    }

  Response: ::

    { "ok" : 1, "n" : 3 }



Update
------

  Request: ::

    {
        update: "coll",
        "updates":
        [
            {
                q: { d: 4 },
                u: { $set: {d: 5} }
            }
        ]
    }

  Response: ::

    { "ok" : 1, "nModified" : 1, "n" : 1 }


Checking if command failed
~~~~~~~~~~~~~~~~~~~~~~~~~~

To check if a write command _failed_

::
  
  if (ok == 0) {
    // The command itself failed (authentication failed.., syntax error)
  } else if (writeErrors is array) {
    // Couldn't write the data (duplicate key.., out of disk space..)
  } else if (writeConcernError is object) {
    // Operation took to long on secondary, hit wtimeout ...,
  }

Command failure to parse or authenticate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Request: ::

    { update: "coll",
      updates: [
        { q: {a:1}, x: {$set: {b: 2} } },
        { q: {a:2}, u: {$set: {c: 2} } }
      ]
    }

  Response: ::

    { ok: 0,
      code: <number>,
      errmsg: "Failed to parse batched update request, missing update expression 'u' field"
    }
    
    { ok: 0,
      code: <number>,
      errmsg: "Not authorized to perform update"
    }

Note that no information is given about command execution - if this was performed against a mongos, for example,
the batch may or may not have been partially applied - there is no programmatic way to determine this.

Write concern failure
~~~~~~~~~~~~~~~~~~~~~

  Request: ::

    { insert: "coll", documents: [ {a: 1}, {a:2} ], writeConcern: {w: 3, wtimeout: 100} }

  Response: ::

    { ok: 1,
      n: 2,
      writeConcernError: {
        code : <number>,
        errInfo: { wtimeout : true },
        errmsg: "Could not replicate operation within requested timeout"
      }
    }

Mixed failures
~~~~~~~~~~~~~~

  Request: ::

    db.coll.ensureIndex( {a:1}, {unique: true} )
    { insert: "coll",
      documents: [
        { a: 1 },
        { a: 1 },
        { a: 2 }
      ],
      ordered: false,
      writeConcern: { w: 3, wtimeout: 100 }
    }

  Response: ::

    { ok: 1,
      n: 2,
      writeErrors: [
        { index: 1,
          code: <number>,
          errmsg: "Attempt to insert duplicate key when unique index is present"
        }
      ],
      writeConcernError: {
        code: <number>,
        errInfo : { wtimeout : true },
        errmsg: "Could not replicate operation within requested timeout"
      }
    }

Note that the field ``n`` in the response came back with 2, even though there are three items
in the batch. This means that there must be an entry in ``writeErrors`` for the item that
failed.  Note also that the request turned off ``ordered``, so the write concern error
was hit when trying to replicate batch items 0 and 2.

Just to illustrate the support for ``{w:0}``, here's how the
response would look, had the request asked for that write concern.

  Response: ::

    { ok: 1 }

FAQ
---

Can a driver still use the OP_INSERT, OP_DELETE, OP_UPDATE?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, a 2.6 server will still support those. But it is unlikely that a 2.8 server would.  Of course, when talking to older servers, the usual op codes will continue working the same. An older server is one that reports ``hello.maxWireVersion`` to be less than 2 or does not include the field.

The rationale here is that we may choose to divert all the write traffic to the new
protocol. (This depends on the having the overhead to issue a batch with one item very low.)

Can an application still issue requests with write concerns {w: 0}?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. The drivers are still required to serve a {w:0} write concern by returning the
control to the application as soon as possible.  But a driver should send the request to
the server via a write command and should, therefore, take the corresponding response off the
wire -- even if the caller is not interested in that result.


What happens if a driver receives a write request against an old server?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It must convert that request into write operations + gle's and use the old op codes.

Are we discontinuing the use of getLastError?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes but as of 2.6 the existing getLastError behavior is supported for backward compatibility.

Changelog
---------

:2014-05-14: First public version
:2014-05-15: Removed text related to bulk operations; see the Bulk API spec for
             bulk details. Clarified some paragraphs; re-ordered the response
             field sections.
:2021-04-22: Updated to use hello command
:2022-07-25: Remove outdated value for ``maxWriteBatchSize``
:2022-10-05: Revise spec front matter and reformat changelog.

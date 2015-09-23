===========
GridFS Spec
===========

:Spec: 105
:Title: GridFS Spec
:Authors: Samantha Ritter and Robert Stam
:Advisors: David Golden and Jeff Yemin
:Status: Approved
:Type: Standards
:Minimum Server Version: 2.2
:Last Modified: July 20, 2015

.. contents::

--------

Abstract
========

GridFS is a convention drivers use to store and retrieve BSON binary
data (type “\\x05”) that exceeds MongoDB’s BSON-document size limit of
16MB. When this data, called a **user file**, is written to the system,
GridFS divides the file into **chunks** that are stored as distinct
documents in a **chunks collection**. To retrieve a stored file, GridFS
locates and returns all of its component chunks. Internally, GridFS
creates a **files collection document** for each stored file. Files
collection documents hold information about stored files, and they are
stored in a **files collection**.

This spec defines a basic API for GridFS. This spec also outlines
advanced GridFS features that drivers can choose to support in their
implementations. Additionally, this document attempts to clarify the
meaning and purpose of all fields in the GridFS data model, disambiguate
GridFS terminology, and document configuration options that were
previously unspecified.

Definitions
===========

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”,
“SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this
document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
-----

Bucket name
  A prefix under which a GridFS system’s collections are stored. Collection names for the files and chunks
  collections are prefixed with the bucket name. The bucket name MUST be configurable by the user. Multiple
  buckets may exist within a single database. The default bucket name is ‘fs’.

Chunk
  A section of a user file, stored as a single document in the ‘chunks’ collection of a GridFS bucket.
  The default size for the data field in chunks is 255KB. Chunk documents have the following form:

  .. code:: javascript
  
    { 
      "_id" : <ObjectId>,
      "files_id" : <ObjectId>,
      "n" : <Int32>,
      "data" : <binary data>
    }

  :_id: a unique ID for this document of type BSON ObjectId
  :files_id: the id for this file (the _id from the files collection document). This field takes the type of
    the corresponding _id in the files collection, which on existing stored files created by legacy drivers may
    not be ObjectId.
  :n: the index number of this chunk, zero-based.
  :data: a chunk of data from the user file

Chunks collection
  A collection in which chunks of a user file are stored. The name for this collection is the word 'chunks'
  prefixed by the bucket name. The default is ‘fs.chunks’.

Empty chunk
  A chunk with a zero length “data” field.

Files collection
  A collection in which information about stored files is stored. There will be one files collection document
  per stored file. The name for this collection is the word ‘files’ prefixed by the bucket name. The default
  is ‘fs.files’.

Files collection document
  A document stored in the files collection that contains information about a single stored file. Files collection
  documents have the following form:

  .. code:: javascript

    {
      "_id" : <ObjectId>,
      "length" : <Int64>,
      "chunkSize" : <Int32>,
      "uploadDate" : <BSON datetime, ms since Unix epoch in UTC>,
      "md5" : <hex string>,
      "filename" : <string>,
      "contentType" : <string>,
      "aliases" : <string array>,
      "metadata" : <Document>
    }
  
  :_id: a unique ID for this document, of type BSON ObjectId. Legacy GridFS systems may store this value as
    a different type. New files must be stored using an ObjectId.
  :length: the length of this stored file, in bytes
  :chunkSize: the size, in bytes, of each data chunk of this file. This value is configurable by file. The default is 255KB.
  :uploadDate: the date and time this file was added to GridFS, stored as a BSON datetime value. The value of this
    field MUST be the datetime when the upload completed, not the datetime when it was begun.
  :md5: a hash of the contents of the stored file
  :filename: the name of this stored file; this does not need to be unique
  :contentType: DEPRECATED, any MIME type, for application use only
  :aliases: DEPRECATED, for application use only
  :metadata: any additional application data the user wishes to store
  
  Note: some older versions of GridFS implementations allowed applications to
  add arbitrary fields to the files collection document at the root level. New
  implementations of GridFS will not allow this, but must be prepared to
  handle existing files collection documents that might have additional fields.

Orphaned chunk
  A document in the chunks collections for which the
  “files_id” does not match any “_id” in the files collection. Orphaned
  chunks may be created if write or delete operations on GridFS fail
  part-way through.

Stored File
  A user file that has been stored in GridFS, consisting
  of a files collection document in the files collection and zero or more
  documents in the chunks collection.
  
Stream
  An abstraction that represents streamed I/O. In some languages a different
  word is used to represent this abstraction.

User File
  A data added by a user to GridFS. This data may map to an actual file on disk, a stream of input, a large data
  object, or any other large amount of consecutive data.

Specification
=============

Guidance
--------

Documentation
~~~~~~~~~~~~~

The documentation provided in code below is merely for driver authors
and SHOULD NOT be taken as required documentation for the driver.

Operations
~~~~~~~~~~

All drivers MUST offer the Basic API operations defined in the following
sections and MAY offer the Advanced API operations. This does not
preclude a driver from offering more.

Operation Parameters
~~~~~~~~~~~~~~~~~~~~

All drivers MUST offer the same options for each operation as defined in
the following sections. This does not preclude a driver from offering
more. The options parameter is optional. A driver SHOULD NOT require a
user to specify optional parameters.

Deviations
~~~~~~~~~~

A non-exhaustive list of acceptable deviations are as follows:

- Using named parameters instead of an options hash. For instance,

  .. code:: javascript
  
    id = bucket.upload_from_stream(filename, source, chunkSizeBytes: 16 * 1024);

- Using a fluent style for constructing a GridFSBucket instance:

  .. code:: javascript
  
    bucket = new GridFSBucket(database)
      .withReadPreference(ReadPreference.Secondary);

When using a fluent-style builder, all options should be named
rather than inventing a new word to include in the pipeline (like
options). Required parameters are still required to be on the
initiating constructor.

Naming
------

All drivers MUST name operations, objects, and parameters as defined in
the following sections.

Deviations are permitted as outlined below.

Deviations
~~~~~~~~~~

When deviating from a defined name, an author should consider if the
altered name is recognizable and discoverable to the user of another
driver.

A non-exhaustive list of acceptable naming deviations are as follows:

- Using "bucketName" as an example, Java would use "bucketName" while
  Python would use "bucket_name". However, calling it
  "bucketPrefix" would not be acceptable.

- Using "maxTimeMS" as an example, .NET would use "MaxTime" where its
  type is a TimeSpan structure that includes units. However,
  calling it "MaximumTime" would not be acceptable.

- Using "GridFSUploadOptions" as an example, Javascript wouldn't need
  to name it while other drivers might prefer to call it
  "GridFSUploadArgs" or "GridFSUploadParams". However, calling it
  "UploadOptions" would not be acceptable.
  
- Languages that use a different word than "Stream" to represent a
  streamed I/O abstraction may replace the word "Stream" with their
  language's equivalent word. For example, open_upload_stream might
  be called open_upload_file or open_upload_writer if appropriate.

- Languages that support overloading MAY shorten the name of some
  methods as appropriate. For example, download_to_stream and
  download_to_stream_by_name MAY be overloaded
  download_to_stream methods with different parameter types.
  Implementers are encouraged not to shorten method names
  unnecessarily, because even if the shorter names are not
  ambiguous today they might become ambiguous in the future as new
  features are added.

API
===

This section presents two groups of features, a basic API that a driver
MUST implement, and a more advanced API that drivers MAY choose to
implement additionally.

Basic API
=========

Configurable GridFSBucket class
-------------------------------

.. code:: javascript

  class GridFSBucketOptions {
    
    /**
     * The bucket name. Defaults to 'fs'.
     */  
    bucketName : String optional;
    
    /**
     * The chunk size in bytes. Defaults to 255KB.
     */
    chunkSizeBytes : Int32 optional;
    
    /**
     * The write concern. Defaults to the write concern of the database.
     */
    writeConcern : WriteConcern optional;
    
    /**
     * The read preference. Defaults to the read preference of the database.
     */
    readPreference : ReadPreference optional;
    
  }

  class GridFSBucket {
  
    /**
     * Create a new GridFSBucket object on @db with the given @options.
     */
    GridFSBucket new(Database db, GridFSBucketOptions options=null);
  
  }

Creates a new GridFSBucket object, managing a GridFS bucket within the
given database.

GridFSBucket objects MUST allow the following options to be
configurable:

- **bucketName:** the name of this GridFS bucket. The files and chunks
  collection for this GridFS bucket are prefixed by this name
  followed by a dot. Defaults to “fs”. This allows multiple GridFS
  buckets, each with a unique name, to exist within the same
  database.

- **chunkSizeBytes:** the number of bytes stored in chunks for new
  user files added through this GridFSBucket object. This will not
  reformat existing files in the system that use a different chunk
  size. Defaults to 255KB.

IF a driver supports configuring writeConcern or readPreference at the
database or collection level, then GridFSBucket objects MUST also allow
the following options to be configurable:

- **writeConcern:** defaults to the write concern on the parent
  database (or client object if the parent database has no write
  concern).

- **readPreference:** defaults to the read preference on the parent
  database (or client object if the parent database has no read
  preference).

GridFSBucket instances are immutable. Their properties MUST NOT be
changed after the instance has been created. If your driver provides a
fluent way to provide new values for properties, these fluent methods
MUST return new instances of GridFSBucket.

Indexes
-------

For efficient execution of various GridFS operations the following
indexes MUST exist:

- an index on { filename : 1, uploadDate : 1 } on the files collection

- a unique index on { files_id : 1, n : 1 } on the chunks collection

Normally we leave it up to the user to create whatever indexes they see
fit, but because GridFS is likely to be looked at as a black box we
should create these indexes automatically in a way that involves the 
least amount of overhead possible.

Before read operations
~~~~~~~~~~~~~~~~~~~~~~

For read operations, drivers MUST assume that the proper indexes exist.

Before write operations
~~~~~~~~~~~~~~~~~~~~~~~

Immediately before the **first** write operation on an instance of a GridFSBucket
class is attempted (and not earlier), drivers MUST:

- determine if the files collection is empty using the primary read preference mode.
- and if so, create the indexes described above if they do not already exist

To determine whether the files collection is empty drivers SHOULD execute
the equivalent of the following shell command:

.. code :: javascript

    > db.fs.files.findOne({}, { _id : 1 })

If no document is returned the files collection is empty.

This method of determining whether the files collection is empty should perform better 
than checking the count in the case where the files collection is sharded.

Drivers MUST check whether the indexes already exist before attempting to create them.
This supports the scenario where an application is running with read-only authorizations.

If a driver determines that it should create the indexes, it  MUST raise an error
if the attempt to create the indexes fails.

Drivers MUST create the indexes in foreground mode.

File Upload
-----------

.. code:: javascript

  class GridFSUploadOptions {
  
    /**
     * The number of bytes per chunk of this file. Defaults to the
     * chunkSizeBytes in the GridFSBucketOptions.
     */
    chunkSizeBytes : Int32 optional;
    
    /**
     * User data for the 'metadata' field of the files collection document.
     * If not provided the driver MUST omit the metadata field from the
     * files collection document.
     */
    metadata : Document optional;
    
    /**
     * DEPRECATED: A valid MIME type. If not provided the driver MUST omit the
     * contentType field from the files collection document.
     *
     * Applications wishing to store a contentType should add a contentType field
     * to the metadata document instead.
     */
    contentType : String optional;
    
    /**
     * DEPRECATED: An array of aliases. If not provided the driver MUST omit the
     * aliases field from the files collection document.
     *
     * Applications wishing to store aliases should add an aliases field to the
     * metadata document instead.
     */
    aliases: String[] optional;
  
  }
  
  class GridFSBucket {
  
    /**
     * Opens a Stream that the application can write the contents of the file to.
     *
     * Returns a Stream to which the application will write the contents.
     */
    Stream open_upload_stream(string filename, GridFSUploadOptions options=null);
    
    /**
     * Uploads a user file to a GridFS bucket.
     *
     * Reads the contents of the user file from the @source Stream and uploads it
     * as chunks in the chunks collection. After all the chunks have been uploaded,
     * it creates a files collection document for @filename in the files collection.
     *
     * Returns the id of the uploaded file.
     */
    ObjectId upload_from_stream(string filename, Stream source, GridFSUploadOptions options=null);
  
  }

Uploads a user file to a GridFS bucket. For languages that have a Stream
abstraction, drivers SHOULD use that Stream abstraction. For languages
that do not have a Stream abstraction, drivers MUST create an
abstraction that supports streaming.

In the case of open_upload_stream, the driver returns a Stream to which the
application will write the contents of the file. As the application writes the
contents to the returned Stream, the contents are uploaded as chunks in the chunks
collection. When the application signals it is done writing the contents of the
file by calling close (or its equivalent) on the returned Stream, a files collection
document is created in the files collection.

The driver MUST make the Id of the new file available to the caller. Typically
a driver SHOULD make the Id available as a property named Id on the 
Stream that is returned. In languages where that is not idiomatic, a driver
MUST make the Id available in a way that is appropriate for that language.

In the case of upload_from_stream, the driver reads the contents of
the user file by consuming the the source Stream until end of file is
reached. The driver does NOT close the source Stream.

Drivers MUST take an ‘options’ document with configurable parameters.
Drivers for dynamic languages MUST ignore any unrecognized fields in the options
for this method (this does not apply to drivers for static languages which
define an Options class that by definition only contains valid fields).

Note that in GridFS, ‘filename’ is not a unique identifier. There may be
many stored files with the same filename stored in a GridFS bucket under
different ids. Multiple stored files with the same filename are called
'revisions', and the 'uploadDate' is used to distinguish newer revisions
from older ones.

**Implementation details:**

If ‘chunkSizeBytes’ is set through the options, that value MUST be used
as the chunk size for this stored file. If this parameter is not
specified, the default chunkSizeBytes setting for this GridFSBucket
object MUST be used instead.

To store a user file, drivers first generate an ObjectId to act as its
id. Then, drivers store the contents of the user file in the chunks
collection by breaking up the contents into chunks of size
‘chunkSizeBytes’. For a non-empty user file, for each n\ :sup:`th`
section of the file, drivers create a chunk document and set its fields
as follows:

:files_id: the id generated for this stored file.
:n: this is the n\ :sup:`th` section of the stored file, zero based.
:data: a section of file data, stored as BSON binary data with subtype 0x00. All chunks except
  the last one must be exactly 'chunkSizeBytes' long. The last chunk can be smaller, 
  and should only be as large as necessary.

While streaming the user file, drivers compute an MD5 digest. This MD5
digest will later be stored in the files collection document.

After storing all chunk documents generated for the user file in the
‘chunks’ collection, drivers create a files collection document for the
file and store it in the files collection. The fields in the files
collection document are set as follows:

:length: the length of this stored file, in bytes.
:chunkSize: the chunk size in bytes used to break the user file into chunks. While the configuration
  option is named ‘chunkSizeBytes’ for clarity, for legacy reasons, the files collection document
  uses only ‘chunkSize’.
:uploadDate: a BSON datetime object for the current time, in UTC, when the files collection document was created.
:md5: MD5 checksum for this user file, computed from the file’s data, stored as a hex string.
:filename: the filename passed to this function, UTF-8 encoded.
:contentType: the ‘contentType’ passed in the options, if provided; otherwise omitted.
:aliases: the array passed in the options, if provided; otherwise omitted.
:metadata: the ‘metadata’ document passed in the options, if provided; otherwise omitted.

If a user file contains no data, drivers MUST still create a files
collection document for it with length set to zero. Drivers MUST NOT
create any empty chunks for this file.

Note that drivers are no longer required to run the 'filemd5' to confirm
that all chunks were successfully uploaded. We assume that if none of
the inserts failed then the chunks must have been successfully inserted,
and running the 'filemd5' command would just be unnecessary overhead.

**Operation Failure**

If any of the above operations fail against the server, drivers MUST
raise an error. If some inserts succeeded before the failed operation,
these become orphaned chunks. Drivers MUST NOT attempt to clean up these
orphaned chunks. The rationale is that whatever failure caused the
orphan chunks will most likely also prevent cleaning up the orphaned
chunks, and any attempts to clean up the orphaned chunks will simply
cause long delays before reporting the original failure to the
application.

**Aborting an upload**

Drivers SHOULD provide a mechanism to abort an upload. When using
open_upload_stream, the returned Stream SHOULD have an Abort method.
When using upload_from_stream, the upload will be aborted if the
source stream raises an error.

When an upload is aborted any chunks already uploaded MUST be deleted.
Note that this differs from the case where an attempt to insert a chunk
fails, in which case drivers immediately report the failure without
attempting to delete any chunks already uploaded.

Abort MUST raise an error if it is unable to succesfully abort the
upload (for example, if an error occurs while deleting any chunks
already uploaded). However, if the upload is being aborted because
the source stream provided to upload_from_stream raised an error
then the original error should be re-raised.

Abort MUST also close the Stream, or at least place it in an aborted
state, so any further attempts to write additional content to the Stream
after Abort has been called fail immediately.

File Download
-------------

.. code:: javascript

  class GridFSBucket {
  
    /** Opens a Stream from which the application can read the contents of the stored file
     * specified by @id.
     *
     * Returns a Stream.
     */
    Stream open_download_stream(ObjectId id);
    
    /**
     * Downloads the contents of the stored file specified by @id and writes
     * the contents to the @destination Stream.
     */
    void download_to_stream(ObjectId id, Stream destination);
  
  }

Downloads a stored file from a GridFS bucket. For languages that have a
Stream abstraction, drivers SHOULD use that Stream abstraction. For
languages that do not have a Stream abstraction, drivers MUST create an
abstraction that supports streaming.

In the case of open_download_stream, the application reads the
contents of the stored file by reading from the returned Stream until
end of file is reached. The application MUST call close (or its
equivalent) on the returned Stream when it is done reading the contents.

In the case of download_to_stream the driver writes the contents of
the stored file to the provided Stream. The driver does NOT call close
(or its equivalent) on the Stream.

Note: if a file in a GridFS bucket was added by a legacy implementation,
its id may be of a type other than ObjectId. Drivers that previously
used id’s of a different type MAY implement a download() method that
accepts that type, but MUST mark that method as deprecated.

**Implementation details:**

Drivers must first retrieve the files collection document for this file.
If there is no files collection document, the file either never existed,
is in the process of being deleted, or has been corrupted, and the
driver MUST raise an error.

Then, implementers retrieve all chunks with files_id equal to id,
sorted in ascending order on “n”. 

However, when downloading a zero length stored file the driver MUST NOT
issue a query against the chunks collection, since that query is not
necessary. For a zero length file, drivers return either an empty stream or
send nothing to the provided stream (depending on the download method).

If a networking error or server error occurs, drivers MUST raise an
error.

As drivers stream the stored file they MUST check that each chunk
received is the next expected chunk (i.e. it has the expected "n" value)
and that the data field is of the expected length. In the case of
open_download_stream, if the application stops reading from the stream
before reaching the end of the stored file, any errors that might exist
beyond the point at which the application stopped reading won't be
detected by the driver.

File Deletion
-------------

.. code:: javascript

  class GridFSBucket {

    /**
     * Given a @id, delete this stored file’s files collection document and
     * associated chunks from a GridFS bucket.
     */
    void delete(ObjectId id);
  
  }

Deletes the stored file’s files collection document and associated
chunks from the underlying database.

As noted for download(), drivers that previously used id’s of a
different type MAY implement a delete() method that accepts that type,
but MUST mark that method as deprecated.

**Implementation details:**

There is an inherent race condition between the chunks and files
collections. Without some transaction-like behavior between these two
collections, it is always possible for one client to delete a stored
file while another client is attempting a read of the stored file. For
example, imagine client A retrieves a stored file’s files collection
document, client B deletes the stored file, then client A attempts to
read the stored file’s chunks. Client A wouldn’t find any chunks for the
given stored file. To minimize the window of vulnerability of reading a
stored file that is the process of being deleted, drivers MUST first
delete the files collection document for a stored file, then delete its
associated chunks.

If there is no such file listed in the files collection, drivers MUST raise an
error. Drivers MAY attempt to delete any orphaned chunks with files_id equal
to id before raising the error.

If a networking or server error occurs, drivers MUST raise an error.

Generic Find on Files Collection
--------------------------------

.. code:: javascript

  class GridFSFindOptions {
  
    /**
     * The number of documents to return per batch.
     */
    batchSize : Int32 optional;
    
    /**
     * The maximum number of documents to return.
     */
    limit : Int32 optional;
    
    /**
     * The maximum amount of time to allow the query to run.
     */
    maxTimeMS: Int64 optional;
    
    /**
     * The server normally times out idle cursors after an inactivity period (10 minutes)
     * to prevent excess memory use. Set this option to prevent that.
     */
    noCursorTimeout : Boolean optional;
    
    /**
     * The number of documents to skip before returning.
     */
    skip : Int32;
    
    /**
     * The order by which to sort results. Defaults to not sorting.
     */
    sort : Document optional;
  
  }
  
  class GridFSBucket {
  
    /**
     * Find and return the files collection documents that match @filter.
     */  
    Iterable find(Document filter, GridFSFindOptions options=null);
  
  }

This call will trigger a find() operation on the files collection using
the given filter. Drivers returns a sequence of documents that can be
iterated over. Drivers return an empty or null set when there are no
matching files collection documents. As the number of files could be
large, drivers SHOULD return a cursor-like iterable type and SHOULD NOT
return a fixed-size array type.

**Implementation details:**

Drivers SHOULD NOT perform any validation on the filter. If the filter
contains fields that do not exist within files collection documents,
then an empty result set will be returned.

Drivers MUST document how users query files collection documents,
including how to query metadata, e.g. using a filter like {
metadata.fieldname : “some_criteria” }.

Advanced API
============

File Download by Filename
-------------------------

.. code:: javascript

  class GridFSDownloadByNameOptions {
  
    /**
     * Which revision (documents with the same filename and different uploadDate)
     * of the file to retrieve. Defaults to -1 (the most recent revision).
     *
     * Revision numbers are defined as follows:
     * 0 = the original stored file
     * 1 = the first revision
     * 2 = the second revision
     * etc…
     * -2 = the second most recent revision
     * -1 = the most recent revision
     */
    revision : Int32 optional;
  
  }
  
  class GridFSBucket {
  
    /** Opens a Stream from which the application can read the contents of the stored file
     * specified by @filename and the revision in @options.
     *
     * Returns a Stream.
     */
    Stream open_download_stream_by_name(string filename, GridFSDownloadByNameOptions options=null);
    
    /**
     * Downloads the contents of the stored file specified by @filename and by the
     * revision in @options and writes the contents to the @destination Stream.
     */
    void download_to_stream_by_name(string filename, Stream destination,
      GridFSDownloadByNameOptions options=null);
  
  }

Retrieves a stored file from a GridFS bucket. For languages that have a
Stream abstraction, drivers SHOULD use that Stream abstraction. For
languages that do not have a Stream abstraction, drivers MUST create an
abstraction that supports streaming.

**Implementation details:**

If there is no file with the given filename, or if the requested
revision does not exist, drivers MUST raise an error with a distinct
message for each case.

Drivers MUST select the files collection document of the file
to-be-returned by running a query on the files collection for the given
filename, sorted by uploadDate (either ascending or descending,
depending on the revision requested) and skipping the appropriate number
of documents. For negative revision numbers, the sort is descending and
the number of documents to skip equals (-revision - 1). For non-negative
revision numbers, the sort is ascending and the number of documents to
skip equals the revision number.

If a networking error or server error occurs, drivers MUST raise an
error.

Partial File Retrieval
----------------------

In the case of open_download_stream, drivers SHOULD support partial
file retrieval by allowing the application to read only part of the
stream. If a driver does support reading only part of the stream, it
MUST do so using the standard stream methods of its language for seeking
to a position in a stream and reading the desired amount of data
from that position. This is the preferred method of supporting
partial file retrieval.

In the case of download_to_stream, drivers are not required to support
partial file retrieval. If they choose to do so, drivers can support
this operation by adding ‘start’ and ‘end’ to their supported options
for download_to_stream. These values represent non-negative
byte offsets from the beginning of the file. When ‘start’ and ‘end’ are
specified, drivers return the bytes of the file in [start, end). If
‘start’ and ‘end’ are equal no data is returned.

If either ‘start’ or ‘end’ is invalid, drivers MUST raise an error.
These values are considered invalid if they are negative, greater than
the file length, or if ‘start’ is greater than ‘end’.

When performing partial reads, drivers SHOULD use the file’s ‘chunkSize’
to calculate which chunks contain the desired section and avoid reading
unneeded documents from the ‘chunks’ collection.

Renaming stored files
---------------------

.. code:: javascript

  class GridFSBucket {
  
    /**
     * Renames the stored file with the specified @id.
     */
    void rename(ObjectId id, string new_filename);
  
  }

Sets the filename field in the stored file’s files collection document
to the new filename.

**Implementation details:**

Drivers construct and execute an update_one command on the files
collection using { _id: @id } as the filter and { $set : { filename :
"new_filename" } } as the update parameter.

To rename multiple revisions of the same filename, users must retrieve
the full list of files collection documents for a given filename and
execute “rename” on each corresponding “_id”.

If there is no file with the given id, drivers MUST raise an error.

Dropping an entire GridFS bucket
--------------------------------

.. code:: javascript

  class GridFSBucket {

    /**
     * Drops the files and chunks collections associated with
     * this bucket.
     */
    void drop();

  }

This method drops the files and chunks collections associated with this
GridFS bucket.

Drivers should drop the files collection first, and then the chunks
collection.

Test Plan
=========

TBD

Motivation for Change
=====================

The `existing GridFS documentation <http://docs.mongodb.org/manual/reference/gridfs/>`__ is
only concerned with the underlying data model for this feature, and does
not specify what basic set of features an implementation of GridFS
should or should not provide. As a result, GridFS is currently
implemented across drivers, but with varying APIs, features, and
behavior guarantees. Current implementations also may not conform to the
existing documentation.

This spec documents minimal operations required by all drivers offering
GridFS support, along with optional features that drivers may choose to
support. This spec is also explicit about what features/behaviors of
GridFS are not specified and should not be supported. Additionally, this
spec validates and clarifies the existing data model, deprecating fields
that are undesirable or incorrect.

Design Rationale
================

Why is the default chunk size 255KB?
  On MMAPv1, the server provides documents with extra padding to allow for
  in-place updates. When the ‘data’ field of a chunk is limited to 255KB,
  it ensures that the whole chunk document (the chunk data along with an
  _id and other information) will fit into a 256KB section of memory,
  making the best use of the provided padding. Users setting custom chunk
  sizes are advised not to use round power-of-two values, as the whole
  chunk document is likely to exceed that space and demand extra padding
  from the system. WiredTiger handles its memory differently, and this
  optimization does not apply. However, because application code generally
  won’t know what storage engine will be used in the database, always
  avoiding round power-of-two chunk sizes is recommended.

Why can’t I alter documents once they are in the system?
  GridFS works with documents stored in multiple collections within
  MongoDB. Because there is currently no way to atomically perform
  operations across collections in MongoDB, there is no way to alter
  stored files in a way that prevents race conditions between GridFS
  clients. Updating GridFS stored files without that server functionality
  would involve a data model that could support this type of concurrency,
  and changing the GridFS data model is outside of the scope of this spec.

Why provide a ‘rename’ method?
  By providing users with a reasonable alternative for renaming a file, we
  can discourage users from writing directly to the files collections
  under GridFS. With this approach we can prevent critical files
  collection documents fields from being mistakenly altered.

Why is there no way to perform arbitrary updates on the files collection?
  The rename helper defined in this spec allows users to easily rename a
  stored file. While updating files collection documents in other, more
  granular ways might be helpful for some users, validating such updates
  to ensure that other files collection document fields remain protected
  is a complicated task. We leave the decision of how best to provide this
  functionality to a future spec.

What is the ‘md5’ field of a files collection document and how is it used?
  ‘md5’ holds an MD5 checksum that is computed from the original contents
  of a user file. Historically, GridFS did not use acknowledged writes, so
  this checksum was necessary to ensure that writes went through properly.
  With acknowledged writes, the MD5 checksum is still useful to ensure
  that files in GridFS have not been corrupted. A third party directly
  accessing the 'files' and ‘chunks’ collections under GridFS could,
  inadvertently or maliciously, make changes to documents that would make
  them unusable by GridFS. Comparing the MD5 in the files collection
  document to a re-computed MD5 allows detecting such errors and
  corruption. However, drivers now assume that the stored file is not
  corrupted, and applications that want to use the MD5 value to check for
  corruption must do so themselves.

Why store the MD5 checksum instead of creating the hash as-needed?
  The MD5 checksum must be computed when a file is initially uploaded to
  GridFS, as this is the only time we are guaranteed to have the entire
  uncorrupted file. Computing it on-the-fly as a file is read from GridFS
  would ensure that our reads were successful, but guarantees nothing
  about the state of the file in the system. A successful check against
  the stored MD5 checksum guarantees that the stored file matches the
  original and no corruption has occurred.

Why do drivers no longer need to call the filemd5 command on upload?
  When a chunk is inserted and no error occurs the application can assume
  that the chunk was correctly inserted. No other operations that insert
  or modify data require the driver to double check that the operation
  succeeded. It can be assumed that any errors would have been detected by
  use of the appropriate write concern.

What about write concern?
  This spec leaves the choice of how to set write concern to driver
  authors. Implementers may choose to accept write concern through options
  on the given methods, to set a configurable write concern on the GridFS
  object, to enforce a single write concern for all GridFS operations, or
  to do something different.

If a user has given GridFS a write concern of 0, should we perform MD5 calculations?
  Yes, because the checksum is used for detecting future corruption or
  misuse of GridFS collections.

Is GridFS limited by sharded systems?
  For best performance, clients using GridFS on a sharded system should
  use a shard key that ensures all chunks for a given stored file are
  routed to the same shard. Therefore, if the chunks collection is
  sharded, you should shard on the files_id. Normally only the chunks
  collection benefits from sharding, since the files collection is usually
  small. Otherwise, there are no limitations to GridFS on sharded systems.

Why is contentType deprecated?
  Most fields in the files collection document are directly used by the
  driver, with the exception of: metadata, contentType and aliases. All
  information that is purely for use of the application should be embedded
  in the 'metadata' document. Users of GridFS who would like to store a
  contentType for use in their applications are encouraged to add a
  'contentType' field to the ‘metadata’ document instead of using the
  deprecated top-level ‘contentType’ field.

Why are aliases deprecated?
  The ‘aliases’ field of the files collection documents was misleading. It
  implies that a file in GridFS could be accessed by alternate names when,
  in fact, none of the existing implementations offer this functionality.
  For GridFS implementations that retrieve stored files by filename or
  support specifying specific revisions of a stored file, it is unclear
  how ‘aliases’ should be interpreted. Users of GridFS who would like to
  store alternate filenames for use in their applications are encouraged
  to add an ‘aliases’ field to the ‘metadata’ document instead of using
  the deprecated top-level ‘aliases’ field.

What happened to the put and get methods from earlier drafts?
  Upload and download are more idiomatic names that more clearly indicate
  their purpose. Get and put are often associated with getting and setting
  properties of a class, and using them instead of download and upload was
  confusing.

Why aren't there methods to upload and download byte arrays?
  We assume that GridFS files are usually quite large and therefore that
  the GridFS API must support streaming. Most languages have easy ways to
  wrap a stream around a byte array. Drivers are free to add helper
  methods that directly support uploading and downloading GridFS files as
  byte arrays.

Should drivers report an error if a stored file has extra chunks?
  The length and the chunkSize fields of the files collection document
  together imply exactly how many chunks a stored file should have. If the
  chunks collection has any extra chunks the stored file is in an
  inconsistent state. Ideally we would like to report that as an error,
  but this is an extremely unlikely state and we don't want to pay a
  performance penalty checking for an error that is almost never there.
  Therefore, drivers MAY ignore extra chunks.

Backwards Compatibility
=======================

This spec presents a new API for GridFS systems, which may break
existing functionality for some drivers. The following are suggestions
for ways to mitigate these incompatibilities.

File revisions
  This document presents a basic API that does not support specifying
  specific revisions of a stored file, and an advanced API that does.
  Drivers MAY choose to implement whichever API is closest to the
  functionality they now support. Note that the methods for file insertion
  are the same whether specifying specific revisions is supported or not.

Method names
  If drivers provide methods that conform to the functionality outlined in
  this document, drivers MAY continue to provide those methods under their
  existing names. In this case, drivers SHOULD make it clear in their
  documentation that these methods have equivalents defined in the spec
  under a different name.

ContentType field
  Drivers MAY continue to create a ‘contentType'’ field within files
  collection documents, so that applications depending on this field
  continue to work. However, drivers SHOULD make it clear in their
  documentation that this field is deprecated, and is not used at all in
  driver code. Documentation SHOULD encourage users to store contentType
  in the ‘metadata’ document instead.

Aliases field
  Drivers MAY continue to create an ‘aliases’ field within files
  collection documents, so that applications depending on this field
  continue to work. However, drivers SHOULD make it clear in their
  documentation that this field is deprecated, and is not used at all in
  driver code. Documentation SHOULD encourage users to store aliases in
  the ‘metadata’ document instead.

Reference Implementation
========================

TBD

Future work
===========

Changes to the GridFS data model are out-of-scope for this spec, but may
be considered for the future.

The ability to alter or append to existing GridFS files has been cited
as something that would greatly improve the system. While this
functionality is not in-scope for this spec (see ‘Why can’t I alter
documents once they are in the system?’) it is a potential area of
growth for the future.

It has also been suggested that the MD5 hashing performed on stored
files be updated to use a more secure algorithm, like SHA-1 or SHA-256.

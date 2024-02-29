# Bulk Write

- Status: In Review
- Minimum Server Version: 8.0

## Abstract

This specification defines the driver API for the `bulkWrite` server command introduced in MongoDB
8.0. The API defined in this specification allows users to perform insert, update, and delete
operations against mixed namespaces in a minimized number of round trips, and to receive detailed
results for each operation performed. This API is distinct from the
[collection-level bulkWrite method](../crud/crud.md#insert-update-replace-delete-and-bulk-writes)
defined in the CRUD specification and the
[deprecated bulk write specification](../driver-bulk-update.rst).

## Specification

### `MongoClient.bulkWrite` Interface

**NOTE:** The types specified in this interface are similar to those used for the collection-level
`bulkWrite` method. Statically typed drivers MUST NOT reuse any types they already define for the
`MongoCollection.bulkWrite` interface and MUST introduce new types. If naming conflicts between
types arise, drivers MAY prepend "Client" to the new type names (e.g. `ClientBulkWriteOptions`).

```typescript
interface MongoClient {
    /**
     * Executes a list of mixed write operations.
     *
     * @throws BulkWriteException
     */
    bulkWrite(models: NamespaceWriteModelPair[], options: Optional<BulkWriteOptions>): BulkWriteResult;
}
```

### Write Models

A `WriteModel` defines a single write operation to be performed as part of a bulk write.

```typescript
/**
 * Unifying interface for the various write model types. Drivers may also use an enum with
 * variants for each write model for this type.
 */
interface WriteModel {}

class InsertOneModel implements WriteModel {
    /**
     * The document to insert.
     */
    document: Document;
}

class UpdateOneModel implements WriteModel {
    /**
     * The filter to apply.
     */
    filter: Document;

    /**
     * The update document or pipeline to apply to the selected document.
     */
    update: (Document | Document[]);

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    arrayFilters: Optional<Document[]>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern. If
     * specified, then the query system will only consider plans using the hinted index.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query. Defaults to false.
     *
     * This options is sent only if the caller explicitly provides a value.
     */
    upsert: Optional<Boolean>;
}

class UpdateManyModel implements WriteModel {
    /**
     * The filter to apply.
     */
    filter: Document;

    /**
     * The update document or pipeline to apply to the selected documents.
     */
    update: (Document | Document[]);

    /**
     * A set of filters specifying to which array elements an update should apply.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    arrayFilters: Optional<Document[]>;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern. If
     * specified, then the query system will only consider plans using the hinted index.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query. Defaults to false.
     *
     * This options is sent only if the caller explicitly provides a value.
     */
    upsert: Optional<Boolean>;
}

class ReplaceOneModel implements WriteModel {
    /**
     * The filter to apply.
     */
    filter: Document;

    /**
     * The replacement document.
     */
    filter: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern. If
     * specified, then the query system will only consider plans using the hinted index.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    hint: Optional<(String | Document)>;

    /**
     * When true, creates a new document if no document matches the query. Defaults to false.
     *
     * This options is sent only if the caller explicitly provides a value.
     */
    upsert: Optional<Boolean>;
}

class DeleteOneModel implements WriteModel {
    /**
     * The filter to apply.
     */
    filter: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern. If
     * specified, then the query system will only consider plans using the hinted index.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    hint: Optional<(String | Document)>;
}

class DeleteManyModel implements WriteModel {
    /**
     * The filter to apply.
     */
    filter: Document;

    /**
     * Specifies a collation.
     *
     * This option is sent only if the caller explicitly provides a value.
     */
    collation: Optional<Document>;

    /**
     * The index to use. Specify either the index name as a string or the index key pattern. If
     * specified, then the query system will only consider plans using the hinted index.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    hint: Optional<(String | Document)>;
}
```

Each write model provided to `MongoClient.bulkWrite` in the `models` parameter MUST have a
corresponding namespace that defines the collection on which the operation should be performed.
Drivers SHOULD design this pairing in whichever way is most ergonomic for its language. For
example, drivers may:

- Include a required `namespace` field on each `WriteModel` variant
- Accept a list of `(Namespace, WriteModel)` tuples for `models`
- Define the following pair class:

```typescript
class NamespaceWriteModelPair {
    /**
     * The namespace on which to perform the write.
     */
    namespace: Namespace;

    /**
     * The write to perform.
     */
    model: WriteModel;
}
```

Drivers MUST throw an exception if the list provided for `models` is empty.

### Options

```typescript
class BulkWriteOptions {
    /**
     * Whether the operations in this bulk write should be executed in the order in which they were
     * specified. If false, writes will continue to be executed if an individual write fails. If
     * true, writes will stop executing if an individual write fails.
     *
     * Defaults to false.
     */
    ordered: Optional<Boolean>;

    /**
     * If true, allows the writes to opt out of document-level validation.
     *
     * Defaults to false.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    bypassDocumentValidation: Optional<Boolean>;

    /**
     * A map of parameter names and values to apply to all operations within the bulk write. Value
     * must be constant or closed expressions that do not reference document fields. Parameters can
     * then be accessed as variables in an aggregate expression context (e.g. "$$var").
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    let: Optional<Document>;

    /**
     * The write concern to use for this bulk write.
     *
     * NOT REQUIRED TO IMPLEMENT. Drivers MUST expose this option if retrieving a handle to a
     * client with a different write concern configured than that of the user's standard URI
     * options is nontrivial. Drivers MAY omit this option if they provide a way to retrieve a
     * lightweight handle to a client with a custom write concern configured, e.g. a
     * MongoClient.withWriteConcern() method.
     */
    writeConcern: Optional<WriteConcern>;

    /**
     * Whether detailed results for each successful operation should be included in the returned
     * BulkWriteResult.
     *
     * Defaults to false.
     */
    verboseResults: Optional<Boolean>;
}
```

### Result

```typescript
class BulkWriteResult {
    /**
     * Indicates whether this write result was acknowledged. If not, then all other members of this
     * result will be undefined.
     *
     * NOT REQUIRED TO IMPLEMENT. See [here](../crud/crud.md#write-results) for more guidance on
     * modeling unacknowledged results.
     */
    acknowledged: Boolean;

    /**
     * Indicates whether the results are verbose. If false, the insertResults, updateResults, and
     * deleteResults fields in this result will be undefined.
     *
     * NOT REQUIRED TO IMPLEMENT. See below for other ways to differentiate summary results from
     * verbose results.
     */
    hasVerboseResults: Boolean;

    /**
     * The total number of documents inserted across all insert operations.
     */
    insertedCount: Int64;

    /**
     * The total number of documents upserted across all update operations.
     */
    upsertedCount: Int64;

    /**
     * The total number of documents matched across all update operations.
     */
    matchedCount: Int64;

    /**
     * The total number of documents modified across all update operations.
     */
    modifiedCount: Int64;

    /**
     * The total number of documents deleted across all delete operations.
     */
    deletedCount: Int64;

    /**
     * The results of each individual insert operation that was successfully performed. Results
     * can be accessed by their index in the list of write models provided to bulkWrite.
     */
    insertResults: Map<Int64, InsertOneResult>;

    /**
     * The results of each individual update operation that was successfully performed. Results
     * can be accessed by their index in the list of write models provided to bulkWrite.
     */
    updateResult: Map<Int64, UpdateResult>;

    /**
     * The results of each individual delete operation that was successfully performed. Results
     * can be accessed by their index in the list of write models provided to bulkWrite.
     */
    deleteResults: Map<Int64, DeleteResult>;
}

class InsertOneResult {
    /**
     * The _id of the inserted document.
     */
    insertedId: Any;
}

class UpdateResult {
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
     * NOT REQUIRED TO IMPLEMENT. Drivers may choose not to provide this property so long as it is
     * always possible to discern whether an upsert took place.
     */
    upsertedCount: Int64;

    /**
     * The _id field of the upserted document if an upsert occurred.
     */
    upsertedId: Optional<Any>;
}

class DeleteResult {
    /**
     * The number of documents that were deleted.
     */
    deletedCount: Int64;
}
```

#### Summary vs. Verbose Results

Users MUST be able to discern whether a `BulkWriteResult` contains summary or verbose results
without inspecting the value provided for `verboseResults` in `BulkWriteOptions`. Drivers MUST
implement this in one of the following ways:

- Expose the `hasVerboseResults` field in `BulkWriteResult` as defined above.
- Implement the `insertResults`, `upsertResults`, and `deleteResults` fields as optional types and
  document that they will be unset when `verboseResults` is false.
- Introduce separate `SummaryBulkWriteResult` and `VerboseBulkWriteResult` types.
  `VerboseBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above.
  `SummaryBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above
  except `insertResults`, `updateResults`, and `deleteResults`.

#### Individual Results

The `InsertOneResult`, `UpdateResult`, and `DeleteResult` classes are the same as or similar to
types of the same name defined in the [CRUD specification](crud.md). Drivers MUST redefine these
classes if their existing result classes deviate from the definitions in this specification (e.g.
if they contain acknowledgement information, which is not applicable for individual bulk write
operations). Drivers MAY reuse their existing types for these classes if they match the ones
defined here exactly.

### Exception

```typescript
class BulkWriteException {
    /**
     * A top-level error that occurred when attempting to communicate with the server or execute
     * the bulk write. This value may not be populated if the exception was thrown due to errors
     * occurring on individual writes.
     */
    error: Optional<Error>;

    /**
     * Write concern errors that occurred while executing the bulk write. This list may have
     * multiple items if more than one server command was required to execute the bulk write.
     */
    writeConcernErrors: WriteConcernError[];

    /**
     * Errors that occurred during the execution of individual write operations. This map will
     * contain at most one entry if the bulk write was ordered.
     */
    writeErrors: Map<Int64, WriteError>;

    /**
     * The results of any successful operations that were performed before the error was
     * encountered.
     */
    partialResult: Optional<BulkWriteResult>;
}
```

## Building a `bulkWrite` Command

The `bulkWrite` server command has the following format:

```json
{
    "bulkWrite": 1,
    "ops": <Array>,
    "nsInfo": <Array>,
    "errorsOnly": <Boolean>,
    "ordered": <Boolean>,
    "bypassDocumentValidation": <Boolean>,
    "comment": <Bson>,
    "let": <Document>,
    ...additional operation-agnostic fields
}
```

Drivers SHOULD use document sequences ([`OP_MSG`](../message/OP_MSG.rst) payload type 1) for the
`ops` and `nsInfo` fields. Drivers MUST NOT use document sequences when auto-encryption is enabled.

The `bulkWrite` command is executed on the "admin" database.

### Operations

The `ops` field is a list of write operation documents. The first entry in each document has
the name of the operation (i.e. "insert", "update", or "delete") as its key and the index in the
`nsInfo` array of the namespace on which the operation should be performed as its value. The
documents have the following format:

#### Insert

```json
{
    "insert": <Int32>,
    "document": <Document>
}
```

Drivers MUST add an `_id` field at the beginning of the insert document if one is not already
present.

When a user executes a bulk write with an unacknowledged write concern, drivers SHOULD check the
size of the insert document to verify that it does not exceed `maxBsonObjectSize`. For acknowledged
bulk writes, drivers MAY rely on the server to return an error if the document exceeds
`maxBsonObjectSize`. The value for `maxBsonObjectSize` can be retrieved from the selected server's
`hello` response.

#### Update

```json
{
    "update": <Int32>,
    "filter": <Document>,
    "updateMods": <Document | Array>,
    "multi": <Boolean>,
    "upsert": <Boolean>,
    "arrayFilters": <Array>,
    "hint": <String>
}
```

#### Delete

```json
{
    "delete": <Int32>,
    "filter": <Document>,
    "multi": <boolean>,
    "hint": <String>,
    "collation": <Document>
}
```

### Namespace Information

The `nsInfo` field contains the namespaces on which the write operations should be performed.
Drivers MUST NOT include duplicate namespaces in this list. The documents in the `nsInfo` field
have the following format:

```json
{
    "ns": <String>
}
```

### Toggling Results Verbosity

The `errorsOnly` field indicates whether the results cursor returned in the `bulkWrite` response
should contain only errors. If false, individual results for successful operations will be returned
in addition to errors.

This field corresponds to the `verboseResults` option defined on `BulkWriteOptions`. Its value
should be provided as `false` if `verboseResults` was set to `true`; otherwise, it should be
provided as `true`. This field MUST always be defined in the `bulkWrite` command regardless of
whether the user specified a value for `verboseResults`.

## Command Batching

Drivers MUST accept an arbitrary number of operations as input to the `Client.bulkWrite` method.
Because the server imposes restrictions on the size of write operations, this means that a single
call to `MongoClient.bulkWrite` may require multiple `bulkWrite` commands to be sent to the server.
Drivers MUST split bulk writes into separate commands when the user's list of operations exceeds
one or more of these maximums: `maxWriteBatchSize`, `maxBsonObjectSize`, and `maxMessageSizeBytes`.
Each of these values can be retrieved from the selected server's `hello` command response.

### Number of Writes

The `ops` array MUST NOT include more than `maxWriteBatchSize` operations.

### Total Message Size

#### Encrypted bulk writes

When auto-encryption is enabled, drivers MUST NOT provide the `ops` and `nsInfo` fields as document
sequences and MUST limit the size of the command according to the auto-encryption size limits
defined in the
[Client Side Encryption Specification](../client-side-encryption/client-side-encryption.rst).

#### Unencrypted bulk writes with document sequences

When `ops` and `nsInfo` are provided as document sequences, drivers MUST ensure that the combined
size of these sequences does not exceed `maxMessageSizeBytes - 16,000`. `maxMessageSizeBytes`
defines the maximum size for an entire `OP_MSG`, so 16KB is subtracted from `maxMessageSizeBytes`
in this size limit to account for the bytes in the rest of the message.

#### Unencrypted bulk writes without document sequences

When `ops` and `nsInfo` are provided within the `bulkWrite` command document and auto-encryption is
not enabled, drivers MUST ensure that the total size of the `bulkWrite` command document does not
exceed `maxBsonObjectSize`.

## Handling the `bulkWrite` Server Response

The server's response to `bulkWrite` has the following format:

```json
{
    "ok": <0 | 1>,
    "cursor": {
        "id": <Int64>,
        "firstBatch": <Array>,
        "ns": <String>
    },
    "nErrors": <Int32>,
    "nInserted": <Int32>,
    "nUpserted": <Int32>,
    "nMatched": <Int32>,
    "nModified": <Int32>,
    "nDeleted": <Int32>,
    ...additional command-agnostic fields
}
```

If any operations were successful (i.e. `nErrors` is less than the number of operations that were
sent), drivers MUST record the summary count fields in a `BulkWriteResult` to be returned to the
user or included in a `BulkWriteException`.

Drivers MUST attempt to consume the contents of the cursor returned in the server's `bulkWrite`
response before returning to the user. This is required regardless of whether the user requested
verbose or summary results, as the results cursor always contains any write errors that occurred.
If the cursor contains a nonzero cursor ID, drivers MUST perform `getMore`s until the cursor has
been exhausted. Drivers MUST use the same session used for the `bulkWrite` command for each
`getMore` call.

The documents in the results cursor have the following format:

```json
{
    "ok": <0 | 1>,
    "code": Optional<Int32>,
    "errmsg": Optional<String>,
    "n": <Int32>,
    "nMatched": <Int32>,
    "nModified": <Int32>,
    "upsertedId": Optional<ObjectId>
}
```

Note that the responses do not contain information about the type of operation that was performed.
Drivers may need to maintain the user's list of write models to infer which type of result should
be recorded.

### Handling Insert Results

Unlike the other result types, `InsertOneResult` contains an `insertedId` field that is generated
driver-side, either by recording the `_id` field present in the user's insert document or creating
and adding one. Drivers MUST only record these `insertedId`s in a `BulkWriteResult` when a
successful response for the insert operation (i.e. `{ "ok": 1, "n": 1 }`) is received in the
results cursor. This ensures that drivers only report an `insertedId` when it is confirmed that the
insert succeeded.

## Handling errors

### Top-level errors

A top-level error is any error that occurs that is not the result of a single write operation
failing or a write concern error. Examples include network errors that occur when communicating
with the server, command errors returned from the server, client-side errors, and errors that occur
when attempting to perform a `getMore` to retrieve results from the server.

When a top-level error is encountered and individual results and/or errors have already been
observed, drivers MUST embed the top-level error within a `BulkWriteException` as the `error` field
to retain this information. Otherwise, drivers MAY throw an exception containing only the top-level
error.

Encountering a top-level error MUST halt execution of a bulk write for both ordered and unordered
bulk writes. This means that drivers MUST NOT attempt to retrieve more responses from the cursor or
execute any further `bulkWrite` batches and MUST immediately throw an exception.

### Write concern errors

Write concern errors are recorded in the `writeConcernErrors` field on `BulkWriteException`. When
a write concern error is encountered, it should not terminate execution of the bulk write for
either ordered or unordered bulk writes. However, drivers MUST throw an exception at the end of
execution if any write concern errors were observed.

### Individual write errors

Individual write errors retrieved from the cursor are recorded in the `writeErrors` field on
`BulkWriteException`. If an individual write error is encountered during an ordered bulk write,
drivers MUST record the error in `writeErrors` and immediately throw the exception. Otherwise,
drivers MUST continue to iterate the results cursor and execute any further `bulkWrite` batches.

## Test Plan

The majority of tests for `MongoClient.bulkWrite` are written in the
[Unified Test Format](../unified-test-format/unified-test-format.md) and reside in the
[CRUD unified tests directory](../crud/tests/unified/).

Additional prose tests are specified [here](../crud/tests/README.md). These tests require
constructing very large documents to test batch splitting, which is not feasible in the unified
test format at the time of writing this specification.

## Q&A

### Why are we adding a new bulk write API rather than updating the `MongoCollection.bulkWrite` implementation?

The new `bulkWrite` command is only available in MongoDB 8.0+, so it cannot function as a drop-in
replacement for the existing bulk write implementation that uses the `insert`, `update`, and
`delete` commands. Additionally, because the new `bulkWrite` command allows operations against
multiple collections and databases, `MongoClient` is a more appropriate place to expose its
functionality.

### Why can't drivers reuse existing bulk write types?

This specification introduces several types that are similar to existing types used in the
`MongoCollection.bulkWrite` API. Although these types are similar now, they may diverge in the
future with the introduction of new options and features to the `bulkWrite` command. Introducing
new types also provides more clarity to users on the existing differences between the
collection-level and client-level bulk write APIs. For example, the `verboseResults` option is only
available for `MongoClient.bulkWrite`.

### Why are bulk write operation results returned in a cursor?

Returning results via a cursor rather than an array in the `bulkWrite` response allows full
individual results and errors to be returned without the risk of the response exceeding the
maximum BSON object size. Using a cursor also leaves open the opportunity to add `findAndModify` to
the list of supported write operations in the future.

### Why was the `verboseResults` option introduced, and why is its default `false`?

The `bulkWrite` command returns top-level summary result counts and, optionally, individual results
for each operation. Compiling the individual results server-side and consuming these results
driver-side is less performant than only recording the summary counts. We expect that most users
are not interested in the individual results of their operations and that most users will rely on
defaults, so `verboseResults` defaults to `false` to improve performance in the common case.

## **Changelog**

- TODO: Bulk write specification created.

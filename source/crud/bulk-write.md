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

> [!NOTE]
>
> The `BulkWriteOptions`, `BulkWriteResult`, and `BulkWriteException` types defined in this
> specification are similar to those used for the `MongoCollection.bulkWrite` method. Statically
> typed drivers MUST NOT reuse their existing definitions for these types for the
> `MongoClient.bulkWrite` API and MUST introduce new types. If naming conflicts arise, drivers
> SHOULD prepend "Client" to the new type names (e.g. `ClientBulkWriteOptions`).

### `MongoClient.bulkWrite` Interface

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
    hint: Optional<Document | String>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is only sent if the caller explicitly provides a value. The server's default
     * value is false.
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
    hint: Optional<Document | String>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is only sent if the caller explicitly provides a value. The server's default
     * value is false.
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
    replacement: Document;

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
    hint: Optional<Document | String>;

    /**
     * When true, creates a new document if no document matches the query.
     *
     * This option is only sent if the caller explicitly provides a value. The server's default
     * value is false.
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
    hint: Optional<Document | String>;
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
    hint: Optional<Document | String>;
}
```

Each write model provided to `MongoClient.bulkWrite` in the `models` parameter MUST have a
corresponding namespace that defines the collection on which the operation should be performed.
Drivers SHOULD design this pairing in whichever way is most idiomatic for its language. For
example, drivers may:

- Include a required `namespace` field on each `WriteModel` variant and accept a list of
  `WriteModel` objects for the `models` parameter.
- Accept a list of `(Namespace, WriteModel)` tuples for `models`.
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
     * Defaults to true.
     */
    ordered: Optional<Boolean>;

    /**
     * If true, allows the writes to opt out of document-level validation.
     *
     * This option is only sent if the caller explicitly provides a value. The server's default
     * value is false.
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
     */
    writeConcern: Optional<WriteConcern>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs.
     *
     * This option is only sent if the caller explicitly provides a value.
     */
    comment: Optional<BSON value>;

    /**
     * Whether detailed results for each successful operation should be included in the returned
     * BulkWriteResult.
     *
     * Defaults to false. This value corresponds inversely to the errorsOnly field in the bulkWrite
     * command.
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
     * NOT REQUIRED TO IMPLEMENT. See below for more guidance on modeling unacknowledged results.
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
     * The results of each individual insert operation that was successfully performed.
     */
    insertResults: Map<Int64, InsertOneResult>;

    /**
     * The results of each individual update operation that was successfully performed.
     */
    updateResults: Map<Int64, UpdateResult>;

    /**
     * The results of each individual delete operation that was successfully performed.
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
     * The _id field of the upserted document if an upsert occurred.
     *
     * It MUST be possible to discern between a BSON Null upserted ID value and this field being
     * unset. If necessary, drivers MAY add a didUpsert boolean field to differentiate between
     * these two cases.
     */
    upsertedId: Optional<BSON value>;
}

class DeleteResult {
    /**
     * The number of documents that were deleted.
     */
    deletedCount: Int64;
}
```

#### Unacknowledged results

`BulkWriteResult` has an optional `acknowledged` field to indicate whether the result was
acknowledged. This is not required to implement. Drivers should follow the guidance in the CRUD
specification [here](../crud/crud.md#write-results) to determine how to model unacknowledged
results.

#### Summary vs. verbose results

Users MUST be able to discern whether a `BulkWriteResult` contains summary or verbose results
without inspecting the value provided for `verboseResults` in `BulkWriteOptions`. Drivers MUST
implement this in one of the following ways:

- Expose the `hasVerboseResults` field in `BulkWriteResult` as defined above. Document that
  `insertResults`, `updateResults`, and `deleteResults` will be undefined when `hasVerboseResults`
  is false. Raise an error if a user tries to access one of these fields when `hasVerboseResults`
  is false.
- Implement the `insertResults`, `updateResults`, and `deleteResults` fields as optional types and
  document that they will be unset when `verboseResults` is false.
- Introduce separate `SummaryBulkWriteResult` and `VerboseBulkWriteResult` types.
  `VerboseBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above.
  `SummaryBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above
  except `insertResults`, `updateResults`, and `deleteResults`.

#### Individual results

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
    "errorsOnly": Optional<Boolean>,
    "ordered": Optional<Boolean>,
    "bypassDocumentValidation": Optional<Boolean>,
    "comment": Optional<BSON value>,
    "let": Optional<Document>,
    ...additional operation-agnostic fields
}
```

Drivers MUST use document sequences ([`OP_MSG`](../message/OP_MSG.rst) payload type 1) for the
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

If the document to be inserted does not contain an `_id` field, drivers MUST generate a new
[`ObjectId`](../objectid.rst) and add it as the `_id` field at the beginning of the document.

#### Update

```json
{
    "update": <Int32>,
    "filter": <Document>,
    "updateMods": <Document | Array>,
    "multi": Optional<Boolean>,
    "upsert": Optional<Boolean>,
    "arrayFilters": Optional<Array>,
    "hint": Optional<Document | String>
}
```

#### Delete

```json
{
    "delete": <Int32>,
    "filter": <Document>,
    "multi": Optional<Boolean>,
    "hint": Optional<Document | String>,
    "collation": Optional<Document>
}
```

### Namespace Information

The `nsInfo` field is an array containing the namespaces on which the write operations should be
performed. Drivers MUST NOT include duplicate namespaces in this list. The documents in the
`nsInfo` array have the following format:

```json
{
    "ns": <String>
}
```

### `errorsOnly` and `verboseResults`

The `errorsOnly` field indicates whether the results cursor returned in the `bulkWrite` response
should contain only errors and omit individual results. If false, both individual results for
successful operations and errors will be returned. This field is optional and defaults to false on
the server.

`errorsOnly` corresponds to the `verboseResults` option defined on `BulkWriteOptions`. If the user
specified a value for `verboseResults`, drivers MUST define `errorsOnly` as the opposite of
`verboseResults`. If the user did not specify a value for `verboseResults`, drivers MUST define
`errorsOnly` as `true`.

### `ordered`

The `ordered` field defines whether writes should be executed in the order in which they were
specified, and, if an error occurs, whether the server should halt execution of further writes. It
is optional and defaults to true on the server. Drivers MUST explicitly define `ordered` as `true`
in the `bulkWrite` command if a value is not specified in `BulkWriteOptions`. This is required to
avoid inconsistencies between server and driver behavior if the server default changes in the
future.

### Size Limits

The server reports a `maxBsonObjectSize` in its `hello` response. This value defines the maximum
size for documents that are inserted into the database. Documents that are sent to the server but
are not intended to be inserted into the database (e.g. command documents) have a size limit of
`maxBsonObjectSize + 16KiB`. When an acknowledged write concern is used, drivers MUST NOT perform
any checks related to these size limits and MUST rely on the server to raise an error if a limit is
exceeded. However, when an unacknowledged write concern is used, drivers MUST raise an error if one
of the following limits is exceeded:

- The size of a document to be inserted MUST NOT exceed `maxBsonObjectSize`. This applies to the
  `document` field of an `InsertOneModel` and the `replacement` field of a `ReplaceOneModel`.
- The size of an entry in the `ops` array MUST NOT exceed `maxBsonObjectSize + 16KiB`.
- The size of the `bulkWrite` command document MUST NOT exceed `maxBsonObjectSize + 16KiB`.

See [SERVER-10643](https://jira.mongodb.org/browse/SERVER-10643) for more details on these size
limits.

## Command Batching

Drivers MUST accept an arbitrary number of operations as input to the `MongoClient.bulkWrite` method.
Because the server imposes restrictions on the size of write operations, this means that a single
call to `MongoClient.bulkWrite` may require multiple `bulkWrite` commands to be sent to the server.
Drivers MUST split bulk writes into separate commands when the user's list of operations exceeds
one or more of these maximums: `maxWriteBatchSize`, `maxBsonObjectSize` (for `OP_MSG` payload type
0), and `maxMessageSizeBytes` (for `OP_MSG` payload type 1). Each of these values can be retrieved
from the selected server's `hello` command response. Drivers MUST merge results from multiple batches
into a single `BulkWriteResult` or `BulkWriteException` to return from `MongoClient.bulkWrite`.

### Number of Writes

`maxWriteBatchSize` defines the total number of writes allowed in one command. Drivers MUST split a
bulk write into multiple commands if the user provides more than `maxWriteBatchSize` operations in
the argument for `models`.

### Total Message Size

#### Encrypted bulk writes

When auto-encryption is enabled, drivers MUST NOT provide the `ops` and `nsInfo` fields as document
sequences and MUST limit the size of each `bulkWrite` command according to the auto-encryption size
limits defined in the
[Client Side Encryption Specification](../client-side-encryption/client-side-encryption.rst).

#### Unencrypted bulk writes

When `ops` and `nsInfo` are provided as document sequences, drivers MUST ensure that the total size
of the `OP_MSG` built for each `bulkWrite` command does not exceed `maxMessageSizeBytes`. Some
drivers may perform batch-splitting prior to constructing the full `OP_MSG` to be sent to the
server. In this case, drivers MAY use `maxMessageSizeBytes - 16,384` as the upper bound for the
combined number of bytes in `ops` and `nsInfo`. 16KiB is subtracted as an approximate overhead
allowance to accommodate for the bytes in the rest of the message.

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
user or embedded in a `BulkWriteException`. Drivers MUST NOT populate the `partialResult` field in
`BulkWriteException` if no operations were successful.

Drivers MUST attempt to consume the contents of the cursor returned in the server's `bulkWrite`
response before returning to the user. This is required regardless of whether the user requested
verbose or summary results, as the results cursor always contains any write errors that occurred.
If the cursor contains a nonzero cursor ID, drivers MUST perform `getMore`s until the cursor has
been exhausted. Drivers MUST use the same session used for the `bulkWrite` command for each
`getMore` call. When connected to a load balancer, drivers MUST use the connection used for the
`bulkWrite` command to create the cursor to ensure the same server is targeted.

The documents in the results cursor have the following format:

```json
{
    "ok": <0 | 1>,
    "idx": Int32,
    "code": Optional<Int32>,
    "errmsg": Optional<String>,
    "errInfo": Optional<Document>,
    "n": <Int32>,
    "nModified": Optional<Int32>,
    "upserted": Optional<Document with "_id" field>
}
```

If an error occurred (i.e. the value for `ok` is 0), the `code`, `errmsg`, and optionally
`errInfo` fields will be populated with details about the failure.

If the write succeeded, (i.e. the value for `ok` is 1), `n`, `nModified`, and `upsertedId` will be
populated with the following values based on the type of write:

| Response Field | Insert | Update | Delete |
| -------------- | ------ | ------ | ------ |
| `n` | The number of documents that were inserted. | The number of documents that matched the filter. | The number of documents that were deleted. |
| `nModified` | Not present. | The number of documents that were modified. | Not present. |
| `upserted` | Not present. | A document containing the `_id` value for the upserted document. Only present if an upsert took place. | Not present. |

Note that the responses do not contain information about the type of operation that was performed.
Drivers may need to maintain the user's list of write models to infer which type of result should
be recorded based on the value of `idx`.

### Handling Insert Results

Unlike the other result types, `InsertOneResult` contains an `insertedId` field that is generated
driver-side, either by recording the `_id` field present in the user's insert document or creating
and adding one. Drivers MUST only record these `insertedId`s in a `BulkWriteResult` when a
successful response for the insert operation (i.e. `{ "ok": 1, "n": 1 }`) is received in the
results cursor. This ensures that drivers only report an `insertedId` when it is confirmed that the
insert succeeded.

## Handling Errors

### Top-Level Errors

A top-level error is any error that occurs that is not the result of a single write operation
failing or a write concern error. Examples include network errors that occur when communicating
with the server, command errors (`{ "ok": 0 }`) returned from the server, client-side errors, and
errors that occur when attempting to perform a `getMore` to retrieve results from the server.

When a top-level error is encountered and individual results and/or errors have already been
observed, drivers MUST embed the top-level error within a `BulkWriteException` as the `error` field
to retain this information. Otherwise, drivers MAY throw an exception containing only the top-level
error.

Encountering a top-level error MUST halt execution of a bulk write for both ordered and unordered
bulk writes. This means that drivers MUST NOT attempt to retrieve more responses from the cursor or
execute any further `bulkWrite` batches and MUST immediately throw an exception.

### Write Concern Errors

Write concern errors are recorded in the `writeConcernErrors` field on `BulkWriteException`. When
a write concern error is encountered, it should not terminate execution of the bulk write for
either ordered or unordered bulk writes. However, drivers MUST throw an exception at the end of
execution if any write concern errors were observed.

### Individual Write Errors

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

## Future Work

### Support using document sequences in encrypted bulk writes

Libmongocrypt is currently only capable of encrypting command documents, not wire protocol
messages. This means that all command fields must be embedded within the command document. When
[DRIVERS-2859](https://jira.mongodb.org/browse/DRIVERS-2859) is completed, drivers will be able to
specify `ops` and `nsInfo` as document sequences (`OP_MSG` payload type 1) for encrypted bulk
writes.

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

### Why should drivers send `bypassDocumentValidation: false` for `bulkWrite`?

[DRIVERS-450](https://jira.mongodb.org/browse/DRIVERS-450) introduced a requirement that drivers
only send a value for `bypassDocumentValidation` on write commands if it was specified as true. The
original motivation for this change is not documented. This specification requires that drivers
send `bypassDocumentValidation` in the `bulkWrite` command if it is set by the user in
`BulkWriteOptions`, regardless of its value.

Explicitly defining `bypassDocumentValidation: false` aligns with the server's default to perform
schema validation and thus has no effect. However, checking the value of an option that the user
specified and omitting it from the command document if it matches the server's default creates
unnecessary work for drivers. Always sending the user's specified value also safeguards against the
unlikely event that the server changes the default value for `bypassDocumentValidation` in the
future.

## **Changelog**

- TODO: Bulk write specification created.

# Bulk Write

isabeltodo table

## Abstract

This specification defines the driver API for the `bulkWrite` server command introduced in MongoDB 8.0. The API defined in this specification allows users to perform insert, update, and delete operations against mixed namespaces in a minimized number of round trips, and to receive detailed results for each operation performed. This API is distinct from the collection-level bulkWrite method defined in the CRUD specification and the deprecated bulk write specification (isabeltodo link).

## Specification

### Definitions

Document sequence: An `OP_MSG` payload type 1 as defined in the `OP_MSG` specification here (isabeltodo link).

Namespace: A database name and collection name pair. This may be represented as a string (e.g. `"db.coll"`) or a class with a field for each name, e.g.

```
class Namespace {
    databaseName: String
    collectionName: String
}
```

`bulkWrite`: This specification discusses both the server `bulkWrite` command and the new `bulkWrite` driver API method. To avoid ambiguity, this specification refers to the server command as `bulkWrite` and the driver method as `MongoClient.bulkWrite`.

### `bulkWrite` Command and Response Format

#### Command

The `bulkWrite` server command has the following format:

```json
{
    bulkWrite: 1
    ops: <Array>
    nsInfo: <Array>
    errorsOnly: <Boolean>
    ordered: <Boolean>
    bypassDocumentValidation: <Boolean>
    comment: <Bson>
    let: <Document>
}
```

##### `ops`

The `ops` field is a list of write operation documents. The documents have the following format:

###### Insert

```json
{
    insert: <Int32 (index of namespace in nsInfo)>
    document: <Document>
}
```

###### Update

```json
{
    update: <Int32 (index of namespace in nsInfo)>
    filter: <Document>
    updateMods: <Document | Array>
    multi: <Boolean>
    upsert: <Boolean>
    arrayFilters: <Array>
    hint: <String>
}
```

###### Delete

```json
{
    delete: <Int32 (index of namespace in nsInfo)>
    filter: <Document>
    multi: <boolean>
    hint: <String>
    collation: <Document>
}
```

##### `nsInfo`

The `nsInfo` field contains the namespaces on which the write operations should be performed. Drivers MUST NOT include duplicate namespaces in this list. The documents in the `nsInfo` field have the following format:

```json
{
    ns: <String>
}
```

##### `errorsOnly`

This field corresponds to the `verboseResults` option defined on `BulkWriteOptions`. Its value should be specified as the opposite of `verboseResults`, or `true` if `verboseResults` is unspecified. Drivers MUST always define this field.

#### Response

The server's response to `bulkWrite` has the following format:

```json
{
    ok: <0 | 1>
    cursor: {
        id: Int64
        firstBatch: <Array>
        ns: <String>
    }
    nErrors: <Int64>
    nInserted: <Int64>
    nUpserted: <Int64>
    nMatched: <Int64>
    nModified: <Int64>
    nDeleted: <Int64>
}
```

##### Results Cursor

The response to `bulkWrite` contains a cursor field with the first batch of individual results and a nonzero cursor ID if there are additional results that did not fit in the initial response. Drivers MUST perform `getMore`s until the cursor is exhausted to retrieve all results and errors before returning from `MongoClient.bulkWrite`. If a top-level error occurs before the cursor has been exhausted, drivers MUST send a `killCursors` command to close the cursor.

### `MongoClient.bulkWrite` Signature

```
interface MongoClient {
    bulkWrite(models: List<NamespaceWriteModelPair>,
        options: Optional<BulkWriteOptions>
    ) -> BulkWriteResult throws BulkWriteException;
}
```

The `WriteModel`, `BulkWriteOptions`, `BulkWriteResult`, and `BulkWriteException` types defined here are similar to the types of the same names in the `MongoCollection.bulkWrite` definition. Statically typed drivers MUST NOT reuse any existing versions of these types and MUST introduce new types for the `MongoClient.bulkWrite` method. If 

#### `WriteModel`

The `WriteModel` type defines a single write operation to be performed as part of a bulk write. `WriteModel` may be designed as separate classes that implement a `WriteModel` interface, an enum with a variant for each operation (as shown below), or another similar type.

```

enum WriteModel {
    InsertOne {
        // The document to insert.
        document: Document
    }
    UpdateOne {
        // The filter to apply.
        filter: Document

        // The update document or pipeline to apply to the selected document.
        update: Document | Array

        // isabeltodo
        arrayFilters: Option<Array>

        // isabeltodo
        collation: Option<Document>

        // isabeltodo
        hint: Optional<Bson>

        // isabeltodo
        upsert: Optional<bool>
    }
    UpdateMany {
        // The filter to apply.
        filter: Document

        // The update document or pipeline to apply to the selected documents.
        update: Document | Document[]

        // isabeltodo
        arrayFilters: Option<Array>

        // isabeltodo
        collation: Option<Document>

        // isabeltodo
        hint: Optional<Bson>

        // isabeltodo
        upsert: Optional<bool>
    }
    ReplaceOne {
        // The filter to apply.
        filter: Document

        // The replacement document.
        replacement: Document

        // isabeltodo
        collation: Option<Document>

        // isabeltodo
        hint: Optional<Bson>

        // isabeltodo
        upsert: Optional<bool>
    }
    DeleteOne {
        // The filter to apply.
        filter: Document

        // isabeltodo
        collation: Option<Document>

        // isabeltodo
        hint: Option<Bson>
    }
    DeleteMany {
        // The filter to apply.
        filter: Document,

        // isabeltodo
        collation: Option<Document>,

        // isabeltodo
        hint: Option<Bson>
    }
}
```

##### Namespaces

Each write model supplied to `Client.bulkWrite` in the `models` parameter MUST have a corresponding namespace that defines the collection on which the operation should be performed. Drivers SHOULD design this pairing in whichever way is most ergonomic for its language. For example, drivers may include a required `namespace` field in each `WriteModel` variant, accept a list of `(Namespace, WriteModel)` tuples for `models`, or define the following pair class:

```

class NamespaceWriteModelPair {
    // The namespace on which to perform the operation.
    namespace: Namespace

    // The write to perform.
    model: WriteModel
}
```

#### `BulkWriteOptions`

```

class BulkWriteOptions {
    // Whether the operations in this bulk write should be executed in the order in which they were specified. If false, writes will continue to be executed if an individual write fails. If true, writes will stop executing if an individual write fails. Defaults to true.
    ordered: Optional<bool>

    // If true, allows the writes to opt out of document-level validation. Defaults to false.
    bypassDocumentValidation: Optional<bool>

    // A map of parameter names and values to apply to all operations within the bulk write. Values must be constant or closed expressions that do not reference document fields. Parameters can then be accessed as variables in an aggregate expression context (e.g. "$$var").
    let: Optional<Document>

    // The write concern to use for this bulk write.
    //
    // NOT REQUIRED. Drivers MUST expose this option if retrieving a handle to a `MongoClient` with a different write concern configured than that of the user's standard URI options is nontrivial. Drivers MAY omit this option if they provide a way to retrieve a lightweight handle to a `MongoClient` with a custom write concern configured, e.g. a `MongoClient.withWriteConcern` method.
    writeConcern: Optional<WriteConcern>

    // Whether detailed results for each successful operation should be included in the returned `BulkWriteResult`. Defaults to false.
    verboseResults: Optional<bool>
}
```

#### `BulkWriteResult`

```

class BulkWriteResult {
    // Indicates whether this write result was acknowledged. If not, then all other members of this result will be undefined.
    //
    // NOT REQUIRED. See here(isabeltodo link) for additional guidance on modeling unacknowledged results.
    acknowledged: boolean

    // Indicates whether the results are verbose. This value will be equal to the value of `verboseResults` in the provided `BulkWriteOptions`. If false, the `insertResults`, `updateResults`, and `deleteResults` fields in this result will be undefined.
    //
    // NOT REQUIRED. See below (link) for other ways to differentiate summary results from verbose results.
    hasVerboseResults: boolean

    // The total number of documents inserted across all insert operations.
    insertedCount: i64

    // The total number of documents upserted across all update operations.
    upsertedCount: i64

    // The total number of documents matched across all update operations.
    matchedCount: i64

    // The total number of documents modified across all update operations.
    modifiedCount: i64

    // The total number of documents deleted across all delete operations.
    deletedCount: i64

    // The results of each individual insert operation that was successfully performed. Results can be accessed by their index in the list of write models provided to the call to `MongoClient.bulkWrite`.
    insertResults: Map<index, InsertOneResult>

    // The results of each individual update operation that was successfully performed. Results can be accessed by their index in the list of write models provided to the call to `MongoClient.bulkWrite`.
    updateResults: Map<index, UpdateResult>

    // The results of each individual delete operation that was successfully performed. Results can be accessed by their index in the list of write models provided to the call to `MongoClient.bulkWrite`.
    deleteResults: Map<index, DeleteResult>
}

class InsertOneResult {
    // The _id of the inserted document.
    insertedId: Bson
}

class UpdateResult {
    // The number of documents that matched the filter.
    matchedCount: Int64

    // The number of documents that were modified.
    modifiedCount: Int64

    // The number of documents that were upserted.
    //
    // NOT REQUIRED. Drivers may choose to not provide this property so long as it is always possible to infer whether an upsert has taken place. Since the _id field of an upserted document could be null, a null upsertedId may be ambiguous in some drivers. If so, this field can be used to indicate whether an upsert has taken place.
    upsertedCount: Int64

    // The _id field of the upserted document if an upsert occurred.
    upsertedId: Optional<Bson>
}

class DeleteResult {
    // The number of documents that were deleted.
    deletedCount: Int64
}
```

##### Summary vs. Verbose Results

Users MUST be able to discern whether the result returned from `MongoClient.bulkWrite` is a summary result or a verbose result without accessing the value provided for `verboseResults`. Drivers MUST implement this in one of the following ways:

* Expose the `hasVerboseResults` field in `BulkWriteResult` as defined above.
* Implement the `insertResults`, `updateResults`, and `deleteResults` fields as optional types and document that they will be unset when `verboseResults` is false.
* Introduce separate `SummaryBulkWriteResult` and `VerboseBulkWriteResult` types. `VerboseBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above. `SummaryBulkWriteResult` MUST have all of the required fields defined on `BulkWriteResult` above except `insertResults`, `updateResults`, and `deleteResults`.

##### Individual Results

The `InsertOneResult`, `UpdateResult`, and `DeleteResult` classes are the same as or similar to those of the same names defined in the CRUD specification. Drivers MUST redefine these classes if their existing result classes deviate from the definitions in this specification (e.g. if they contain acknowledgement information). Drivers MAY reuse their existing types for these classes if they match the ones defined here exactly.

#### `BulkWriteException`

```

class BulkWriteException {
    // A top-level error that occurred when attempting to communicate with the server or execute the bulk write. This value may not be populated if the exception was thrown due to errors occurrring on individual writes.
    error: Optional<Error>

    // Write concern errors that occurred while executing the bulk write. This list may have multiple items if more than one round trip was required to execute the bulk write.
    writeConcernErrors: List<WriteConcernError>

    // Errors that occurred during the execution of individual write operations. This map will contain at most one entry if the bulk write was ordered.
    writeErrors: Map<Index, BulkWriteOperationError>

    // The results of any successful operations that were performed before the error was encountered.
    partialResult: Optional<BulkWriteResult>
}
```

##### Top-level errors

A top-level error is defined as any error that occurs during a bulk write that is not the result of an individual write operation failing or a write concern error. Possible top-level errors include, but are not limited to, network errors that occur when communicating with the server, command errors returned from the server, and client-side errors (e.g. an oversized insert document was provided). When a top-level error occurs, drivers MUST embed that error within a `BulkWriteException` as the `error` field and MUST include any results and/or non-top-level errors that have been observed so far in the `writeConcernErrors`, `writeErrors`, and `partialResults` fields.

If a retryable top-level error is encountered and the `bulkWrite` is retryable, drivers MUST perform a retry according to the retryable writes specification. Note that any bulk write that contains a `multi: true` operation (i.e. `UpdateMany` or `DeleteMany`) is not retryable. If the retry fails or if the bulk write or error was not retryable, drivers MUST halt execution for both ordered and unordered bulk writes and immediately throw a `BulkWriteException`.

##### Write concern errors

At most one write concern error may be returned per `bulkWrite` command response. If the driver observes a write concern error, it MUST record the error in the `writeConcernErrors` field and MUST continue executing the bulk write for both ordered and unordered bulk writes. If the `writeConcernErrors` field is not empty at the end of execution, drivers MUST throw the `BulkWriteException` and include any results and/or additional errors that were observed.

##### Individual write errors

Failures of individual write operations are reported in the cursor of results returned from the server. Drivers MUST iterate the this cursor fully and record all errors in the `writeErrors` map. If an individual write error is encountered during an ordered bulk write, drivers MUST record the error in `writeErrors` and immediately throw a `BulkWriteException`. Otherwise, drivers MUST continue iterating the cursor and execute any further `bulkWrite` batches.

### Command Batching

Drivers MUST accept an arbitrary number of operations as input to the `Client.bulkWrite` method. Because the server imposes restrictions on the size of write operations, this means that a single call to `Client.bulkWrite` may require multiple `bulkWrite` commands to be sent to the server. Drivers MUST split bulk writes into separate commands when the user's list of operations exceeds one of these maximums: `maxWriteBatchSize`, `maxBsonObjectSize`, or `maxMessageSizeBytes`. Each of these values can be retrieved from the selected server's `hello` command response.

#### Number of Writes

The `ops` array MUST NOT include more than `maxWriteBatchSize` operations.

#### Document Size

All entries within the `ops` array MUST be within `maxBsonObjectSize` bytes. Drivers MUST throw a `BulkWriteException` with a top-level client error if an operation exceeds this size.

#### Total Message Size

##### Encrypted bulk writes

When auto-encryption is enabled, drivers MUST NOT provide the `ops` and `nsInfo` fields as document sequences and MUST limit the size of the command according to the auto-encryption size limits defined here (isabeltodo link and update language in link).

##### Unencrypted bulk writes with document sequences

When `ops` and `nsInfo` are provided as document sequences, drivers MUST ensure that the combined size of these sequences does not exceed `maxMessageSizeBytes - 16,000`. `maxMessageSizeBytes` defines the maximum size for an entire `OP_MSG`, so 16KB is subtracted from `maxMessageSizeBytes` here to account for the bytes in the rest of the message.

##### Unencrypted bulk writes without document sequences

When `ops` and `nsInfo` are provided within the `bulkWrite` command document and auto-encryption is not enabled, drivers MUST ensure that the total size of the `bulkWrite` command document does not exceed `maxBsonObjectSize`.

### Pseudocode Implementation

The following pseudocode is a sample implementation of `MongoClient.bulkWrite`.

```
executeBulkWrite(client: MongoClient, models: List<NamespaceWriteModelPair>, options: BulkWriteOptions) {
    let exception = empty BulkWriteException

    while !models.isEmpty() {
        try {
            let bulkWrite = batchSplitAndBuildCommand(models, options)
            let (summaryInfo, resultsCursor, writeConcernError) = client.executeOperation(bulkWrite)

            if writeConcernError != null {
                exception.writeConcernErrors.add(writeConcernError)
            }

            for result in resultsCursor {
                if result.isSuccess() {
                    exception.partialResult.add(result)
                } else { // error
                    exception.writeErrors.add(result)
                    if options.ordered {
                        throw exception
                    }
                }
            }
        } catch error {
            exception.error = error
            throw exception
        }
    }

    if !exception.writeConcernErrors.isEmpty() || !exception.writeErrors.isEmpty() {
        throw exception
    } else {
        return exception.partialResult
    }
}
```

### Q&A

#### Why are we adding a new bulk write API rather than updating the `MongoCollection.bulkWrite` implementation?

The new `bulkWrite` command is only available in MongoDB 8.0+, so it cannot function as a drop-in replacement for the existing bulk write implementation that uses the `insert`, `update`, and `delete` commands. Additionally, because the new `bulkWrite` command allows operations against multiple collections and databases, `MongoClient` is a more appropriate place to expose its functionality.

#### Why can't drivers reuse existing bulk write types?

This specification introduces several types that are similar to existing types used in the legacy bulk write API. Although these types are similar now, they may diverge in the future with the introduction of new options and features to the `bulkWrite` command. Introducing new types also provides more clarity to users on the existing differences between the legacy and new bulk write APIs. For example, the `verboseResults` option is only available for `MongoClient.bulkWrite`.

#### Why are bulk write operation results returned in a cursor?

Returning results via a cursor rather than an array in the `bulkWrite` response allows full individual results and errors to be returned without the risk of the response exceeding the maximum BSON object size. Using a cursor also leaves open the opportunity to add `findAndModify` to the list of supported write operations in the future.

#### Why was the `verboseResults` option introduced, and why is its default `false`?

The `bulkWrite` command returns top-level summary result counts and, optionally, individual results for each operation. Compiling the individual results server-side and consuming these results driver-side is less performant than only recording the summary counts. We expect that most users are not interested in the individual results of their operations and that most users will rely on defaults, so `verboseResults` defaults to `false` to improve performance in the common case.

#### Why must all errors be embedded within a `BulkWriteException`?

An error may occur at any point during the execution of the `MongoClient.bulkWrite` method, including after some individual writes have already been executed. Embedding errors in a `BulkWriteException` gives users more information about what had happened during their bulk write prior to the error occurring.

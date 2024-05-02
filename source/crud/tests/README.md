# CRUD Tests

## Introduction

The YAML and JSON files in this directory tree are platform-independent tests that drivers can use to prove their
conformance to the CRUD spec.

Running these integration tests will require a running MongoDB server or cluster with server versions 2.6.0 or later.
Some tests have specific server version requirements as noted by the `runOn` section, if provided.

### Subdirectories for Test Formats

This document describes a legacy format for CRUD tests: legacy-v1, which dates back to the first version of the CRUD
specification. New CRUD tests should be written in the
[unified test format](../../unified-test-format/unified-test-format.md) and placed under `unified/`. Until such time
that all original tests have been ported to the unified test format, tests in each format will be grouped in their own
subdirectory:

- `v1/`: Legacy-v1 format tests
- `unified/`: Tests using the [unified test format](../../unified-test-format/unified-test-format.md)

Since some drivers may not have a unified test runner capable of executing tests in all two formats, segregating tests
in this manner will make it easier for drivers to sync and feed test files to different test runners.

### Legacy-v1 Test Format for Single Operations

*Note: this section pertains to test files in the "v1" directory.*

The test format above supports both multiple operations and APM expectations, and is consistent with the formats used by
other specifications. Previously, the CRUD spec tests used a simplified format that only allowed for executing a single
operation. Notable differences from the legacy-v2 format are as follows:

- Instead of a `tests[i].operations` array, a single operation was defined as a document in `tests[i].operation`. That
  document consisted of only the `name`, `arguments`, and an optional `object` field.
- Instead of `error` and `result` fields within each element in the `tests[i].operations` array, the single operation's
  error and result were defined under the `tests[i].outcome.error` and `tests[i].outcome.result` fields.
- Instead of a top-level `runOn` field, server requirements are denoted by separate top-level `minServerVersion`,
  `maxServerVersion`, and `serverless` fields. The minimum server version is an inclusive lower bound for running the
  test. The maximum server version is an exclusive upper bound for running the test. If a field is not present, it
  should be assumed that there is no corresponding bound on the required server version. The `serverless` requirement
  behaves the same as the `serverless` field of the
  [unified test format's runOnRequirement](../../unified-test-format/unified-test-format.md#runonrequirement).

The legacy-v1 format should not conflict with the newer, multi-operation format used by other specs (e.g. Transactions).
It is possible to create a unified test runner capable of executing both legacy formats (as some drivers do).

## Error Assertions for Bulk Write Operations

When asserting errors (e.g. `errorContains`, `errorCodeName`) for bulk write operations, the test harness should inspect
the `writeConcernError` and/or `writeErrors` properties of the bulk write exception. This may not be needed for
`errorContains` if a driver concatenates all write and write concern error messages into the bulk write exception's
top-level message.

## Test Runner Implementation

This section provides guidance for implementing a test runner for legacy-v1 tests. See the
[unified test format spec](../../unified-test-format/unified-test-format.md) for how to run tests under `unified/`.

Before running the tests:

- Create a global MongoClient (`globalMongoClient`) and connect to the server. This client will be used for executing
  meta operations, such as checking server versions and preparing data fixtures.

For each test file:

- Using `globalMongoClient`, check that the current server version satisfies one of the configurations provided in the
  top-level `runOn` field in the test file (if applicable). If the requirements are not satisfied, the test file should
  be skipped.
- Determine the collection and database under test, utilizing the top-level `collection_name` and/or `database_name`
  fields if present.
- For each element in the `tests` array:
  - Using `globalMongoClient`, ensure that the collection and/or database under test is in a "clean" state, as needed.
    This may be accomplished by dropping the database; however, drivers may also decide to drop individual collections
    as needed (this may be more performant).
  - If the top-level `data` field is present in the test file, insert the corresponding data into the collection under
    test using `globalMongoClient`.
  - If the the `failPoint` field is present, use `globalMongoClient` to configure the fail point on the primary server.
    See [Server Fail Point](../../transactions/tests#server-fail-point) in the Transactions spec test documentation for
    more information.
  - Create a local MongoClient (`localMongoClient`) and connect to the server. This client will be used for executing
    the test case.
    - If `clientOptions` is present, those options should be used to create the client. Drivers MAY merge these options
      atop existing defaults (e.g. reduced `serverSelectionTimeoutMS` value for faster test failures) at their own
      discretion.
  - Activate command monitoring for `localMongoClient` and begin capturing events. Note that some events may need to be
    filtered out if the driver uses global listeners or reports internal commands (e.g. `hello`, legacy hello,
    authentication).
  - For each element in the `operations` array:
    - Using `localMongoClient`, select the appropriate `object` to execute the operation. Default to the collection
      under test if this field is not present.
      - If `collectionOptions` is present, those options should be used to construct the collection object.
    - Given the `name` and `arguments`, execute the operation on the object under test. Capture the result of the
      operation, if any, and observe whether an error occurred. If an error is encountered that includes a result (e.g.
      BulkWriteException), extract the result object.
    - If `error` is present and true, assert that the operation encountered an error. Otherwise, assert that no error
      was encountered.
    - if `result` is present, assert that it matches the operation's result.
  - Deactivate command monitoring for `localMongoClient`.
  - If the `expectations` array is present, assert that the sequence of emitted CommandStartedEvents from executing the
    operation(s) matches the sequence of `command_started_event` objects in the `expectations` array.
  - If the `outcome` field is present, assert the contents of the specified collection using `globalMongoClient`. Note
    the server does not guarantee that documents returned by a find command will be in inserted order. This find MUST
    sort by `{_id:1}`.

### Evaluating Matches

The expected values for results (e.g. `result` for an operation operation, `command_started_event.command`, elements in
`outcome.data`) are written in [Extended JSON](../../extended-json.rst). Drivers may adopt any of the following
approaches to comparisons, as long as they are consistent:

- Convert `actual` to Extended JSON and compare to `expected`
- Convert `expected` and `actual` to BSON, and compare them
- Convert `expected` and `actual` to native representations, and compare them

#### Extra Fields in Actual Documents

When comparing `actual` and `expected` *documents*, drivers should permit `actual` documents to contain additional
fields not present in `expected`. For example, the following documents match:

- `expected` is `{ "x": 1 }`
- `actual` is `{ "_id": { "$oid" : "000000000000000000000001" }, "x": 1 }`

In this sense, `expected` may be a subset of `actual`. It may also be helpful to think of `expected` as a form of query
criteria. The intention behind this rule is that it is not always feasible for the test to express all fields in the
expected document(s) (e.g. session and cluster time information in a `command_started_event.command` document).

This rule for allowing extra fields in `actual` only applies for values that correspond to a document. For instance, an
actual result of `[1, 2, 3, 4]` for a `distinct` operation would not match an expected result of `[1, 2, 3]`. Likewise
with the `find` operation, this rule would only apply when matching documents *within* the expected result array and
actual cursor.

Note that in the case of result objects for some CRUD operations, `expected` may condition additional, optional fields
(see: [Optional Fields in Expected Result Objects](#optional-fields-in-expected-result-objects)).

#### Fields that must NOT be present in Actual Documents

Some command-started events in `expectations` include `null` values for optional fields such as `allowDiskUse`. Tests
MUST assert that the actual command **omits** any field that has a `null` value in the expected command.

#### Optional Fields in Expected Result Objects

Some `expected` results may include fields that are optional in the CRUD specification, such as `insertedId` (for
InsertOneResult), `insertedIds` (for InsertManyResult), and `upsertedCount` (for UpdateResult). Drivers that do not
implement these fields should ignore them when comparing `actual` with `expected`.

## Prose Tests

The following tests have not yet been automated, but MUST still be tested.

### 1. WriteConcernError.details exposes writeConcernError.errInfo

Test that `writeConcernError.errInfo` in a command response is propagated as `WriteConcernError.details` (or equivalent)
in the driver.

Using a 4.0+ server, set the following failpoint:

```javascript
{
  "configureFailPoint": "failCommand",
  "data": {
    "failCommands": ["insert"],
    "writeConcernError": {
      "code": 100,
      "codeName": "UnsatisfiableWriteConcern",
      "errmsg": "Not enough data-bearing nodes",
      "errInfo": {
        "writeConcern": {
          "w": 2,
          "wtimeout": 0,
          "provenance": "clientSupplied"
        }
      }
    }
  },
  "mode": { "times": 1 }
}
```

Then, perform an insert operation and assert that a WriteConcernError occurs and that its `details` property is both
accessible and matches the `errInfo` object from the failpoint.

### 2. WriteError.details exposes writeErrors\[\].errInfo

Test that `writeErrors[].errInfo` in a command response is propagated as `WriteError.details` (or equivalent) in the
driver.

Using a 5.0+ server, create a collection with
[document validation](https://www.mongodb.com/docs/manual/core/schema-validation/) like so:

```javascript
{
  "create": "test",
  "validator": {
    "x": { $type: "string" }
  }
}
```

Enable [command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) to observe
CommandSucceededEvents. Then, insert an invalid document (e.g. `{x: 1}`) and assert that a WriteError occurs, that its
code is `121` (i.e. DocumentValidationFailure), and that its `details` property is accessible. Additionally, assert that
a CommandSucceededEvent was observed and that the `writeErrors[0].errInfo` field in the response document matches the
WriteError's `details` property.

### 3. `MongoClient.bulkWrite` batch splits a `writeModels` input with greater than `maxWriteBatchSize` operations

Test that `MongoClient.bulkWrite` properly handles `writeModels` inputs containing a number of writes greater than
`maxWriteBatchSize`.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxWriteBatchSize` value contained in the
response. Then, construct the following write model (referred to as `model`):

```json
InsertOne: {
  "namespace": "db.coll",
  "document": { "a": "b" }
}
```

Construct a list of write models (referred to as `models`) with `model` repeated `maxWriteBatchSize + 1` times.
Execute `bulkWrite` on `client` with `models`. Assert that the bulk write succeeds and returns a `BulkWriteResult`
with an `insertedCount` value of `maxWriteBatchSize + 1`.

Assert that two CommandStartedEvents (referred to as `firstEvent` and `secondEvent`) were observed for the `bulkWrite` command.
Assert that the length of `firstEvent.command.ops` is `maxWriteBatchSize`. Assert that the length of `secondEvent.command.ops`
is 1. If the driver exposes `operationId`s in its CommandStartedEvents, assert that `firstEvent.operationId` is equal to
`secondEvent.operationId`.

### 4. `MongoClient.bulkWrite` batch splits when an `ops` payload exceeds `maxMessageSizeBytes`

Test that `MongoClient.bulkWrite` properly handles a `writeModels` input which constructs an `ops` array larger than
`maxMessageSizeBytes`.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the following values from the response:
`maxBsonObjectSize` and `maxMessageSizeBytes`. Then, construct the following document (referred to as `document`):

```json
{
  "a": "b".repeat(maxBsonObjectSize - 500)
}
```

Construct the following write model (referred to as `model`):

```json
InsertOne: {
  "namespace": "db.coll",
  "document": document
}
```

Use the following calculation to determine the number of inserts that should be provided to `MongoClient.bulkWrite`:
`maxMessageSizeBytes / maxBsonObjectSize + 1` (referred to as `numModels`). This number ensures that the inserts
provided to `MongoClient.bulkWrite` will require multiple `bulkWrite` commands to be sent to the server.

Construct as list of write models (referred to as `models`) with `model` repeated `numModels` times. Then execute
`bulkWrite` on `client` with `models`. Assert that the bulk write succeeds and returns a `BulkWriteResult` with
an `insertedCount` value of `numModels`.

Assert that two CommandStartedEvents (referred to as `firstEvent` and `secondEvent`) were observed. Assert that the
length of `firstEvent.command.ops` is `numModels - 1`. Assert that the length of `secondEvent.command.ops` is 1. If
the driver exposes `operationId`s in its CommandStartedEvents, assert that `firstEvent.operationId` is equal to
`secondEvent.operationId`.

### 5. `MongoClient.bulkWrite` collects `WriteConcernError`s across batches

Test that `MongoClient.bulkWrite` properly collects and reports `writeConcernError`s returned in separate batches.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with `retryWrites: false` configured and
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxWriteBatchSize` value contained
in the response. Then, configure the following fail point with `client`:

```json
{
  "configureFailPoint": "failCommand",
  "mode": { "times": 2 },
  "data": {
    "failCommands": ["bulkWrite"],
    "writeConcernError": {
      "code": 91,
      "errmsg": "Replication is being shut down"
    }
  }
}
```

Construct the following write model (referred to as `model`):

```json
InsertOne: {
  "namespace": "db.coll",
  "document": { "a": "b" }
}
```

Construct a list of write models (referred to as `models`) with `model` repeated `maxWriteBatchSize + 1` times.
Execute `bulkWrite` on `client` with `models`. Assert that the bulk write fails and returns a `BulkWriteError`
(referred to as `error`).

Assert that `error.writeConcernErrors` has a length of 2.

Assert that `error.partialResult` is populated. Assert that `error.partialResult.insertedCount` is equal to
`maxWriteBatchSize + 1`.

Assert that two CommandStartedEvents were observed for the `bulkWrite` command.

### 6. `MongoClient.bulkWrite` handles individual `WriteError`s across batches

Test that `MongoClient.bulkWrite` handles individual write errors across batches for ordered and unordered bulk
writes.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxWriteBatchSize` value contained in the
response.

Construct a `MongoCollection` (referred to as `collection`) with the namespace "db.coll" (referred to as `namespace`).
Drop `collection`. Then, construct the following document (referred to as `document`):

```json
{
  "_id": 1
}
```

Insert `document` into `collection`.

Create the following write model (referred to as `model`):

```json
InsertOne {
  "namespace": namespace,
  "document": document
}
```

Construct a list of write models (referred to as `models`) with `model` repeated `maxWriteBatchSize + 1` times.

#### Unordered

Test that an unordered bulk write collects `WriteError`s across batches.

Execute `bulkWrite` on `client` with `models` and `ordered` set to false. Assert that the bulk write fails and returns
a `BulkWriteError` (referred to as `unorderedError`).

Assert that `unorderedError.writeErrors` has a length of `maxWriteBatchSize + 1`.

Assert that two CommandStartedEvents were observed for the `bulkWrite` command.

#### Ordered

Test that an ordered bulk write does not execute further batches when a `WriteError` occurs.

Execute `bulkWrite` on `client` with `models` and `ordered` set to true. Assert that the bulk write fails and returns
a `BulkWriteError` (referred to as `orderedError`).

Assert that `orderedError.writeErrors` has a length of 1.

Assert that one CommandStartedEvent was observed for the `bulkWrite` command.

### 7. `MongoClient.bulkWrite` handles a cursor requiring a `getMore`

Test that `MongoClient.bulkWrite` properly iterates the results cursor when `getMore` is required.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxBsonObjectSize` value from the
response.

Construct a `MongoCollection` (referred to as `collection`) with the namespace "db.coll" (referred to as `namespace`).
Drop `collection`. Then create the following list of write models (referred to as `models`):

```json
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "a".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "b".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
```

Execute `bulkWrite` on `client` with `models` and `verboseResults` set to true. Assert that the bulk write succeeds and
returns a `BulkWriteResult` (referred to as `result`).

Assert that `result.upsertedCount` is equal to 2.

Assert that the length of `result.updateResults` is equal to 2.

Assert that a CommandStartedEvent was observed for the `getMore` command.

### 8. `MongoClient.bulkWrite` handles a cursor requiring `getMore` within a transaction

Test that `MongoClient.bulkWrite` executed within a transaction properly iterates the results cursor when `getMore` is
required.

This test must only be run on 8.0+ servers. This test must not be run against standalone servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxBsonObjectSize` value from the
response.

Construct a `MongoCollection` (referred to as `collection`) with the namespace "db.coll" (referred to as `namespace`).
Drop `collection`.

Start a session on `client` (referred to as `session`). Start a transaction on `session`.

Create the following list of write models (referred to as `models`):

```json
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "a".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "b".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
```

Execute `bulkWrite` on `client` with `models`, `session`, and `verboseResults` set to true. Assert that the bulk write
succeeds and returns a `BulkWriteResult` (referred to as `result`).

Assert that `result.upsertedCount` is equal to 2.

Assert that the length of `result.updateResults` is equal to 2.

Assert that a CommandStartedEvent was observed for the `getMore` command.

### 9. `MongoClient.bulkWrite` handles a `getMore` error

Test that `MongoClient.bulkWrite` properly handles a failure that occurs when attempting a `getMore`.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the `maxBsonObjectSize` value from the
response. Then, configure the following fail point with `client`:

```json
{
  "configureFailPoint": "failCommand",
  "mode": { "times": 1 },
  "data": {
    "failCommands": ["getMore"],
    "errorCode": 8
  }
}
```

Construct a `MongoCollection` (referred to as `collection`) with the namespace "db.coll" (referred to as `namespace`).
Drop `collection`. Then create the following list of write models (referred to as `models`):

```json
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "a".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
UpdateOne {
  "namespace": namespace,
  "filter": { "_id": "b".repeat(maxBsonObjectSize / 2) },
  "update": { "$set": { "x": 1 } },
  "upsert": true
},
```

Execute `bulkWrite` on `client` with `models` and `verboseResults` set to true. Assert that the bulk write fails and returns
a `BulkWriteError` (referred to as `bulkWriteError`).

Assert that `bulkWriteError.error` is populated with an error (referred to as `topLevelError`). Assert that
`topLevelError.errorCode` is equal to 8.

Assert that `bulkWriteError.partialResult` is populated with a result (referred to as `partialResult`). Assert that
`partialResult.upsertedCount` is equal to 2. Assert that the length of `partialResult.updateResults` is equal to 1.

Assert that a CommandStartedEvent was observed for the `getMore` command.

Assert that a CommandStartedEvent was observed for the `killCursors` command.

### 10. `MongoClient.bulkWrite` returns error for unacknowledged too-large insert

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`).

Perform a `hello` command using `client` and record the following values from the response: `maxBsonObjectSize`.

Then, construct the following document (referred to as `document`):

```json
{
  "a": "b".repeat(maxBsonObjectSize)
}
```

#### With insert

Construct the following write model (referred to as `model`):

```json
InsertOne: {
  "namespace": "db.coll",
  "document": document
}
```

Construct as list of write models (referred to as `models`) with the one `model`.

Call `MongoClient.bulkWrite` with `models` and `BulkWriteOptions.writeConcern` set to an unacknowledged write concern.

Expect a client-side error due the size.

#### With replace

Construct the following write model (referred to as `model`):

```json
ReplaceOne: {
  "namespace": "db.coll",
  "filter": {},
  "replacement": document
}
```

Construct as list of write models (referred to as `models`) with the one `model`.

Call `MongoClient.bulkWrite` with `models` and `BulkWriteOptions.writeConcern` set to an unacknowledged write concern.

Expect a client-side error due the size.

### 11. `MongoClient.bulkWrite` batch splits when the addition of a new namespace exceeds the maximum message size

Test that `MongoClient.bulkWrite` batch splits a bulk write when the addition of a new namespace to `nsInfo`
causes the size of the message to exceed `maxMessageSizeBytes - 1000`.

This test must only be run on 8.0+ servers.

Repeat the following setup for each test case:

### Setup

Construct a `MongoClient` (referred to as `client`) with
[command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) enabled to observe
CommandStartedEvents. Perform a `hello` command using `client` and record the following values from the response:
`maxBsonObjectSize` and `maxMessageSizeBytes`.

Calculate the following values:

```
opsBytes = maxMessageSizeBytes - 1122
numModels = opsBytes / maxBsonObjectSize
remainderBytes = opsBytes % maxBsonObjectSize
```

Construct the following write model (referred to as `firstModel`):

```json
InsertOne {
  "namespace": "db.coll",
  "document": { "a": "b".repeat(maxBsonObjectSize - 57) }
}
```

Create a list of write models (referred to as `models`) with `firstModel` repeated `numModels` times.

If `remainderBytes` is greater than or equal to 217, add 1 to `numModels` and append the following write model
to `models`:

```json
InsertOne {
  "namespace": "db.coll",
  "document": { "a": "b".repeat(remainderBytes - 57) }
}
```

Then perform the following two tests:

#### Case 1: No batch-splitting required

Create the following write model (referred to as `sameNamespaceModel`):

```json
InsertOne {
  "namespace": "db.coll",
  "document": { "a": "b" }
}
```

Append `sameNamespaceModel` to `models`.

Execute `bulkWrite` on `client` with `models`. Assert that the bulk write succeeds and returns a `BulkWriteResult`
(referred to as `result`).

Assert that `result.insertedCount` is equal to `numModels + 1`.

Assert that one CommandStartedEvent was observed for the `bulkWrite` command (referred to as `event`).

Assert that the length of `event.command.ops` is `numModels + 1`. Assert that the length of `event.command.nsInfo`
is 1. Assert that the namespace contained in `event.command.nsInfo` is "db.coll".

#### Case 2: Batch-splitting required

Construct the following namespace (referred to as `namespace`):

```
"db." + "c".repeat(200)
```

Create the following write model (referred to as `newNamespaceModel`):

```json
InsertOne {
  "namespace": namespace,
  "document": { "a": "b" }
}
```

Append `newNamespaceModel` to `models`.

Execute `bulkWrite` on `client` with `models`. Assert that the bulk write succeeds and returns a `BulkWriteResult`
(referred to as `result`).

Assert that `result.insertedCount` is equal to `numModels + 1`.

Assert that two CommandStartedEvents were observed for the `bulkWrite` command (referred to as `firstEvent` and
`secondEvent`).

Assert that the length of `firstEvent.command.ops` is equal to `numModels`. Assert that the length of
`firstEvent.command.nsInfo` is equal to 1. Assert that the namespace contained in `firstEvent.command.nsInfo` is
"db.coll".

Assert that the length of `secondEvent.command.ops` is equal to 1. Assert that the length of
`secondEvent.command.nsInfo` is equal to 1. Assert that the namespace contained in `secondEvent.command.nsInfo` is
`namespace`.

#### Details on size calculations

This information is not needed to implement this prose test, but is documented for future reference. This test is
designed to work if `maxBsonObjectSize` or `maxMessageSizeBytes` changes, but will need to be updated if a required
field is added to the `bulkWrite` command or the `insert` operation document, or if the overhead `OP_MSG` allowance
is changed in the bulk write specification.

The command document for the `bulkWrite` has the following structure and size:

```json
{
  "bulkWrite": 1,
  "errorsOnly": true,
  "ordered": true
}

Size: 43 bytes
```

Each write model will create an `ops` document with the following structure and size:

```json
{
  "insert": <0 | 1>,
  "document": {
    "_id": <object ID>,
    "a": <string>
  }
}

Size: 57 bytes + <number of characters in string>
```

The `ops` document for both `newNamespaceModel` and `sameNamespaceModel` has a string with one character, so
it is a total of 58 bytes.

The models using the "db.coll" namespace will create one `nsInfo` document with the following structure and size:

```json
{
  "ns": "db.coll"
}

Size: 21 bytes
```

`newNamespaceModel` will create an `nsInfo` document with the following structure and size:

```json
{
  "ns": "db.<c repeated 200 times>"
}

Size: 217 bytes
```

We need to fill up the rest of the message with bytes such that another `ops` document will fit, but another
`nsInfo` entry will not. The following calculations are used:

```
# 1000 is the OP_MSG overhead required in the spec
maxBulkWriteBytes = maxMessageSizeBytes - 1000

# bulkWrite command + first namespace entry
existingMessageBytes = 43 + 21

# Space to fit the last model's ops entry
lastModelBytes = 58

remainingBulkWriteBytes = maxBulkWriteBytes - existingMessageBytes - lastModelBytes

# With the actual numbers plugged in
remainingBulkWriteBytes = maxMessageSizeBytes - 1122
```

### 12. `MongoClient.bulkWrite` returns an error if no operations can be added to `ops`

Test that `MongoClient.bulkWrite` returns an error if an operation provided exceeds `maxMessageSizeBytes` such
that no operations would be sent.

This test must only be run on 8.0+ servers. This test may be skipped by drivers that are not able to construct
arbitrarily large documents.

Construct a `MongoClient` (referred to as `client`). Perform a `hello` command using `client` and record the
`maxMessageSizeBytes` value contained in the response.

#### Case 1: `document` too large

Construct the following write model (referred to as `largeDocumentModel`):

```json
InsertOne {
  "namespace": "db.coll",
  "document": { "a": "b".repeat(maxMessageSizeBytes) }
}
```

Execute `bulkWrite` on `client` with `largeDocumentModel`. Assert that an error (referred to as `error`) is returned.
Assert that `error` is a client error.

#### Case 2: `namespace` too large

Construct the following namespace (referred to as `namespace`):

```
"db." + "c".repeat(maxMessageSizeBytes)
```

Construct the following write model (referred to as `largeNamespaceModel`):

```json
InsertOne {
  "namespace": namespace,
  "document": { "a": "b" }
}
```

Execute `bulkWrite` on `client` with `largeNamespaceModel`. Assert that an error (referred to as `error`) is returned.
Assert that `error` is a client error.

### 13. `MongoClient.bulkWrite` returns an error if auto-encryption is configured

This test is expected to be removed when
[DRIVERS-2888](https://jira.mongodb.org/browse/DRIVERS-2888) is resolved.

Test that `MongoClient.bulkWrite` returns an error if the client has auto-encryption configured.

This test must only be run on 8.0+ servers.

Construct a `MongoClient` (referred to as `client`) configured with the following `AutoEncryptionOpts`:

```json
AutoEncryptionOpts {
  "keyVaultNamespace": "db.coll",
  "kmsProviders": {
    "aws": {
      "accessKeyId": "foo",
      "secretAccessKey": "bar"
    }
  }
}
```

Construct the following write model (referred to as `model`):

```json
InsertOne {
  "namespace": "db.coll",
  "document": { "a": "b" }
}
```

Execute `bulkWrite` on `client` with `model`. Assert that an error (referred to as `error`) is returned.
Assert that `error` is a client error containing the message: "bulkWrite does not currently support automatic
encryption".

# Legacy Transactions Tests Format

______________________________________________________________________

## Introduction

This test format is no longer used by the transactions spec but may still be referenced by other specs (e.g. CSFLE) and
is preserved for historical record.

## Server Fail Point

### failCommand

Some tests depend on a server fail point, expressed in the `failPoint` field. For example the `failCommand` fail point
allows the client to force the server to return an error. Keep in mind that the fail point only triggers for commands
listed in the "failCommands" field. See [SERVER-35004](https://jira.mongodb.org/browse/SERVER-35004) and
[SERVER-35083](https://jira.mongodb.org/browse/SERVER-35083) for more information.

The `failCommand` fail point may be configured like so:

```javascript
    db.adminCommand({
        configureFailPoint: "failCommand",
        mode: <string|document>,
        data: {
          failCommands: ["commandName", "commandName2"],
          closeConnection: <true|false>,
          errorCode: <Number>,
          writeConcernError: <document>,
          appName: <string>,
          blockConnection: <true|false>,
          blockTimeMS: <Number>,
        }
    });
```

`mode` is a generic fail point option and may be assigned a string or document value. The string values `"alwaysOn"` and
`"off"` may be used to enable or disable the fail point, respectively. A document may be used to specify either `times`
or `skip`, which are mutually exclusive:

- `{ times: <integer> }` may be used to limit the number of times the fail point may trigger before transitioning to
    `"off"`.
- `{ skip: <integer> }` may be used to defer the first trigger of a fail point, after which it will transition to
    `"alwaysOn"`.

The `data` option is a document that may be used to specify options that control the fail point's behavior.
`failCommand` supports the following `data` options, which may be combined if desired:

- `failCommands`: Required, the list of command names to fail.
- `closeConnection`: Boolean option, which defaults to `false`. If `true`, the command will not be executed, the
    connection will be closed, and the client will see a network error.
- `errorCode`: Integer option, which is unset by default. If set, the command will not be executed and the specified
    command error code will be returned as a command error.
- `appName`: A string to filter which MongoClient should be affected by the failpoint.
    [New in mongod 4.4.0-rc2](https://jira.mongodb.org/browse/SERVER-47195).
- `blockConnection`: Whether the server should block the affected commands. Default false.
- `blockTimeMS`: The number of milliseconds the affect commands should be blocked for. Required when blockConnection is
    true. [New in mongod 4.3.4](https://jira.mongodb.org/browse/SERVER-41070).

## Test Format

Each YAML file has the following keys:

- `runOn` (optional): An array of server version and/or topology requirements for which the tests can be run. If the
    test environment satisfies one or more of these requirements, the tests may be executed; otherwise, this file should
    be skipped. If this field is omitted, the tests can be assumed to have no particular requirements and should be
    executed. Each element will have some or all of the following fields:
    - `minServerVersion` (optional): The minimum server version (inclusive) required to successfully run the tests. If
        this field is omitted, it should be assumed that there is no lower bound on the required server version.

    - `maxServerVersion` (optional): The maximum server version (inclusive) against which the tests can be run
        successfully. If this field is omitted, it should be assumed that there is no upper bound on the required server
        version.

    - `topology` (optional): An array of server topologies against which the tests can be run successfully. Valid
        topologies are "single", "replicaset", "sharded", and "load-balanced". If this field is omitted, the default is
        all topologies (i.e. `["single", "replicaset", "sharded", "load-balanced"]`).

    - `serverless`: (optional): Whether or not the test should be run on Atlas Serverless instances. Valid values are
        "require", "forbid", and "allow". If "require", the test MUST only be run on Atlas Serverless instances. If
        "forbid", the test MUST NOT be run on Atlas Serverless instances. If omitted or "allow", this option has no
        effect.

        The test runner MUST be informed whether or not Atlas Serverless is being used in order to determine if this
        requirement is met (e.g. through an environment variable or configuration option).

        Note: the Atlas Serverless proxy imitates mongos, so the test runner is not capable of determining if Atlas
        Serverless is in use by issuing commands such as `buildInfo` or `hello`. Furthermore, connections to Atlas
        Serverless use a load balancer, so the topology will appear as "load-balanced".
- `database_name` and `collection_name`: The database and collection to use for testing.
- `data`: The data that should exist in the collection under test before each test run.
- `tests`: An array of tests that are to be run independently of each other. Each test will have some or all of the
    following fields:
    - `description`: The name of the test.

    - `skipReason`: Optional, string describing why this test should be skipped.

    - `useMultipleMongoses` (optional): If `true`, and the topology type is `Sharded`, the MongoClient for this test
        should be initialized with multiple mongos seed addresses. If `false` or omitted, only a single mongos address
        should be specified.

        If `true`, the topology type is `LoadBalanced`, and Atlas Serverless is not being used, the MongoClient for this
        test should be initialized with the URI of the load balancer fronting multiple servers. If `false` or omitted, the
        MongoClient for this test should be initialized with the URI of the load balancer fronting a single server.

        `useMultipleMongoses` only affects `Sharded` and `LoadBalanced` topologies (excluding Atlas Serverless).

    - `clientOptions`: Optional, parameters to pass to MongoClient().

    - `failPoint`: Optional, a server failpoint to enable expressed as the configureFailPoint command to run on the admin
        database. This option and `useMultipleMongoses: true` are mutually exclusive.

    - `sessionOptions`: Optional, map of session names (e.g. "session0") to parameters to pass to
        MongoClient.startSession() when creating that session.

    - `operations`: Array of documents, each describing an operation to be executed. Each document has the following
        fields:

        - `name`: The name of the operation on `object`.
        - `object`: The name of the object to perform the operation on. Can be "database", "collection", "session0",
            "session1", or "testRunner". See the "targetedFailPoint" operation in
            [Special Test Operations](#special-test-operations).
        - `collectionOptions`: Optional, parameters to pass to the Collection() used for this operation.
        - `databaseOptions`: Optional, parameters to pass to the Database() used for this operation.
        - `command_name`: Present only when `name` is "runCommand". The name of the command to run. Required for languages
            that are unable preserve the order keys in the "command" argument when parsing JSON/YAML.
        - `arguments`: Optional, the names and values of arguments.
        - `error`: Optional. If true, the test should expect an error or exception. This could be a server-generated or a
            driver-generated error.
        - `result`: The return value from the operation, if any. This field may be a single document or an array of
            documents in the case of a multi-document read. If the operation is expected to return an error, the `result` is
            a single document that has one or more of the following fields:
            - `errorContains`: A substring of the expected error message.
            - `errorCodeName`: The expected "codeName" field in the server error response.
            - `errorLabelsContain`: A list of error label strings that the error is expected to have.
            - `errorLabelsOmit`: A list of error label strings that the error is expected not to have.

    - `expectations`: Optional list of command-started events.

    - `outcome`: Document describing the return value and/or expected state of the collection after the operation is
        executed. Contains the following fields:

        - `collection`:
            - `data`: The data that should exist in the collection after the operations have run, sorted by "\_id".

## Use as Integration Tests

Run a MongoDB replica set with a primary, a secondary, and an arbiter, **server version 4.0.0 or later**. (Including a
secondary ensures that server selection in a transaction works properly. Including an arbiter helps ensure that no new
bugs have been introduced related to arbiters.)

A driver that implements support for sharded transactions MUST also run these tests against a MongoDB sharded cluster
with multiple mongoses and **server version 4.2 or later**. Some tests require initializing the MongoClient with
multiple mongos seeds to ensures that mongos transaction pinning and the recoveryToken works properly.

Load each YAML (or JSON) file using a Canonical Extended JSON parser.

Then for each element in `tests`:

1. If the `skipReason` field is present, skip this test completely.

2. Create a MongoClient and call `client.admin.runCommand({killAllSessions: []})` to clean up any open transactions
    from previous test failures. Ignore a command failure with error code 11601 ("Interrupted") to work around
    [SERVER-38335](https://jira.mongodb.org/browse/SERVER-38335).

    - Running `killAllSessions` cleans up any open transactions from a previously failed test to prevent the current
        test from blocking. It is sufficient to run this command once before starting the test suite and once after each
        failed test.
    - When testing against a sharded cluster run this command on ALL mongoses.

3. Create a collection object from the MongoClient, using the `database_name` and `collection_name` fields of the YAML
    file.

4. Drop the test collection, using writeConcern "majority".

5. Execute the "create" command to recreate the collection, using writeConcern "majority". (Creating the collection
    inside a transaction is prohibited, so create it explicitly.)

6. If the YAML file contains a `data` array, insert the documents in `data` into the test collection, using
    writeConcern "majority".

7. When testing against a sharded cluster run a `distinct` command on the newly created collection on all mongoses. For
    an explanation see,
    [Why do tests that run distinct sometimes fail with StaleDbVersion?](#why-do-tests-that-run-distinct-sometimes-fail-with-staledbversion)

8. If `failPoint` is specified, its value is a configureFailPoint command. Run the command on the admin database to
    enable the fail point.

9. Create a **new** MongoClient `client`, with Command Monitoring listeners enabled. (Using a new MongoClient for each
    test ensures a fresh session pool that hasn't executed any transactions previously, so the tests can assert actual
    txnNumbers, starting from 1.) Pass this test's `clientOptions` if present.

    - When testing against a sharded cluster and `useMultipleMongoses` is `true` the client MUST be created with
        multiple (valid) mongos seed addresses.

10. Call `client.startSession` twice to create ClientSession objects `session0` and `session1`, using the test's
    "sessionOptions" if they are present. Save their lsids so they are available after calling `endSession`, see
    [Logical Session Id](#logical-session-id).

11. For each element in `operations`:

    - If the operation `name` is a special test operation type, execute it and go to the next operation, otherwise
        proceed to the next step.

    - Enter a "try" block or your programming language's closest equivalent.

    - Create a Database object from the MongoClient, using the `database_name` field at the top level of the test file.

    - Create a Collection object from the Database, using the `collection_name` field at the top level of the test file.
        If `collectionOptions` or `databaseOptions` is present, create the Collection or Database object with the
        provided options, respectively. Otherwise create the object with the default options.

    - Execute the named method on the provided `object`, passing the arguments listed. Pass `session0` or `session1` to
        the method, depending on which session's name is in the arguments list. If `arguments` contains no "session",
        pass no explicit session to the method.

    - If the driver throws an exception / returns an error while executing this series of operations, store the error
        message and server error code.

    - If the operation's `error` field is `true`, verify that the method threw an exception or returned an error.

    - If the result document has an "errorContains" field, verify that the method threw an exception or returned an
        error, and that the value of the "errorContains" field matches the error string. "errorContains" is a substring
        (case-insensitive) of the actual error message.

        If the result document has an "errorCodeName" field, verify that the method threw a command failed exception or
        returned an error, and that the value of the "errorCodeName" field matches the "codeName" in the server error
        response.

        If the result document has an "errorLabelsContain" field, verify that the method threw an exception or returned an
        error. Verify that all of the error labels in "errorLabelsContain" are present in the error or exception using
        the `hasErrorLabel` method.

        If the result document has an "errorLabelsOmit" field, verify that the method threw an exception or returned an
        error. Verify that none of the error labels in "errorLabelsOmit" are present in the error or exception using the
        `hasErrorLabel` method.

    - If the operation returns a raw command response, eg from `runCommand`, then compare only the fields present in the
        expected result document. Otherwise, compare the method's return value to `result` using the same logic as the
        CRUD Spec Tests runner.

12. Call `session0.endSession()` and `session1.endSession`.

13. If the test includes a list of command-started events in `expectations`, compare them to the actual command-started
    events using the same logic as the
    [legacy Command Monitoring Spec Tests runner](../../command-logging-and-monitoring/tests/README.md), plus the
    rules in the Command-Started Events instructions below.

14. If `failPoint` is specified, disable the fail point to avoid spurious failures in subsequent tests. The fail point
    may be disabled like so:

    ```javascript
        db.adminCommand({
            configureFailPoint: "<fail point name>",
            mode: "off"
        });
    ```

15. For each element in `outcome`:

    - If `name` is "collection", verify that the test collection contains exactly the documents in the `data` array.
        Ensure this find reads the latest data by using **primary read preference** with **local read concern** even
        when the MongoClient is configured with another read preference or read concern. Note the server does not
        guarantee that documents returned by a find command will be in inserted order. This find MUST sort by `{_id:1}`.

### Special Test Operations

Certain operations that appear in the "operations" array do not correspond to API methods but instead represent special
test operations. Such operations are defined on the "testRunner" object and documented here:

#### targetedFailPoint

The "targetedFailPoint" operation instructs the test runner to configure a fail point on a specific mongos. The mongos
to run the `configureFailPoint` is determined by the "session" argument (either "session0" or "session1"). The session
must already be pinned to a mongos server. The "failPoint" argument is the `configureFailPoint` command to run.

If a test uses `targetedFailPoint`, disable the fail point after running all `operations` to avoid spurious failures in
subsequent tests. The fail point may be disabled like so:

```javascript
  db.adminCommand({
      configureFailPoint: "<fail point name>",
      mode: "off"
  });
```

Here is an example which instructs the test runner to enable the failCommand fail point on the mongos server which
"session0" is pinned to:

```yaml
# Enable the fail point only on the Mongos that session0 is pinned to.
- name: targetedFailPoint
  object: testRunner
  arguments:
    session: session0
    failPoint:
      configureFailPoint: failCommand
      mode: { times: 1 }
      data:
        failCommands: ["commitTransaction"]
        closeConnection: true
```

Tests that use the "targetedFailPoint" operation do not include `configureFailPoint` commands in their command
expectations. Drivers MUST ensure that `configureFailPoint` commands do not appear in the list of logged commands,
either by manually filtering it from the list of observed commands or by using a different MongoClient to execute
`configureFailPoint`.

#### assertSessionTransactionState

The "assertSessionTransactionState" operation instructs the test runner to assert that the transaction state of the
given session is equal to the specified value. The possible values are as follows: `none`, `starting`, `in_progress`,
`committed`, `aborted`:

```yaml
- name: assertSessionTransactionState
  object: testRunner
  arguments:
    session: session0
    state: in_progress
```

#### assertSessionPinned

The "assertSessionPinned" operation instructs the test runner to assert that the given session is pinned to a mongos:

```yaml
- name: assertSessionPinned
  object: testRunner
  arguments:
    session: session0
```

#### assertSessionUnpinned

The "assertSessionUnpinned" operation instructs the test runner to assert that the given session is not pinned to a
mongos:

```yaml
- name: assertSessionPinned
  object: testRunner
  arguments:
    session: session0
```

#### assertCollectionExists

The "assertCollectionExists" operation instructs the test runner to assert that the given collection exists in the
database:

```yaml
- name: assertCollectionExists
  object: testRunner
  arguments:
    database: db
    collection: test
```

Use a `listCollections` command to check whether the collection exists. Note that it is currently not possible to run
`listCollections` from within a transaction.

#### assertCollectionNotExists

The "assertCollectionNotExists" operation instructs the test runner to assert that the given collection does not exist
in the database:

```yaml
- name: assertCollectionNotExists
  object: testRunner
  arguments:
    database: db
    collection: test
```

Use a `listCollections` command to check whether the collection exists. Note that it is currently not possible to run
`listCollections` from within a transaction.

#### assertIndexExists

The "assertIndexExists" operation instructs the test runner to assert that the index with the given name exists on the
collection:

```yaml
- name: assertIndexExists
  object: testRunner
  arguments:
    database: db
    collection: test
    index: t_1
```

Use a `listIndexes` command to check whether the index exists. Note that it is currently not possible to run
`listIndexes` from within a transaction.

#### assertIndexNotExists

The "assertIndexNotExists" operation instructs the test runner to assert that the index with the given name does not
exist on the collection:

```yaml
- name: assertIndexNotExists
  object: testRunner
  arguments:
    database: db
    collection: test
    index: t_1
```

Use a `listIndexes` command to check whether the index exists. Note that it is currently not possible to run
`listIndexes` from within a transaction.

### Command-Started Events

The event listener used for these tests MUST ignore the security commands listed in the Command Monitoring Spec.

#### Logical Session Id

Each command-started event in `expectations` includes an `lsid` with the value "session0" or "session1". Tests MUST
assert that the command's actual `lsid` matches the id of the correct ClientSession named `session0` or `session1`.

#### Null Values

Some command-started events in `expectations` include `null` values for top level `command` fields such as `txnNumber`,
`autocommit`, and `writeConcern`. Tests MUST assert that the actual command **omits** any field that has a `null` value
in the expected command.

#### Cursor Id

A `getMore` value of `"42"` in a command-started event is a fake cursorId that MUST be ignored. (In the Command
Monitoring Spec tests, fake cursorIds are correlated with real ones, but that is not necessary for Transactions Spec
tests.)

#### afterClusterTime

A `readConcern.afterClusterTime` value of `42` in a command-started event is a fake cluster time. Drivers MUST assert
that the actual command includes an afterClusterTime.

#### recoveryToken

A `recoveryToken` value of `42` in a command-started event is a placeholder for an arbitrary recovery token. Drivers
MUST assert that the actual command includes a "recoveryToken" field and SHOULD assert that field is a BSON document.

## Q & A

### Why do tests that run distinct sometimes fail with StaleDbVersion?

When a shard receives its first command that contains a dbVersion, the shard returns a StaleDbVersion error and the
Mongos retries the operation. In a sharded transaction, Mongos does not retry these operations and instead returns the
error to the client. For example:

```text
Command distinct failed: Transaction aa09e296-472a-494f-8334-48d57ab530b6:1 was aborted on statement 0 due to: an error from cluster data placement change :: caused by :: got stale databaseVersion response from shard sh01 at host localhost:27217 :: caused by :: don't know dbVersion.
```

To workaround this limitation, a driver test runner MUST run a non-transactional `distinct` command on each Mongos
before running any test that uses `distinct`. To ease the implementation drivers can simply run `distinct` before
*every* test.

Note that drivers can remove this workaround once [SERVER-39704](https://jira.mongodb.org/browse/SERVER-39704) is
resolved so that mongos retries this operation transparently. The `distinct` command is the only command allowed in a
sharded transaction that uses the `dbVersion` concept so it is the only command affected.

## Changelog

- 2024-02-15: Migrated from reStructuredText to Markdown.

- 2024-02-07: Moved legacy test format docs to this file from README.md.

- 2023-09-28: Add `load-balanced` to test topology requirements.

- 2022-04-22: Clarifications to `serverless` and `useMultipleMongoses`.

- 2019-05-15: Add operation level `error` field to assert any error.

- 2019-03-25: Add workaround for StaleDbVersion on distinct.

- 2019-03-01: Add top-level `runOn` field to denote server version and/or topology requirements requirements for the
    test file. Removes the `topology` top-level field, which is now expressed within `runOn` elements.

- 2019-02-28: `useMultipleMongoses: true` and non-targeted fail points are mutually exclusive.

- 2019-02-13: Modify test format for 4.2 sharded transactions, including "useMultipleMongoses", `object: testRunner`,
    the `targetedFailPoint` operation, and recoveryToken assertions.

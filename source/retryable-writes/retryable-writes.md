# Retryable Writes

- Status: Accepted
- Minimum Server Version: 3.6

______________________________________________________________________

## Abstract

MongoDB 3.6 will implement support for server sessions, which are shared resources within a cluster identified by a
session ID. Drivers compatible with MongoDB 3.6 will also implement support for client sessions, which are always
associated with a server session and will allow for certain commands to be executed within the context of a server
session.

Additionally, MongoDB 3.6 will utilize server sessions to allow some write commands to specify a transaction ID to
enforce at-most-once semantics for the write operation(s) and allow for retrying the operation if the driver fails to
obtain a write result (e.g. network error or "not writable primary" error after a replica set failover). This
specification will outline how an API for retryable write operations will be implemented in drivers. The specification
will define an option to enable retryable writes for an application and describe how a transaction ID will be provided
to write commands executed therein.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

**Transaction ID**

The transaction ID identifies the transaction as part of which the command is running. In a write command where the
client has requested retryable behavior, it is expressed by the top-level `lsid` and `txnNumber` fields. The `lsid`
component is the corresponding server session ID. which is a BSON value defined in the
[Driver Session](../sessions/driver-sessions.md) specification. The `txnNumber` component is a monotonically increasing
(per server session), positive 64-bit integer.

**ClientSession**

Driver object representing a client session, which is defined in the [Driver Session](../sessions/driver-sessions.md)
specification. This object is always associated with a server session; however, drivers will pool server sessions so
that creating a ClientSession will not always entail creation of a new server session. The name of this object MAY vary
across drivers.

**Retryable Error**

An error is considered retryable if it has a RetryableWriteError label in its top-level "errorLabels" field. See
[Determining Retryable Errors](#determining-retryable-errors) for more information.

Additional terms may be defined in the [Driver Session](../sessions/driver-sessions.md) specification.

### Naming Deviations

This specification defines the name for a new MongoClient option, `retryWrites`. Drivers MUST use the defined name for
the connection string parameter to ensure portability of connection strings across applications and drivers.

If drivers solicit MongoClient options through another mechanism (e.g. options dictionary provided to the MongoClient
constructor), drivers SHOULD use the defined name but MAY deviate to comply with their existing conventions. For
example, a driver may use `retry_writes` instead of `retryWrites`.

For any other names in the spec, drivers SHOULD use the defined name but MAY deviate to comply with their existing
conventions.

### MongoClient Configuration

This specification introduces the following client-level configuration option.

#### retryWrites

This boolean option determines whether retryable behavior will be applied to all supported write operations executed
within the MongoClient. This option MUST default to true.

This option MUST NOT be configurable at the level of a database object, collection object, or at the level of an
individual write operation.

### Requirements for Retryable Writes

#### Supported Server Versions

Like sessions, retryable writes require a MongoDB 3.6 replica set or shard cluster operating with feature compatibility
version 3.6 (i.e. the `{setFeatureCompatibilityVersion: 3.6}` administrative command has been run on the cluster).
Drivers MUST verify server eligibility by ensuring that `maxWireVersion` is at least six, the
`logicalSessionTimeoutMinutes` field is present in the server's `hello` or legacy hello response, and the server type is
not standalone.

Retryable writes are only supported by storage engines that support document-level locking. Notably, that excludes the
MMAPv1 storage engine which is available in both MongoDB 3.6 and 4.0. Since `retryWrites` defaults to `true`, Drivers
MUST raise an actionable error message when the server returns code 20 with errmsg starting with "Transaction numbers".
The replacement error message MUST be:

```text
This MongoDB deployment does not support retryable writes. Please add
retryWrites=false to your connection string.
```

If the server selected for the first attempt of a retryable write operation does not support retryable writes, drivers
MUST execute the write as if retryable writes were not enabled. Drivers MUST NOT include a transaction ID in the write
command and MUST not retry the command under any circumstances.

In a sharded cluster, it is possible that mongos may appear to support retryable writes but one or more shards in the
cluster do not (e.g. replica set shard is configured with feature compatibility version 3.4, a standalone is added as a
new shard). In these rare cases, a write command that fans out to a shard that does not support retryable writes may
partially fail and an error may be reported in the write result from mongos (e.g. `writeErrors` array in the bulk write
result). This does not constitute a retryable error. Drivers MUST relay such errors to the user.

#### Supported Write Operations

MongoDB 3.6 will support retryability for some, but not all, write operations.

Supported single-statement write operations include `insertOne()`, `updateOne()`, `replaceOne()`, `deleteOne()`,
`findOneAndDelete()`, `findOneAndReplace()`, and `findOneAndUpdate()`.

Supported multi-statement write operations include `insertMany()` and `bulkWrite()`. The ordered option may be `true` or
`false`. For both the collection-level and client-level `bulkWrite()` methods, a bulk write batch is only retryable if
it does not contain any `multi: true` writes (i.e. `UpdateMany` and `DeleteMany`). Drivers MUST evaluate eligibility for
each write command sent as part of the `bulkWrite()` (after order and batch splitting) individually. Drivers MUST NOT
alter existing logic for order and batch splitting in an attempt to maximize retryability for operations within a bulk
write.

These methods above are defined in the [CRUD](../crud/crud.md) specification.

Later versions of MongoDB may add support for additional write operations.

Drivers MUST document operations that support retryable behavior and the conditions for which retryability is determined
(see: [How will users know which operations are supported?](#how-will-users-know-which-operations-are-supported)).
Drivers are not required to exhaustively document all operations that do not support retryable behavior.

#### Unsupported Write Operations

Write commands specifying an unacknowledged write concern (e.g. `{w: 0})`) do not support retryable behavior. Drivers
MUST NOT add a transaction ID to any write command with an unacknowledged write concern executed within a MongoClient
where retryable writes have been enabled. Drivers MUST NOT retry these commands.

Write commands where a single statement might affect multiple documents will not be initially supported by MongoDB 3.6,
although this may change in the future. This includes an
[update](https://www.mongodb.com/docs/manual/reference/command/update/) command where any statement in the updates
sequence specifies a `multi` option of `true` or a
[delete](https://www.mongodb.com/docs/manual/reference/command/delete/) command where any statement in the `deletes`
sequence specifies a `limit` option of `0`. In the context of the [CRUD](../crud/crud.md) specification, this includes
the `updateMany()` and `deleteMany()` methods and, in some cases, `bulkWrite()`. Drivers MUST NOT add a transaction ID
to any single- or multi-statement write commands that include one or more multi-document write operations. Drivers MUST
NOT retry these commands if they fail to return a response. With regard to `bulkWrite()`, drivers MUST evaluate
eligibility for each write command sent as part of the `bulkWrite()` (after order and batch splitting) individually.

Write commands other than [insert](https://www.mongodb.com/docs/manual/reference/command/insert/),
[update](https://www.mongodb.com/docs/manual/reference/command/update/),
[delete](https://www.mongodb.com/docs/manual/reference/command/delete/), or
[findAndModify](https://www.mongodb.com/docs/manual/reference/command/findAndModify/) will not be initially supported by
MongoDB 3.6, although this may change in the future. This includes, but is not limited to, an
[aggregate](https://www.mongodb.com/docs/manual/reference/command/aggregate/) command using a write stage (e.g. `$out`,
`$merge`). Drivers MUST NOT add a transaction ID to these commands and MUST NOT retry these commands if they fail to
return a response.

#### Retryable Writes Within Transactions

In MongoDB 4.0 the only supported retryable write commands within a transaction are `commitTransaction` and
`abortTransaction`. Therefore drivers MUST NOT retry write commands within transactions even when `retryWrites` has been
set to true on the `MongoClient`. In addition, drivers MUST NOT add the `RetryableWriteError` label to any error that
occurs during a write command within a transaction (excepting `commitTransation` and `abortTransaction`), even when
`retryWrites` has been set to true on the `MongoClient`.

### Implementing Retryable Writes

#### Determining Retryable Errors

When connected to a MongoDB instance that supports retryable writes (versions 3.6+), the driver MUST treat all errors
with the RetryableWriteError label as retryable. This error label can be found in the top-level "errorLabels" field of
the error.

##### RetryableWriteError Labels

The RetryableWriteError label might be added to an error in a variety of ways:

- When the driver encounters a network error establishing an initial connection to a server, it MUST add a
    RetryableWriteError label to that error if the MongoClient performing the operation has the retryWrites
    configuration option set to true.

- When the driver encounters a network error communicating with any server version that supports retryable writes, it
    MUST add a RetryableWriteError label to that error if the MongoClient performing the operation has the retryWrites
    configuration option set to true.

- When a CMAP-compliant driver encounters a
    [PoolClearedError](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#connection-pool-errors)
    during connection check out, it MUST add a RetryableWriteError label to that error if the MongoClient performing the
    operation has the retryWrites configuration option set to true.

- For server versions 4.4 and newer, the server will add a RetryableWriteError label to errors or server responses that
    it considers retryable before returning them to the driver. As new server versions are released, the errors that are
    labeled with the RetryableWriteError label may change. Drivers MUST NOT add a RetryableWriteError label to any error
    derived from a 4.4+ server response (i.e. any error that is not a network error).

- When receiving a command result with an error from a pre-4.4 server that supports retryable writes, the driver MUST
    add a RetryableWriteError label to errors that meet the following criteria if the retryWrites option is set to true
    on the client performing the relevant operation:

    - a mongod or mongos response with any the following error codes in the top-level `code` field:

        | Error Name                      | Error Code |
        | ------------------------------- | ---------- |
        | InterruptedAtShutdown           | 11600      |
        | InterruptedDueToReplStateChange | 11602      |
        | NotWritablePrimary              | 10107      |
        | NotPrimaryNoSecondaryOk         | 13435      |
        | NotPrimaryOrSecondary           | 13436      |
        | PrimarySteppedDown              | 189        |
        | ShutdownInProgress              | 91         |
        | HostNotFound                    | 7          |
        | HostUnreachable                 | 6          |
        | NetworkTimeout                  | 89         |
        | SocketException                 | 9001       |
        | ExceededTimeLimit               | 262        |

    - a mongod response with any of the previously listed codes in the `writeConcernError.code` field.

    Drivers MUST NOT add a RetryableWriteError label based on the following:

    - any `writeErrors[].code` fields in a mongod or mongos response
    - the `writeConcernError.code` field in a mongos response

    The criteria for retryable errors is similar to the discussion in the SDAM spec's section on
    [Error Handling](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#error-handling), but includes
    additional error codes. See [What do the additional error codes mean?](#what-do-the-additional-error-codes-mean) for
    the reasoning behind these additional errors.

To understand why the driver should only add the RetryableWriteError label to an error when the retryWrites option is
true on the MongoClient performing the operation, see
[Why does the driver only add the RetryableWriteError label to errors that occur on a MongoClient with retryWrites set to true?](#why-does-the-driver-only-add-the-retryablewriteerror-label-to-errors-that-occur-on-a-mongoclient-with-retrywrites-set-to-true)

Note: During a retryable write operation on a sharded cluster, mongos may retry the operation internally, in which case
it will not add a RetryableWriteError label to any error that occurs after those internal retries to prevent excessive
retrying.

For more information about error labels, see the
[Transactions specification](../transactions/transactions.md#error-labels).

#### Generating Transaction IDs

The server requires each retryable write operation to provide a unique transaction ID in its command document. The
transaction ID consists of a server session ID and a monotonically increasing transaction number. The session ID is
obtained from the ClientSession object, which will have either been passed to the write operation from the application
or constructed internally for the operation. Drivers will be responsible for maintaining a monotonically increasing
transaction number for each server session used by a ClientSession object. Drivers that pool server sessions MUST
preserve the transaction number when reusing a server session from the pool with a new ClientSession (this can be
tracked as another property on the driver's object for the server session).

Drivers MUST ensure that each retryable write command specifies a transaction number larger than any previously used
transaction number for its session ID.

Since ClientSession objects are not thread safe and may only be used by one thread at a time, drivers should not need to
worry about race conditions when incrementing the transaction number.

#### Behavioral Changes for Write Commands

Drivers MUST automatically add a transaction ID to all supported write commands executed via a specific
[CRUD](../crud/crud.md) method (e.g. `updateOne()`) or write command method (e.g. `executeWriteCommand()`) within a
MongoClient where retryable writes have been enabled and when the selected server supports retryable writes.

If your driver offers a generic command method on your database object (e.g. `runCommand()`), it MUST NOT check the
user's command document to determine if it is a supported write operation and MUST NOT automatically add a transaction
ID. The method should send the user's command document to the server as-is.

This specification does not affect write commands executed within a MongoClient where retryable writes have not been
enabled.

#### Constructing Write Commands

When constructing a supported write command that will be executed within a MongoClient where retryable writes have been
enabled, drivers MUST increment the transaction number for the corresponding server session and include the server
session ID and transaction number in top-level `lsid` and `txnNumber` fields, respectively. `lsid` is a BSON value
(discussed in the [Driver Session](../sessions/driver-sessions.md) specification). `txnNumber` MUST be a positive 64-bit
integer (BSON type 0x12).

The following example illustrates a possible write command for an `updateOne()` operation:

```typescript
{
  update: "coll",
  lsid: { ... },
  txnNumber: 100,
  updates: [
    { q: { x: 1 }, u: { $inc: { y: 1 } } },
  ],
  ordered: true
}
```

When constructing multiple write commands for a multi-statement write operation (i.e. `insertMany()` and `bulkWrite()`),
drivers MUST increment the transaction number for each supported write command in the batch.

#### Executing Retryable Write Commands

When selecting a writable server for the first attempt of a retryable write command, drivers MUST allow a server
selection error to propagate. In this case, the caller is able to infer that no attempt was made.

If retryable writes is not enabled or the selected server does not support retryable writes, drivers MUST NOT include a
transaction ID in the command and MUST attempt to execute the write command exactly once and allow any errors to
propagate. In this case, the caller is able to infer that an attempt was made.

If retryable writes are enabled and the selected server supports retryable writes, drivers MUST add a transaction ID to
the command. Drivers MUST only attempt to retry a write command if the first attempt yields a retryable error. Drivers
MUST NOT attempt to retry a write command on any other error.

If the first attempt of a write command including a transaction ID encounters a retryable error, the driver MUST update
its topology according to the SDAM spec (see:
[Error Handling](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#error-handling)) and capture this
original retryable error.

Drivers MUST then retry the operation as many times as necessary until any one of the following conditions is reached:

- the operation succeeds.

- the operation fails with a non-retryable error.

- CSOT is enabled and the operation times out per
    [Client Side Operations Timeout: Retryability](../client-side-operations-timeout/client-side-operations-timeout.md#retryability).

- CSOT is not enabled and one retry was attempted.

For each retry attempt, drivers MUST select a writable server. In a sharded cluster, the server on which the operation
failed MUST be provided to the server selection mechanism as a deprioritized server.

If the driver cannot select a server for a retry attempt or the selected server does not support retryable writes,
retrying is not possible and drivers MUST raise the retryable error from the previous attempt. In both cases, the caller
is able to infer that an attempt was made.

If a retry attempt also fails, drivers MUST update their topology according to the SDAM spec (see:
[Error Handling](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#error-handling)). If an error
would not allow the caller to infer that an attempt was made (e.g. connection pool exception originating from the
driver) or the error is labeled "NoWritesPerformed", the error from the previous attempt should be raised. If all server
errors are labeled "NoWritesPerformed", then the first error should be raised.

If a driver associates server information (e.g. the server address or description) with an error, the driver MUST ensure
that the reported server information corresponds to the server that originated the error.

The above rules are implemented in the following pseudo-code:

```typescript
/**
 * Checks if a server supports retryable writes.
 */
function isRetryableWritesSupported(server) {
  if (server.getMaxWireVersion() < RETRYABLE_WIRE_VERSION) {
    return false;
  }

  if ( ! server.hasLogicalSessionTimeoutMinutes()) {
    return false;
  }

  if (server.isStandalone()) {
    return false;
  }

  return true;
}

/**
 * Executes a write command in the context of a MongoClient where retryable
 * writes have been enabled. The session parameter may be an implicit or
 * explicit client session (depending on how the CRUD method was invoked).
 */
function executeRetryableWrite(command, session) {
  /* Allow ServerSelectionException to propagate to our caller, which can then
   * assume that no attempts were made. */
  server = selectServer("writable");

  /* If the server does not support retryable writes, execute the write as if
   * retryable writes are not enabled. */
  if ( ! isRetryableWritesSupported(server)) {
    return executeCommand(server, command);
  }

  /* Incorporate lsid and txnNumber fields into the command document. These
   * values will be derived from the implicit or explicit session object. */
  retryableCommand = addTransactionIdToCommand(command, session);

  Exception previousError = null;
  retrying = false;
  while true {
    try {
      return executeCommand(server, retryableCommand);
    } catch (Exception currentError) {
      handleError(currentError);

      /* If the error has a RetryableWriteError label, remember the exception
       * and proceed with retrying the operation.
       *
       * IllegalOperation (code 20) with errmsg starting with "Transaction
       * numbers" MUST be re-raised with an actionable error message.
       */
      if (!currentError.hasErrorLabel("RetryableWriteError")) {
        if ( currentError.code == 20 && previousError.errmsg.startsWith("Transaction numbers") ) {
          currentError.errmsg = "This MongoDB deployment does not support retryable...";
        }
        throw currentError;
      }

      /*
       * If the "previousError" is "null", then the "currentError" is the
       * first error encountered during the retry attempt cycle. We must
       * persist the first error in the case where all succeeding errors are
       * labeled "NoWritesPerformed", which would otherwise raise "null" as
       * the error.
       */
      if (previousError == null) {
        previousError = currentError;
      }

      /*
       * For exceptions that originate from the driver (e.g. no socket available
       * from the connection pool), we should raise the previous error if there
       * was one.
       */
      if (currentError is not DriverException && ! previousError.hasErrorLabel("NoWritesPerformed")) {
        previousError = currentError;
      }
    }

    /*
     * We try to select server that is not the one that failed by passing the
     * failed server as a deprioritized server.
     * If we cannot select a writable server, do not proceed with retrying and
     * throw the previous error. The caller can then infer that an attempt was
     * made and failed. */
    try {
      deprioritizedServers = [ server ];
      server = selectServer("writable", deprioritizedServers);
    } catch (Exception ignoredError) {
      throw previousError;
    }

    /* If the server selected for retrying is too old, throw the previous error.
     * The caller can then infer that an attempt was made and failed. This case
     * is very rare, and likely means that the cluster is in the midst of a
     * downgrade. */
    if ( ! isRetryableWritesSupported(server)) {
      throw previousError;
    }

    if (timeoutMS == null) {
      /* If CSOT is not enabled, allow any retryable error from the second
       * attempt to propagate to our caller, as it will be just as relevant
       * (if not more relevant) than the original error. */
      if (retrying) {
        throw previousError;
      }
    } else if (isExpired(timeoutMS)) {
      /* CSOT is enabled and the operation has timed out. */
      throw previousError;
    }
    retrying = true;
  }
}
```

`handleError` in the above pseudocode refers to the function defined in the
[Error handling pseudocode](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#error-handling-pseudocode)
section of the SDAM specification.

When retrying a write command, drivers MUST resend the command with the same transaction ID. Drivers MUST NOT resend the
original wire protocol message if doing so would violate rules for
[gossipping the cluster time](../sessions/driver-sessions.md#gossipping-the-cluster-time) (see:
[Can drivers resend the same wire protocol message on retry attempts?](#can-drivers-resend-the-same-wire-protocol-message-on-retry-attempts)).

In the case of a multi-statement write operation split across multiple write commands, a failed retry attempt will also
interrupt execution of any additional write operations in the batch (regardless of the ordered option). This is no
different than if a retryable error had been encountered without retryable behavior enabled or supported by the driver.
Drivers are encouraged to provide access to an intermediary write result (e.g. BulkWriteResult, InsertManyResult)
through the BulkWriteException, in accordance with the [CRUD](../crud/crud.md) specification.

## Logging Retry Attempts

Drivers MAY choose to log retry attempts for write operations. This specification does not define a format for such log
messages.

## Command Monitoring

In accordance with the
[Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md) specification,
drivers MUST guarantee that each `CommandStartedEvent` has either a correlating `CommandSucceededEvent` or
`CommandFailedEvent` and that every "command started" log message has either a correlating "command succeeded" log
message or "command failed" log message. If the first attempt of a retryable write operation encounters a retryable
error, drivers MUST fire a `CommandFailedEvent` and emit a "command failed" log message for the retryable error and fire
a separate `CommandStartedEvent` and "command succeeded" log message when executing the subsequent retry attempt. Note
that the second `CommandStartedEvent` and "command succeeded" log message may have a different `connectionId`, since a
writable server is reselected for the retry attempt.

Each attempt of a retryable write operation SHOULD report a different `requestId` so that events for each attempt can be
properly correlated with one another.

The [Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md) specification
states that the `operationId` field is a driver-generated, 64-bit integer and may be "used to link events together such
as bulk write operations." Each attempt of a retryable write operation SHOULD report the same `operationId`; however,
drivers SHOULD NOT use the `operationId` field to relay information about a transaction ID. A bulk write operation may
consist of multiple write commands, each of which may specify a unique transaction ID.

## Test Plan

See the [README](tests/README.md) for tests.

At a high level, the test plan will cover the following scenarios for executing supported write operations within a
MongoClient where retryable writes have been enabled:

- Executing the same write operation (and transaction ID) multiple times should yield an identical write result.
- Test at-most-once behavior by observing that subsequent executions of the same write operation do not incur further
    modifications to the collection data.
- Exercise supported single-statement write operations (i.e. deleteOne, insertOne, replaceOne, updateOne, and
    findAndModify).
- Exercise supported multi-statement insertMany and bulkWrite operations, which contain only supported single-statement
    write operations. Both ordered and unordered execution should be tested.

Additional prose tests for other scenarios are also included.

## Motivation for Change

Drivers currently have no API for specifying at-most-once semantics and retryable behavior for write operations. The
driver API needs to be extended to support this behavior.

## Design Rationale

The design of this specification piggy-backs that of the [Driver Session](../sessions/driver-sessions.md) specification
in that it modifies the driver API as little as possible to introduce the concept of at-most-once semantics and
retryable behavior for write operations. A transaction ID will be included in all supported write commands executed
within the scope of a MongoClient where retryable writes have been enabled.

Drivers expect the server to yield an error if a transaction ID is included in an unsupported write command. This
requires drivers to maintain an allow list and track which write operations support retryable behavior for a given
server version (see:
[Why must drivers maintain an allow list of supported operations?](#why-must-drivers-maintain-an-allow-list-of-supported-operations)).

While this approach will allow applications to take advantage of retryable write behavior with minimal code changes, it
also presents a documentation challenge. Users must understand exactly what can and will be retried (see:
[How will users know which operations are supported?](#how-will-users-know-which-operations-are-supported)).

## Backwards Compatibility

The API changes to support retryable writes extend the existing API but do not introduce any backward breaking changes.
Existing programs that do not make use of retryable writes will continue to compile and run correctly.

## Reference Implementation

The C# and C drivers will provide reference implementations. JIRA links will be added here at a later point.

## Future Work

Supporting at-most-once semantics and retryable behavior for updateMany and deleteMany operations may become possible
once the server implements support for multi-document transactions.

A separate specification for retryable read operations could complement this specification. Retrying read operations
would not require client or server sessions and could be implemented independently of retryable writes.

## Q & A

### What do the additional error codes mean?

The errors `HostNotFound`, `HostUnreachable`, `NetworkTimeout`, `SocketException` may be returned from mongos during
problems routing to a shard. These may be transient, or localized to that mongos.

### Why are write operations only retried once by default?

The spec concerns itself with retrying write operations that encounter a retryable error (i.e. no response due to
network error or a response indicating that the node is no longer a primary). A retryable error may be classified as
either a transient error (e.g. dropped connection, replica set failover) or persistent outage. In the case of a
transient error, the driver will mark the server as "unknown" per the
[SDAM](../server-discovery-and-monitoring/server-discovery-and-monitoring.md) spec. A subsequent retry attempt will
allow the driver to rediscover the primary within the designated server selection timeout period (30 seconds by
default). If server selection times out during this retry attempt, we can reasonably assume that there is a persistent
outage. In the case of a persistent outage, multiple retry attempts are fruitless and would waste time. See
[How To Write Resilient MongoDB Applications](https://emptysqua.re/blog/how-to-write-resilient-mongodb-applications/)
for additional discussion on this strategy.

However when [Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md) is
enabled, the driver will retry multiple times until the operation succeeds, a non-retryable error is encountered, or the
timeout expires. Retrying multiple times provides greater resilience to cascading failures such as rolling server
restarts during planned maintenance events.

### What if the transaction number overflows?

Since server sessions are pooled and session lifetimes are configurable on the server, it is theoretically possible for
the transaction number to overflow if it reaches the limits of a signed 64-bit integer. The spec does not address this
scenario. Drivers may decide to handle this as they wish. For example, they may raise a client-side error if a
transaction number would overflow, eagerly remove sessions with sufficiently high transactions numbers from the pool in
an attempt to limit such occurrences, or simply rely on the server to raise an error when a transaction number is
reused.

### Why are unacknowledged write concerns unsupported?

The server does not consider the write concern when deciding if a write operation supports retryable behavior.
Technically, operations with an unacknowledged write concern can specify a transaction ID and be retried. However, the
spec elects not to support unacknowledged write concerns due to various ways that drivers may issue write operations
with unacknowledged write concerns.

When using `OP_QUERY` to issue a write command to the server, a command response is always returned. A write command
with an unacknowledged write concern (i.e. `{w: 0}`) will return a response of `{ok: 1}`. If a retryable error is
encountered (either a network error or "not writeable primary" response), the driver could attempt to retry the
operation by executing it again with the same transaction ID.

Some drivers fall back to legacy opcodes (e.g. `OP_INSERT`) to execute write operations with an unacknowledged write
concern. In the future, `OP_MSG` may allow the server to avoid returning any response for write operations sent with an
unacknowledged write concern. In both of these cases, there is no response for which the driver might encounter a
retryable error and decide to retry the operation.

Rather than depend on an implementation detail to determine if retryable behavior might apply, the spec has chosen to
not support retryable behavior for unacknowledged write concerns and guarantee a consistent user experience across all
drivers.

### Why must drivers maintain an allow list of supported operations?

Requiring that drivers maintain an allow list of supported write operations is unfortunate. It both adds complexity to
the driver's implementation and limits the driver's ability to immediately take advantage of new server functionality
(i.e. the driver must be upgraded to support additional write operations).

Several other alternatives were discussed:

- The server could inform drivers which write operations support retryable behavior in its `hello` or legacy hello
    response. This would be a form of feature discovery, for which there is no established protocol. It would also add
    complexity to the connection handshake.
- The server could ignore a transaction ID on the first observed attempt of an unsupported write command and only yield
    an error on subsequent attempts. This would require the server to create a transaction record for unsupported writes
    to avoid the risk of applying a write twice and ensuring that retry attempts could be differentiated. It also poses
    a significant problem for sharding if a multi-document write does not reach all shards, since those shards would not
    know to create a transaction record.
- The driver could allow more fine-grained control retryable write behavior by supporting a `retryWrites` option on the
    database and collection objects. This would allow users to enable `retryWrites` on a MongoClient and disable it as
    needed to execute unsupported write operations, or vice versa. Since we expect the `retryWrites` option to become
    less relevant once transactions are implemented, we would prefer not to add the option throughout the driver API.

### How will users know which operations are supported?

The initial list of supported operations is already quite permissive. Most [CRUD](../crud/crud.md) operations are
supported apart from `updateMany()`, `deleteMany()`, and `aggregate()` with a write stage (e.g. `$out`, `$merge`). Other
write operations (e.g. `renameCollection`) are rare.

That said, drivers will need to clearly document exactly which operations support retryable behavior. In the case
`bulkWrite()`, which may or may not support retryability, drivers should discuss how eligibility is determined.

### Can drivers resend the same wire protocol message on retry attempts?

Since retry attempts entail sending the same command and transaction ID to the server, drivers might consider resending
the same wire protocol message in order to avoid constructing a new message and computing its checksum. The server will
not complain if it receives two messages with the same `requestId`, as the field is only used for logging and populating
the `responseTo` field in its replies to the client. That said, re-using a wire protocol message might violate rules for
[gossipping the cluster time](../sessions/driver-sessions.md#gossipping-the-cluster-time) and might also have
implications for [Command Monitoring](#command-monitoring), since the original write command and its retry attempt may
report the same `requestId`.

### Why can't drivers split bulk write commands to maximize retryability?

In [Supported Write Operations](#supported-write-operations), the spec prohibits drivers from altering existing logic
for splits `bulkWrite()`'s `requests` parameter into write commands in an attempt to segregate unsupported,
multi-document write operations and maximize retryability for other, supported write operations. The reasoning behind
this prohibition is that such behavior would conflict with a primary goal of the bulk API in reducing the number of
command round-trips to the server.

### retryWrites originally defaulted to false, why does it now default to true?

Since the initial release of retryable writes in MongoDB 3.6 testing showed that the overhead for supported operations
was sufficiently small that there was no risk in changing the default. Additionally, the fact that some operations
continue to be unsupported for retryable writes (updateMany and deleteMany) does not seem to pose a problem in practice.

### Why do drivers have to parse errmsg to determine storage engine support?

There is no reliable way to determine the storage engine in use for shards in a sharded cluster, and replica sets (and
shards) can have mixed deployments using different storage engines on different members. This is especially true when a
replica set or sharded cluster is being upgraded from one storage engine to another. This could be common when upgrading
to MongoDB 4.2, where MMAPv1 is no longer supported.

The server returns error code 20 (IllegalOperation) when the storage engine doesn't support document-level locking and
txnNumbers. Error code 20 is used for a large number of different error cases in the server so we need some other way to
differentiate this error case from any other. The error code and errmsg are the same in MongoDB 3.6 and 4.0, and the
same from a replica set or sharded cluster (mongos just forwards the error from the shard's replica set).

### Why does the driver only add the RetryableWriteError label to errors that occur on a MongoClient with retryWrites set to true?

The driver does this to maintain consistency with the MongoDB server. Servers that support the RetryableWriteError label
(MongoDB version 4.4 and newer) only add the label to an error when the client has added a txnNumber to the command,
which only happens when the retryWrites option is true on the client. For the driver to add the label even if
retryWrites is not true would be inconsistent with the server and potentially confusing to developers.

## Changelog

- 2024-05-08: Add guidance for client-level `bulkWrite()` retryability.

- 2024-05-02: Migrated from reStructuredText to Markdown.

- 2024-04-29: Fix the link to the Driver Sessions spec.

- 2024-01-16: Do not use `writeConcernError.code` in pre-4.4 mongos response to determine retryability. Do not use
    `writeErrors[].code` in pre-4.4 server responses to determine retryability.

- 2023-12-06: Clarify that writes are not retried within transactions.

- 2023-12-05: Add that any server information associated with retryable exceptions MUST reflect the originating server,
    even in the presence of retries.

- 2023-10-02: When CSOT is not enabled, one retry attempt occurs.

- 2023-08-26: Require that in a sharded cluster the server on which the operation failed MUST be provided to the server
    selection mechanism as a deprioritized server.

- 2022-11-17: Add logic for persisting "currentError" as "previousError" on first retry attempt, avoiding raising "null"
    errors.

- 2022-11-09: CLAM must apply both events and log messages.

- 2022-10-18: When CSOT is enabled multiple retry attempts may occur.

- 2022-10-05: Remove spec front matter and reformat changelog.

- 2022-01-25: Note that drivers should retry handshake network failures.

- 2021-11-02: Clarify that error labels are only specified in a top-level field of an error.

- 2021-04-26: Replaced deprecated terminology

- 2021-03-24: Require that PoolClearedErrors be retried

- 2020-09-01: State the the driver should only add the RetryableWriteError label to network errors when connected to a
    4.4+ server.

- 2020-02-25: State that the driver should only add the RetryableWriteError label when retryWrites is on, and make it
    clear that mongos will sometimes perform internal retries and not return the RetryableWriteError label.

- 2020-02-10: Remove redundant content in Tests section.

- 2020-01-14: Add ExceededTimeLimit to the list of error codes that should receive a RetryableWriteError label.

- 2019-10-21: Change the definition of "retryable write" to be based on the RetryableWriteError label. Stop requiring
    drivers to parse errmsg to categorize retryable errors for pre-4.4 servers.

- 2019-07-30: Drivers must rewrite error messages for error code 20 when txnNumber is not supported by the storage
    engine.

- 2019-06-07: Mention `$merge` stage for aggregate alongside `$out`

- 2019-05-29: Renamed InterruptedDueToStepDown to InterruptedDueToReplStateChange

- 2019-03-06: retryWrites now defaults to true.

- 2019-03-05: Prohibit resending wire protocol messages if doing so would violate rules for gossipping the cluster time.

- 2018-06-07: WriteConcernFailed is not a retryable error code.

- 2018-04-25: Evaluate retryable eligibility of bulkWrite() commands individually.

- 2018-03-14: Clarify that retryable writes may fail with a FCV 3.4 shard.

- 2017-11-02: Drivers should not raise errors if selected server does not support retryable writes and instead fall back
    to non-retryable behavior. In addition to wire protocol version, drivers may check for
    `logicalSessionTimeoutMinutes` to determine if a server supports sessions and retryable writes.

- 2017-10-26: Errors when retrying may be raised instead of the original error provided they allow the user to infer
    that an attempt was made.

- 2017-10-23: Drivers must document operations that support retryability.

- 2017-10-23: Raise the original retryable error if server selection or wire protocol checks fail during the retry
    attempt. Encourage drivers to provide intermediary write results after an unrecoverable failure during a bulk write.

- 2017-10-18: Standalone servers do not support retryable writes.

- 2017-10-18: Also retry writes after a "not writable primary" error.

- 2017-10-08: Renamed `txnNum` to `txnNumber` and noted that it must be a 64-bit integer (BSON type 0x12).

- 2017-08-25: Drivers will maintain an allow list so that only supported write operations may be retried. Transaction
    IDs will not be included in unsupported write commands, irrespective of the `retryWrites` option.

- 2017-08-18: `retryWrites` is now a MongoClient option.

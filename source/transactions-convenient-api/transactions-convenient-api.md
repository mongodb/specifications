# Convenient API for Transactions

- Status: Accepted
- Minimum Server Version: 4.0

______________________________________________________________________

## Abstract

Reliably committing a transaction in the face of errors can be a complicated endeavor using the MongoDB 4.0 drivers API.
This specification introduces a `withTransaction` method on the ClientSession object that allows application logic to be
executed within a transaction. This method is capable of retrying either the commit operation or entire transaction as
needed (and when the error permits) to better ensure that the transaction can complete successfully.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

<span id="callback"></span>

**Callback**

A user-defined function that will be passed to the helper method defined in this specification. Depending on the
implementing language, this may be a closure, function pointer, or other callable type.

**ClientSession**

Driver object representing a client session, as defined in the [Driver Session](../sessions/driver-sessions.md)
specification. The name of this object MAY vary across drivers.

**MongoClient**

The root object of a driver's API. The name of this object MAY vary across drivers.

<span id="TransactionOptions"></span>

**TransactionOptions**

Options for `ClientSession.startTransaction`, as defined in the [Transactions](../transactions/transactions.md)
specification. The structure of these options MAY vary across drivers (e.g. dictionary, typed class).

### Naming Deviations

This specification defines the name for a new ClientSession method, `withTransaction`. Drivers SHOULD use the defined
name but MAY deviate to comply with their existing conventions. For example, a driver may use `with_transaction` instead
of `withTransaction`.

### Callback Semantics

The purpose of the callback is to allow the application to specify some sequence of operations to be executed within the
body of a transaction. In an ideal scenario, `withTransaction` will start a transaction, execute the callback, and
commit the transaction. In the event of error, the commit or entire transaction may need to be retried and thusly the
callback could be invoked multiple times.

Drivers MUST ensure that the application can access the ClientSession within the callback, since the ClientSession will
be needed to associate operations with the transaction. Drivers may elect an idiomatic approach to satisfy this
requirement (e.g. require the callback to receive the ClientSession as its first argument, expect the callback to access
the ClientSession from its lexical scope). Drivers MAY allow the callback to support additional parameters as needed
(e.g. user data parameter, error output parameter). Drivers MAY allow the callback to return a value to be propagated as
the return value of `withTransaction`.

### ClientSession Changes

This specification introduces a `withTransaction` method on the ClientSession class:

```typescript
interface ClientSession {
    withTransaction(function<any(...)> callback,
                    Optional<TransactionOptions> options,
                    ... /* other arguments as needed */): any

    // other existing members of ClientSession
}
```

#### ClientSession.withTransaction

This method is responsible for starting a transaction, invoking a callback, and committing a transaction. The callback
is expected to execute one or more operations with the transaction; however, that is not enforced. The callback is
allowed to execute other operations not associated with the transaction.

Since `withTransaction` includes logic to retry transactions and commits, drivers MUST apply timeouts per
[Client Side Operations Timeout: Convenient Transactions API](../client-side-operations-timeout/client-side-operations-timeout.md#convenient-transactions-api).
If `timeoutMS` is unset for a `withTransaction` call, drivers MUST enforce a 120-second timeout to limit retry behavior
and safeguard applications from long-running (or infinite) retry loops. Drivers SHOULD use a monotonic clock to
determine elapsed time.

If an UnknownTransactionCommitResult error is encountered for a commit, the driver MUST retry the commit if and only if
the error is not MaxTimeMSExpired and the retry timeout has not been exceeded. Otherwise, the driver MUST NOT retry the
commit and allow `withTransaction` to propagate the error to its caller.

If a TransientTransactionError is encountered at any point, the entire transaction may be retried. If the retry timeout
has not been exceeded, the driver MUST retry a transaction that fails with an error bearing the
"TransientTransactionError" label. Since retrying the entire transaction will entail invoking the callback again,
drivers MUST document that the callback may be invoked multiple times (i.e. one additional time per retry attempt) and
MUST document the risk of side effects from using a non-idempotent callback. If the retry timeout has been exceeded,
drivers MUST NOT retry the transaction and allow `withTransaction` to propagate the error to its caller. When retrying,
drivers MUST implement an exponential backoff with jitter following the algorithm described below.

If an error bearing neither the UnknownTransactionCommitResult nor the TransientTransactionError label is encountered at
any point, the driver MUST NOT retry and MUST allow `withTransaction` to propagate the error to its caller.

This method MUST receive a [callback](#callback) as its first parameter. An optional
[TransactionOptions](#TransactionOptions) MUST be provided as its second parameter (with deviations permitted as
outlined in the [CRUD](../crud/crud.md#deviations) specification). Drivers MAY support other parameters or options as
needed (e.g. user data to pass as a parameter to the callback).

##### Sequence of Actions

This method should perform the following sequence of actions:

1. Define the following:

    1. Record the current monotonic time, which will be used to enforce the 120-second / CSOT timeout before later retry
        attempts.
    2. Set `transactionAttempt` to `0`.
    3. Set `TIMEOUT_MS` to be `timeoutMS` if given, otherwise 120-seconds.

2. If `transactionAttempt` > 0:

    1. If elapsed time + `backoffMS` > `TIMEOUT_MS`, then raise the previously encountered error (see Note 1 below). If
        the elapsed time of `withTransaction` is less than TIMEOUT_MS, calculate the backoffMS to be
        `jitter * min(BACKOFF_INITIAL * 1.5 ** (transactionAttempt - 1), BACKOFF_MAX)`. sleep for `backoffMS`.

        1. jitter is a random float between \[0, 1)

        2. `transactionAttempt` is the variable defined in step 1.

        3. `BACKOFF_INITIAL` is 5ms

        4. `BACKOFF_MAX` is 500ms

3. Invoke [startTransaction](../transactions/transactions.md#starttransaction) on the session and increment
    `transactionAttempt`. If TransactionOptions were specified in the call to `withTransaction`, those MUST be used
    for `startTransaction`. Note that `ClientSession.defaultTransactionOptions` will be used in the absence of any
    explicit TransactionOptions.

4. If `startTransaction` reported an error, propagate that error to the caller of `withTransaction` and return
    immediately.

5. Invoke the callback. Drivers MUST ensure that the ClientSession can be accessed within the callback (e.g. pass
    ClientSession as the first parameter, rely on lexical scoping). Drivers MAY pass additional parameters as needed
    (e.g. user data solicited by withTransaction).

6. Control returns to `withTransaction`. Determine the current
    [state](../transactions/transactions.md#clientsession-changes) of the ClientSession and whether the callback
    reported an error (e.g. thrown exception, error output parameter).

7. If the callback reported an error:

    1. If the ClientSession is in the "starting transaction" or "transaction in progress" state, invoke
        [abortTransaction](../transactions/transactions.md#aborttransaction) on the session.

    2. If the callback's error includes a "TransientTransactionError" label, jump back to step two.

    3. If the callback's error includes a "UnknownTransactionCommitResult" label, the callback must have manually
        committed a transaction, propagate the callback's error to the caller of `withTransaction` and return
        immediately.

    4. Otherwise, propagate the callback's error (see Note 1 below) to the caller of `withTransaction` and return
        immediately.

8. If the ClientSession is in the "no transaction", "transaction aborted", or "transaction committed" state, assume the
    callback intentionally aborted or committed the transaction and return immediately.

9. Invoke [commitTransaction](../transactions/transactions.md#committransaction) on the session.

10. If `commitTransaction` reported an error:

    1. If the `commitTransaction` error includes a "UnknownTransactionCommitResult" label and the error is not
        MaxTimeMSExpired and the elapsed time of `withTransaction` is less than TIMEOUT_MS, jump back to step nine. We
        will trust `commitTransaction` to apply a majority write concern on retry attempts (see:
        [Majority write concern is used when retrying commitTransaction](#majority-write-concern-is-used-when-retrying-committransaction)).

    2. If the `commitTransaction` error includes a "TransientTransactionError" label, jump back to step two.

    3. Otherwise, propagate the `commitTransaction` error (see Note 1 below) to the caller of `withTransaction` and
        return immediately.

11. The transaction was committed successfully. Return immediately.

______________________________________________________________________

**Note 1:** When the `TIMEOUT_MS` (calculated in step [1.3](#sequence-of-actions)) is reached we MUST report a timeout
error wrapping the last error that was encountered which triggered the retry behavior. If `timeoutMS` is set, then
timeout error is a special type which is defined in CSOT
[specification](https://github.com/mongodb/specifications/blob/master/source/client-side-operations-timeout/client-side-operations-timeout.md#errors)
, If `timeoutMS` is not set, then propagate it as timeout error if the language allows to expose the underlying error as
a cause of a timeout error (see `makeTimeoutError` below in [pseudo-code](#pseudo-code)). If timeout error is thrown
then it SHOULD expose error label(s) from the transient error.

##### Pseudo-code

This method can be expressed by the following pseudo-code:

```typescript
var BACKOFF_INITIAL = 5  // 5ms initial backoff
var BACKOFF_MAX = 500  // 500ms max backoff
withTransaction(callback, options) {
    // Note: drivers SHOULD use a monotonic clock to determine elapsed time
    var startTime = Date.now(); // milliseconds since Unix epoch
    // See the CSOT specification for information on calculating timeoutMS for a convenient transaction API call.
    var timeout = getCSOTTimeoutIfSet() ?? 120_000;
    var transactionAttempt = 0;
    var lastError = null;

    retryTransaction: while (true) {
        if (transactionAttempt > 0) {
            var backoff = Math.random() * min(BACKOFF_INITIAL * 1.5 ** (transactionAttempt - 1), 
                                              BACKOFF_MAX);

            if (Date.now() + backoff - startTime >= timeout) {
                throw makeTimeoutError(lastError);
            }
            sleep(backoff);
        }

        this.startTransaction(options); // may throw on error
        transactionAttempt += 1;

        try {
            callback(this);
        } catch (error) {
            lastError = error;
            if (this.transactionState == STARTING ||
                this.transactionState == IN_PROGRESS) {
                this.abortTransaction();
            }

            if (error.hasErrorLabel("TransientTransactionError")) {
                if (Date.now() - startTime < timeout) {
                    continue retryTransaction;
                } else {
                    throw makeTimeoutError(error)
                }
            }

            throw error;
        }

        if (this.transactionState == NO_TXN ||
            this.transactionState == COMMITTED ||
            this.transactionState == ABORTED) {
            return; // Assume callback intentionally ended the transaction
        }

        retryCommit: while (true) {
            try {
                /* We will rely on ClientSession.commitTransaction() to
                 * apply a majority write concern if commitTransaction is
                 * being retried (see: DRIVERS-601) */
                this.commitTransaction();
            } catch (error) {
                /* Note: a maxTimeMS error will have the MaxTimeMSExpired
                 * code (50) and can be reported as a top-level error or
                 * inside writeConcernError, ie:
                 * {ok:0, code: 50, codeName: "MaxTimeMSExpired"}
                 * {ok:1, writeConcernError: {code: 50, codeName: "MaxTimeMSExpired"}}
                 */
                lastError = error;
                if (Date.now() - startTime >= timeout) {
                    throw makeTimeoutError(error);
                }
                if (!isMaxTimeMSExpiredError(error) &&
                    error.hasErrorLabel("UnknownTransactionCommitResult")) {
                    continue retryCommit;
                }

                if (error.hasErrorLabel("TransientTransactionError")) {
                    continue retryTransaction;
                }

                throw error;
            }
            break; // Commit was successful
        }
        break; // Transaction was successful
    }
}

function makeTimeoutError(error) {
    return getCSOTTimeoutIfSet() != null ? createCSOTMongoTimeoutException(error) : createLegacyMongoTimeoutException(error);
}
```

### ClientSession must provide access to a MongoClient

The callback invoked by `withTransaction` is only guaranteed to receive a ClientSession parameter. Drivers MUST ensure
that it is possible to obtain a MongoClient within the callback in order to execute operations within the transaction.
Per the [Driver Session](../sessions/driver-sessions.md) specification, ClientSessions should already provide access to
a client object.

### Handling errors inside the callback

Drivers MUST document that the callback MUST NOT silently handle command errors without allowing such errors to
propagate. Command errors may abort the transaction on the server, and an attempt to commit the transaction will be
rejected with `NoSuchTransaction` error.

For example, `DuplicateKeyError` is an error that aborts a transaction on the server. If the callback catches
`DuplicateKeyError` and does not re-throw it, the driver will attempt to commit the transaction. The server will reject
the commit attempt with `NoSuchTransaction` error. This error has the "TransientTransactionError" label and the driver
will retry the commit. This will result in an infinite loop.

Drivers MUST recommend that the callback re-throw command errors if they need to be handled inside the callback. Drivers
SHOULD also recommend using Core Transaction API if a user wants to handle errors in a custom way.

## Test Plan

See the [README](tests/README.md) for tests.

## Motivation for Change

Reliably committing a transaction in the face of errors can be a complicated endeavor using the MongoDB 4.0 drivers API.
Providing helper method in the driver to execute a transaction (and retry when possible) will enable our users to make
better use of transactions in their applications.

## Design Rationale

This specification introduces a helper method on the ClientSession object that applications may optionally employ to
execute a user-defined function within a transaction. An application does not need to be modified unless it wants to
take advantage of this helper method.

### Majority write concern is used when retrying commitTransaction

Drivers should apply a majority write concern when retrying commitTransaction to guard against a transaction being
applied twice. This requirement was originally enforced in the implementation of `withTransaction`, but will now be
handled by the transaction spec itself in order to benefit applications irrespective of whether they use
`withTransaction` (see the corresponding section in the
[Transactions spec Design Rationale](../transactions/transactions.md#majority-write-concern-is-used-when-retrying-committransaction)).

### The callback function has a flexible signature

An original design considered requiring the callback to accept a ClientSession as its first parameter. That could be
superfluous for languages where the callback might already have access to ClientSession through its lexical scope.
Instead, the spec simply requires that drivers ensure the callback will be able to access the ClientSession.

Similarly, the specification does not concern itself with the return type of the callback function. If drivers allow the
callback to return a value, they may also choose to propagate that value as the return value of withTransaction.

An earlier design also considered using the callback's return value to indicate whether control should break out of
`withTransaction` (and its retry loop) and return to the application. The design allows this to be accomplished in one
of two ways:

- The callback aborts the transaction directly and returns to `withTransaction`, which will then return to its caller.
- The callback raises an error without the "TransientTransactionError" label, in which case `withTransaction` will abort
    the transaction and return to its caller.

### Applications are responsible for passing ClientSession for operations within a transaction

It remains the responsibility of the application to pass a ClientSession to all operations that should be included in a
transaction. With regard to `withTransaction`, applications are free to execute any operations within the callback,
irrespective of whether those operations are associated with the transaction.

### It is assumed that the callback will not start a new transaction on the ClientSession

Under normal circumstances, the callback should not commit the transaction nor should it start a new transaction. The
`withTransaction` method will inspect the ClientSession's transaction state after the callback returns and take the most
sensible course of action; however, it will not detect whether the callback has started a new transaction.

### The callback function may be executed multiple times

The callback may be executed any number of times. Drivers are free to encourage their users to design idempotent
callbacks.

### The commit is retried after a write concern timeout (i.e. wtimeout) error

Per the Transactions specification, drivers internally retry `commitTransaction` once if it fails due to a retryable
error (as defined in the [Retryable Writes](../retryable-writes/retryable-writes.md#terms) specification). Beyond that,
applications may manually retry `commitTransaction` if it fails with any error bearing the
[UnknownTransactionCommitResult](../transactions/transactions.md#unknowntransactioncommitresult) error label. This label
is applied for the the following errors:

- Server selection failure
- Retryable error (as defined in the [Retryable Writes](../retryable-writes/retryable-writes.md#terms) specification)
- Write concern failure or timeout (excluding UnsatisfiableWriteConcern and UnknownReplWriteConcern)
- MaxTimeMSExpired errors, ie `{ok:0, code: 50, codeName: "MaxTimeMSExpired"}` and
    `{ok:1, writeConcernError: {code: 50, codeName: "MaxTimeMSExpired"}}`.

A previous design for `withTransaction` retried for all of these errors *except* for write concern timeouts, so as not
to exceed the user's original intention for `wtimeout`. The current design of this specification no longer excludes
write concern timeouts, and simply retries `commitTransaction` within its timeout period for all errors bearing the
"UnknownTransactionCommitResult" label.

### The commit is not retried after a MaxTimeMSExpired error

This specification intentionally chooses not to retry commit operations after a MaxTimeMSExpired error as doing so would
exceed the user's original intention for `maxTimeMS`.

### The transaction and commit may be retried any number of times within a timeout period

The callback may be executed any number of times. Drivers are free to encourage their users to design idempotent
callbacks.

A previous design had no limits for retrying commits or entire transactions. The callback is always able to indicate
that `withTransaction` should return to its caller (without future retry attempts) by aborting the transaction directly;
however, that puts the onus on avoiding very long (or infinite) retry loops on the application. We expect the most
common cause of retry loops will be due to TransientTransactionErrors caused by write conflicts, as those can occur
regularly in a healthy application, as opposed to UnknownTransactionCommitResult, which would typically be caused by an
election.

In order to avoid blocking the application with infinite retry loops, `withTransaction` will cease retrying invocations
of the callback or commitTransaction if it has exceeded a fixed timeout period of 120 seconds. This limit is a
non-configurable default and is intentionally twice the value of MongoDB 4.0's default for the
[transactionLifetimeLimitSeconds](https://www.mongodb.com/docs/manual/reference/parameters/#param.transactionLifetimeLimitSeconds)
parameter (60 seconds). Applications that desire longer retry periods may call `withTransaction` additional times as
needed. Applications that desire shorter retry periods should not use this method.

### Backoff Benefits

Previously, the driver would retry transactions immediately, which is fine for low levels of contention. But, as the
server load increases, immediate retries can result in retry storms, unnecessarily further overloading the server.

Exponential backoff is well-researched and accepted backoff strategy that is simple to implement. A low initial backoff
(1-millisecond) and growth value (1.25x) were chosen specifically to mitigate latency in low levels of contention.
Empirical evidence suggests that 500-millisecond max backoff ensured that a transaction did not wait so long as to
exceed the 120-second timeout and reduced load spikes.

## Backwards Compatibility

The specification introduces a new method on the ClientSession class and does not introduce any backward breaking
changes. Existing programs that do not make use of this new method will continue to compile and run correctly.

## Reference Implementation

The C, Java, and Ruby drivers will provide reference implementations. The corresponding tickets for those
implementations may be found via [DRIVERS-556](https://jira.mongodb.org/browse/DRIVERS-556).

## Security Implication

Applications that use transaction guarantees to enforce security rules will benefit from a less error-prone API. Adding
a helper method to execute a user-defined function within a transaction has few security implications, as it only
provides an implementation of a technique already described in the MongoDB 4.0 documentation
([DRIVERS-488](https://jira.mongodb.org/browse/DRIVERS-488)).

## Changelog

- 2026-02-17: Clarify expected error when timeout is reached
    [DRIVERS-3391](https://jira.mongodb.org/browse/DRIVERS-3391).

- 2025-11-20: withTransaction applies exponential backoff when retrying.

- 2024-09-06: Migrated from reStructuredText to Markdown.

- 2023-11-22: Document error handling inside the callback.

- 2022-10-05: Remove spec front matter and reformat changelog.

- 2022-01-19: withTransaction applies timeouts per the client-side operations timeout specification.

- 2019-04-24: withTransaction does not retry when commit fails with MaxTimeMSExpired.

- 2018-02-13: withTransaction should retry commits after a wtimeout

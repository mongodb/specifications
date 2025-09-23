# Connection Monitoring and Pooling (CMAP)

______________________________________________________________________

## Introduction

Drivers MUST implement all of the following types of CMAP tests:

- Pool unit and integration tests as described in [cmap-format/README](./cmap-format/README.md)
- Pool prose tests as described below in [Prose Tests](#prose-tests)
- Logging tests as described below in [Logging Tests](#logging-tests)

## Prose Tests

The following tests have not yet been automated, but MUST still be tested:

1. All ConnectionPoolOptions MUST be specified at the MongoClient level
2. All ConnectionPoolOptions MUST be the same for all pools created by a MongoClient
3. A user MUST be able to specify all ConnectionPoolOptions via a URI string
4. A user MUST be able to subscribe to Connection Monitoring Events in a manner idiomatic to their language and driver
5. When a check out attempt fails because connection set up throws an error, assert that a ConnectionCheckOutFailedEvent
    with reason="connectionError" is emitted.

### Pending Response

Due to the complexity of managing a proxy layer, the following qualifying tests should only be run for non-ssl,
non-auth, and non-compression connections.

#### Recover Partially Read Response

This test verifies that if only part of a response was read before the timeout, the driver can drain the rest of the
response and reuse the connection for the next operation.

1. Connect to the proxy server with `maxPoolSize=1` and `direct=true`, subscribing to the following CMAP events:
    - `PendingResponseStarted`
    - `PendingResponseSucceeded`
    - `PendingResponseFailed`
    - `ConnectionClosed`
2. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:
    - `sendBytes`: We have 3 possible states here:
        1. Message size was partially read: random value between 1 and 3 inclusive
        2. Message size was read, body was not read at all: use 4
        3. Message size was read, body read partially: random value between 5 and 100 inclusive
    - `delayMS`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`
3. Assert that the operation failed with timeout error.
4. Issue another operation (e.g. another insert) and assert that it does not return an error.
5. Verify that the following sequence of events was observed:
    - `ConnectionPendingResponseStarted`
    - `ConnectionPendingResponseSucceeded`
6. Verify that NONE the following events was observed:
    - `ConnectionPendingResponseFailed`
    - `ConnectionClosed`

#### Non-destructive Aliveness Check

This test verifies that if a connection idles past the pending response window (3 seconds) after a partial header, the
aliveness check does not attempt to discard bytes from the TCP stream.

1. Connect to the proxy server with `maxPoolSize=1` and `direct=true`, subscribing to the following CMAP events:
    - `PendingResponseStarted`
    - `PendingResponseSucceeded`
    - `PendingResponseFailed`
    - `ConnectionClosed`
2. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:
    - `sendBytes`: any value between 1 and 3
    - `delayMS`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`
3. Assert that the operation failed with timeout error.
4. Sleep for 3 seconds
5. Issue another operation (e.g. another insert) and assert that it does not return an error.
6. Verify that the following sequence of events was observed:
    - `ConnectionPendingResponseStarted`
    - `ConnectionPendingResponseFailed`
    - `ConnectionPendingResponseStarted`
    - `ConnectionPendingResponseSucceeded`
7. Verify that NONE the following events was observed:
    - `ConnectionClosed`

#### Exhaust Cursors

Drivers that support the `exhaustAllowed` `OP_MSG` bit flag must ensure that responses which contain `moreToCome` will
not result in a connection being put into a "pending response" state. Drivers that don't support this behavior can skip
this prose test.

1. Configure a failpoint to block `getMore` for 500ms.
2. Insert > 2 records into the collection.
3. Create an exhaust cursor using `find` and iterate one `getMore` using `batchSize=1`.
4. Call a subsequent `getMore` on the exhaust cursor with a client-side timeout of 100ms.
5. Ensure that the `ConnectionClosed` event is emitted due to timeout.

## Logging Tests

Tests for connection pool logging can be found in the `/logging` subdirectory and are written in the
[Unified Test Format](../../unified-test-format/unified-test-format.md).

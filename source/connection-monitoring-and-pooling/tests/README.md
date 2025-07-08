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

If a connection with a pending response is idle for > 3 seconds, then drivers are expected to perform an aliveness check
by attempting a non-blocking read of 1 byte from the inbound TCP buffer. The following two cases test both a successful
read and a failed one.

Due to the complexity of managing a proxy layer, the following qualifying tests should only be run for non-ssl,
non-auth, and non-compression connections.

#### Recover Partial Header Response

This test verifies that if only part of a response header arrives before a socket timeout, the driver can drain the rest
of the response and reuse the connection for the next operation.

1. Connect to the proxy server with `maxPoolSize=1` and `direct=true`, subscribing to the following CMAP events:
    - `PendingResponseStarted`
    - `PendingResponseSucceeded`
    - `PendingResponseFailed`
    - `ConnectionClosed`
2. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:
    - `sendBytes`: any value between 1 and 3
    - `delayMS`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`
3. Issue any follow-up operation and assert that it does not return an error.
4. Verify that we've received the following events from the `insertOne` step:
    - 1x`ConnectionPendingResponseStarted`
    - 0x`ConnectionPendingResponseFailed`
    - 1x`ConnectionPendingResponseSucceeded`
    - 0x`ConnectionClosed`

#### Recover Partial Body Response

This test verifies that if only part of a response body arrives before a socket timeout, the driver can drain the rest
of the response and reuse the connection for the next operation.

1. Connect to the proxy server with `maxPoolSize=1` and `direct=true`, subscribing to the following CMAP events:
    - `PendingResponseStarted`
    - `PendingResponseSucceeded`
    - `PendingResponseFailed`
    - `ConnectionClosed`
2. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:
    - `sendBytes`: Any value > 16
    - `delayMS`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`
3. Issue any follow-up operation and assert that it does not return an error.
4. Verify that we've received the following events from the `insertOne` step:
    - 1x`ConnectionPendingResponseStarted`
    - 0x`ConnectionPendingResponseFailed`
    - 1x`ConnectionPendingResponseSucceeded`
    - 0x`ConnectionClosed`

#### Non-destructive Aliveness Check

This test verifies that if a connection idles past the driver's aliveness window (3 seconds) after a partial header, the
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
3. Sleep for 3 seconds
4. Issue any follow-up operation and assert that it does not return an error.
5. Verify that we've received the following events from the `insertOne` step:
    - 2x`ConnectionPendingResponseStarted`
    - 1x`ConnectionPendingResponseFailed`
    - 1x`ConnectionPendingResponseSucceeded`
    - 0x`ConnectionClosed`

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

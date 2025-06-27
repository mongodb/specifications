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

Due to the complexity of managing a proxy layer, the following tests should only be run for non-ssl, non-auth, and 
non-compression connections.

#### Connection Aliveness Check Fails

1. Create a direct connection with `maxPoolSize=1` to the [proxy server](https://github.com/mongodb-labs/drivers-evergreen-tools/pull/662/files) which defaults to 
    port 28017. See the associated  README.md file for more information. Subscribe to the following CMAP events:
      - `PendingResponseStarted`
      - `PendingResponseSucceeded`
      - `PendingResponseFailed`
      - `ConnectionClosed`
2. Use `db.RunCommand` to `insert` a record into the database with a timeout of 200 milliseconds. Include the following
    option to be intercepted by the proxy server: `{"proxyTest":{"actions":[{"delayMs":400},{"sendBytes":0}]}}`. This
    will instruct the proxy to:
      1. Delay the response by 400ms, causing a timeout.
      2. Withhold the response bytes indefinitely, forcing the aliveness check to fail on a subsequent operation.
3. Verify that `db.RunCommand` returns a timeout error.
4. Sleep for 3 seconds to ensure there is no time remaining in the pending response state, creating the necessary 
    condition to force an aliveness check.
5. Run an `insertOne` command and verify there it does not return an error.
6. Verify that we've recieved the following events from the `insertOne` step:
    - 1x`ConnectionPendingResponseStarted` 
    - 1x`ConnectionPendingResponseFailed`
    - 0x`ConnectionPendingResponseSucceeded` 
    - 1x`ConnectionClosed`

#### Connection Aliveness Check Succeeds

1. Create a direct connection with `maxPoolSize=1` to the [proxy server](https://github.com/mongodb-labs/drivers-evergreen-tools/pull/662/files) which defaults to 
    port 28017. See the associated  README.md file for more information. Subscribe to the following CMAP events:
      - `PendingResponseStarted`
      - `PendingResponseSucceeded`
      - `PendingResponseFailed`
      - `ConnectionClosed`
2. Use `db.RunCommand` to `insert` a record into the database with a timeout of 200 milliseconds. Include the following
    option to be intercepted by the proxy server: `{"proxyTest":{"actions":[{"delayMs":400},{"sendAll":true}]}}`. This
    will instruct the proxy to:
      1. Delay the response by 400ms, causing a timeout.
      2. Send all bytes in the response, allowing the aliveness check to succeed on a subsequent operation.
3. Verify that `db.RunCommand` returns a timeout error.
4. Sleep for 3 seconds to ensure there is no time remaining in the pending response state, creating the necessary 
    condition to force an aliveness check.
5. Run an `insertOne` command and verify there it does not return an error.
6. Verify that we've recieved the following events from the `insertOne` step:
    - 2x`ConnectionPendingResponseStarted` (one for the aliveness check, one for the retry)
    - 1x`ConnectionPendingResponseFailed` (the aliveness check is a failure to drain the connection due to a timeout)
    - 1x`ConnectionPendingResponseSucceeded` 
    - 1x`ConnectionClosed`

#### Exhaust Cursors 

Drivers that support the `exhaustAllowed` `OP_MSG` bit flag must ensure that responses which contain `moreToCome` will 
not result in a connection being put into a "pending response" state. Drivers that don't support this behavior can 
skip this prose test.

1. Configure a failpoint to block `getMore` for 500ms.
2. Insert > 2 records into the collection.
2. Create an exhaust cursor using `find` and iterate one `getMore` using `batchSize=1`.
3. Call a subsequent `getMore` on the exhaust cursor with a client-side timeout of 100ms.
4. Ensure that the `ConnectionClosed` event is emitted due to timeout.

## Logging Tests

Tests for connection pool logging can be found in the `/logging` subdirectory and are written in the
[Unified Test Format](../../unified-test-format/unified-test-format.md).

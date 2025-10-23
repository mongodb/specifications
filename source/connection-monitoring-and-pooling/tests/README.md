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

We use mongoproxy to emulate the network delays. See
[mongoproxy/README.md](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/mongoproxy/README.md)
for more details. Due to the complexity of managing a proxy layer, the following qualifying tests should only be run for
non-ssl, non-auth, and non-compression connections.

#### Recover Partially Read Response

This test verifies that if only part of a response was read before the timeout, the driver can drain the rest of the
response and reuse the connection for the next operation. This test has 3 variation, see step 4, `sendBytes` parameter.

1. Setup mongoproxy.

2. Connect to the proxy server with `maxPoolSize=1`, `direct=true`, disable read and write retryability, subscribing to
    the following CMAP events:

    - `PendingResponseStartedEvent`
    - `PendingResponseSucceededEvent`
    - `PendingResponseFailedEvent`
    - `ConnectionCreatedEvent`
    - `ConnectionClosedEvent`

3. Execute `ping` command to populate the connection pool.

4. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:

    - `sendBytes`: Depending on implementation, we have 4 test cases here (some driver could read message size only to
        determine the message size, other could read entire message header):
        1. Message size was partially read: 2
        2. Message size was read: 4
        3. Message header was read, body was not read: 16
        4. Message header was read, body read partially: 20
    - `delayMs`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`

    Example of run command payload:

    ```
    {
       insert: "coll",
       documents: [{ _id : 42 }],
       proxyTest: {
          actions: [
             { sendBytes : 2 },
             { delayMs : 400 },
             { sendAll : true },
          ]
       }
    }
    ```

5. Assert that the operation failed with timeout error.

6. Issue another operation (e.g. another insert) and assert that it does not return an error.

7. Verify that the following sequence of events was observed:

    - `ConnectionCreatedEvent`
    - `ConnectionPendingResponseStartedEvent`
    - `ConnectionPendingResponseSucceededEvent`

8. Verify that NONE the following events was observed:

    - `ConnectionPendingResponseFailedEvent`
    - `ConnectionClosedEvent`

#### Non-destructive Aliveness Check

This test verifies that if a connection idles past the pending response window (3 seconds) after a partial header, the
aliveness check does not attempt to discard bytes from the TCP stream.

1. Setup mongoproxy.

2. Connect to the proxy server with `maxPoolSize=1`, `direct=true`, disable read and write retryability, subscribing to
    the following CMAP events:

    - `PendingResponseStartedEvent`
    - `PendingResponseSucceededEvent`
    - `PendingResponseFailedEvent`
    - `ConnectionCreatedEvent`
    - `ConnectionClosedEvent`

3. Execute `ping` command to populate the connection pool.

4. Send a command (e.g. an insert) with a 200 millisecond timeout and the following `proxyTest` actions:

    - `sendBytes`: 2
    - `delayMs`: 400 ( to exceed the 200 ms timeout)
    - `sendAll`: `true`

    Example of run command payload:

    ```
    {
       insert: "coll",
       documents: [{ _id : 42 }],
       proxyTest: {
          actions: [
             { sendBytes : 2 },
             { delayMs : 400 },
             { sendAll : true },
          ]
       }
    }
    ```

5. Assert that the operation failed with timeout error.

6. Sleep for 4 seconds (to pass the 3-seconds expiration window)

7. Issue another operation (e.g. another insert) and assert that it does not return an error.

8. Verify that the following sequence of events was observed:

    - `ConnectionCreatedEvent`
    - `ConnectionPendingResponseStartedEvent`
    - `ConnectionPendingResponseSucceededEvent`

9. Verify that NONE the following events was observed:

    - `ConnectionClosedEvent`
    - `ConnectionPendingResponseFailedEvent`

#### Exhaust Cursors

Drivers that support the `exhaustAllowed` `OP_MSG` bit flag must ensure that responses which contain `moreToCome` will
not result in a connection being put into a "pending response" state. Drivers that don't support this behavior can skip
this prose test.

1. Configure a failpoint to block `getMore` for 500ms.
2. Insert > 2 records into the collection.
3. Create an exhaust cursor using `find` and iterate one `getMore` using `batchSize=1`.
4. Call a subsequent `getMore` on the exhaust cursor with a client-side timeout of 100ms.
5. Ensure that the `ConnectionClosedEvent` event is emitted due to timeout.

## Logging Tests

Tests for connection pool logging can be found in the `/logging` subdirectory and are written in the
[Unified Test Format](../../unified-test-format/unified-test-format.md).

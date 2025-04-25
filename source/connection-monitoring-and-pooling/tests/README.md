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

### Pending Response: Connection Aliveness Tests

If a connection with a pending response is idle for > 3 seconds, then drivers are expected to perform an aliveness check
by attempting a non-blocking read of 1 byte from the inbound TCP buffer. The following two cases test both a successful
read and a failed one.

#### Connection Aliveness Check Fails

1. Initialize a mock TCP listener to simulate the server-side behavior. The listener should write at least 5 bytes to
    the connection to prevent size-related errors (e.g. `0x01, 0x02, 0x03, 0x04, 0x05, 0xFF`). The response should be
    delayed by 2x the size of the socket timeout.
2. Implement a monitoring mechanism to capture the `ConnectionPendingResponseStarted` and
    `ConnectionPendingResponseFailed` events.
3. Instantiate a connection pool using the mock listener’s address, ensuring readiness without error. Attach the event
    monitor to observe the connection’s state.
4. Check out a connection from the pool and initiate a read operation with an appropriate socket timeout (e.g, 10ms)
    that will trigger a timeout due to the artificial delay of 2x the socket timeout (step 1). Ensure that the read
    operation returns a timeout error.
5. Check the connection back into the pool and sleep for 3 seconds so that the pending response state timestamp exceeds
    the pending response timeout, forcing an aliveness check.
6. Check the connection out. The aliveness check should fail since no additional bytes were added after the delay in
    step 1.
7. Verify that one event for each `ConnectionPendingResponseStarted` and `ConnectionPendingResponseFailed` was emitted.
    Also verify that the fields were correctly set for each event.

#### Connection Aliveness Check Succeeds

1. Initialize a mock TCP listener to simulate the server-side behavior. The listener should write at least 5 bytes to
    the connection to prevent size-related errors (e.g. `0x01, 0x02, 0x03, 0x04, 0x05, 0xFF`). The response should be
    delayed by 2x the size of the socket timeout. Write at least 1 additional byte after the delay so that the
    aliveness check succeeds (e.g. `0xAA`).
2. Implement a monitoring mechanism to capture the `ConnectionPendingResponseStarted` and
    `ConnectionPendingResponseSucceeded` events.
3. Instantiate a connection pool using the mock listener’s address, ensuring readiness without error. Attach the event
    monitor to observe the connection’s state.
4. Check out a connection from the pool and initiate a read operation with an appropriate socket timeout (e.g, 10ms)
    that will trigger a timeout due to the artificial delay of 2x the socket timeout (step 1). Ensure that the read
    operation returns a timeout error.
5. Check the connection back into the pool and sleep for 3 seconds so that the pending response state timestamp exceeds
    the pending response timeout, forcing an aliveness check.
6. Check the connection out. The aliveness check should succeed since no additional bytes were added after the delay in
    step 1.
7. Verify that one event for each `ConnectionPendingResponseStarted` and `ConnectionPendingResponseSucceeded` was
    emitted. Also verify that the fields were correctly set for each event.

## Logging Tests

Tests for connection pool logging can be found in the `/logging` subdirectory and are written in the
[Unified Test Format](../../unified-test-format/unified-test-format.md).
